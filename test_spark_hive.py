# ============================================================
# 文件名: test_spark_hive.py
# 用途: 测试 PySpark 连接 Hive，并进行数据画像和每日汇总
# ============================================================

from quality_engine.spark_profiler import SparkProfiler


if __name__ == "__main__":
    # 连接到 Hive Metastore（端口 9083）
    profiler = SparkProfiler(hive_host="localhost", hive_port=9083)
    spark = profiler.spark

    # 1. 删除表（如果存在，忽略错误）
    spark.sql("DROP TABLE IF EXISTS ods_raw_logs PURGE")
    print("✅ 旧表已尝试删除")

    # 2. 创建外部表，指定新的位置（避免目录冲突）
    spark.sql("""
        CREATE EXTERNAL TABLE IF NOT EXISTS ods_raw_logs (
            user_id STRING,
            session_id STRING,
            event_type STRING,
            product_id STRING,
            event_time STRING,
            device_type STRING,
            ip STRING
        )
        ROW FORMAT DELIMITED
        FIELDS TERMINATED BY ','
        STORED AS TEXTFILE
        LOCATION '/tmp/ods_raw_logs'
    """)
    print("✅ 外部表已创建")

    # 3. 读取 CSV 并写入表（覆盖写入）
    csv_path = "D:/user_behavior_quality_platform/output/raw_logs.csv"
    df = spark.read.option("header", "true").csv(csv_path)
    df.write.mode("overwrite").insertInto("ods_raw_logs")
    print("✅ 数据已加载到 Hive 表")

    # 4. 验证数据行数
    count = spark.sql("SELECT COUNT(*) FROM ods_raw_logs").collect()[0][0]
    print(f"✅ 表中共 {count} 条记录")

    # 5. 数据画像分析
    profile = profiler.profile_table("ods_raw_logs")
    print(f"\n📊 数据画像结果:")
    print(f"总行数: {profile['total_rows']}")
    print("空值统计:")
    for col, stats in profile['null_counts'].items():
        print(f"  {col}: {stats['null_count']} ({stats['null_pct']}%)")

    # 6. 每日汇总
    daily_df = profiler.get_daily_summary("ods_raw_logs")
    print("\n📈 每日 PV/UV:")
    print(daily_df.head(10) if not daily_df.empty else "无数据")

    profiler.close()
    print("\n✅ 测试完成！")