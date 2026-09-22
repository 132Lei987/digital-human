# 文旅数字人「真人对话」功能实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 构建一个网页数字人应用：文字输入 → DeepSeek-flash 生成回复 → Edge TTS 合成语音（带字级时间戳）→ 前端按时间戳切换 4 张嘴型帧，实现「嘴跟话走」。

**架构：** FastAPI 后端串联「DeepSeek 生成 → Edge TTS 合成」，一次性返回音频 + 字级时间戳；前端用原生 HTML/JS 播放音频并对照时间戳切换嘴型帧图片。数字人形象由素材视频抽帧离线生成 4 张嘴型帧。

**技术栈：** Python 3.12 / FastAPI / edge-tts / openai（DeepSeek 兼容接口）/ numpy / pillow / imageio-ffmpeg / 原生 HTML+CSS+JS。

**规格文档：** `docs/superpowers/specs/2026-09-22-digital-human-design.md`

---

## 文件结构

```
digital-human/
├── backend/
│   ├── main.py            # FastAPI 入口：/api/chat 接口 + 静态资源托管
│   ├── llm.py             # DeepSeek-flash 调用，返回回复文本
│   ├── tts.py             # Edge TTS 合成，返回 mp3 + 字级时间戳
│   ├── mouthframes.py     # 离线抽帧：素材.mp4 → 4 张嘴型帧
│   ├── tests/
│   │   ├── test_llm.py
│   │   ├── test_tts.py
│   │   ├── test_mouthframes.py
│   │   └── test_main.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── assets/
│   ├── 素材.mp4           # 从仓库根目录复制而来
│   └── mouth_frames/      # mouthframes.py 的产物
├── .env.example
└── README.md
```

**职责边界：** `llm.py` 只负责「文本→文本」；`tts.py` 只负责「文本→音频+时间戳」；`main.py` 只做串联和 HTTP；`mouthframes.py` 是独立离线脚本，与运行期无关；前端只做「对表切帧」。各模块可独立测试。

---

## 任务 1：项目骨架与依赖

**文件：**
- 创建：`digital-human/backend/requirements.txt`
- 创建：`digital-human/backend/tests/__init__.py`（空文件，保证 pytest 能识别包）
- 创建：`digital-human/backend/__init__.py`（空文件）
- 创建：`digital-human/frontend/index.html`（占位）
- 创建：`digital-human/frontend/style.css`（占位）
- 创建：`digital-human/frontend/app.js`（占位）
- 创建：`digital-human/assets/mouth_frames/.gitkeep`
- 创建：`digital-human/.env.example`
- 创建：`digital-human/README.md`（骨架）
- 复制：仓库根目录 `素材.mp4` → `digital-human/assets/素材.mp4`

- [ ] **步骤 1：创建目录结构**

```bash
mkdir -p digital-human/backend/tests digital-human/frontend digital-human/assets/mouth_frames
cp 素材.mp4 digital-human/assets/素材.mp4
```

- [ ] **步骤 2：写 requirements.txt**

`digital-human/backend/requirements.txt`：

```
fastapi
uvicorn
edge-tts
openai
imageio-ffmpeg
numpy
pillow
httpx
pytest
```

- [ ] **步骤 3：写空 `__init__.py` 与占位文件**

```bash
touch digital-human/backend/__init__.py digital-human/backend/tests/__init__.py digital-human/assets/mouth_frames/.gitkeep
```

`digital-human/frontend/index.html`（占位，任务 6 会覆盖）：

```html
<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>文旅数字人</title></head><body>占位</body></html>
```

`digital-human/frontend/style.css`（占位）：

```css
/* 占位，任务 6 实现 */
```

`digital-human/frontend/app.js`（占位）：

```js
// 占位，任务 6 实现
```

- [ ] **步骤 4：写 .env.example**

`digital-human/.env.example`：

