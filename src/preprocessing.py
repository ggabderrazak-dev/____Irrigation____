from src.utils import drop_unused_columns, handle_missing_values, process_dates, encode_ordinal, encode_nominal, clean_data, scale_data, detect_outliers
def preprocess_pipeline(df):
    df = drop_unused_columns(df)
    df = handle_missing_values(df)
    df = process_dates(df)
    df = encode_ordinal(df)
    df = encode_nominal(df)
    df = clean_data(df)
    df, scaler = scale_data(df)

    return df, scaler