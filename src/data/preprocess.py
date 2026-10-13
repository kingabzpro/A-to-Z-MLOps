"""
Preprocess the BBC articles dataset: clean, split, and save train/val/test sets.
"""

import os
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

DATA_DIR = Path(__file__).parent.parent.parent / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# The main CSV file in the BBC dataset is usually named 'bbc_articles.csv' or similar
RAW_CSV = next(RAW_DATA_DIR.glob("*.csv"), None)


def preprocess():
    if RAW_CSV is None:
        raise FileNotFoundError(
            "Raw BBC articles CSV not found. Please download the dataset first."
        )
    # Create the output directory here rather than relying on import-time
    # side effects, so the function is safe to call with any target path.
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(RAW_CSV, sep="\t", on_bad_lines="skip")
    # Basic cleaning: drop NA, keep only needed columns
    df = df.dropna(subset=["title", "category"])
    df = df[["title", "category"]]
    # Split into train/val/test
    train, temp = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df["category"]
    )
    val, test = train_test_split(
        temp, test_size=0.5, random_state=42, stratify=temp["category"]
    )
    train.to_csv(PROCESSED_DATA_DIR / "train.csv", index=False)
    val.to_csv(PROCESSED_DATA_DIR / "val.csv", index=False)
    test.to_csv(PROCESSED_DATA_DIR / "test.csv", index=False)
    print(f"Saved train/val/test splits to {PROCESSED_DATA_DIR}")


if __name__ == "__main__":
    preprocess()
