import pandas as pd

from src.train_pipeline import (
    FEATURES,
    TARGET,
    build_target_if_missing,
    normalize_columns,
    validate_feature_columns,
)


def test_normalize_columns_maps_sensor_csv_names_to_api_features():
    df = pd.DataFrame(
        {
            "soil_moisture_%": [34.0, 55.0],
            "temperature_C": [31.0, 22.0],
            "rainfall_mm": [2.0, 10.0],
            "humidity_%": [45.0, 80.0],
            "sunlight_hours": [8.0, 4.0],
        }
    )

    normalized = normalize_columns(df)

    assert all(column in normalized.columns for column in FEATURES)
    validate_feature_columns(normalized)


def test_build_target_if_missing_uses_canonical_features():
    df = pd.DataFrame(
        {
            "soil_moisture_%": [34.0, 55.0],
            "temperature_C": [31.0, 22.0],
            "rainfall_mm": [2.0, 10.0],
            "humidity_%": [45.0, 80.0],
            "sunlight_hours": [8.0, 4.0],
        }
    )

    normalized = normalize_columns(df)
    with_target = build_target_if_missing(normalized)

    assert TARGET in with_target.columns
    assert with_target[TARGET].tolist() == [1, 0]
