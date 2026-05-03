from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, count, max as spark_max, min as spark_min


def main() -> None:
    spark = (
        SparkSession.builder
        .appName("smart-irrigation-profile")
        .getOrCreate()
    )

    df = spark.read.csv(
        "data/Smart_Farming_Crop_Yield_2024.csv",
        header=True,
        inferSchema=True,
    )

    df.printSchema()
    df.select([count(column).alias(column) for column in df.columns]).show()

    numeric_columns = [
        field.name
        for field in df.schema.fields
        if field.dataType.simpleString() in {"int", "bigint", "double", "float"}
    ]
    for column in numeric_columns:
        df.select(
            avg(column).alias(f"avg_{column}"),
            spark_min(column).alias(f"min_{column}"),
            spark_max(column).alias(f"max_{column}"),
        ).show()

    spark.stop()


if __name__ == "__main__":
    main()
