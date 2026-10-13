"""
Champion/challenger promotion gate.

A freshly trained model version is only promoted to the ``champion`` alias
(the alias the serving API loads) if it beats the incumbent champion on the
held-out test split. Otherwise the incumbent keeps serving.

This replaces the previous behaviour where every training run silently became
the deployed model, because the API loaded ``models:/<name>/latest``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import mlflow
import pandas as pd
import yaml
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "mlflow_config.yaml"

# Alias the API resolves at startup. Aliases replace the deprecated
# "Production"/"Staging" stages removed in MLflow 3.
CHAMPION_ALIAS = "champion"


def load_mlflow_config() -> dict:
    """Load MLflow configuration from YAML file."""
    with open(CONFIG_PATH, "r") as file:
        return yaml.safe_load(file)


def get_client() -> MlflowClient:
    """Return a client bound to the configured tracking server."""
    config = load_mlflow_config()
    # Env wins over the config file so CI/containers can override it.
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI") or config["tracking_uri"]
    mlflow.set_tracking_uri(tracking_uri)
    return MlflowClient()


def latest_version(client: MlflowClient, model_name: str) -> str | None:
    """Return the highest registered version number for a model."""
    versions = client.search_model_versions(f"name='{model_name}'")
    if not versions:
        return None
    return max(versions, key=lambda v: int(v.version)).version


def get_champion_version(
    client: MlflowClient, model_name: str, alias: str = CHAMPION_ALIAS
) -> str | None:
    """Return the version currently assigned to ``alias``, or None."""
    try:
        return client.get_model_version_by_alias(model_name, alias).version
    except MlflowException:
        return None


def load_version(model_name: str, version: str):
    """Load a specific registered version. Indirection seam for tests."""
    return mlflow.sklearn.load_model(f"models:/{model_name}/{version}")


def evaluate_on_holdout(model) -> dict:
    """Score a model on the untouched test split."""
    test_df = pd.read_csv(PROCESSED_DATA_DIR / "test.csv")
    X_test = test_df["title"]
    y_test = test_df["category"]

    y_pred = model.predict(X_test)
    return {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1_score": float(f1_score(y_test, y_pred, average="weighted")),
        "precision_weighted": float(
            precision_score(y_test, y_pred, average="weighted", zero_division=0)
        ),
        "recall_weighted": float(
            recall_score(y_test, y_pred, average="weighted", zero_division=0)
        ),
    }


def promote_if_better(
    model_name: str,
    candidate_version: str,
    metric: str = "f1_score",
    min_delta: float = 0.0,
) -> dict:
    """
    Promote ``candidate_version`` to the champion alias if it beats the
    incumbent on the holdout split by at least ``min_delta``.

    Args:
        model_name: Registered model name.
        candidate_version: Version produced by the latest training run.
        metric: Metric used for the comparison.
        min_delta: Required improvement over the incumbent champion.

    Returns:
        A decision record describing what happened.
    """
    client = get_client()
    candidate = load_version(model_name, str(candidate_version))
    candidate_metrics = evaluate_on_holdout(candidate)

    champion_version = get_champion_version(client, model_name)

    decision: dict = {
        "model_name": model_name,
        "candidate_version": str(candidate_version),
        "previous_champion": str(champion_version) if champion_version else None,
        "metric": metric,
        "min_delta": min_delta,
        "candidate_metrics": candidate_metrics,
    }

    if champion_version is None or str(champion_version) == str(candidate_version):
        promoted = True
        reason = (
            "no incumbent champion"
            if champion_version is None
            else "candidate is already the champion"
        )
    else:
        champion = load_version(model_name, str(champion_version))
        champion_metrics = evaluate_on_holdout(champion)
        decision["champion_metrics"] = champion_metrics

        promoted = candidate_metrics[metric] >= champion_metrics[metric] + min_delta
        reason = (
            f"{metric}: candidate {candidate_metrics[metric]:.4f} "
            f"vs champion {champion_metrics[metric]:.4f} "
            f"(min_delta={min_delta})"
        )

    if promoted:
        client.set_registered_model_alias(
            model_name, CHAMPION_ALIAS, str(candidate_version)
        )
        logger.info(
            "Promoted %s v%s to '%s' (%s)",
            model_name,
            candidate_version,
            CHAMPION_ALIAS,
            reason,
        )
    else:
        logger.warning(
            "Rejected %s v%s, champion v%s retained (%s)",
            model_name,
            candidate_version,
            champion_version,
            reason,
        )

    decision["promoted"] = promoted
    decision["reason"] = reason
    decision["champion_version"] = (
        str(candidate_version) if promoted else str(champion_version)
    )
    return decision


def main(model_name: str, candidate_version: str | None = None, min_delta: float = 0.0):
    """CLI entrypoint: promote the newest version if it beats the champion."""
    client = get_client()
    version = candidate_version or latest_version(client, model_name)
    if version is None:
        raise RuntimeError(f"No registered versions found for '{model_name}'")
    decision = promote_if_better(model_name, version, min_delta=min_delta)
    print(decision)
    return decision


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main("news_classifier_logistic")
