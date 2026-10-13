"""
News Classifier API v0.6
───────────────────────
FastAPI-based micro-service for text-classification inference.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import mlflow
import yaml
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response, Security
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from mlflow.tracking import MlflowClient
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pydantic import AliasChoices, BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ───────────────────────────────────────────────────────────────────────────────
# Settings
# ───────────────────────────────────────────────────────────────────────────────
load_dotenv()  # allow .env overrides for local dev


class Settings(BaseSettings):
    """Runtime configuration. Env var names map to fields case-insensitively."""

    model_config = SettingsConfigDict(extra="ignore")  # ignore stray env vars

    api_key: str | None = None
    model_name: str = "news_classifier_logistic"
    # Optional explicit pin. When unset (default) the API serves the
    # ``champion`` alias maintained by the promotion gate.
    model_version: str | None = None
    cache_ttl: int = 3600  # Cache TTL in seconds (1 hour)
    # Explicit alias: the field name would otherwise map to TRACKING_URI.
    tracking_uri: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MLFLOW_TRACKING_URI", "TRACKING_URI"),
    )
    # Rate limiting settings
    rate_limit_default: str = "10000/minute"
    rate_limit_predict: str = "3000/minute"
    rate_limit_batch: str = "1000/minute"

    @field_validator("model_version", mode="before")
    @classmethod
    def _coerce_version(cls, v):
        # Empty string (e.g. an unset ConfigMap key) means "no pin".
        if v is None or v == "":
            return None
        return str(v)

    @field_validator("cache_ttl", mode="before")
    @classmethod
    def _parse_cache_ttl(cls, v):
        if isinstance(v, str):
            # Remove any comments and strip whitespace
            v = v.split("#")[0].strip()
        return int(v)


settings = Settings()


# ───────────────────────────────────────────────────────────────────────────────
# Structured (JSON) logging
# ───────────────────────────────────────────────────────────────────────────────
class JsonFormatter(logging.Formatter):
    """Emit one JSON object per line so logs are queryable in production."""

    _RESERVED = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "taskName",
        "message",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Promote any structured ``extra=`` fields onto the log line.
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


configure_logging()
logger = logging.getLogger("news-api")

# Alias maintained by the promotion gate (src/models/promote.py).
CHAMPION_ALIAS = "champion"

# Paths
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR.parent.parent / "models"
CONFIG_YAML = BASE_DIR.parent.parent / "configs" / "mlflow_config.yaml"

# Shared thread pool for every CPU-bound call
EXECUTOR = ThreadPoolExecutor(max_workers=4)


# ───────────────────────────────────────────────────────────────────────────────
# In-memory timed cache
# ───────────────────────────────────────────────────────────────────────────────
class TTLCache:
    def __init__(self, ttl_seconds: int):
        self._ttl = timedelta(seconds=ttl_seconds)
        self._store: Dict[str, Tuple[datetime, dict]] = {}

    def get(self, key: str) -> Optional[dict]:
        ts_val = self._store.get(key)
        if not ts_val:
            return None
        ts, val = ts_val
        if datetime.utcnow() - ts > self._ttl:
            del self._store[key]
            return None
        return val

    def set(self, key: str, value: dict) -> None:
        self._store[key] = (datetime.utcnow(), value)


prediction_cache = TTLCache(settings.cache_ttl)


# ───────────────────────────────────────────────────────────────────────────────
# Rate Limiter
# ───────────────────────────────────────────────────────────────────────────────
def get_client_identifier(request: Request) -> str:
    """Get client identifier for rate limiting (API key or IP address)."""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key}"
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[settings.rate_limit_default],
    storage_uri="memory://",
)


# ───────────────────────────────────────────────────────────────────────────────
# Model loading helpers
# ───────────────────────────────────────────────────────────────────────────────
def _load_mlflow_cfg() -> dict:
    if CONFIG_YAML.exists():
        with CONFIG_YAML.open() as fh:
            return yaml.safe_load(fh)
    return {}


def _load_from_registry(name: str, version: str | None) -> Tuple[object, str]:
    """
    Resolve the serving model from the MLflow registry.

    Resolution order:
      1. explicit MODEL_VERSION, when configured;
      2. the ``champion`` alias set by the promotion gate;
      3. the newest registered version (last-resort fallback).
    """
    cfg = _load_mlflow_cfg()

    # Env wins over the config file so containers/CI can override the
    # hardcoded local-dev address without editing tracked config.
    uri = settings.tracking_uri or cfg.get("tracking_uri")
    if not uri:
        raise RuntimeError("MLflow tracking URI not configured")

    # Bound how long a registry outage can stall startup. MLflow's defaults
    # (7 retries x 120s) would block readiness for ~15 minutes before falling
    # back to a local model.
    os.environ.setdefault("MLFLOW_HTTP_REQUEST_TIMEOUT", "10")
    os.environ.setdefault("MLFLOW_HTTP_REQUEST_MAX_RETRIES", "2")

    mlflow.set_tracking_uri(uri)

    client = MlflowClient()

    attempts: list[Tuple[str, str]] = []
    if version and str(version).lower() not in {"", "latest", "champion"}:
        attempts.append((f"models:/{name}/{version}", str(version)))
    attempts.append((f"models:/{name}@{CHAMPION_ALIAS}", CHAMPION_ALIAS))
    attempts.append((f"models:/{name}/latest", "latest"))

    last_error: Exception | None = None
    for model_uri, label in attempts:
        try:
            logger.info("Loading model from registry: %s", model_uri)
            model = mlflow.sklearn.load_model(model_uri)
            resolved = label
            if label == CHAMPION_ALIAS:
                try:
                    resolved = str(
                        client.get_model_version_by_alias(name, CHAMPION_ALIAS).version
                    )
                except Exception:  # alias may be missing on older servers
                    pass
            return model, resolved
        except Exception as exc:
            last_error = exc
            logger.warning("Registry load failed for %s: %s", model_uri, exc)

    raise RuntimeError(
        f"Unable to load '{name}' from the model registry"
    ) from last_error


def _load_local_fallback() -> Tuple[object, str]:
    # MODELS_DIR.glob (not Path().glob) - absolute patterns are unsupported.
    local_path = next(MODELS_DIR.glob("news_classifier_*.joblib"), None)
    if not local_path:
        raise FileNotFoundError(
            f"No local model found in {MODELS_DIR} matching news_classifier_*.joblib"
        )
    logger.warning("Falling back to local model: %s", local_path)
    return joblib.load(local_path), "local"


# ───────────────────────────────────────────────────────────────────────────────
# FastAPI app & lifecycle
# ───────────────────────────────────────────────────────────────────────────────
app: FastAPI  # forward ref for typing
model: Any | None = None
model_version: str | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global model, model_version
    try:
        # MLflow first, else disk
        model, model_version = await asyncio.to_thread(
            _load_from_registry, settings.model_name, settings.model_version
        )
    except Exception as e:
        logger.error("Registry load failed: %s", e)
        try:
            model, model_version = await asyncio.to_thread(_load_local_fallback)
        except Exception as inner:
            logger.critical("No model available: %s", inner)
            model = model_version = None
    _record_model_state()
    yield
    EXECUTOR.shutdown(wait=True)


# ------------------------------------------------------------------------------
# App description (appears in /docs and /openapi.json)
# ------------------------------------------------------------------------------
APP_DESCRIPTION = """
Async micro-service that classifies short news headlines into predefined
categories using a scikit-learn model.  
•  **/health** — liveness probe  
•  **/ready** — readiness probe (503 until a model is loaded)  
•  **/info** — model & class metadata  
•  **/predict** — JSON inference endpoint (title → category + confidence)  
•  **/predict/batch** — up to 100 titles per request  
•  Prometheus metrics exposed at **/metrics**
"""

# ------------------------------------------------------------------------------
# FastAPI app
# ------------------------------------------------------------------------------
app = FastAPI(
    title="News Classifier API",
    version="0.7",
    description=APP_DESCRIPTION,
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Metadata", "description": "Service health & model details"},
        {"name": "Inference", "description": "Predict category for a headline"},
    ],
)

# Attach limiter to app state
app.state.limiter = limiter


# Rate limit error handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Handle rate limit exceeded errors with proper JSON response."""
    client_id = get_client_identifier(request)
    client_type = "api_key" if client_id.startswith("apikey:") else "ip"

    # Record metric
    metrics.rate_limit_exceeded.labels(
        endpoint=request.url.path,
        client_type=client_type,
    ).inc()

    logger.warning(
        "Rate limit exceeded for %s on endpoint %s",
        client_id,
        request.url.path,
    )

    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded",
            "retry_after": (
                str(exc.detail).split(" ")[-1] if exc.detail else "60 seconds"
            ),
        },
        headers={"Retry-After": "60"},
    )