```
# DeepSeek API Key（必填），到 https://platform.deepseek.com 申请
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx

# 模型名，可按需改为你的 flash 型号
DEEPSEEK_MODEL=deepseek-chat
```

- [ ] **步骤 5：Commit**

```bash
git add digital-human/
git commit -m "chore: 数字人项目骨架与依赖"
```

---

## 任务 2：TTS 模块（tts.py）

**文件：**
- 创建：`digital-human/backend/tts.py`
- 测试：`digital-human/backend/tests/test_tts.py`

- [ ] **步骤 1：编写失败的测试**

`digital-human/backend/tests/test_tts.py`：

```python
from tts import _offset_to_ms, build_words


def test_offset_to_ms():
    assert _offset_to_ms(1000000) == 100.0
    assert _offset_to_ms(4625000) == 462.5


def test_build_words_只提取字级边界并过滤音频块():
    chunks = [
        {"type": "audio", "data": b"x"},
        {"type": "WordBoundary", "offset": 1000000, "duration": 4625000, "text": "你"},
        {"type": "WordBoundary", "offset": 8500000, "duration": 3250000, "text": "好"},
        {"type": "audio", "data": b"y"},
    ]
    assert build_words(chunks) == [
        {"text": "你", "start_ms": 100.0, "duration_ms": 462.5},
        {"text": "好", "start_ms": 850.0, "duration_ms": 325.0},
    ]
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd digital-human && python -m pytest backend/tests/test_tts.py -v
```

预期：FAIL，报错 `ModuleNotFoundError: No module named 'tts'`。

- [ ] **步骤 3：编写实现**

`digital-human/backend/tts.py`：

```python
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
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd digital-human && python -m pytest backend/tests/test_tts.py -v
```

预期：PASS（2 项通过）。

- [ ] **步骤 5：Commit**

```bash
git add digital-human/backend/tts.py digital-human/backend/tests/test_tts.py
git commit -m "feat: TTS 模块（Edge TTS + 字级时间戳）"
```

---

## 任务 3：LLM 模块（llm.py）

**文件：**
- 创建：`digital-human/backend/llm.py`
- 测试：`digital-human/backend/tests/test_llm.py`

- [ ] **步骤 1：编写失败的测试**

`digital-human/backend/tests/test_llm.py`：

```python
import asyncio

import llm


class _FakeCompletions:
    def __init__(self):
        self.last_kwargs = {}

    async def create(self, **kwargs):
        self.last_kwargs = kwargs
        return _FakeResp()


class _FakeResp:
    class _Choice:
        class _Msg:
            content = "你好，欢迎来到古城！"
        message = _Msg()
    choices = [_Choice()]


class _FakeChat:
    def __init__(self):
        self.completions = _FakeCompletions()


class _FakeClient:
    def __init__(self):
        self.chat = _FakeChat()


def test_generate_返回回复文本并传入模型名(monkeypatch):
    fake = _FakeClient()
    monkeypatch.setattr(llm, "_client", lambda: fake)
    result = asyncio.run(llm.generate("你好"))
    assert result == "你好，欢迎来到古城！"
    assert fake.chat.completions.last_kwargs["model"] == "deepseek-chat"


def test_generate_缺key时抛RuntimeError(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    try:
        asyncio.run(llm.generate("你好"))
    except RuntimeError:
        return
    assert False, "应当抛出 RuntimeError"
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd digital-human && python -m pytest backend/tests/test_llm.py -v
```

预期：FAIL，报错 `ModuleNotFoundError: No module named 'llm'`。

- [ ] **步骤 3：编写实现**

`digital-human/backend/llm.py`：

```python
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
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd digital-human && python -m pytest backend/tests/test_llm.py -v
```

预期：PASS（2 项通过）。

- [ ] **步骤 5：Commit**

```bash
git add digital-human/backend/llm.py digital-human/backend/tests/test_llm.py
git commit -m "feat: LLM 模块（DeepSeek 生成回复）"
```

