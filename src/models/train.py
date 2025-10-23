"""
Model training script with MLflow tracking.
"""

import logging
import os
import warnings
from pathlib import Path

import joblib

# Added imports for new metrics and plotting
import mlflow
import numpy as np
import pandas as pd
import yaml
from mlflow.models import infer_signature
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

os.environ["JOBLIB_START_METHOD"] = "spawn"
warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODEL_DIR = Path(__file__).parent.parent.parent / "models"
CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "mlflow_config.yaml"
MODEL_PARAMS_PATH = (
    Path(__file__).parent.parent.parent / "configs" / "model_params.yaml"
)


def load_mlflow_config():
    """Load MLflow configuration from YAML file with environment variable substitution"""
    with open(CONFIG_PATH, "r") as file:
        content = file.read()
        # Replace environment variables in format ${VAR:default}
        import re
        def replace_env_var(match):
            var_expr = match.group(1)
            if ':' in var_expr:
                var_name, default_value = var_expr.split(':', 1)
                return os.getenv(var_name, default_value)
            else:
                return os.getenv(var_expr, '')

        content = re.sub(r'\$\{([^}]+)\}', replace_env_var, content)
        config = yaml.safe_load(content)
    return config


def load_model_params():
    """Load model parameter grid from YAML file"""
    with open(MODEL_PARAMS_PATH, "r") as file:
        params = yaml.safe_load(file)
    return params


def setup_mlflow():
    """Set up MLflow tracking"""
    config = load_mlflow_config()

    tracking_uri = config["tracking_uri"]

    # Set environment variables to help with host header resolution
    os.environ['MLFLOW_TRACKING_URI'] = tracking_uri
    os.environ['MLFLOW_TRACKING_HOST'] = 'mlflow'
    os.environ['MLFLOW_TRACKING_PORT'] = '5000'

    # Configure MLflow tracking
    mlflow.set_tracking_uri(tracking_uri)

    # Set experiment with error handling
    try:
        mlflow.set_experiment(config["experiment_name"])
        logger.info(f"MLflow tracking URI: {mlflow.get_tracking_uri()}")
        experiment = mlflow.get_experiment_by_name(config["experiment_name"])
        logger.info(f"MLflow experiment: {experiment}")
    except Exception as e:
        logger.error(f"Failed to set MLflow experiment: {e}")
        # Try to create the experiment directly
        client = mlflow.tracking.MlflowClient()
        try:
            experiment_id = client.create_experiment(config["experiment_name"])
            logger.info(f"Created new MLflow experiment with ID: {experiment_id}")
        except Exception as create_error:
            logger.error(f"Failed to create MLflow experiment: {create_error}")
            raise


def create_pipeline(classifier_type="logistic"):
    """
    Create a sklearn pipeline with TF-IDF and classifier.

    Args:
        classifier_type: Type of classifier ('logistic', 'svm', or 'rf')

    Returns:
        sklearn Pipeline
    """
    if classifier_type == "logistic":
        classifier = LogisticRegression(max_iter=1000, random_state=42)
    elif classifier_type == "svm":
        classifier = LinearSVC(random_state=42)
    elif classifier_type == "rf":
        classifier = RandomForestClassifier(random_state=42)
    else:
        raise ValueError(f"Unsupported classifier type: {classifier_type}")

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=10000, stop_words="english")),
            ("classifier", classifier),
        ]
    )

    return pipeline


