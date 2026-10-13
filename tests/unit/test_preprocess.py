"""Unit tests for the preprocessing step."""

import pandas as pd
import pytest

from src.data import preprocess


def _write_raw_csv(path, rows=60):
    categories = ["tech", "sport"]
    data = {
        "title": [f"headline number {i}" for i in range(rows)],
        "category": [categories[i % 2] for i in range(rows)],
    }
    pd.DataFrame(data).to_csv(path, sep="\t", index=False)


def test_preprocess_writes_train_val_test(tmp_path, monkeypatch):
    raw_csv = tmp_path / "raw.csv"
    _write_raw_csv(raw_csv)
    processed_dir = tmp_path / "processed"

    monkeypatch.setattr(preprocess, "RAW_CSV", raw_csv)
    monkeypatch.setattr(preprocess, "PROCESSED_DATA_DIR", processed_dir)

    preprocess.preprocess()

    for name in ("train.csv", "val.csv", "test.csv"):
        out = processed_dir / name
        assert out.exists(), f"{name} was not written"

    train = pd.read_csv(processed_dir / "train.csv")
    val = pd.read_csv(processed_dir / "val.csv")
    test = pd.read_csv(processed_dir / "test.csv")

    # 60 rows -> 80/10/10 split.
    assert len(train) == 48
    assert len(val) == 6
    assert len(test) == 6

    # Only the two expected columns survive cleaning.
    assert list(train.columns) == ["title", "category"]


def test_preprocess_drops_null_rows(tmp_path, monkeypatch):
    raw_csv = tmp_path / "raw.csv"
    rows = 20
    df = pd.DataFrame(
        {
            "title": [f"headline {i}" for i in range(rows)] + [None],
            "category": ["tech" if i % 2 == 0 else "sport" for i in range(rows)]
            + ["tech"],
        }
    )
    df.to_csv(raw_csv, sep="\t", index=False)
    processed_dir = tmp_path / "processed"

    monkeypatch.setattr(preprocess, "RAW_CSV", raw_csv)
    monkeypatch.setattr(preprocess, "PROCESSED_DATA_DIR", processed_dir)

    preprocess.preprocess()

    total = sum(
        len(pd.read_csv(processed_dir / name))
        for name in ("train.csv", "val.csv", "test.csv")
    )
    assert total == rows


def test_preprocess_without_raw_data_raises(monkeypatch):
    monkeypatch.setattr(preprocess, "RAW_CSV", None)
    with pytest.raises(FileNotFoundError):
        preprocess.preprocess()