# Static HTML/JS assets
templates_dir = BASE_DIR / "templates"
app.mount("/static", StaticFiles(directory=templates_dir), name="static")


# Prometheus metrics
class Metrics:
    _instance = None
    _initialized = False
    _registry = CollectorRegistry()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Metrics, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not Metrics._initialized:
            # Request metrics
            self.request_count = Counter(
                "http_requests_total",
                "Total number of HTTP requests",
                ["method", "endpoint", "status"],
                registry=self._registry,
            )

            self.request_latency = Histogram(
                "http_request_duration_seconds",
                "HTTP request latency in seconds",
                ["method", "endpoint"],
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
                registry=self._registry,
            )

            # Cache metrics
            self.cache_hits = Counter(
                "prediction_cache_hits_total",
                "Total number of cache hits for predictions",
                ["category"],
                registry=self._registry,
            )

            self.cache_misses = Counter(
                "prediction_cache_misses_total",
                "Total number of cache misses for predictions",
                ["category"],
                registry=self._registry,
            )

            # Prediction metrics
            self.prediction_counter = Counter(
                "news_predictions_total",
                "Total number of predictions made",
                ["category"],
                registry=self._registry,
            )

            self.prediction_confidence = Histogram(
                "news_prediction_confidence",
                "Confidence scores of predictions",
                ["category"],
                buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                registry=self._registry,
            )

            self.prediction_rate = Gauge(
                "news_prediction_rate",
                "Current prediction rate per category",
                ["category"],
                registry=self._registry,
            )

            # Rate limiting metrics
            self.rate_limit_exceeded = Counter(
                "rate_limit_exceeded_total",
                "Total number of rate limit exceeded errors",
                ["endpoint", "client_type"],
                registry=self._registry,
            )

            # Serving-state metrics
            self.model_loaded = Gauge(
                "model_loaded",
                "1 when a model is loaded and able to serve, else 0",
                registry=self._registry,
            )
            self.model_info = Gauge(
                "model_info",
                "Serving model metadata (value is always 1)",
                ["model_name", "model_version"],
                registry=self._registry,
            )
            Metrics._initialized = True


