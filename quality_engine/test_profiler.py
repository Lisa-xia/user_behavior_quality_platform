# ============================================================
# 文件名: quality_engine/test_profiler.py
# 用途: 完整测试 - 数据画像 + 异常检测 + 报告生成
# ============================================================

import pandas as pd
import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quality_engine.profiler import DataProfiler
from quality_engine.anomaly_detector import AnomalyDetector
from quality_engine.reporter import QualityReporter

# 构建正确的文件路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(project_root, 'output', 'raw_logs.csv')

print(f"📂 尝试读取文件: {csv_path}")

if not os.path.exists(csv_path):
    print(f"❌ 文件不存在: {csv_path}")
    print("请先运行 data_generator/log_simulator.py 生成数据")
    sys.exit(1)

df = pd.read_csv(csv_path)

print(f"📂 加载了 {len(df)} 条记录")

# ========== 1. 生成数据画像 ==========
profiler = DataProfiler(df)
profile = profiler.generate_profile()
profiler.print_summary()

# ========== 2. 运行异常检测 ==========
detector = AnomalyDetector(df, profile)
anomalies = detector.run_all_checks()

# ========== 3. 生成质量报告 ==========
reporter = QualityReporter(profile, anomalies, df)
report_path = os.path.join(project_root, 'output', 'quality_report.md')
reporter.save_report(report_path)

# ========== 4. 生成可视化看板 ==========
from quality_engine.visualizer import QualityVisualizer

print("\n📊 开始生成可视化看板...")
viz = QualityVisualizer()
viz.create_dashboard()

print(f"\n🎉 全部完成！报告已生成: {report_path}")