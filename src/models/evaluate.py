"""
Evaluate the trained model using scikit-learn.
"""

import logging
import os
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
import seaborn as sns
import yaml
from dotenv import load_dotenv
from sklearn.metrics import (
    accuracy_score,
    auc,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.preprocessing import label_binarize

from src.models.promote import CHAMPION_ALIAS

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODEL_DIR = Path(__file__).parent.parent.parent / "models"
CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "mlflow_config.yaml"

# Load model configuration from environment variables
MODEL_NAME = os.getenv("MODEL_NAME", "news_classifier_logistic")
MODEL_VERSION = os.getenv("MODEL_VERSION", "1")


def load_mlflow_config():
    """Load MLflow configuration from YAML file"""
    with open(CONFIG_PATH, "r") as file:
        config = yaml.safe_load(file)
    return config


def load_model_from_registry(model_name: str, version: str | None = None):
    """
    Load a model from MLflow Model Registry.

    Args:
        model_name: Name of the model in the registry
        version: Specific version to load. If None, loads the latest version.

    Returns:
        Loaded model
    """
    config = load_mlflow_config()
    # Env wins over the config file so CI/containers can override it.
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI") or config["tracking_uri"])

    try:
        if version:
            model_uri = f"models:/{model_name}/{version}"
            logger.info(f"Loading model {model_name} version {version}")
        else:
            # Aliases replace the deprecated Production/Staging stages.
            model_uri = f"models:/{model_name}@{CHAMPION_ALIAS}"
            logger.info(f"Loading champion version of model {model_name}")

        model = mlflow.sklearn.load_model(model_uri)
        logger.info("Model loaded successfully from MLflow Model Registry")
        return model
    except Exception as e:
        logger.error(f"Failed to load model from MLflow: {e}")
        return None


def evaluate_model(model, X_val, y_val):
    """
    Evaluate a model and generate evaluation metrics and visualizations.

    Args:
        model: Trained model to evaluate
        X_val: Validation features
        y_val: Validation labels
    """
    y_pred = model.predict(X_val)
    acc = accuracy_score(y_val, y_pred)
    f1 = f1_score(y_val, y_pred, average="weighted")
    precision = precision_score(y_val, y_pred, average="weighted", zero_division=0)
    recall = recall_score(y_val, y_pred, average="weighted", zero_division=0)
    report_str = classification_report(y_val, y_pred)

    # Calculate log loss if possible
    log_loss_value = None
    if hasattr(model, "predict_proba"):
        try:
            y_pred_proba = model.predict_proba(X_val)
            log_loss_value = log_loss(y_val, y_pred_proba, labels=model.classes_)
        except Exception as e:
            logger.warning(f"Could not calculate log loss: {e}")

    # Confusion Matrix
    cm = confusion_matrix(y_val, y_pred, labels=np.unique(y_val))
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=np.unique(y_val),
        yticklabels=np.unique(y_val),
    )
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix")
    cm_path = MODEL_DIR / "confusion_matrix.png"
    plt.savefig(cm_path)
    plt.close()

    # ROC Curve
    roc_path = None
    roc_auc = None
    if hasattr(model, "predict_proba"):
        y_pred_proba = model.predict_proba(X_val)
        y_val_binarized = label_binarize(y_val, classes=model.classes_)
        n_classes = y_val_binarized.shape[1]
        fig_roc, ax_roc = plt.subplots()
        if n_classes > 1:
            fpr_micro, tpr_micro, _ = roc_curve(
                y_val_binarized.ravel(), y_pred_proba.ravel()
            )
            roc_auc = auc(fpr_micro, tpr_micro)
            ax_roc.plot(
                fpr_micro,
                tpr_micro,
                label=f"micro-average ROC curve (area = {roc_auc:.2f})",
                color="deeppink",
                linestyle=":",
                linewidth=4,
            )
            try:
                roc_auc_macro = roc_auc_score(
                    y_val,
                    y_pred_proba,
                    multi_class="ovr",
                    average="macro",
                    labels=model.classes_,
                )
                roc_auc = roc_auc_macro  # Use macro average for consistency
            except Exception as e:
                logger.warning(f"Could not calculate macro ROC AUC: {e}")
        elif n_classes == 1:
            positive_class_proba = (
                y_pred_proba[:, 1] if y_pred_proba.shape[1] == 2 else y_pred_proba[:, 0]
            )
            fpr_binary, tpr_binary, _ = roc_curve(
                y_val_binarized[:, 0], positive_class_proba
            )
            roc_auc = auc(fpr_binary, tpr_binary)
            ax_roc.plot(
                fpr_binary,
                tpr_binary,
                label=f"ROC curve (area = {roc_auc:.2f})",
                color="blue",
                linewidth=2,
            )
        ax_roc.plot([0, 1], [0, 1], "k--")
        ax_roc.set_xlim([0.0, 1.0])
        ax_roc.set_ylim([0.0, 1.05])
        ax_roc.set_xlabel("False Positive Rate")
        ax_roc.set_ylabel("True Positive Rate")
        ax_roc.set_title("Receiver Operating Characteristic (ROC)")
        ax_roc.legend(loc="lower right")
        roc_path = MODEL_DIR / "roc_auc_curves.png"
        fig_roc.savefig(roc_path)
        plt.close(fig_roc)
    else:
        logger.info(
            "Model does not support predict_proba. Skipping log loss and ROC AUC."
        )

    # Markdown Report
    md_path = MODEL_DIR / "model_evaluation_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Model Evaluation Report\n\n")

        # Overall Metrics
        f.write("## Overall Metrics\n\n")
        f.write(f"- **Accuracy:** {acc:.4f}\n")
        f.write(f"- **F1 Score (weighted):** {f1:.4f}\n")
        f.write(f"- **Precision (weighted):** {precision:.4f}\n")
        f.write(f"- **Recall (weighted):** {recall:.4f}\n")
        if log_loss_value is not None:
            f.write(f"- **Log Loss:** {log_loss_value:.4f}\n")
        if roc_auc is not None:
            f.write(f"- **ROC AUC:** {roc_auc:.4f}\n")
        f.write("\n")

        # Per-class Metrics
        f.write("## Per-class Metrics\n\n")
        f.write("```\n" + report_str + "\n```\n\n")

        # Visualizations
        f.write("## Visualizations\n\n")
        f.write("### Confusion Matrix\n")
        f.write(f"![Confusion Matrix]({cm_path.name})\n\n")
        if roc_path:
            f.write("### ROC Curve\n")
            f.write(f"![ROC Curve]({roc_path.name})\n\n")

        # Model Information
        f.write("## Model Information\n\n")
        f.write(f"- **Model Name:** {MODEL_NAME}\n")
        f.write(f"- **Model Version:** {MODEL_VERSION}\n")
        f.write(f"- **Classes:** {', '.join(map(str, model.classes_))}\n")
        f.write(f"- **Feature Count:** {X_val.shape[0]}\n")

    logger.info(f"Markdown evaluation report saved to {md_path}")


def main(model_name: str | None = None, version: str | None = None):
    """
    Main evaluation function that loads a model from either local storage
    or the MLflow registry.

    Args:
        model_name: Name of the model in MLflow registry. If None, loads
            from local storage.
        version: Specific version to load. If None, loads the champion.
    """
    val_df = pd.read_csv(PROCESSED_DATA_DIR / "val.csv")
    X_val = val_df["title"]
    y_val = val_df["category"]

    if model_name:
        model = load_model_from_registry(model_name, version)
    else:
        model_path = next(MODEL_DIR.glob("news_classifier_*.joblib"), None)
        if model_path is not None:
            logger.info(f"Loading model from local path: {model_path}")
            model = joblib.load(model_path)
        else:
            logger.error("No model found in local storage")
            return

    if model is not None:
        evaluate_model(model, X_val, y_val)
    else:
        logger.error("Failed to load model for evaluation")


if __name__ == "__main__":
    main(MODEL_NAME, MODEL_VERSION)
