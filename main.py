# ============================================================
# 文件名: main.py
# 用途: 智能数据质量监控平台 - 完整流程入口
# 说明: 支持命令行参数，集成统一日志系统
# 示例: python main.py --days 7 --rows 10000 --threshold 10.0
# ============================================================

import os
import sys
import argparse
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quality_engine.logger import setup_logger
from data_generator.log_simulator import generate_logs
from quality_engine.profiler import DataProfiler
from quality_engine.anomaly_detector import AnomalyDetector
from quality_engine.alert import AlertManager
from quality_engine.ai_advisor import AIAdvisor
from quality_engine.reporter import QualityReporter
from quality_engine.visualizer import QualityVisualizer


# 全局 logger
logger = None


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="智能数据质量监控平台 - 自动化数据质量保障系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                              # 使用默认参数运行
  python main.py --days 14                    # 生成14天数据
  python main.py --rows 5000                  # 每天生成5000条数据
  python main.py --threshold 5.0              # 空值率阈值设为5%
  python main.py --no-ai                      # 禁用AI功能
  python main.py --days 7 --rows 20000 --threshold 8.0
  python main.py --log-level DEBUG            # 启用调试日志
        """
    )
    
    parser.add_argument(
        "--days", 
        type=int, 
        default=7,
        help="生成数据的天数（默认: 7）"
    )
    
    parser.add_argument(
        "--rows", 
        type=int, 
        default=10000,
        help="每天生成的数据行数（默认: 10000）"
    )
    
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=10.0,
        help="空值率告警阈值（百分比，默认: 10.0）"
    )
    
    parser.add_argument(
        "--no-ai", 
        action="store_true",
        help="禁用AI智能建议功能"
    )
    
    parser.add_argument(
        "--no-viz", 
        action="store_true",
        help="禁用可视化图表生成"
    )
    
    parser.add_argument(
        "--output", 
        type=str, 
        default="./output",
        help="输出目录路径（默认: ./output）"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别（默认: INFO）"
    )
    
    return parser.parse_args()


def main():
    global logger
    
    args = parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(os.path.join(args.output, "images"), exist_ok=True)
    
    # ========== 初始化日志系统 ==========
    log_level_map = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40
    }
    logger = setup_logger(
        log_dir=args.output,
        log_level=log_level_map.get(args.log_level, 20)
    )
    
    logger.info("=" * 60)
    logger.info("🚀 智能数据质量监控平台 - 完整流程")
    logger.info(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📋 参数配置:")
    logger.info(f"   - 数据天数: {args.days} 天")
    logger.info(f"   - 每天行数: {args.rows} 条")
    logger.info(f"   - 告警阈值: {args.threshold}%")
    logger.info(f"   - AI功能: {'禁用' if args.no_ai else '启用'}")
    logger.info(f"   - 可视化: {'禁用' if args.no_viz else '启用'}")
    logger.info(f"   - 输出目录: {args.output}")
    logger.info(f"   - 日志级别: {args.log_level}")
    logger.info("=" * 60)

    # ==================== 1. 数据生成 ====================
    logger.info("📦 步骤 1/7: 生成模拟数据...")
    df = generate_logs(days=args.days, rows_per_day=args.rows)
    logger.info(f"   ✅ 生成 {len(df)} 条数据")

    # ==================== 2. 数据画像 ====================
    logger.info("📊 步骤 2/7: 数据画像分析...")
    profiler = DataProfiler(df)
    profile = profiler.generate_profile()
    # profiler.print_summary() 会输出到终端，继续保留
    profiler.print_summary()

    # ==================== 3. 异常检测 ====================
    logger.info("🔍 步骤 3/7: 异常检测...")
    detector = AnomalyDetector(df, profile)
    anomalies = detector.run_all_checks(threshold=args.threshold)

    # ==================== 4. AI 增强 ====================
    logger.info("🧠 步骤 4/7: AI 智能建议...")
    if anomalies and not args.no_ai:
        advisor = AIAdvisor()
        profile_summary = f"总行数: {profile['basic']['total_rows']}, 质量评分: {profile['quality_score']}"
        anomalies = advisor.get_suggestions(anomalies, profile_summary)
    else:
        if anomalies and args.no_ai:
            logger.info("   ⏭️ AI 功能已禁用，跳过")
        else:
            logger.info("   ✅ 无异常，跳过 AI 分析")

    # ==================== 5. 告警推送 ====================
    logger.info("📨 步骤 5/7: 告警推送...")
    alert = AlertManager()
    alert.push_alerts(anomalies, profile)

    # ==================== 6. 质量报告 ====================
    logger.info("📝 步骤 6/7: 生成质量报告...")
    reporter = QualityReporter(profile, anomalies, df)
    report_path = os.path.join(args.output, 'quality_report.md')
    reporter.save_report(report_path)

    # ==================== 7. 可视化看板 ====================
    logger.info("📊 步骤 7/7: 生成可视化看板...")
    if not args.no_viz:
        viz = QualityVisualizer()
        viz.create_dashboard(output_dir=os.path.join(args.output, 'images'))
    else:
        logger.info("   ⏭️ 可视化功能已禁用，跳过")

    # ==================== 完成 ====================
    logger.info("=" * 60)
    logger.info("✅ 全部完成！")
    logger.info(f"📄 质量报告: {args.output}/quality_report.md")
    logger.info(f"🌐 告警报告: {args.output}/alert_report.html")
    logger.info(f"📊 可视化图表: {args.output}/images/")
    logger.info(f"📋 日志文件: {args.output}/app_{datetime.now().strftime('%Y%m%d')}.log")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()