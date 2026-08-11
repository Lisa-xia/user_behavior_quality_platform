# ============================================================
# 文件名: quality_engine/profiler.py
# 用途: 数据画像分析 - 计算数据集的统计特征
# 输出: 返回包含各种统计指标的字典
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime


class DataProfiler:
    """
    数据画像分析器
    对数据集进行全面的统计描述，为异常检测提供基准
    """
    
    def __init__(self, df):
        """
        初始化画像分析器
        
        参数:
            df: pandas DataFrame，待分析的数据集
        """
        self.df = df
        self.profile = {}
    
    def generate_profile(self):
        """
        生成完整的数据画像
        
        返回:
            dict: 包含以下维度的统计信息
                - basic: 基础信息（行数、列数、内存占用）
                - missing: 缺失值统计
                - numeric: 数值列统计（均值、标准差、分位数）
                - categorical: 分类列统计（唯一值数量、众数）
                - datetime: 时间列统计（范围、时间跨度）
        """
        
        print(" 开始生成数据画像...")
        
        # ==================== 1. 基础信息 ====================
        self.profile['basic'] = {
            'total_rows': len(self.df),
            'total_columns': len(self.df.columns),
            'memory_usage_mb': round(self.df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
        }
        
        # ==================== 2. 缺失值统计 ====================
        missing_stats = {}
        for col in self.df.columns:
            null_count = self.df[col].isna().sum()
            null_pct = round(null_count / len(self.df) * 100, 2)
            # 只记录有缺失值的列
            if null_count > 0:
                missing_stats[col] = {
                    'null_count': null_count,
                    'null_pct': null_pct
                }
        self.profile['missing'] = missing_stats
        
        # ==================== 3. 数值列分析 ====================
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        numeric_stats = {}
        for col in numeric_cols:
            # 过滤掉全部为空的列
            if self.df[col].notna().sum() > 0:
                numeric_stats[col] = {
                    'mean': round(self.df[col].mean(), 2),
                    'std': round(self.df[col].std(), 2),
                    'min': round(self.df[col].min(), 2),
                    'q1': round(self.df[col].quantile(0.25), 2),
                    'median': round(self.df[col].quantile(0.50), 2),
                    'q3': round(self.df[col].quantile(0.75), 2),
                    'max': round(self.df[col].max(), 2),
                    'skewness': round(self.df[col].skew(), 3),  # 偏度
                    'kurtosis': round(self.df[col].kurtosis(), 3)  # 峰度
                }
        self.profile['numeric'] = numeric_stats
        
        # ==================== 4. 分类列分析 ====================
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns
        categorical_stats = {}
        for col in categorical_cols:
            # 检查是否为日期时间列（通过列名或内容判断）
            if 'time' in col.lower() or 'date' in col.lower():
                continue
            # 过滤掉全部为空的列
            if self.df[col].notna().sum() > 0:
                value_counts = self.df[col].value_counts()
                top_values = value_counts.head(3).to_dict() if len(value_counts) > 0 else {}
                categorical_stats[col] = {
                    'unique_count': self.df[col].nunique(),
                    'top_values': top_values
                }
        self.profile['categorical'] = categorical_stats
        
        # ==================== 5. 时间列分析 ====================
        datetime_cols = []
        for col in self.df.columns:
            if 'time' in col.lower() or 'date' in col.lower():
                # 尝试转换为datetime类型
                try:
                    if self.df[col].notna().sum() > 0:
                        # 检查是否能成功转换（排除无效日期）
                        temp = pd.to_datetime(self.df[col], errors='coerce')
                        if temp.notna().sum() > 0:
                            datetime_cols.append(col)
                except:
                    pass
        
        datetime_stats = {}
        for col in datetime_cols:
            temp = pd.to_datetime(self.df[col], errors='coerce')
            # 排除无效日期
            valid_dates = temp.dropna()
            if len(valid_dates) > 0:
                datetime_stats[col] = {
                    'min_date': valid_dates.min().strftime('%Y-%m-%d %H:%M:%S'),
                    'max_date': valid_dates.max().strftime('%Y-%m-%d %H:%M:%S'),
                    'date_range_days': (valid_dates.max() - valid_dates.min()).days,
                    'valid_rate': round(len(valid_dates) / len(self.df) * 100, 2)
                }
        self.profile['datetime'] = datetime_stats
        
        # ==================== 6. 总体质量评分 ====================
        # 根据缺失率计算初步质量分
        total_cells = len(self.df) * len(self.df.columns)
        total_null = self.df.isna().sum().sum()
        null_rate = total_null / total_cells
        
        # 基础分100分，每1%的缺失率扣2分，最低0分
        quality_score = max(0, 100 - null_rate * 100 * 2)
        # 如果存在时间列，检查有效时间比例
        if datetime_stats:
            avg_valid_rate = sum([v['valid_rate'] for v in datetime_stats.values()]) / len(datetime_stats)
            quality_score = quality_score * (avg_valid_rate / 100) if avg_valid_rate > 0 else quality_score * 0.5
        
        self.profile['quality_score'] = round(quality_score, 2)
        
        print(f" 数据画像生成完成！质量评分: {self.profile['quality_score']}/100")
        
        return self.profile
    
    def print_summary(self):
        """
        打印画像摘要（用于快速查看）
        """
        if not self.profile:
            print("⚠️ 请先运行 generate_profile() 生成画像")
            return
        
        print("\n" + "="*60)
        print(" 数据画像摘要")
        print("="*60)
        print(f"总行数: {self.profile['basic']['total_rows']:,}")
        print(f"总列数: {self.profile['basic']['total_columns']}")
        print(f"内存占用: {self.profile['basic']['memory_usage_mb']} MB")
        print(f"质量评分: {self.profile['quality_score']}/100")
        
        # 缺失值概览
        if self.profile['missing']:
            print(f"\n存在缺失值的列: {len(self.profile['missing'])} 列")
            for col, stats in self.profile['missing'].items():
                print(f"   - {col}: {stats['null_count']:,} ({stats['null_pct']}%)")
        else:
            print("\n无缺失值")
        
        # 数值列概览
        print(f"\n 数值列数: {len(self.profile['numeric'])}")
        for col in list(self.profile['numeric'].keys())[:3]:
            print(f"   - {col}: 均值={self.profile['numeric'][col]['mean']}")
        if len(self.profile['numeric']) > 3:
            print(f"   ... 及其他 {len(self.profile['numeric']) - 3} 列")
        
        # 时间列概览
        print(f"\n⏰ 时间列数: {len(self.profile['datetime'])}")
        for col, stats in self.profile['datetime'].items():
            print(f"   - {col}: {stats['min_date']} ~ {stats['max_date']} (有效 {stats['valid_rate']}%)")
        
        print("="*60)