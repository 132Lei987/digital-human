"""TTS 模块：调用 Edge TTS 合成语音并返回字级时间戳。

工单编号：人工智能CV-AIGC-18-文旅智能体-智能导览与互动体验任务
"""
from __future__ import annotations

import io

import edge_tts

VOICE = "zh-CN-XiaoxiaoNeural"


def _offset_to_ms(offset_100ns: int) -> float:
    """Edge TTS 的 offset/duration 单位为 100ns，转换为毫秒。"""
    return offset_100ns / 10000.0


def build_words(chunks: list[dict]) -> list[dict]:
    """从流式 chunk 中提取字级时间戳，过滤掉音频块。"""
    words = []
    for c in chunks:
        if c.get("type") == "WordBoundary":
            words.append(
                {
                    "text": c["text"],
                    "start_ms": _offset_to_ms(c["offset"]),
                    "duration_ms": _offset_to_ms(c["duration"]),
                }
            )
    return words


async def synthesize(text: str, voice: str = VOICE) -> tuple[bytes, list[dict]]:
    """合成语音，返回 (mp3 字节, 字级时间戳列表)。"""
    communicate = edge_tts.Communicate(text, voice, boundary="WordBoundary")
    audio = io.BytesIO()
    chunks: list[dict] = []
    async for chunk in communicate.stream():
        chunks.append(chunk)
        if chunk["type"] == "audio":
            audio.write(chunk["data"])
    return audio.getvalue(), build_words(chunks)
