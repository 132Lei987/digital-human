# 文旅数字人「真人对话」项目

> 工单编号：人工智能CV-AIGC-18-文旅智能体-智能导览与互动体验任务

一个能「像真人一样对话」的数字人网页应用：你在网页里打字提问，数字人用语音回答，而且**嘴巴会跟着说的话一张一合**（口型同步）。

## 一、它是什么 / 怎么工作的

整条链路是这样的：

```
你打字提问
   ↓
后端调 DeepSeek 大模型 → 生成回复文本
   ↓
Edge TTS 把回复合成语音，并给出「每个字在音频里的时间点」
   ↓
前端播放语音，同时照着时间点切换数字人的嘴型帧
   ↓
效果：数字人一边说话，嘴巴一边跟着动
```

一句话总结：**文字进 → 语音出 → 嘴跟话走**。

## 二、目录结构

```
day6_week1_digital-human/
├── digital-human/                    # 项目本体
│   ├── backend/                      # Python 后端（FastAPI）
│   │   ├── main.py                   # 入口：/api/chat 接口 + 托管静态资源
│   │   ├── llm.py                    # 调 DeepSeek 生成回复
│   │   ├── tts.py                    # 调 Edge TTS 合成语音 + 字级时间戳
│   │   ├── mouthframes.py            # 从素材视频抽取 4 张嘴型帧（离线脚本）
│   │   ├── tests/                    # 单元测试（8 个用例）
│   │   └── requirements.txt          # 后端依赖清单
│   ├── frontend/                     # 前端（原生 HTML/CSS/JS）
│   │   ├── index.html
│   │   ├── style.css
│   │   └── app.js                    # 播放语音 + 口型同步逻辑
│   ├── assets/
│   │   ├── 素材.mp4                  # 数字人素材视频（口型帧从这里抽取）
│   │   └── mouth_frames/             # 抽好的 4 张嘴型帧（mouth_0~3.png）
│   └── README.md                     # 项目内说明（含配置与运行）
├── requirements.txt                  # 一键安装全部依赖（本文件）
├── 素材.mp4                          # 素材视频的冗余副本（与 assets 内相同）
├── docs/superpowers/
│   ├── specs/                        # 设计文档
│   └── plans/                        # 实现计划
└── 03-Agent数字人项目-文旅智能体方向/  # 原始任务工单（5 份）
```

## 三、环境要求

- **Python 3.10+**（本项目在 **3.12.7** 下验证通过）
- Windows / macOS / Linux 均可
- 能访问外网（调 DeepSeek API 和 Edge TTS 需要）

## 四、快速开始（从零跑通，约 5 分钟）

### 第 1 步：安装依赖

在项目根目录执行：

```bash
pip install -r requirements.txt
```

> 国内网络慢的话，用清华源加速：
> ```bash
> pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
> ```

### 第 2 步：配置 DeepSeek API Key

到 [https://platform.deepseek.com](https://platform.deepseek.com) 注册并申请一个 API Key，然后设置环境变量：

**Windows（PowerShell）：**
```powershell
$env:DEEPSEEK_API_KEY="sk-你的key"
```

**macOS / Linux：**
```bash
export DEEPSEEK_API_KEY="sk-你的key"
```

> 没配 key 也能启动、能打开页面，只是发消息时会得到一句兜底回复「抱歉，我暂时没听清，请稍后再试」。想真正对话，必须配 key。

### 第 3 步：抽取嘴型帧（首次运行才需要）

```bash
cd digital-human/backend
python mouthframes.py
cd ../..
```

会生成 `digital-human/assets/mouth_frames/` 下的 4 张嘴型帧。**如果这个目录里已经有 `mouth_0.png`~`mouth_3.png`，这步可以跳过。**

> 注意：脚本会读取 `digital-human/assets/素材.mp4`，所以素材视频必须放在那里且文件名是 `素材.mp4`。

### 第 4 步：启动服务

```bash
cd digital-human/backend
python -m uvicorn main:app --reload
```

> ⚠️ 必须从 `backend` 目录启动（`python -m uvicorn main:app`），
> 不要从项目根目录写 `python -m uvicorn backend.main:app`——那样会报 `No module named 'llm'`。

看到类似下面的输出就说明启动成功了：

```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 第 5 步：打开浏览器对话

浏览器访问 **http://127.0.0.1:8000/**

在输入框里输入问题（比如「介绍一下这座古城」），点发送，数字人就会开口说话、嘴巴跟着动。

## 五、运行测试

```bash
cd digital-human
python -m pytest backend/tests -v
```

预期 **8 个测试全部通过**。

## 六、常见问题（FAQ）

| 问题 | 原因 | 解决 |
|------|------|------|
| 启动报 `No module named 'llm'` | 从根目录用 `backend.main:app` 启动了 | 必须 `cd digital-human/backend` 后再 `python -m uvicorn main:app` |
| 发消息回「抱歉，我暂时没听清」 | 没配 `DEEPSEEK_API_KEY` | 按上面第 2 步配置环境变量后重启服务 |
| 数字人图片不显示 / 裂图 | `mouth_frames/` 目录缺失 | 先跑第 3 步的 `mouthframes.py` 抽帧 |
| 抽帧报 `FileNotFoundError` | 素材文件名/位置不对 | 素材必须叫 `素材.mp4` 且放在 `digital-human/assets/` 下 |
| 端口 8000 被占用 | 别的程序占了端口 | 加 `--port 8080` 换个端口，浏览器访问对应端口 |

## 七、技术栈一览

| 环节 | 技术 |
|------|------|
| 大模型 | DeepSeek（OpenAI 兼容接口） |
| 语音合成 | Edge TTS（免费、无需 key、带字级时间戳） |
| 后端 | Python + FastAPI |
| 前端 | 原生 HTML / CSS / JavaScript |
| 数字人形象 | 素材视频抽帧 → 4 张嘴型帧切换 |
| 口型同步 | 字级时间戳精确对齐（按字时长映射张嘴幅度） |

## 八、说明

- 本功能对应工单 18「智能导览与互动体验」的数字人导览部分；完整的文旅智能体还包括多模态 RAG（工单 17）、创意内容生成（工单 19）、集成部署（工单 20），详见 `03-Agent数字人项目-文旅智能体方向/` 下的工单。
- 详细设计见 `docs/superpowers/specs/2026-09-22-digital-human-design.md`。
- 代码注释中均已标注工单编号。