# Initialize metrics
metrics = Metrics()


def _record_model_state() -> None:
    """Publish serving-state gauges so alerts can fire on a model-less pod."""
    metrics.model_loaded.set(1 if model is not None else 0)
    if model is not None:
        metrics.model_info.labels(
            model_name=settings.model_name, model_version=str(model_version)
        ).set(1)


# Observability middleware: request IDs, metrics, and structured access logs
@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
    request.state.request_id = request_id

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    metrics.request_count.labels(
        method=request.method, endpoint=request.url.path, status=response.status_code
    ).inc()

    metrics.request_latency.labels(
        method=request.method, endpoint=request.url.path
    ).observe(duration)

    logger.info(
        "request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        },
    )

    response.headers["X-Request-ID"] = request_id
    return response


# Metrics endpoint
@app.get("/metrics")
async def metrics_endpoint():
    return Response(generate_latest(metrics._registry), media_type=CONTENT_TYPE_LATEST)


# ───────────────────────────────────────────────────────────────────────────────
# Auth
# ───────────────────────────────────────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(header: str = Security(api_key_header)):
    if settings.api_key and header != settings.api_key:
        detail = (
            "X-API-Key header missing" if header is None else "Invalid API key supplied"
        )
        raise HTTPException(status_code=403, detail=detail)
    return header


