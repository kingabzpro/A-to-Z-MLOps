# Repository Guidelines

## Project Structure & Module Organization
The repo centers on `src/`, where `data/` handles ingestion/validation, `models/` trains via MLflow, `api/` exposes FastAPI endpoints, and `pipelines/` defines Prefect flows. Support assets live in `configs/` (Grafana, Prometheus, hyperparameters), `k8s/` manifests, `notebooks/` for exploration, and `tests/` split into `unit/`, `integration/`, and `stress/`. Expect trained artifacts in `models/` and experiment runs in `mlruns/`.

## Build, Test, and Development Commands
Bootstrap Python deps with `uv pip install -r requirements.txt` (add `requirements-dev.txt` for tooling). Local services run through `docker-compose up -d`, `docker-compose ps`, and logs via `docker-compose logs api`. For iterative dev, run `python -m src.api.main` once `.env` mirrors `.env.example`. Monitoring stacks launch automatically in Compose; use `docker-compose down -v` for a clean reset.

## Coding Style & Naming Conventions
Python code follows Black defaults (88 chars, 4-space indents) and is validated by `flake8` plus `mypy`. Run `black src/ tests/`, `flake8 src/ tests/`, and `mypy src/` before pushing or wire them through `pre-commit run --all-files`. Name Prefect flows/tasks with snake_case, FastAPI routes with descriptive verbs (`/run_pipeline`), and configs with kebab-case YAML keys. Keep secrets out of Git; load from `.env` or `.kube-secrets`.

## Testing Guidelines
Pytest drives the suite; execute `pytest tests/ -v` for fast feedback and `pytest tests/ --cov=src --cov-report=html` before opening a PR. New features must touch matching tests in `tests/unit/` for logic and `tests/integration/` for FastAPI or pipeline boundaries. Use `tests/stress/` with `locust -f tests/stress_test.py --host=http://localhost:7860` to capture performance regressions when touching inference code. Flag flaky tests in the PR description with reproduction steps.

## Commit & Pull Request Guidelines
Recent history favors imperative, present-tense summaries without trailing periods (e.g., `Update docker-compose configuration`). Scope commits narrowly, re-running lint + pytest beforehand. Pull requests should include: concise summary, linked issue (`Fixes #123`), notes on pipelines touched, screenshots or curl output for API-visible changes, and mention of any configuration updates (e.g., `.env`, `k8s/*`). Request review from owners of the affected module and wait for green CI before merging.