---

## 任务 4：口型帧抽取（mouthframes.py）

**文件：**
- 创建：`digital-human/backend/mouthframes.py`
- 测试：`digital-human/backend/tests/test_mouthframes.py`

- [ ] **步骤 1：编写失败的测试**

`digital-human/backend/tests/test_mouthframes.py`：

```python
import numpy as np

from mouthframes import find_motion_bbox, select_frames_by_openness


def test_select_frames_by_openness_闭帧最小全帧最大():
    scores = np.array([0.0, 0.1, 0.5, 0.3, 0.9, 0.2])
    idx = select_frames_by_openness(scores)
    assert len(idx) == 4
    assert idx[0] == 0          # 最小分数 -> 闭嘴帧
    assert idx[-1] == 4         # 最大分数 -> 全张嘴帧
    assert len(set(idx)) == 4   # 不重复


def test_find_motion_bbox_定位闪烁区域():
    frames = []
    for i in range(6):
        f = np.zeros((40, 60), dtype=np.float32)
        f[25:35, 20:30] = 1.0 if i % 2 == 0 else 0.0  # 底部中央一块闪烁
        frames.append(f)
    x, y, w, h = find_motion_bbox(frames)
    assert 18 <= x <= 22
    assert 23 <= y <= 26
    assert w >= 8 and h >= 8
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd digital-human && python -m pytest backend/tests/test_mouthframes.py -v
```

预期：FAIL，报错 `ModuleNotFoundError: No module named 'mouthframes'`。

- [ ] **步骤 3：编写实现**

`digital-human/backend/mouthframes.py`：

```python
"""口型帧抽取：从素材视频抽取 4 张不同嘴型的帧（闭/微张/半张/全张）。

工单编号：人工智能CV-AIGC-18-文旅智能体-智能导览与互动体验任务

用法：python backend/mouthframes.py
输出：assets/mouth_frames/mouth_0.png ~ mouth_3.png（除嘴巴区域外画面一致）
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
VIDEO = PROJECT_ROOT / "assets" / "素材.mp4"
OUT_DIR = PROJECT_ROOT / "assets" / "mouth_frames"


def _run_ffmpeg(args: list[str]) -> None:
    subprocess.run([FFMPEG, "-y", *args], check=True, capture_output=True)


def extract_frames(video: str, out_dir: str, fps: int = 10, width: int = 720) -> list[str]:
    """抽取降采样帧用于分析，返回帧文件路径列表。"""
    _run_ffmpeg(["-i", video, "-vf", f"fps={fps},scale={width}:-2", f"{out_dir}/f_%04d.jpg"])
    return sorted(
        os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.endswith(".jpg")
    )


def find_motion_bbox(frames: list[np.ndarray]) -> tuple[int, int, int, int]:
    """用帧间差异定位嘴巴区域，返回 (x, y, w, h)。

    frames: 灰度帧列表，形状 (H, W)，取值 0~1。
    """
    motion = np.zeros_like(frames[0])
    for a, b in zip(frames[:-1], frames[1:]):
        motion += np.abs(a.astype(np.float32) - b.astype(np.float32))
    motion /= len(frames) - 1  # 平均帧间差异
    mask = motion > 0.05
    ys, xs = np.where(mask)
    if len(xs) == 0:
        h, w = mask.shape
        return (int(w * 0.35), int(h * 0.5), int(w * 0.3), int(h * 0.3))
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    pad_y = int((y1 - y0) * 0.6)  # 向下扩展容纳张嘴时下颌下移
    return (x0, y0, x1 - x0 + 1, y1 - y0 + 1 + pad_y)


def openness_scores(frames: list[np.ndarray], bbox: tuple[int, int, int, int]) -> np.ndarray:
    """计算每帧嘴巴区域相对中位帧的差异，作为张嘴程度。"""
    x, y, w, h = bbox
    crops = np.stack([f[y:y + h, x:x + w] for f in frames])
    med = np.median(crops, axis=0)
    return np.array([float(np.mean(np.abs(c - med))) for c in crops])


def select_frames_by_openness(scores: np.ndarray) -> list[int]:
    """按张嘴程度选 4 帧：闭 / 微张 / 半张 / 全张，返回帧索引。"""
    order = np.argsort(scores)
    n = len(scores)

    def pick(frac: float) -> int:
        return int(order[int((n - 1) * frac)])

    return [int(order[0]), pick(0.33), pick(0.66), int(order[-1])]


def composite_frames(
    frame_files: list[str],
    indices: list[int],
    bbox: tuple[int, int, int, int],
    out_dir: Path,
) -> None:
    """以闭合帧为底图，把其余 3 帧的嘴巴区域贴到底图，输出 4 张全尺寸帧。"""
    x, y, w, h = bbox
    base = Image.open(frame_files[indices[0]]).convert("RGB")
    base.save(out_dir / "mouth_0.png")
    for i, idx in enumerate(indices[1:], start=1):
        img = Image.open(frame_files[idx]).convert("RGB")
        mouth = img.crop((x, y, x + w, y + h))
        out = base.copy()
        out.paste(mouth, (x, y))
        out.save(out_dir / f"mouth_{i}.png")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        files = extract_frames(str(VIDEO), tmp)
        gray = [
            np.asarray(Image.open(f).convert("L"), dtype=np.float32) / 255.0
            for f in files
        ]
        bbox = find_motion_bbox(gray)
        scores = openness_scores(gray, bbox)
        indices = select_frames_by_openness(scores)
        composite_frames(files, indices, bbox, OUT_DIR)
    print(f"已生成 4 张嘴型帧到 {OUT_DIR}")
    print(f"嘴巴区域 bbox={bbox}，选中帧索引(闭/微张/半张/全张)={indices}")


if __name__ == "__main__":
    main()
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd digital-human && python -m pytest backend/tests/test_mouthframes.py -v
```

