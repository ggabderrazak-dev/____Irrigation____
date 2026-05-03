import json
from pathlib import Path

import joblib
import mlflow
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import StandardScaler

from src.train_pipeline import FEATURES, TARGET, build_target_if_missing, normalize_columns


def main() -> None:
    data_path = Path("data/Smart_Farming_Crop_Yield_2024.csv")
    df = normalize_columns(pd.read_csv(data_path))
    df = build_target_if_missing(df).dropna(subset=FEATURES + [TARGET])

    X = df[FEATURES]
    y = df[TARGET].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y if y.nunique() > 1 else None,
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    search = GridSearchCV(
        estimator=RandomForestClassifier(random_state=42),
        param_grid={
            "n_estimators": [100, 200, 300],
            "max_depth": [None, 5, 10],
            "min_samples_split": [2, 5],
        },
        scoring="f1",
        cv=3,
        n_jobs=-1,
    )

    mlflow.set_experiment("smart-irrigation-automl")
    with mlflow.start_run(run_name="gridsearch-random-forest"):
        search.fit(X_train_scaled, y_train)
        predictions = search.best_estimator_.predict(X_test_scaled)
        metrics = {
            "accuracy": float(accuracy_score(y_test, predictions)),
            "f1": float(f1_score(y_test, predictions, zero_division=0)),
        }

        mlflow.log_params(search.best_params_)
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(search.best_estimator_, artifact_path="best_model")

    Path("models").mkdir(exist_ok=True)
    joblib.dump(search.best_estimator_, "models/model.pkl")
    joblib.dump(scaler, "models/scaler.pkl")
    Path("automl_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Best params: {search.best_params_}")
    print(f"Metrics: {metrics}")


if __name__ == "__main__":
    main()
