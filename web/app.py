# ============================================================
# 文件名: web/app.py
# 用途: Streamlit Web UI - 数据质量监控可视化界面
# 说明: 启动命令 streamlit run web/app.py
# ============================================================

import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quality_engine.profiler import DataProfiler
from quality_engine.anomaly_detector import AnomalyDetector
from quality_engine.alert import AlertManager
from quality_engine.ai_advisor import AIAdvisor
from quality_engine.reporter import QualityReporter
from quality_engine.visualizer import QualityVisualizer


# ==================== 页面配置 ====================
st.set_page_config(
    page_title="智能数据质量监控平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== 侧边栏 ====================
with st.sidebar:
    st.title("📊 质量监控")
    st.markdown("---")

    # 参数配置
    st.subheader("⚙️ 参数配置")
    threshold = st.slider(
        "告警阈值 (%)",
        min_value=1.0,
        max_value=20.0,
        value=10.0,
        step=0.5,
        help="空值率超过此阈值时触发告警"
    )
    enable_ai = st.checkbox("启用 AI 智能建议", value=True)

    st.markdown("---")
    st.caption(f"版本 1.0 | {datetime.now().strftime('%Y-%m-%d')}")


# ==================== 主区域 ====================
st.title("📊 智能数据质量监控平台")
st.markdown("上传数据文件或使用示例数据，系统将自动进行质量分析、异常检测和报告生成。")

# 选项卡
tab1, tab2, tab3, tab4 = st.tabs(["📤 数据上传", "📊 质量报告", "🚨 异常告警", "📈 可视化看板"])


# ==================== Tab 1: 数据上传 ====================
with tab1:
    st.subheader("📤 上传数据文件")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader(
            "选择 CSV 文件",
            type=['csv'],
            help="支持 UTF-8 编码的 CSV 文件，首行为列名"
        )

        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ 成功加载 {len(df)} 行 × {len(df.columns)} 列")
            st.dataframe(df.head(10))

    with col2:
        st.markdown("### 或使用示例数据")
        if st.button("📦 生成示例数据（7天×10000条）"):
            from data_generator.log_simulator import generate_logs
            with st.spinner("正在生成数据..."):
                df = generate_logs(days=7, rows_per_day=10000)
                st.session_state['df'] = df
            st.success(f"✅ 已生成 {len(df)} 条示例数据")
            st.rerun()

    # 存储上传的数据到 session
    if uploaded_file is not None:
        st.session_state['df'] = df
        st.session_state['filename'] = uploaded_file.name

    # 运行按钮
    if 'df' in st.session_state:
        if st.button("🚀 开始质量分析", type="primary"):
            with st.spinner("正在分析数据，请稍候..."):
                df = st.session_state['df']

                # 1. 画像分析
                profiler = DataProfiler(df)
                profile = profiler.generate_profile()
                st.session_state['profile'] = profile

                # 2. 异常检测
                detector = AnomalyDetector(df, profile)
                anomalies = detector.run_all_checks(threshold=threshold)
                st.session_state['anomalies'] = anomalies

                # 3. AI 建议
                if enable_ai and anomalies:
                    advisor = AIAdvisor()
                    profile_summary = f"总行数: {profile['basic']['total_rows']}, 质量评分: {profile['quality_score']}"
                    anomalies = advisor.get_suggestions(anomalies, profile_summary)
                    st.session_state['anomalies'] = anomalies

                # 4. 告警
                alert = AlertManager()
                alert.push_alerts(anomalies, profile)

                # 5. 报告
                reporter = QualityReporter(profile, anomalies, df)
                report_path = os.path.join('output', 'quality_report.md')
                reporter.save_report(report_path)

                st.session_state['analysis_done'] = True
                st.success("✅ 质量分析完成！请切换到其他选项卡查看结果。")


# ==================== Tab 2: 质量报告 ====================
with tab2:
    st.subheader("📊 质量报告")

    if 'profile' in st.session_state:
        profile = st.session_state['profile']

        # 评分展示
        score = profile.get('quality_score', 0)
        if score >= 90:
            status = "🟢 优秀"
        elif score >= 70:
            status = "🟡 良好"
        else:
            status = "🔴 需关注"

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📊 总行数", f"{profile['basic']['total_rows']:,}")
        col2.metric("📋 总列数", profile['basic']['total_columns'])
        col3.metric("💾 内存占用", f"{profile['basic']['memory_usage_mb']} MB")
        col4.metric("⭐ 质量评分", f"{score} 分")

        st.metric("📌 质量等级", status)

        # 缺失值详情
        if profile.get('missing'):
            st.subheader("🔍 缺失值分析")
            missing_data = []
            for col, stats in profile['missing'].items():
                missing_data.append({
                    '列名': col,
                    '缺失数量': stats['null_count'],
                    '缺失比例': f"{stats['null_pct']}%"
                })
            st.dataframe(pd.DataFrame(missing_data), use_container_width=True)

        # 数值列统计
        if profile.get('numeric'):
            st.subheader("📈 数值列统计")
            numeric_data = []
            for col, stats in profile['numeric'].items():
                numeric_data.append({
                    '列名': col,
                    '均值': stats['mean'],
                    '标准差': stats['std'],
                    '最小值': stats['min'],
                    '最大值': stats['max']
                })
            st.dataframe(pd.DataFrame(numeric_data), use_container_width=True)

    else:
        st.info("请先在「数据上传」选项卡中上传数据并运行分析。")


# ==================== Tab 3: 异常告警 ====================
with tab3:
    st.subheader("🚨 异常告警")

    if 'anomalies' in st.session_state:
        anomalies = st.session_state['anomalies']

        if anomalies:
            st.warning(f"⚠️ 发现 {len(anomalies)} 个异常项")

            for i, anomaly in enumerate(anomalies, 1):
                severity = anomaly.get('severity', 'medium')
                severity_emoji = "🔴" if severity == 'high' else "🟡" if severity == 'medium' else "🟢"

                with st.expander(f"{severity_emoji} 异常 #{i}: {anomaly.get('type', 'unknown')}"):
                    st.markdown(f"**消息:** {anomaly.get('message', '无')}")
                    st.markdown(f"**建议:** {anomaly.get('suggestion', '无')}")
                    if 'ai_suggestion' in anomaly:
                        st.markdown(f"**🤖 AI 智能建议:** {anomaly['ai_suggestion']}")
        else:
            st.success("✅ 未发现异常，数据质量良好！")
    else:
        st.info("请先在「数据上传」选项卡中上传数据并运行分析。")


# ==================== Tab 4: 可视化看板 ====================
with tab4:
    st.subheader("📈 可视化看板")

    if 'df' in st.session_state:
        df = st.session_state['df']

        # 时间列检测
        time_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
        if time_cols:
            try:
                df['_date'] = pd.to_datetime(df[time_cols[0]], errors='coerce')
                daily = df.groupby(df['_date'].dt.date).size().reset_index(name='count')

                st.line_chart(daily.set_index('_date'))
                st.caption(f"数据来源: {time_cols[0]} 列")
            except Exception as e:
                st.warning(f"无法解析日期列: {e}")
        else:
            st.info("未检测到日期列，无法生成时间趋势图。")
    else:
        st.info("请先在「数据上传」选项卡中上传数据。")