def train_model(classifier_type="logistic", tune_hyperparams=True):
    """
    Train a text classification model and track with MLflow.

    Args:
        classifier_type: Type of classifier ('logistic', 'svm', or 'rf')
        tune_hyperparams: Whether to tune hyperparameters with GridSearchCV

    Returns:
        Trained model pipeline
    """
    # Set up MLflow
    setup_mlflow()

    # Create model directory
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    train_df = pd.read_csv(PROCESSED_DATA_DIR / "train.csv")
    val_df = pd.read_csv(PROCESSED_DATA_DIR / "val.csv")

    X_train = train_df["title"]
    y_train = train_df["category"]
    X_val = val_df["title"]
    y_val = val_df["category"]

    logger.info(f"Training data shape: {X_train.shape}")
    logger.info(f"Classes: {np.unique(y_train)}")

    # Create pipeline
    pipeline = create_pipeline(classifier_type)

    # Load model parameter grid
    model_params = load_model_params()

    # Start MLflow run
    with mlflow.start_run() as run:
        # Log parameters
        mlflow.log_param("classifier_type", classifier_type)
        mlflow.log_param("tune_hyperparams", tune_hyperparams)

        if tune_hyperparams:
            # Get hyperparameter grid from model_params.yaml
            param_grid = model_params.get(classifier_type, {})

            # Convert ngram_range lists to tuples if present
            if "tfidf__ngram_range" in param_grid:
                param_grid["tfidf__ngram_range"] = [
                    tuple(x) for x in param_grid["tfidf__ngram_range"]
                ]

            # Log hyperparameter search space
            for param, values in param_grid.items():
                mlflow.log_param(f"grid_{param}", values)
            # Tune hyperparameters
            logger.info("Tuning hyperparameters")
            grid_search = GridSearchCV(
                pipeline, param_grid, cv=5, scoring="f1_weighted", n_jobs=-1
            )
            grid_search.fit(X_train, y_train)

            # Use best model
            pipeline = grid_search.best_estimator_

            # Log best hyperparameters
            for param, value in grid_search.best_params_.items():
                mlflow.log_param(f"best_{param}", value)
        else:
            # Train model without tuning
            logger.info("Training model without hyperparameter tuning")
            pipeline.fit(X_train, y_train)

        # Log model and register in Model Registry
        signature = infer_signature(X_val, pipeline.predict(X_val))
        model_name = f"news_classifier_{classifier_type}"

        # Log the model
        mlflow.sklearn.log_model(
            pipeline, "model", signature=signature, registered_model_name=model_name
        )

        # Get the latest version of the model
        client = mlflow.tracking.MlflowClient()
        latest_versions = client.get_latest_versions(model_name)
        if latest_versions:
            logger.info(
                f"Model registered successfully. Latest version: {latest_versions[0].version}"
            )

        # Save model locally
        model_path = MODEL_DIR / f"news_classifier_{classifier_type}.joblib"
        joblib.dump(pipeline, model_path)
        logger.info(f"Model saved to {model_path}")

        # Evaluate on validation set
        y_pred = pipeline.predict(X_val)
        accuracy = accuracy_score(y_val, y_pred)
        f1 = f1_score(y_val, y_pred, average="weighted")
        precision = precision_score(y_val, y_pred, average="weighted", zero_division=0)
        recall = recall_score(y_val, y_pred, average="weighted", zero_division=0)

        # log metrics
        logger.info(f"Accuracy: {accuracy}")
        logger.info(f"F1 score: {f1}")
        logger.info(f"Precision: {precision}")
        logger.info(f"Recall: {recall}")

        # Log mlflow metrics
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)
        mlflow.log_metric("precision_weighted", precision)
        mlflow.log_metric("recall_weighted", recall)

        # Log log_loss and ROC AUC if possible
        if hasattr(pipeline, "predict_proba"):
            y_pred_proba = pipeline.predict_proba(X_val)
            try:
                ll = log_loss(y_val, y_pred_proba, labels=pipeline.classes_)
                mlflow.log_metric("log_loss", ll)
            except Exception as e:
                logger.warning(f"Could not calculate log loss: {e}")
            try:
                # Macro ROC AUC for multiclass, binary for binary
                if len(pipeline.classes_) > 2:
                    roc_auc = roc_auc_score(
                        y_val,
                        y_pred_proba,
                        multi_class="ovr",
                        average="macro",
                        labels=pipeline.classes_,
                    )
                else:
                    roc_auc = roc_auc_score(y_val, y_pred_proba[:, 1])
                mlflow.log_metric("roc_auc", roc_auc)
            except Exception as e:
                logger.warning(f"Could not calculate ROC AUC: {e}")

        return pipeline


if __name__ == "__main__":
    train_model(classifier_type="logistic", tune_hyperparams=True)