预期：PASS（2 项通过）。

- [ ] **步骤 5：对真实素材运行抽帧脚本**

```bash
cd digital-human && python backend/mouthframes.py
```

预期：输出 `已生成 4 张嘴型帧...`，`assets/mouth_frames/` 下出现 `mouth_0.png` ~ `mouth_3.png` 四个文件，尺寸一致（约 720 宽）。

- [ ] **步骤 6：Commit**

```bash
git add digital-human/backend/mouthframes.py digital-human/backend/tests/test_mouthframes.py digital-human/assets/mouth_frames/
git commit -m "feat: 口型帧抽取脚本（素材视频 → 4 张嘴型帧）"
```

---

## 任务 5：FastAPI 主服务（main.py）

**文件：**
- 创建：`digital-human/backend/main.py`
- 测试：`digital-human/backend/tests/test_main.py`

- [ ] **步骤 1：编写失败的测试**

`digital-human/backend/tests/test_main.py`：

```python
from fastapi.testclient import TestClient

import main


def test_chat_success(monkeypatch):
    async def fake_generate(text):
        return "你好，欢迎来到古城！"

    async def fake_synthesize(text):
        return (
            b"fake-mp3-bytes",
            [{"text": "你", "start_ms": 0.0, "duration_ms": 400.0}],
        )

    monkeypatch.setattr(main, "generate", fake_generate)
    monkeypatch.setattr(main, "synthesize", fake_synthesize)
    client = TestClient(main.app)
    r = client.post("/api/chat", json={"message": "你好"})
    assert r.status_code == 200
    data = r.json()
    assert data["reply_text"] == "你好，欢迎来到古城！"
    assert data["audio_base64"] is not None
    assert len(data["words"]) == 1


def test_chat_empty_message_返回400():
    client = TestClient(main.app)
    r = client.post("/api/chat", json={"message": "   "})
    assert r.status_code == 400
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd digital-human && python -m pytest backend/tests/test_main.py -v
```

