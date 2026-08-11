# ============================================================
# 文件名: data_generator/continuous_simulator.py
# 用途: 持续生成模拟日志数据（追加模式），模拟实时数据流
# ============================================================

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os
import time


def generate_batch(batch_size=100):
    """
    生成一批新的日志数据（不含异常，保持干净）
    """
    data = []
    now = datetime.now()
    for _ in range(batch_size):
        row = {
            'user_id': random.randint(1000, 9999),
            'session_id': f'sess_{random.randint(10000, 99999)}_{int(time.time())}_{random.randint(1,100)}',
            'event_type': random.choice(['click', 'view', 'purchase']),
            'product_id': random.randint(1, 500),
            'event_time': (now - timedelta(seconds=random.randint(0, 300))).strftime('%Y-%m-%d %H:%M:%S'),
            'device_type': random.choice(['iOS', 'Android', 'Web']),
            'ip': f'192.168.{random.randint(1,255)}.{random.randint(1,255)}'
        }
        data.append(row)
    return pd.DataFrame(data)


def append_to_csv(df, filepath):
    """
    追加到CSV文件，如果文件不存在则创建并写入表头
    """
    if not os.path.exists(filepath):
        df.to_csv(filepath, index=False)
    else:
        df.to_csv(filepath, mode='a', header=False, index=False)


if __name__ == "__main__":
    # 配置
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
    CSV_PATH = os.path.join(OUTPUT_DIR, 'raw_logs.csv')
    BATCH_SIZE = 100  # 每批生成100条
    INTERVAL = 10      # 每10秒生成一批

    print(f"🚀 持续数据生成器启动，每 {INTERVAL} 秒生成 {BATCH_SIZE} 条数据")
    print(f"📁 数据将追加到: {CSV_PATH}")
    print("按 Ctrl+C 停止\n")

    try:
        while True:
            df = generate_batch(BATCH_SIZE)
            append_to_csv(df, CSV_PATH)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 追加 {len(df)} 条记录")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\n🛑 数据生成已停止")