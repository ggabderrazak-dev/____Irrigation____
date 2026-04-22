import pandas as pd
from typing import Union

def drop_unused_columns(df):
    cols_to_drop = ["farm_id", "sensor_id", "timestamp"]
    return df.drop(columns=[col for col in cols_to_drop if col in df.columns])

def handle_missing_values(df):
    df = df.copy()
    if "irrigation_type" in df.columns:
        df["irrigation_type"] = df["irrigation_type"].fillna("Unknown")
    if "crop_disease_status" in df.columns:
        df["crop_disease_status"] = df["crop_disease_status"].fillna("Unknown")
    return df

def process_dates(df):
    import pandas as pd
    df = df.copy()
    if "sowing_date" in df.columns and "harvest_date" in df.columns:
        df["sowing_date"] = pd.to_datetime(df["sowing_date"], errors="coerce")
        df["harvest_date"] = pd.to_datetime(df["harvest_date"], errors="coerce")
        df["season_duration"] = (df["harvest_date"] - df["sowing_date"]).dt.days
        df = df.drop(columns=["sowing_date", "harvest_date"])
    return df

def encode_ordinal(df):
    df = df.copy()
    if "crop_disease_status" in df.columns:
        mapping = {"None": 0, "Mild": 1, "Severe": 2, "Unknown": -1}
        df["crop_disease_status"] = df["crop_disease_status"].map(mapping)
    return df

def encode_nominal(df):
    df = df.copy()
    categorical_cols = ["region", "crop_type", "irrigation_type", "fertilizer_type"]
    existing_cols = [col for col in categorical_cols if col in df.columns]
    df = pd.get_dummies(df, columns=existing_cols, drop_first=True)
    return df

def clean_data(df):
    import pandas as pd
    df = df.copy()
    df.replace([float("inf"), float("-inf")], pd.NA, inplace=True)
    df = df.dropna()
    return df

def scale_data(df):
    from sklearn.preprocessing import StandardScaler
    df = df.copy()
    scaler = StandardScaler()
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    return df, scaler

def detect_outliers(df: pd.DataFrame, column: str = 'soil_moisture') -> pd.DataFrame:
    """
    Detect outliers in specified column using IQR method.
    Returns DataFrame with outlier rows.
    """
    if len(df) == 0 or column not in df.columns:
        return pd.DataFrame()
    
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)].copy()
    return outliers