# ───────────────────────────────────────────────────────────────────────────────
# Schemas
# ───────────────────────────────────────────────────────────────────────────────
class NewsRequest(BaseModel):
    title: str = Field(..., min_length=3)


class BatchNewsRequest(BaseModel):
    titles: list[str] = Field(..., min_length=1, max_length=100)

    @field_validator("titles")
    def validate_titles(cls, v):
        for i, title in enumerate(v):
            if len(title) < 3:
                raise ValueError(f"Title at index {i} must be at least 3 characters")
        return v


class Prediction(BaseModel):
    category: str
    confidence: float | None = Field(None, ge=0, le=1)


class BatchPredictionItem(BaseModel):
    title: str
    category: str | None = None
    confidence: float | None = Field(None, ge=0, le=1)
    error: str | None = None


class BatchPrediction(BaseModel):
    predictions: list[BatchPredictionItem]
    total: int
    successful: int
    failed: int


class Info(BaseModel):
    model_loaded: bool
    model_name: str | None = None
    model_version: str | None = None
    classes: list[str] | None = None


# ───────────────────────────────────────────────────────────────────────────────
# Helper: run sync in threadpool
# ───────────────────────────────────────────────────────────────────────────────
async def _run_blocking(func, *args):
    return await asyncio.to_thread(func, *args)


# ───────────────────────────────────────────────────────────────────────────────
# End-points
# ───────────────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Metadata"])
async def health() -> dict:
    """
    Liveness probe: the process is up.

    Deliberately independent of model state so a model-less pod is restarted
    only when the process itself is wedged.
    """
    return {"status": "ok"}


@app.get("/ready", tags=["Metadata"])
async def ready() -> JSONResponse:
    """
    Readiness probe: 503 until a model is loaded and able to serve.

    Kubernetes should route traffic based on this, not on /health.
    """
    if model is None:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "model not loaded"},
        )
    return JSONResponse(
        status_code=200,
        content={
            "status": "ready",
            "model_name": settings.model_name,
            "model_version": model_version,
        },
    )


@app.get("/info", response_model=Info, tags=["Metadata"])
@limiter.limit(settings.rate_limit_default)
async def info(request: Request) -> Info:
    return Info(
        model_loaded=model is not None,
        model_name=settings.model_name if model else None,
        model_version=model_version,
        classes=list(getattr(model, "classes_", [])) if model else None,
    )


