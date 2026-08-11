# ============================================================
# 文件名: quality_engine/ai_advisor.py
# 用途: 调用 DeepSeek API 生成智能修复建议
# ============================================================

import requests
import json
from datetime import datetime
from openai import OpenAI

class AIAdvisor:
    def __init__(self, api_key="sk-feea32d77d6042ad9714bf855cfe269d", model="deepseek-chat"):
        """
        初始化 AI 顾问
        :param api_key: 你的 DeepSeek API Key
        :param model: 使用的 DeepSeek 模型，推荐 deepseek-chat
        """
        self.model = model
        # 初始化 OpenAI 客户端，并指向 DeepSeek 的 API 地址[reference:16][reference:17]
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

    def _build_prompt(self, anomalies, profile_summary=None):
        """
        构造发给 AI 的提示词（Prompt）
        """
        prompt = "你是一位资深数据开发工程师，负责数据质量保障。\n"
        prompt += "请根据以下数据异常信息，给出具体、可执行的修复建议。\n\n"
        
        if profile_summary:
            prompt += f"【数据概况】\n{profile_summary}\n\n"
        
        prompt += "【异常列表】\n"
        for idx, a in enumerate(anomalies, 1):
            prompt += f"异常 {idx}: {a.get('message', '')}\n"
            if 'suggestion' in a:
                prompt += f"  基础建议: {a['suggestion']}\n"
        
        prompt += "\n请针对每条异常，按以下格式输出回复（严格对应顺序）：\n"
        prompt += "--- 异常 1 ---\n【根因分析】...\n【具体操作】...\n【预防措施】...\n"
        prompt += "--- 异常 2 ---\n..."

        return prompt

    def get_suggestions(self, anomalies, profile_summary=None):
        """
        调用 DeepSeek API 获取 AI 建议
        """
        if not anomalies:
            return []

        print("🧠 正在调用 DeepSeek API 生成智能修复建议...")

        prompt = self._build_prompt(anomalies, profile_summary)

        try:
            # 调用 DeepSeek 的对话补全 API[reference:18][reference:19]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的数据质量分析专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 降低随机性，让回答更稳定[reference:20]
                stream=False
            )
            
            ai_text = response.choices[0].message.content.strip()
            print("✅ AI 建议生成成功！")
            return self._parse_ai_response(anomalies, ai_text)

        except Exception as e:
            print(f"⚠️ AI 调用异常: {e}")
            return self._fallback_suggestions(anomalies)

    def _parse_ai_response(self, anomalies, ai_text):
        """
        将 AI 回复拆分，分别匹配到对应的异常上
        """
        if "--- 异常" not in ai_text:
            for a in anomalies:
                a['ai_suggestion'] = ai_text
            return anomalies

        parts = ai_text.split("--- 异常")
        ai_parts = parts[1:]

        for i, a in enumerate(anomalies):
            if i < len(ai_parts):
                a['ai_suggestion'] = "--- 异常 " + ai_parts[i].strip()
            else:
                a['ai_suggestion'] = "AI 未针对此异常给出详细建议。"

        return anomalies

    def _fallback_suggestions(self, anomalies):
        """
        如果 AI 不可用，使用默认建议
        """
        for a in anomalies:
            if 'ai_suggestion' not in a:
                a['ai_suggestion'] = "（AI服务未启用）建议人工检查数据源配置及采集脚本。"
        return anomalies