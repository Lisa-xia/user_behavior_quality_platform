# ============================================================
# 文件名: tests/test_profiler.py
# 用途: 数据画像模块单元测试
# ============================================================

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quality_engine.profiler import DataProfiler


class TestDataProfiler:
    """数据画像测试类"""

    def test_basic_profile(self):
        """测试基础画像功能"""
        df = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': ['a', 'b', 'c', 'd', 'e'],
            'col3': [1.1, 2.2, 3.3, 4.4, 5.5]
        })
        profiler = DataProfiler(df)
        profile = profiler.generate_profile()

        assert profile['basic']['total_rows'] == 5
        assert profile['basic']['total_columns'] == 3
        assert profile['quality_score'] >= 90

    def test_null_detection(self):
        """测试空值检测"""
        df = pd.DataFrame({
            'col1': [1, None, 3, None, 5],
            'col2': ['a', 'b', None, 'd', 'e']
        })
        profiler = DataProfiler(df)
        profile = profiler.generate_profile()

        assert 'col1' in profile['missing']
        assert profile['missing']['col1']['null_count'] == 2
        assert profile['missing']['col1']['null_pct'] == 40.0

    def test_numeric_stats(self):
        """测试数值列统计"""
        df = pd.DataFrame({
            'age': [20, 25, 30, 35, 40],
            'score': [80, 85, 90, 95, 100]
        })
        profiler = DataProfiler(df)
        profile = profiler.generate_profile()

        assert 'age' in profile['numeric']
        assert profile['numeric']['age']['mean'] == 30.0
        assert profile['numeric']['age']['min'] == 20.0
        assert profile['numeric']['age']['max'] == 40.0

    def test_categorical_stats(self):
        """测试分类列统计"""
        df = pd.DataFrame({
            'category': ['A', 'B', 'A', 'C', 'B', 'A']
        })
        profiler = DataProfiler(df)
        profile = profiler.generate_profile()

        assert 'category' in profile['categorical']
        assert profile['categorical']['category']['unique_count'] == 3

    def test_empty_dataframe(self):
        """测试空数据框"""
        df = pd.DataFrame()
        profiler = DataProfiler(df)
        profile = profiler.generate_profile()

        assert profile['basic']['total_rows'] == 0
        assert profile['basic']['total_columns'] == 0

    def test_all_null_columns(self):
        """测试全空列"""
        df = pd.DataFrame({
            'col1': [None, None, None],
            'col2': [1, 2, 3]
        })
        profiler = DataProfiler(df)
        profile = profiler.generate_profile()

        assert profile['missing']['col1']['null_pct'] == 100.0