预期：FAIL，报错 `ModuleNotFoundError: No module named 'main'`。

- [ ] **步骤 3：编写实现**

`digital-human/backend/main.py`：

```python
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
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd digital-human && python -m pytest backend/tests/test_main.py -v
```

预期：PASS（2 项通过）。

- [ ] **步骤 5：Commit**

```bash
git add digital-human/backend/main.py digital-human/backend/tests/test_main.py
git commit -m "feat: FastAPI 主服务（/api/chat + 静态托管）"
```

---

## 任务 6：前端（index.html / style.css / app.js）

**文件：**
- 修改：`digital-human/frontend/index.html`
- 修改：`digital-human/frontend/style.css`
- 修改：`digital-human/frontend/app.js`

- [ ] **步骤 1：编写 index.html**

`digital-human/frontend/index.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>文旅数字人</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <div id="stage">
    <img id="avatar" src="/assets/mouth_frames/mouth_0.png" alt="数字人">
  </div>
  <div id="controls">
    <input id="input" type="text" placeholder="输入你的问题，例如：介绍一下这座古城">
    <button id="send">发送</button>
  </div>
  <audio id="audio"></audio>
  <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **步骤 2：编写 style.css**

`digital-human/frontend/style.css`：

```css
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  background: #14161a;
  color: #eee;
  font-family: "Microsoft YaHei", sans-serif;
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
}

#stage {
  width: min(720px, 92vw);
  aspect-ratio: 16 / 9;
  border-radius: 12px;
  overflow: hidden;
  background: #000;
}

#avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

#controls {
  display: flex;
  gap: 10px;
  width: min(720px, 92vw);
}

#input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #333;
  border-radius: 8px;
  background: #1e2126;
  color: #eee;
  font-size: 15px;
}

#send {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  background: #2f6fed;
  color: #fff;
  font-size: 15px;
  cursor: pointer;
}

#send:disabled { opacity: 0.5; cursor: not-allowed; }
```

- [ ] **步骤 3：编写 app.js**

`digital-human/frontend/app.js`：

```js
// 工单编号：人工智能CV-AIGC-18-文旅智能体-智能导览与互动体验任务
const avatar = document.getElementById('avatar');
const audio = document.getElementById('audio');
const input = document.getElementById('input');
const send = document.getElementById('send');

const MOUTH = [
  '/assets/mouth_frames/mouth_0.png',
  '/assets/mouth_frames/mouth_1.png',
  '/assets/mouth_frames/mouth_2.png',
  '/assets/mouth_frames/mouth_3.png',
];

let words = [];
let rafId = null;

function mouthLevelForWord(word) {
  if (!word) return 0;              // 不说话 -> 闭嘴
  if (word.duration_ms < 250) return 1;  // 短音 -> 微张
  if (word.duration_ms < 450) return 2;  // 中音 -> 半张
  return 3;                             // 长音 -> 全张
}

function currentWord(tMs) {
  for (const w of words) {
    if (tMs >= w.start_ms && tMs <= w.start_ms + w.duration_ms) return w;
  }
  return null;
}

function tick() {
  const tMs = audio.currentTime * 1000;
  avatar.src = MOUTH[mouthLevelForWord(currentWord(tMs))];
  rafId = requestAnimationFrame(tick);
}

function stopPlayback() {
  cancelAnimationFrame(rafId);
  audio.pause();
  audio.currentTime = 0;
  avatar.src = MOUTH[0];
}

function base64ToBlob(b64, mime) {
  const bin = atob(b64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  return new Blob([arr], { type: mime });
}

async function sendMessage() {
  const message = input.value.trim();
  if (!message) return;
  input.value = '';
  send.disabled = true;
  stopPlayback();
  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    const data = await resp.json();
    if (data.audio_base64) {
      audio.src = URL.createObjectURL(base64ToBlob(data.audio_base64, 'audio/mpeg'));
      words = data.words || [];
      await audio.play();
      tick();
    } else {
      console.warn('未返回音频', data.error);
      avatar.src = MOUTH[0];
    }
  } catch (e) {
    console.error(e);
    avatar.src = MOUTH[0];
  } finally {
    send.disabled = false;
  }
}

