"""Unit tests for the champion/challenger promotion gate."""

import pandas as pd
import pytest

from src.models import promote


class _FakeClient:
    """Minimal stand-in for MlflowClient recording alias assignments."""

    def __init__(self):
        self.assigned = None

    def set_registered_model_alias(self, name, alias, version):
        self.assigned = (name, alias, version)


def _patch(monkeypatch, client, champion_version, metrics_by_uri):
    monkeypatch.setattr(promote, "get_client", lambda: client)
    monkeypatch.setattr(
        promote,
        "get_champion_version",
        lambda c, n, alias=promote.CHAMPION_ALIAS: champion_version,
    )
    monkeypatch.setattr(
        promote, "load_version", lambda name, version: f"models:/{name}/{version}"
    )
    monkeypatch.setattr(promote, "evaluate_on_holdout", lambda m: metrics_by_uri[m])


def test_promotes_when_no_incumbent(monkeypatch):
    client = _FakeClient()
    _patch(monkeypatch, client, None, {"models:/m/1": {"f1_score": 0.5}})

    decision = promote.promote_if_better("m", "1")

    assert decision["promoted"] is True
    assert decision["reason"] == "no incumbent champion"
    assert client.assigned == ("m", promote.CHAMPION_ALIAS, "1")


def test_promotes_better_candidate(monkeypatch):
    client = _FakeClient()
    _patch(
        monkeypatch,
        client,
        "2",
        {"models:/m/3": {"f1_score": 0.91}, "models:/m/2": {"f1_score": 0.80}},
    )

    decision = promote.promote_if_better("m", "3")

    assert decision["promoted"] is True
    assert decision["champion_version"] == "3"
    assert client.assigned == ("m", promote.CHAMPION_ALIAS, "3")


def test_rejects_worse_candidate(monkeypatch):
    client = _FakeClient()
    _patch(
        monkeypatch,
        client,
        "2",
        {"models:/m/3": {"f1_score": 0.70}, "models:/m/2": {"f1_score": 0.80}},
    )

    decision = promote.promote_if_better("m", "3")

    assert decision["promoted"] is False
    assert decision["champion_version"] == "2"
    assert client.assigned is None


def test_min_delta_blocks_marginal_improvement(monkeypatch):
    client = _FakeClient()
    _patch(
        monkeypatch,
        client,
        "2",
        {"models:/m/3": {"f1_score": 0.801}, "models:/m/2": {"f1_score": 0.800}},
    )

    decision = promote.promote_if_better("m", "3", min_delta=0.01)

    assert decision["promoted"] is False
    assert client.assigned is None


def test_latest_version_picks_highest(monkeypatch):
    class _Version:
        def __init__(self, version):
            self.version = version

    class _Client:
        def search_model_versions(self, query):
            return [_Version("1"), _Version("10"), _Version("3")]

    assert promote.latest_version(_Client(), "m") == "10"


def test_evaluate_on_holdout_scores_a_real_model(tmp_path, monkeypatch):
    processed = tmp_path / "processed"
    processed.mkdir()
    pd.DataFrame(
        {
            "title": [
                "great goal in the match",
                "the team scored again",
                "goal goal goal",
            ],
            "category": ["sport", "sport", "sport"],
        }
    ).to_csv(processed / "test.csv", index=False)
    monkeypatch.setattr(promote, "PROCESSED_DATA_DIR", processed)

    class _AlwaysSport:
        def predict(self, X):
            return ["sport"] * len(X)

    metrics = promote.evaluate_on_holdout(_AlwaysSport())

    assert metrics["accuracy"] == pytest.approx(1.0)
    assert metrics["f1_score"] == pytest.approx(1.0)
