# 文旅数字人「真人对话」演示

工单编号：人工智能CV-AIGC-18-文旅智能体-智能导览与互动体验任务

## 功能

文字输入 → DeepSeek 生成回复 → Edge TTS 合成语音（字级时间戳）→ 数字人嘴型随语音同步切换（4 张嘴型帧）。

## 环境要求

- Python 3.12
- 依赖安装：`pip install -r backend/requirements.txt`

## 配置

设置 DeepSeek API Key 环境变量（到 https://platform.deepseek.com 申请）：

- Windows PowerShell：`$env:DEEPSEEK_API_KEY="sk-xxx"`
- Linux/macOS：`export DEEPSEEK_API_KEY="sk-xxx"`

可选：`DEEPSEEK_MODEL` 环境变量指定模型名，默认 `deepseek-chat`。

## 运行

```bash
# 1. 首次运行先抽取嘴型帧（素材 video 需已放在 assets/ 下）
cd backend && python mouthframes.py && cd ..

# 2. 启动服务（从 backend 目录启动）
cd backend && python -m uvicorn main:app --reload
```

浏览器打开 http://127.0.0.1:8000/ ，输入问题即可对话。

## 测试

```bash
python -m pytest backend/tests -v
```

## 项目结构

```
backend/    # FastAPI 后端（main/llm/tts/mouthframes）
frontend/   # 前端（index.html/style.css/app.js）
assets/     # 素材视频 + 嘴型帧
```
