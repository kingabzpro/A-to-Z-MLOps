"""
Shared test configuration.

Environment variables are set *before* ``src.api.main`` is imported so the
app never tries to reach a real MLflow server during tests. The local file
store fails fast and the app falls back to "no model", which the API tests
treat as a valid state.
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("API_KEY", "test_key")
os.environ.setdefault("MLFLOW_TRACKING_URI", "file:./mlruns")
# MLflow 3 requires an explicit opt-in for the filesystem tracking backend.
os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
os.environ.setdefault("MODEL_NAME", "news_classifier_logistic")

# stress_test.py is a Locust load-test script, not a pytest module. Importing
# it triggers gevent's monkey-patching, which deadlocks the httpx TestClient.
collect_ignore = ["stress_test.py"]
