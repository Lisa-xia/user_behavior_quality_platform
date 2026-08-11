# ============================================================
# 文件名: quality_engine/reporter.py
# 用途: 生成数据质量报告（Markdown格式）
# ============================================================

import os
import pandas as pd
from datetime import datetime


class QualityReporter:
    """
    数据质量报告生成器
    将数据画像和异常检测结果整合为一份Markdown报告
    """
    
    def __init__(self, profile, anomalies, df=None):
        """
        初始化报告生成器
        
        参数:
            profile: dict，数据画像结果
            anomalies: list，异常检测结果
            df: pandas DataFrame，原始数据（用于补充信息）
        """
        self.profile = profile
        self.anomalies = anomalies
        self.df = df
        self.report_lines = []
    
    def generate_report(self):
        """
        生成完整的Markdown报告
        """
        print("\n📝 开始生成质量报告...")
        
        # ========== 1. 报告标题和元信息 ==========
        self._add_line(f"# 📊 数据质量报告")
        self._add_line(f"")
        self._add_line(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._add_line(f"")
        self._add_line(f"---")
        self._add_line(f"")
        
        # ========== 2. 总体概览 ==========
        self._add_line(f"## 📌 总体概览")
        self._add_line(f"")
        basic = self.profile.get('basic', {})
        self._add_line(f"- **数据总行数**: {basic.get('total_rows', 0):,}")
        self._add_line(f"- **数据总列数**: {basic.get('total_columns', 0)}")
        self._add_line(f"- **内存占用**: {basic.get('memory_usage_mb', 0)} MB")
        self._add_line(f"- **质量评分**: **{self.profile.get('quality_score', 0)}/100**")
        self._add_line(f"")
        
        # ========== 3. 质量评分仪表盘 ==========
        score = self.profile.get('quality_score', 0)
        if score >= 90:
            status = "🟢 优秀"
        elif score >= 70:
            status = "🟡 良好"
        else:
            status = "🔴 需关注"
        self._add_line(f"**质量等级**: {status}")
        self._add_line(f"")
        self._add_line(f"---")
        self._add_line(f"")
        
        # ========== 4. 缺失值分析 ==========
        self._add_line(f"## 🔍 缺失值分析")
        self._add_line(f"")
        missing = self.profile.get('missing', {})
        if missing:
            self._add_line(f"存在缺失值的列共 **{len(missing)}** 列：")
            self._add_line(f"")
            self._add_line(f"| 列名 | 缺失数量 | 缺失比例 |")
            self._add_line(f"|------|----------|----------|")
            for col, stats in missing.items():
                self._add_line(f"| {col} | {stats['null_count']:,} | {stats['null_pct']}% |")
            self._add_line(f"")
        else:
            self._add_line(f"✅ **无缺失值**，数据完整性良好。")
            self._add_line(f"")
        
        self._add_line(f"---")
        self._add_line(f"")
        
        # ========== 5. 数值列统计 ==========
        self._add_line(f"## 📈 数值列统计")
        self._add_line(f"")
        numeric = self.profile.get('numeric', {})
        if numeric:
            self._add_line(f"| 列名 | 均值 | 标准差 | 最小值 | 中位数 | 最大值 |")
            self._add_line(f"|------|------|--------|--------|--------|--------|")
            for col, stats in numeric.items():
                self._add_line(f"| {col} | {stats['mean']} | {stats['std']} | {stats['min']} | {stats['median']} | {stats['max']} |")
            self._add_line(f"")
        else:
            self._add_line(f"⚠️ 无数值列")
            self._add_line(f"")
        
        self._add_line(f"---")
        self._add_line(f"")
        
        # ========== 6. 时间列统计 ==========
        self._add_line(f"## ⏰ 时间列统计")
        self._add_line(f"")
        datetime_info = self.profile.get('datetime', {})
        if datetime_info:
            for col, stats in datetime_info.items():
                self._add_line(f"**{col}**")
                self._add_line(f"- 时间范围: {stats['min_date']} ~ {stats['max_date']}")
                self._add_line(f"- 跨度: {stats['date_range_days']} 天")
                self._add_line(f"- 有效比例: {stats['valid_rate']}%")
                self._add_line(f"")
        else:
            self._add_line(f"⚠️ 无时间列")
            self._add_line(f"")
        
        self._add_line(f"---")
        self._add_line(f"")
        
        # ========== 7. 异常检测结果 ==========
        self._add_line(f"## 🚨 异常检测结果")
        self._add_line(f"")
        
        if self.anomalies and len(self.anomalies) > 0:
            self._add_line(f"发现 **{len(self.anomalies)}** 个异常项：")
            self._add_line(f"")
            for i, anomaly in enumerate(self.anomalies, 1):
                severity_emoji = "🔴" if anomaly.get('severity') == 'high' else "🟡"
                self._add_line(f"### {severity_emoji} 异常 #{i}: {anomaly.get('type', 'unknown')}")
                self._add_line(f"")
                self._add_line(f"- **描述**: {anomaly.get('message', '无')}")
                if 'suggestion' in anomaly:
                    self._add_line(f"- **建议**: {anomaly['suggestion']}")
                self._add_line(f"")
        else:
            self._add_line(f"✅ **未发现异常**，数据质量良好！")
            self._add_line(f"")
        
        self._add_line(f"---")
        self._add_line(f"")
        
        # ========== 8. 总结 ==========
        self._add_line(f"## 📝 总结")
        self._add_line(f"")
        self._add_line(f"- 数据整体质量 **{'良好' if score >= 70 else '需要关注'}**")
        self._add_line(f"- 建议定期运行此报告，监控数据质量变化趋势")
        self._add_line(f"- 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._add_line(f"")
        self._add_line(f"---")
        self._add_line(f"*报告由智能数据质量引擎自动生成*")
        
        print("✅ 报告生成完成！")
        
        return '\n'.join(self.report_lines)
    
    def _add_line(self, line):
        """添加一行到报告"""
        self.report_lines.append(line)
    
    def save_report(self, output_path):
        """
        保存报告到文件
        
        参数:
            output_path: 保存路径
        """
        report_content = self.generate_report()
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 报告已保存至: {output_path}")
        return output_path