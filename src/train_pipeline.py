import json
from contextlib import nullcontext
from pathlib import Path

import joblib
import pandas as pd
import yaml
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

try:
    import mlflow
except ImportError:
    mlflow = None


FEATURES = [
    "soil_moisture",
    "temperature",
    "humidity",
    "rainfall",
    "sunlight_hours",
]
TARGET = "irrigation_needed"
CANONICAL_COLUMNS = {
    "soil_moisture_%": "soil_moisture",
    "soil_moisture_percent": "soil_moisture",
    "soil_moisture_percentage": "soil_moisture",
    "temperature_c": "temperature",
    "temperature_°c": "temperature",
    "temperature_celsius": "temperature",
    "humidity_%": "humidity",
    "humidity_percent": "humidity",
    "humidity_percentage": "humidity",
    "rainfall_mm": "rainfall",
    "rainfall_millimeters": "rainfall",
    "sunlight_hours": "sunlight_hours",
}


def load_params(path: str = "params.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)["train"]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )
    df = df.rename(columns=CANONICAL_COLUMNS)
    return df


def validate_feature_columns(df: pd.DataFrame) -> None:
    missing = [column for column in FEATURES if column not in df.columns]
    if missing:
        available = ", ".join(df.columns)
        raise ValueError(
            f"Colonnes features manquantes: {missing}. Colonnes disponibles apres normalisation: {available}"
        )


def build_target_if_missing(df: pd.DataFrame) -> pd.DataFrame:
    if TARGET in df.columns:
        return df

    validate_feature_columns(df)

    df = df.copy()
    df[TARGET] = (
        (df["soil_moisture"] < 35)
        | ((df["temperature"] > 30) & (df["rainfall"] < 5))
    ).astype(int)
    return df


def main() -> None:
    params = load_params()
    data_path = Path(params["data_path"])
    model_path = Path(params["model_path"])
    scaler_path = Path(params["scaler_path"])
    metrics_path = Path(params["metrics_path"])

    df = normalize_columns(pd.read_csv(data_path))
    validate_feature_columns(df)
    df = build_target_if_missing(df)
    df = df.dropna(subset=FEATURES + [TARGET])

    X = df[FEATURES]
    y = df[TARGET].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=float(params["test_size"]),
        random_state=int(params["random_state"]),
        stratify=y if y.nunique() > 1 else None,
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=int(params["n_estimators"]),
        random_state=int(params["random_state"]),
    )

    if mlflow is None:
        run_context = nullcontext()
    else:
        mlflow.set_experiment("smart-irrigation")
        run_context = mlflow.start_run(run_name="random-forest-irrigation")

    with run_context:
        if mlflow is not None:
            mlflow.log_params(params)

        model.fit(X_train_scaled, y_train)
        predictions = model.predict(X_test_scaled)

        metrics = {
            "accuracy": float(accuracy_score(y_test, predictions)),
            "f1": float(f1_score(y_test, predictions, zero_division=0)),
        }
        if mlflow is not None:
            mlflow.log_metrics(metrics)

        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        if mlflow is not None:
            mlflow.sklearn.log_model(model, artifact_path="model")

    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Training done. Metrics: {metrics}")


if __name__ == "__main__":
    main()
