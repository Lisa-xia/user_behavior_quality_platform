# ============================================================
# 文件名: data_generator/log_simulator.py
# 用途: 模拟生成用户行为日志数据（含异常注入）
# 输出: D:\user_behavior_quality_platform\data\raw_logs.csv
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# 设置随机种子，保证每次运行结果可复现
np.random.seed(42)
random.seed(42)


def generate_logs(days=7, rows_per_day=10000):
    """
    生成用户行为日志，并故意注入异常数据
    
    参数:
        days: 生成多少天的数据
        rows_per_day: 每天生成多少条日志
    
    返回:
        df: 包含所有日志的DataFrame
    """
    
    data = []
    start_date = datetime.now() - timedelta(days=days)
    
    event_types = ['click', 'view', 'purchase']
    device_types = ['iOS', 'Android', 'Web']
    
    print(f"🚀 开始生成 {days} 天的用户行为日志（每天 {rows_per_day} 条）...")
    
    for d in range(days):
        date = start_date + timedelta(days=d)
        
        for i in range(rows_per_day):
            # ----- 正常数据生成 -----
            row = {
                'user_id': random.randint(1000, 9999),
                'session_id': f'sess_{random.randint(10000, 99999)}_{d}_{i}',
                'event_type': random.choice(event_types),
                'product_id': random.randint(1, 500),
                'event_time': (date + timedelta(seconds=random.randint(0, 86399))).strftime('%Y-%m-%d %H:%M:%S'),
                'device_type': random.choice(device_types),
                'ip': f'192.168.{random.randint(1,255)}.{random.randint(1,255)}'
            }
            
            # ----- 注入异常：5%的 product_id 为空 -----
            if random.random() < 0.05:
                row['product_id'] = None
            
            # ----- 注入异常：3%的 event_time 格式错误 -----
            if random.random() < 0.03:
                row['event_time'] = 'invalid_date_format'
            
            # ----- 注入异常：2%的 user_id 为空 -----
            if random.random() < 0.02:
                row['user_id'] = None
            
            data.append(row)
    
    df = pd.DataFrame(data)
    
    # 确保 output 目录存在
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 保存为CSV
    output_path = os.path.join(output_dir, 'raw_logs.csv')
    df.to_csv(output_path, index=False)
    
    # 打印统计信息
    print(f"✅ 数据生成完成！")
    print(f"   - 总行数: {len(df)}")
    print(f"   - 保存路径: {output_path}")
    print(f"   - 异常注入统计:")
    print(f"       - product_id 为空: {df['product_id'].isna().sum()} 条 ({df['product_id'].isna().mean()*100:.1f}%)")
    print(f"       - user_id 为空: {df['user_id'].isna().sum()} 条 ({df['user_id'].isna().mean()*100:.1f}%)")
    print(f"       - event_time 格式错误: {(df['event_time'] == 'invalid_date_format').sum()} 条 ({(df['event_time'] == 'invalid_date_format').mean()*100:.1f}%)")
    
    return df


# ================== 程序入口 ==================
if __name__ == "__main__":
    # 生成7天数据，每天1万条
    df = generate_logs(days=7, rows_per_day=10000)
    
    # 预览前5行
    print("\n📊 数据预览（前5行）:")
    print(df.head().to_string())