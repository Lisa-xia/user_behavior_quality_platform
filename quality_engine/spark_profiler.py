# ============================================================
# 文件名: quality_engine/spark_profiler.py
# 用途: 使用 PySpark 读取 Hive 表进行数据画像分析
# ============================================================

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, countDistinct
import pandas as pd


class SparkProfiler:
    def __init__(self, hive_host="localhost", hive_port=9083, db_name="user_behavior_db"):
        self.db_name = db_name
        self.spark = SparkSession.builder \
            .appName("HiveQualityEngine") \
            .config("hive.metastore.uris", f"thrift://{hive_host}:{hive_port}") \
            .config("spark.sql.warehouse.dir", "/tmp/warehouse") \
            .config("spark.sql.catalogImplementation", "hive") \
            .config("spark.sql.ansi.enabled", "false") \
            .enableHiveSupport() \
            .getOrCreate()

        self.spark.sql(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        self.spark.sql(f"USE {db_name}")
        print("Spark session started, connected to Hive Metastore successfully")

    def profile_table(self, table_name):
        df = self.spark.table(table_name)
        total_rows = df.count()

        null_counts = {}
        for c in df.columns:
            null_count = df.filter(col(c).isNull()).count()
            null_pct = round(null_count / total_rows * 100, 2) if total_rows > 0 else 0
            null_counts[c] = {"null_count": null_count, "null_pct": null_pct}

        numeric_cols = [c for c, dt in df.dtypes if dt in ('int', 'double', 'float', 'bigint')]
        numeric_stats = {}
        for c in numeric_cols:
            stats = df.select(c).describe().collect()
            row_dict = {row['summary']: row[c] for row in stats}
            numeric_stats[c] = {
                "mean": float(row_dict.get('mean', 0)),
                "std": float(row_dict.get('stddev', 0)),
                "min": float(row_dict.get('min', 0)),
                "max": float(row_dict.get('max', 0))
            }

        categorical_cols = [c for c in df.columns if c not in numeric_cols]
        unique_counts = {}
        for c in categorical_cols:
            unique_counts[c] = df.select(c).distinct().count()

        return {
            "table": table_name,
            "total_rows": total_rows,
            "null_counts": null_counts,
            "numeric_stats": numeric_stats,
            "unique_counts": unique_counts
        }

    def get_daily_summary(self, fact_table, date_col='event_time'):
        df = self.spark.table(fact_table)
        date_col_casted = col(date_col).cast("date").alias("date")
        daily = df \
            .filter(date_col_casted.isNotNull()) \
            .groupBy(date_col_casted) \
            .agg(
                count("*").alias("pv"),
                countDistinct("user_id").alias("uv")
            ) \
            .orderBy("date")
        return daily.toPandas()

    def close(self):
        self.spark.stop()