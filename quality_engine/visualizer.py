# ============================================================
# 文件名: quality_engine/visualizer.py
# 用途: 数据可视化看板 - 生成质量趋势图
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
import os
from datetime import datetime
import pymysql


class QualityVisualizer:
    """
    数据质量可视化
    从MySQL读取DWS层数据，生成趋势图
    """
    
    def __init__(self, db_config=None):
        """
        初始化可视化器
        
        参数:
            db_config: dict，MySQL连接配置
        """
        self.db_config = db_config or {
            'host': 'localhost',
            'user': 'root',
            'password': '123456',  # 请修改为你的密码
            'database': 'user_behavior_db',
            'charset': 'utf8mb4'
        }
        self.conn = None
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = pymysql.connect(**self.db_config)
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
    
    def load_daily_metrics(self):
        """
        从DWS层加载每日汇总数据
        """
        query = """
        SELECT 
            stat_date,
            pv,
            uv,
            avg_visits_per_user,
            total_orders
        FROM dws_daily_metrics
        ORDER BY stat_date
        """
        return pd.read_sql(query, self.conn)
    
    def load_event_distribution(self):
        """
        加载事件类型分布
        """
        query = """
        SELECT 
            stat_date,
            event_type,
            event_count
        FROM dws_daily_events
        ORDER BY stat_date, event_type
        """
        return pd.read_sql(query, self.conn)
    
    def load_hourly_trend(self):
        """
        加载小时级趋势
        """
        query = """
        SELECT 
            stat_hour,
            pv
        FROM dws_hourly_trend
        ORDER BY stat_hour
        """
        return pd.read_sql(query, self.conn)
    
    def create_dashboard(self, output_dir='output/images'):
        """
        生成所有图表并保存
        """
        if not self.connect():
            return
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        print("📊 开始生成可视化图表...")
        
        # ----- 图1：每日PV/UV趋势（核心指标） -----
        df_daily = self.load_daily_metrics()
        if not df_daily.empty:
            fig1, ax1 = plt.subplots(figsize=(12, 5))
            
            ax1.plot(df_daily['stat_date'], df_daily['pv'], 
                     marker='o', label='PV', linewidth=2, color='#2E86C1')
            ax1.plot(df_daily['stat_date'], df_daily['uv'], 
                     marker='s', label='UV', linewidth=2, color='#E67E22')
            ax1.set_xlabel('日期')
            ax1.set_ylabel('数量')
            ax1.set_title('每日 PV / UV 趋势', fontsize=14, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 添加数据标签
            for i, row in df_daily.iterrows():
                ax1.annotate(str(row['pv']), (row['stat_date'], row['pv']), 
                            textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)
            
            plt.tight_layout()
            fig1.savefig(os.path.join(output_dir, 'daily_pv_uv.png'), dpi=150)
            plt.close(fig1)
            print(f"   ✅ 保存: daily_pv_uv.png")
        
        # ----- 图2：事件类型分布（堆叠面积图） -----
        df_events = self.load_event_distribution()
        if not df_events.empty:
            fig2, ax2 = plt.subplots(figsize=(12, 5))
            
            # 转换为透视表
            pivot = df_events.pivot(index='stat_date', columns='event_type', values='event_count')
            pivot.fillna(0, inplace=True)
            
            # 堆叠面积图
            pivot.plot(kind='area', stacked=True, ax=ax2, alpha=0.7,
                      color=['#2ECC71', '#3498DB', '#E74C3C'])
            ax2.set_xlabel('日期')
            ax2.set_ylabel('事件数量')
            ax2.set_title('每日事件类型分布（堆叠图）', fontsize=14, fontweight='bold')
            ax2.legend(title='事件类型')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            fig2.savefig(os.path.join(output_dir, 'event_distribution.png'), dpi=150)
            plt.close(fig2)
            print(f"   ✅ 保存: event_distribution.png")
        
        # ----- 图3：质量评分仪表盘（环形图） -----
        # 直接使用画像中的质量评分
        try:
            # 从profile获取质量分（我们稍后会从reporter传入）
            # 这里先用模拟值，实际使用时会从profile传入
            pass
        except:
            pass
        
        # ----- 图4：小时级流量热力图（可选高级） -----
        df_hourly = self.load_hourly_trend()
        if not df_hourly.empty and len(df_hourly) >= 24:
            fig4, ax4 = plt.subplots(figsize=(14, 6))
            
            # 提取小时和日期
            df_hourly['hour'] = pd.to_datetime(df_hourly['stat_hour']).dt.hour
            df_hourly['date'] = pd.to_datetime(df_hourly['stat_hour']).dt.date
            
            # 透视表
            pivot_hour = df_hourly.pivot(index='date', columns='hour', values='pv')
            
            # 热力图
            im = ax4.imshow(pivot_hour.values, cmap='YlOrRd', aspect='auto', interpolation='nearest')
            ax4.set_xticks(range(0, 24, 2))
            ax4.set_xticklabels([f'{h}:00' for h in range(0, 24, 2)])
            ax4.set_yticks(range(len(pivot_hour.index)))
            ax4.set_yticklabels(pivot_hour.index)
            ax4.set_xlabel('小时')
            ax4.set_ylabel('日期')
            ax4.set_title('小时级流量热力图', fontsize=14, fontweight='bold')
            
            plt.colorbar(im, ax=ax4, label='PV')
            plt.tight_layout()
            fig4.savefig(os.path.join(output_dir, 'hourly_heatmap.png'), dpi=150)
            plt.close(fig4)
            print(f"   ✅ 保存: hourly_heatmap.png")
        
        self.close()
        print(f"🎉 所有图表已保存至: {output_dir}")
        
        return output_dir