@app.post(
    "/predict",
    response_model=Prediction,
    tags=["Inference"],
    dependencies=[Depends(get_api_key)],
)
@limiter.limit(settings.rate_limit_predict)
async def predict(request: Request, req: NewsRequest) -> Prediction:
    if model is None:
        raise HTTPException(status_code=503, detail="Model not available")

    cached = prediction_cache.get(req.title)
    if cached:
        # Record cache hit
        metrics.cache_hits.labels(category=cached["category"]).inc()
        # Record prediction metrics for cache hits too
        metrics.prediction_counter.labels(category=cached["category"]).inc()
        if cached["confidence"] is not None:
            metrics.prediction_confidence.labels(category=cached["category"]).observe(
                cached["confidence"]
            )
        metrics.prediction_rate.labels(category=cached["category"]).inc()
        return Prediction(**cached)

    try:
        pred = await _run_blocking(model.predict, [req.title])
        cat = pred[0]
        conf = None
        if hasattr(model, "predict_proba"):
            proba = await _run_blocking(model.predict_proba, [req.title])
            conf = float(proba[0].max())

            # Record cache miss
            metrics.cache_misses.labels(category=cat).inc()

            # Record prediction metrics
            metrics.prediction_counter.labels(category=cat).inc()
            if conf is not None:
                metrics.prediction_confidence.labels(category=cat).observe(conf)
            metrics.prediction_rate.labels(category=cat).inc()

        result = {"category": cat, "confidence": conf}
        prediction_cache.set(req.title, result)
        return Prediction(**result)
    except Exception as e:
        logger.exception("Inference failure")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post(
    "/predict/batch",
    response_model=BatchPrediction,
    tags=["Inference"],
    dependencies=[Depends(get_api_key)],
)
@limiter.limit(settings.rate_limit_batch)
async def predict_batch(request: Request, req: BatchNewsRequest) -> BatchPrediction:
    """Batch prediction endpoint for multiple news titles.

    Accepts up to 100 titles and returns predictions for each.
    Uses caching and processes uncached titles in a single batch for efficiency.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not available")

    results: list[BatchPredictionItem | None] = []
    uncached_titles: list[str] = []
    uncached_indices: list[int] = []
    successful = 0
    failed = 0

    # Check cache for each title
    for i, title in enumerate(req.titles):
        cached = prediction_cache.get(title)
        if cached:
            metrics.cache_hits.labels(category=cached["category"]).inc()
            metrics.prediction_counter.labels(category=cached["category"]).inc()
            if cached["confidence"] is not None:
                metrics.prediction_confidence.labels(
                    category=cached["category"]
                ).observe(cached["confidence"])
            results.append(
                BatchPredictionItem(
                    title=title,
                    category=cached["category"],
                    confidence=cached["confidence"],
                )
            )
            successful += 1
        else:
            results.append(None)  # Placeholder
            uncached_titles.append(title)
            uncached_indices.append(i)

    # Process uncached titles in batch
    if uncached_titles:
        try:
            preds = await _run_blocking(model.predict, uncached_titles)
            confs = None
            if hasattr(model, "predict_proba"):
                probas = await _run_blocking(model.predict_proba, uncached_titles)
                confs = [float(p.max()) for p in probas]

            for j, idx in enumerate(uncached_indices):
                title = uncached_titles[j]
                cat = preds[j]
                conf = confs[j] if confs else None

                # Record metrics
                metrics.cache_misses.labels(category=cat).inc()
                metrics.prediction_counter.labels(category=cat).inc()
                if conf is not None:
                    metrics.prediction_confidence.labels(category=cat).observe(conf)
                metrics.prediction_rate.labels(category=cat).inc()

                # Cache the result
                result = {"category": cat, "confidence": conf}
                prediction_cache.set(title, result)

                results[idx] = BatchPredictionItem(
                    title=title,
                    category=cat,
                    confidence=conf,
                )
                successful += 1

        except Exception as e:
            logger.exception("Batch inference failure")
            # Mark all uncached as failed
            for j, idx in enumerate(uncached_indices):
                results[idx] = BatchPredictionItem(
                    title=uncached_titles[j],
                    error=str(e),
                )
                failed += 1

    # Every placeholder is filled by this point (either a prediction or an
    # error), so narrowing away the None is safe.
    ordered = [item for item in results if item is not None]
    return BatchPrediction(
        predictions=ordered,
        total=len(req.titles),
        successful=successful,
        failed=failed,
    )


@app.get("/", response_class=HTMLResponse, tags=["Metadata"])
@limiter.limit(settings.rate_limit_default)
async def root(request: Request):
    return (templates_dir / "index.html").read_text()


# ───────────────────────────────────────────────────────────────────────────────
# Local dev entry-point
# ───────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="localhost",
        port=7860,
        # workers=4,
        reload=True,
        log_level="info",
    )
