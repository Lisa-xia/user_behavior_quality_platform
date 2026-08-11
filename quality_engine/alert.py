# ============================================================
# 文件名: quality_engine/alert.py
# 用途: 告警推送模块（本地版）
# 功能: 控制台输出 + 日志记录 + 美观HTML报告（含图表+PDF导出）
# ============================================================

import os
from datetime import datetime


class AlertManager:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.log_path = os.path.join(self.project_root, 'output', 'alerts.log')
        self.html_path = os.path.join(self.project_root, 'output', 'alert_report.html')

    def push_alerts(self, anomalies, profile=None):
        """
        统一入口：根据异常列表生成告警
        """
        if not anomalies:
            print("✅ 无异常，无需告警")
            return

        print(f"\n📨 开始处理 {len(anomalies)} 条告警...")

        # 1. 控制台打印
        self._console_alert(anomalies)

        # 2. 写入日志
        self._log_to_file(anomalies)

        # 3. 生成HTML报告
        self._generate_html(anomalies, profile)

        print("✅ 告警处理完成！")

    # ---------- 内部方法 ----------
    def _console_alert(self, anomalies):
        print("\n" + "="*60)
        print("🔔 【控制台告警】检测到以下异常：")
        print("="*60)
        for i, a in enumerate(anomalies, 1):
            print(f"\n  {i}. [{a.get('type', 'unknown')}]")
            print(f"     消息: {a.get('message', '无')}")
            if 'suggestion' in a:
                print(f"     建议: {a['suggestion']}")
        print("\n" + "="*60)

    def _log_to_file(self, anomalies):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"告警时间: {timestamp}\n")
            f.write(f"异常数量: {len(anomalies)}\n")
            for a in anomalies:
                f.write(f"- [{a.get('type')}] {a.get('message')}\n")
                if 'suggestion' in a:
                    f.write(f"  建议: {a['suggestion']}\n")
            f.write(f"{'='*60}\n")
        print(f"📄 告警已记录到: {self.log_path}")

    def _generate_html(self, anomalies, profile=None):
        """
        生成美观的 HTML 告警报告（含图表 + PDF导出）
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 按严重程度分组
        high = [a for a in anomalies if a.get('severity') == 'high']
        medium = [a for a in anomalies if a.get('severity') == 'medium']
        low = [a for a in anomalies if a.get('severity') == 'low']
        total = len(anomalies)

        # 准备图表数据
        severity_data = [len(high), len(medium), len(low)]
        severity_labels = ['高危', '中危', '低危']
        severity_colors = ['#E74C3C', '#F39C12', '#2ECC71']

        # 异常类型分布
        type_counts = {}
        for a in anomalies:
            t = a.get('type', 'unknown')
            type_counts[t] = type_counts.get(t, 0) + 1
        type_labels = list(type_counts.keys())
        type_values = list(type_counts.values())
        type_colors = ['#3498DB', '#9B59B6', '#1ABC9C', '#E67E22', '#E74C3C'][:len(type_labels)]

        # 构建异常卡片
        cards_html = ""
        for i, a in enumerate(anomalies, 1):
            severity = a.get('severity', 'medium')
            color_map = {
                'high': {'border': '#E74C3C', 'bg': '#FDEDEC', 'badge': '🔴 高危'},
                'medium': {'border': '#F39C12', 'bg': '#FEF9E7', 'badge': '🟡 中危'},
                'low': {'border': '#2ECC71', 'bg': '#EAFAF1', 'badge': '🟢 低危'}
            }
            colors = color_map.get(severity, color_map['medium'])

            suggestion = a.get('suggestion', '无')
            ai_suggestion = a.get('ai_suggestion', '')

            ai_html = ""
            if ai_suggestion:
                ai_html = f"""
                <div style="margin-top: 10px; padding: 12px 14px; background: #F4ECF7; border-radius: 8px; border-left: 3px solid #8E44AD;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                        <span style="font-size: 16px;">🤖</span>
                        <span style="font-weight: 600; color: #6C3483; font-size: 13px;">AI 智能建议</span>
                    </div>
                    <div style="color: #4A235A; font-size: 13px; line-height: 1.6; white-space: pre-wrap;">{ai_suggestion}</div>
                </div>
                """

            cards_html += f"""
            <div style="border: 1px solid #E8E8E8; border-radius: 10px; padding: 16px 20px; margin-bottom: 14px; background: {colors['bg']}; border-left: 5px solid {colors['border']}; box-shadow: 0 1px 3px rgba(0,0,0,0.06);">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="font-weight: 700; color: #2C3E50; font-size: 15px;">#{i}</span>
                        <span style="background: {colors['border']}; color: #fff; padding: 2px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">{a.get('type', 'unknown')}</span>
                        <span style="font-size: 13px; color: #555;">{colors['badge']}</span>
                    </div>
                </div>
                <div style="margin-top: 8px; color: #2C3E50; font-size: 14px; line-height: 1.5;">
                    {a.get('message', '无')}
                </div>
                <div style="margin-top: 8px; font-size: 13px; color: #7F8C8D;">
                    💡 基础建议: {suggestion}
                </div>
                {ai_html}
            </div>
            """

        # 完整 HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>数据质量告警报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: #f0f2f5;
            padding: 30px 20px;
            color: #2C3E50;
        }}
        .container {{
            max-width: 960px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            padding: 40px 44px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.08);
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid #E74C3C;
            padding-bottom: 16px;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .header h1 {{ font-size: 26px; font-weight: 700; color: #1A1A2E; letter-spacing: 0.5px; }}
        .header .badge {{ background: #E74C3C; color: white; padding: 6px 18px; border-radius: 30px; font-size: 15px; font-weight: 600; }}

        .toolbar {{
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            margin: 16px 0 20px 0;
            flex-wrap: wrap;
        }}
        .btn {{
            padding: 8px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s, transform 0.1s;
        }}
        .btn:hover {{ transform: scale(1.02); }}
        .btn-pdf {{ background: #E74C3C; color: white; }}
        .btn-pdf:hover {{ background: #C0392B; }}
        .btn-print {{ background: #3498DB; color: white; }}
        .btn-print:hover {{ background: #2E86C1; }}

        .summary {{
            display: flex;
            gap: 20px;
            margin: 20px 0 24px 0;
            padding: 18px 24px;
            background: #f8f9fa;
            border-radius: 12px;
            justify-content: space-around;
            flex-wrap: wrap;
        }}
        .summary-item {{ text-align: center; flex: 1; min-width: 80px; }}
        .summary-item .num {{ font-size: 28px; font-weight: 700; }}
        .summary-item .label {{ font-size: 13px; color: #7F8C8D; margin-top: 2px; }}
        .high-color {{ color: #E74C3C; }}
        .medium-color {{ color: #F39C12; }}
        .low-color {{ color: #2ECC71; }}

        .charts-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin: 24px 0 28px 0;
        }}
        .chart-box {{
            background: #fafbfc;
            padding: 16px 18px 12px 18px;
            border-radius: 12px;
            border: 1px solid #ECF0F1;
        }}
        .chart-box h3 {{
            font-size: 14px;
            font-weight: 600;
            color: #555;
            text-align: center;
            margin-bottom: 8px;
        }}
        .chart-box canvas {{
            max-height: 180px;
            max-width: 100%;
        }}

        .section-title {{
            font-size: 18px;
            font-weight: 600;
            color: #1A1A2E;
            margin: 28px 0 16px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .section-title span {{
            background: #ECF0F1;
            padding: 0 12px;
            border-radius: 20px;
            font-size: 13px;
            color: #7F8C8D;
        }}

        .footer {{
            margin-top: 32px;
            padding-top: 16px;
            border-top: 1px solid #ECF0F1;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            color: #95A5A6;
            font-size: 13px;
        }}
        .footer .tag {{
            background: #ECF0F1;
            padding: 2px 14px;
            border-radius: 20px;
            font-size: 12px;
            color: #7F8C8D;
        }}

        @media (max-width: 640px) {{
            .container {{ padding: 20px 16px; }}
            .header h1 {{ font-size: 20px; }}
            .charts-row {{ grid-template-columns: 1fr; }}
            .summary {{ padding: 12px 8px; gap: 8px; }}
            .summary-item .num {{ font-size: 22px; }}
        }}

        @media print {{
            body {{ background: #fff; padding: 0; }}
            .container {{ box-shadow: none; padding: 20px; }}
            .toolbar {{ display: none !important; }}
            .btn {{ display: none !important; }}
            .chart-box {{ break-inside: avoid; }}
            .footer .tag {{ display: none; }}
        }}
    </style>
</head>
<body>
<div class="container" id="report-container">
    <div class="header">
        <h1>🚨 数据质量告警报告</h1>
        <span class="badge">{total} 项异常</span>
    </div>

    <div class="toolbar">
        <button class="btn btn-pdf" onclick="window.print()">📄 导出 PDF</button>
        <button class="btn btn-print" onclick="window.print()">🖨️ 打印 / 另存为 PDF</button>
    </div>

    <div class="summary">
        <div class="summary-item"><div class="num high-color">{len(high)}</div><div class="label">🔴 高危</div></div>
        <div class="summary-item"><div class="num medium-color">{len(medium)}</div><div class="label">🟡 中危</div></div>
        <div class="summary-item"><div class="num low-color">{len(low)}</div><div class="label">🟢 低危</div></div>
    </div>

    <div class="charts-row">
        <div class="chart-box">
            <h3>📊 严重程度分布</h3>
            <canvas id="severityChart"></canvas>
        </div>
        <div class="chart-box">
            <h3>📊 异常类型分布</h3>
            <canvas id="typeChart"></canvas>
        </div>
    </div>

    <div class="section-title">
        📋 异常明细
        <span>{total} 条</span>
    </div>
    {cards_html}

    <div class="footer">
        <div>生成时间: {timestamp}</div>
        <div class="tag">⚡ 智能数据质量引擎 · AI 增强版</div>
    </div>
</div>

<script>
    const severityCtx = document.getElementById('severityChart').getContext('2d');
    new Chart(severityCtx, {{
        type: 'doughnut',
        data: {{
            labels: {severity_labels},
            datasets: [{{
                data: {severity_data},
                backgroundColor: {severity_colors},
                borderWidth: 0
            }}]
        }},
        options: {{
            responsive: true,
            plugins: {{
                legend: {{
                    position: 'bottom',
                    labels: {{ padding: 12, usePointStyle: true, pointStyle: 'circle' }}
                }}
            }},
            cutout: '60%'
        }}
    }});

    const typeCtx = document.getElementById('typeChart').getContext('2d');
    new Chart(typeCtx, {{
        type: 'bar',
        data: {{
            labels: {type_labels},
            datasets: [{{
                label: '异常数量',
                data: {type_values},
                backgroundColor: {type_colors},
                borderRadius: 6,
                borderSkipped: false
            }}]
        }},
        options: {{
            responsive: true,
            plugins: {{
                legend: {{ display: false }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    ticks: {{ stepSize: 1 }}
                }}
            }}
        }}
    }});
</script>
</body>
</html>
        """

        with open(self.html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"🌐 升级版 HTML 报告已生成（含图表 + PDF导出）: {self.html_path}")