# ============================================================
# 文件名: quality_engine/anomaly_detector.py
# 用途: 数据异常检测 - 基于画像结果识别异常
# 支持: 空值率异常、数据量突降、Z-score异常
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class AnomalyDetector:
    """
    数据异常检测器
    基于数据画像的结果，识别数据中的异常模式
    """
    
    def __init__(self, df, profile):
        """
        初始化异常检测器
        
        参数:
            df: pandas DataFrame，原始数据集
            profile: dict，由DataProfiler生成的画像
        """
        self.df = df
        self.profile = profile
        self.anomalies = []
    
    def detect_null_rate_anomaly(self, threshold=10.0):
        """
        检测1：空值率异常
        当某列的空值率超过阈值时报警
        
        参数:
            threshold: float，空值率阈值（百分比），默认10%
        """
        print(f"\n🔍 检测空值率异常（阈值: {threshold}%）...")
        
        has_anomaly = False
        for col, stats in self.profile.get('missing', {}).items():
            null_pct = stats['null_pct']
            if null_pct > threshold:
                has_anomaly = True
                self.anomalies.append({
                    'type': 'null_rate_anomaly',
                    'severity': 'high' if null_pct > 20 else 'medium',
                    'column': col,
                    'null_pct': null_pct,
                    'message': f"列 '{col}' 空值率达到 {null_pct}%，超过阈值 {threshold}%",
                    'suggestion': f"建议检查数据源，确认是否有字段缺失或采集逻辑变更"
                })
                print(f"   ⚠️ 列 '{col}': 空值率 {null_pct}% (超过阈值)")
        
        if not has_anomaly:
            print("   ✅ 未检测到空值率异常")
    
    def detect_volume_drop(self, date_column='event_time', value_column='pv', days_back=7, drop_threshold=30):
        """
        检测2：数据量突降
        检测最近一天的数据量是否相比历史均值有明显下降
        
        参数:
            date_column: 日期列名
            value_column: 要检测的指标列名（pv/uv）
            days_back: 历史天数
            drop_threshold: 下降百分比阈值
        """
        print(f"\n🔍 检测数据量突降（对比前{days_back}天，阈值: {drop_threshold}%）...")
        
        # 检查是否有时间列
        if date_column not in self.df.columns:
            print("   ⚠️ 未找到日期列，跳过该检测")
            return
        
        # 将日期列转为datetime
        try:
            self.df['_temp_date'] = pd.to_datetime(self.df[date_column], errors='coerce')
            valid_data = self.df.dropna(subset=['_temp_date'])
            
            if len(valid_data) == 0:
                print("   ⚠️ 无有效日期数据，跳过该检测")
                return
            
            # 按天分组计算
            daily_counts = valid_data.groupby(valid_data['_temp_date'].dt.date).size()
            
            if len(daily_counts) < days_back + 1:
                print(f"   ⚠️ 数据天数不足（需要 {days_back+1} 天，实际 {len(daily_counts)} 天），跳过检测")
                return
            
            # 按日期排序
            daily_counts = daily_counts.sort_index()
            
            # 最近一天 vs 前N天均值
            latest_date = daily_counts.index[-1]
            latest_count = daily_counts[latest_date]
            historical_mean = daily_counts.iloc[-(days_back+1):-1].mean()
            
            drop_pct = (1 - latest_count / historical_mean) * 100
            
            if drop_pct > drop_threshold:
                self.anomalies.append({
                    'type': 'volume_drop',
                    'severity': 'high' if drop_pct > 50 else 'medium',
                    'latest_date': latest_date.strftime('%Y-%m-%d'),
                    'latest_count': latest_count,
                    'historical_mean': round(historical_mean, 0),
                    'drop_pct': round(drop_pct, 1),
                    'message': f"最新数据量 {latest_count}，相比前{days_back}天均值 {round(historical_mean, 0)} 下降了 {round(drop_pct, 1)}%",
                    'suggestion': f"建议检查数据采集链路是否中断，或业务量是否确实在下降"
                })
                print(f"   ⚠️ {latest_date}: 数据量 {latest_count}，下降 {round(drop_pct, 1)}%")
            else:
                print(f"   ✅ 无显著数据量突降（最新 {latest_count}，历史均值 {round(historical_mean, 0)}，变化 {round(drop_pct, 1)}%）")
                
        except Exception as e:
            print(f"   ⚠️ 数据量检测执行失败: {e}")
    
    def detect_zscore_anomaly(self, column, threshold=3):
        """
        检测3：Z-score异常
        找出数值列中偏离均值超过threshold倍标准差的点
        
        参数:
            column: 要检测的列名
            threshold: Z-score阈值，默认3
        """
        print(f"\n🔍 检测Z-score异常（列: {column}，阈值: {threshold}σ）...")
        
        if column not in self.df.columns:
            print(f"   ⚠️ 列 '{column}' 不存在，跳过该检测")
            return
        
        # 只检测数值列
        if not pd.api.types.is_numeric_dtype(self.df[column]):
            print(f"   ⚠️ 列 '{column}' 不是数值类型，跳过该检测")
            return
        
        # 过滤空值
        valid_data = self.df[column].dropna()
        if len(valid_data) < 10:
            print(f"   ⚠️ 有效数据不足（{len(valid_data)}条），跳过该检测")
            return
        
        mean = valid_data.mean()
        std = valid_data.std()
        
        if std == 0:
            print("   ⚠️ 标准差为0，跳过该检测")
            return
        
        # 计算Z-score
        z_scores = (valid_data - mean) / std
        outliers = z_scores[abs(z_scores) > threshold]
        
        if len(outliers) > 0:
            self.anomalies.append({
                'type': 'zscore_anomaly',
                'severity': 'high' if len(outliers) / len(valid_data) > 0.05 else 'medium',
                'column': column,
                'outlier_count': len(outliers),
                'outlier_pct': round(len(outliers) / len(valid_data) * 100, 2),
                'mean': round(mean, 2),
                'std': round(std, 2),
                'message': f"列 '{column}' 发现 {len(outliers)} 个异常值（占比 {round(len(outliers) / len(valid_data) * 100, 2)}%）",
                'suggestion': f"建议检查这些异常值是否由数据采集错误或业务异常导致"
            })
            print(f"   ⚠️ 发现 {len(outliers)} 个异常值")
        else:
            print(f"   ✅ 无异常值")
    
    def run_all_checks(self, threshold=10.0):
        """
        运行所有异常检测
        
        参数:
            threshold: 空值率告警阈值（百分比）
        """
        print("\n" + "="*60)
        print("🚀 开始运行异常检测...")
        print("="*60)
        
        # 清空之前的异常记录
        self.anomalies = []
        
        # 检测1：空值率异常（使用传入的阈值）
        self.detect_null_rate_anomaly(threshold=threshold)
        
        # 检测2：数据量突降（如果有时间列）
        time_cols = [col for col in self.df.columns if 'time' in col.lower() or 'date' in col.lower()]
        if time_cols:
            self.detect_volume_drop(date_column=time_cols[0], days_back=3, drop_threshold=30)
        
        # 检测3：Z-score异常（检测数值列）
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            # 只检测前2个数值列作为示例
            for col in numeric_cols[:2]:
                self.detect_zscore_anomaly(col, threshold=3)
        
        # 打印汇总
        print("\n" + "="*60)
        print("📊 异常检测结果汇总")
        print("="*60)
        
        if self.anomalies:
            print(f"发现 {len(self.anomalies)} 个异常项：")
            for i, anomaly in enumerate(self.anomalies, 1):
                print(f"\n   {i}. [{anomaly['type']}] {anomaly['message']}")
                print(f"      建议: {anomaly.get('suggestion', '无')}")
        else:
            print("✅ 未发现异常，数据质量良好！")
        
        print("="*60)
        
        # ===== 新增：AI 增强 =====
        if self.anomalies:
            try:
                from quality_engine.ai_advisor import AIAdvisor
                print("\n🧠 启动 AI 增强分析...")
                advisor = AIAdvisor()
                profile_summary = f"总行数: {self.profile['basic']['total_rows']}, 质量评分: {self.profile['quality_score']}"
                self.anomalies = advisor.get_suggestions(self.anomalies, profile_summary)
            except ImportError:
                print("   ⚠️ AI 模块未找到，跳过 AI 增强")
            except Exception as e:
                print(f"   ⚠️ AI 增强执行失败: {e}")
        
        # ===== 新增：告警推送 =====
        if self.anomalies:
            try:
                from quality_engine.alert import AlertManager
                alert = AlertManager()
                alert.push_alerts(self.anomalies, self.profile)
            except ImportError:
                print("   ⚠️ 告警模块未找到，跳过告警推送")
            except Exception as e:
                print(f"   ⚠️ 告警推送执行失败: {e}")
        
        return self.anomalies