send.addEventListener('click', sendMessage);
input.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMessage(); });
audio.addEventListener('ended', () => {
  cancelAnimationFrame(rafId);
  avatar.src = MOUTH[0];
});
```

- [ ] **步骤 4：启动服务做手动冒烟验证**

```bash
cd digital-human && DEEPSEEK_API_KEY=sk-xxx python -m uvicorn backend.main:app --reload
```

浏览器打开 `http://127.0.0.1:8000/`，确认：页面显示数字人、有输入框；输入"你好"发送后能听到语音、嘴型随语音切换（需先填真实 Key）。

- [ ] **步骤 5：Commit**

```bash
git add digital-human/frontend/
git commit -m "feat: 数字人前端（口型同步 + 语音播放）"
```

---

## 任务 7：端到端联调与 README 完善

**文件：**
- 修改：`digital-human/README.md`

- [ ] **步骤 1：全量测试**

```bash
cd digital-human && python -m pytest backend/tests -v
```

预期：全部 PASS（8 项）。

- [ ] **步骤 2：真实端到端验证**

```bash
cd digital-human
# 先设置真实 Key（Windows PowerShell: $env:DEEPSEEK_API_KEY="sk-xxx"）
python -m uvicorn backend.main:app --reload
```

浏览器访问 `http://127.0.0.1:8000/`，逐条验证规格文档 8.1 节的测试点（你好 / 长句 / 连续发送 / 断网兜底等）。

- [ ] **步骤 3：完善 README**

`digital-human/README.md`：

````markdown
# 文旅数字人「真人对话」演示

工单编号：人工智能CV-AIGC-18-文旅智能体-智能导览与互动体验任务

## 功能

文字输入 → DeepSeek-flash 生成回复 → Edge TTS 合成语音（字级时间戳）→ 数字人嘴型随语音同步切换。

## 环境要求

- Python 3.12
- 依赖：`pip install -r backend/requirements.txt`

## 配置

复制 `.env.example` 为 `.env` 并填写 `DEEPSEEK_API_KEY`（到 https://platform.deepseek.com 申请）。
或直接设置环境变量：

- Windows PowerShell：`$env:DEEPSEEK_API_KEY="sk-xxx"`
- Linux/macOS：`export DEEPSEEK_API_KEY=sk-xxx`

## 运行

```bash
# 1. 首次运行先抽取嘴型帧
python backend/mouthframes.py

# 2. 启动服务
python -m uvicorn backend.main:app --reload
```

浏览器打开 http://127.0.0.1:8000/

## 测试

```bash
python -m pytest backend/tests -v
```
````

- [ ] **步骤 4：Commit**

```bash
git add digital-human/README.md
git commit -m "docs: 数字人 README（配置与运行说明）"
```

---

## 自检记录

- **规格覆盖度：** 规格九节均已映射——架构/数据流→任务 5；项目结构→任务 1；组件职责→任务 2/3/4；核心算法（抽帧、字级映射、同步）→任务 4/6；错误处理→任务 5（后端兜底）与任务 6（前端兜底）；测试验收→任务 2/3/4/5/7。
- **占位符扫描：** 无「待定/TODO」；每个代码步骤均含完整可运行代码。
- **类型一致性：** `build_words` 返回 `[{text, start_ms, duration_ms}]`，前端 `currentWord` 读取同名字段；`synthesize` 返回 `(bytes, list)`，`main.py` 解包为 `audio, words`；`select_frames_by_openness` 返回 4 个索引，`composite_frames` 按序消费。字段名全链路一致。
