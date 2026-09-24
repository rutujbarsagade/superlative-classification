"""Random Forest training for CSV classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from .evaluator import evaluate_classifier
from .preprocessing import build_feature_schema, build_preprocessor, identify_feature_types
from .validation import DatasetValidationError, validate_dataframe, validate_target_column


@dataclass(frozen=True)
class TrainingResult:
    pipeline: Pipeline
    metrics: dict
    metadata: dict
    stratified: bool


def _json_value(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    return value


def train_random_forest(
    dataframe: pd.DataFrame,
    target_column: str,
    *,
    test_size: float = 0.2,
    random_state: int = 42,
    n_estimators: int = 100,
) -> TrainingResult:
    validate_dataframe(dataframe, min_rows=10)
    validate_target_column(dataframe, target_column, test_size=test_size)

    features = dataframe.drop(columns=[target_column])
    target = dataframe[target_column]
    class_counts = target.value_counts()
    test_rows = max(1, int(len(dataframe) * test_size))
    train_rows = len(dataframe) - test_rows
    can_stratify = bool(
        class_counts.min() >= 2
        and test_rows >= len(class_counts)
        and train_rows >= len(class_counts)
    )
    if not can_stratify:
        raise DatasetValidationError(
            "Every target class must be represented in both the training and evaluation splits."
        )
    split_kwargs = {
        "test_size": test_size,
        "random_state": random_state,
        "stratify": target,
    }

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        **split_kwargs,
    )
    for column in x_train.columns:
        if x_train[column].isna().all():
            raise DatasetValidationError(
                f"Feature '{column}' has no usable values in the training split."
            )
    expected_classes = set(target.unique())
    if set(y_train.unique()) != expected_classes or set(y_test.unique()) != expected_classes:
        raise DatasetValidationError(
            "Every target class must be represented in both the training and evaluation splits."
        )
    preprocessor = build_preprocessor(x_train, target_column)
    pipeline = Pipeline(
        [
            ("preprocessor", preprocessor),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=n_estimators,
                    random_state=random_state,
                ),
            ),
        ]
    )
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    class_labels = pipeline.named_steps["classifier"].classes_
    metrics = evaluate_classifier(y_test, predictions, class_labels)
    numeric_columns, categorical_columns = identify_feature_types(x_train, target_column)
    metadata = {
        "algorithm": "RANDOM_FOREST",
        "target_column": target_column,
        "features": build_feature_schema(x_train, target_column),
        "feature_types": {
            "numerical": numeric_columns,
            "categorical": categorical_columns,
        },
        "class_labels": [_json_value(label) for label in class_labels],
        "test_size": test_size,
        "random_state": random_state,
        "n_estimators": n_estimators,
        "stratified": can_stratify,
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        "preprocessing": {
            "numeric": "SimpleImputer(constant=0)",
            "categorical": "SimpleImputer(constant=__MISSING__) + OneHotEncoder(handle_unknown=ignore)",
            "scaling": False,
        },
    }
    return TrainingResult(
        pipeline=pipeline,
        metrics=metrics,
        metadata=metadata,
        stratified=can_stratify,
    )
