"""LLM 模块：调用 DeepSeek 生成回复文本。

工单编号：人工智能CV-AIGC-18-文旅智能体-智能导览与互动体验任务
"""
from __future__ import annotations

import os

from openai import AsyncOpenAI

BASE_URL = "https://api.deepseek.com"
SYSTEM_PROMPT = (
    "你是一位亲切的文旅数字人导览员，用自然、口语化的中文回答游客的问题。"
    "回答简洁，一般不超过 100 字。"
)


def _client() -> AsyncOpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("未配置 DEEPSEEK_API_KEY 环境变量")
    return AsyncOpenAI(api_key=api_key, base_url=BASE_URL)


async def generate(text: str, model: str | None = None) -> str:
    """输入游客提问文本，返回数字人回复文本。"""
    model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    client = _client()
    resp = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0.7,
        max_tokens=300,
    )
    return resp.choices[0].message.content or ""
