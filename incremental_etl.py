# ============================================================
# 文件名: incremental_etl.py
# 用途: 增量 ETL 处理 + 质量检测（仅处理新增数据）
# ============================================================

import pandas as pd
import pymysql
from datetime import datetime, timedelta
import os
import sys

# 导入质量检测模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from quality_engine.profiler import DataProfiler
from quality_engine.anomaly_detector import AnomalyDetector
from quality_engine.alert import AlertManager
from quality_engine.ai_advisor import AIAdvisor


# 配置
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',  # 请修改
    'database': 'user_behavior_db',
    'charset': 'utf8mb4'
}

LAST_RUN_FILE = 'output/last_run.txt'
CSV_PATH = 'output/raw_logs.csv'


def get_last_run_time():
    """读取上次运行时间，如果不存在则返回一个很久以前的时间"""
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            return datetime.strptime(f.read().strip(), '%Y-%m-%d %H:%M:%S')
    else:
        # 首次运行，处理过去1小时的数据
        return datetime.now() - timedelta(hours=1)


def save_last_run_time(dt):
    with open(LAST_RUN_FILE, 'w') as f:
        f.write(dt.strftime('%Y-%m-%d %H:%M:%S'))


def load_new_data(csv_path, last_time):
    """从CSV加载新增数据"""
    df = pd.read_csv(csv_path)
    df['event_time'] = pd.to_datetime(df['event_time'], errors='coerce')
    # 筛选新增数据
    new_df = df[df['event_time'] > last_time].copy()
    return new_df


def process_incrementally(new_df):
    """
    对新增数据进行清洗、汇总，并执行质量检测
    简化版：这里仅做质量检测，不重新加载到MySQL（实际生产需要）
    """
    if len(new_df) == 0:
        print("✅ 无新增数据")
        return

    print(f"📊 新增 {len(new_df)} 条数据")

    # 1. 数据画像（针对新增数据）
    profiler = DataProfiler(new_df)
    profile = profiler.generate_profile()
    profiler.print_summary()

    # 2. 异常检测
    detector = AnomalyDetector(new_df, profile)
    anomalies = detector.run_all_checks()

    # 3. AI 增强
    if anomalies:
        advisor = AIAdvisor()
        profile_summary = f"总行数: {profile['basic']['total_rows']}, 质量评分: {profile['quality_score']}"
        anomalies = advisor.get_suggestions(anomalies, profile_summary)

        # 4. 告警推送
        alert = AlertManager()
        alert.push_alerts(anomalies, profile)
    else:
        print("✅ 新增数据质量良好，无异常")


def main():
    print("="*60)
    print(f"🔄 增量 ETL 启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # 1. 获取上次运行时间
    last_time = get_last_run_time()
    print(f"⏰ 上次运行时间: {last_time}")

    # 2. 加载新增数据
    if not os.path.exists(CSV_PATH):
        print("⚠️ 原始数据文件不存在，请先运行数据生成器")
        return

    new_df = load_new_data(CSV_PATH, last_time)

    # 3. 处理新增数据
    process_incrementally(new_df)

    # 4. 更新运行时间
    now = datetime.now()
    save_last_run_time(now)
    print(f"✅ 运行完成，下次将从 {now} 开始处理")


if __name__ == "__main__":
    main()