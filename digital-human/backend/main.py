"""FastAPI 主服务：数字人对话接口 + 静态资源托管。

工单编号：人工智能CV-AIGC-18-文旅智能体-智能导览与互动体验任务
"""
from __future__ import annotations

import base64
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from llm import generate
from tts import synthesize

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

app = FastAPI(title="文旅数字人")

app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "frontend")), name="static")
app.mount("/assets", StaticFiles(directory=str(PROJECT_ROOT / "assets")), name="assets")


class ChatRequest(BaseModel):
    message: str


@app.get("/")
async def index():
    return FileResponse(str(PROJECT_ROOT / "frontend" / "index.html"))


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not req.message.strip():
        return JSONResponse({"error": "消息不能为空"}, status_code=400)

    try:
        reply = await generate(req.message)
    except Exception as e:  # noqa: BLE001 - 兜底，保证接口不崩
        return JSONResponse(
            {
                "reply_text": "抱歉，我暂时没听清，请稍后再试。",
                "audio_base64": None,
                "words": [],
                "error": f"LLM 调用失败: {e}",
            }
        )

    try:
        audio, words = await synthesize(reply)
        audio_b64 = base64.b64encode(audio).decode("ascii")
    except Exception as e:  # noqa: BLE001 - 兜底，保证接口不崩
        return JSONResponse(
            {
                "reply_text": reply,
                "audio_base64": None,
                "words": [],
                "error": f"TTS 合成失败: {e}",
            }
        )

    return {"reply_text": reply, "audio_base64": audio_b64, "words": words}
