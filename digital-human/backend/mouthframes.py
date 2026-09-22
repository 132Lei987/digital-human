"""口型帧抽取：从素材视频抽取 4 张不同嘴型的帧（闭/微张/半张/全张）。

工单编号：人工智能CV-AIGC-18-文旅智能体-智能导览与互动体验任务

用法：cd backend && python mouthframes.py
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


def find_motion_bbox(
    frames: list[np.ndarray],
    upper_limit: float = 0.65,
    window_w_frac: float = 0.18,
    window_h_frac: float = 0.10,
) -> tuple[int, int, int, int]:
    """用运动密度峰值定位嘴巴区域，返回 (x, y, w, h)。

    frames: 灰度帧列表，形状 (H, W)，取值 0~1。

    思路：固定阈值会因全局低幅运动/压缩噪声而把大量噪声像素算进包围盒，
    导致 bbox 膨胀到整个画面。这里改为滑窗积分（二维前缀和）求运动密度最大
    的窗口：把窗口中心锚定在运动密度峰值处，返回该窗口作为 bbox。

    upper_limit: 搜索范围限制（占图上部的比例）。真实半身像素材嘴巴在画面上部，
        默认 0.65 只搜 y < 65% 高度，避免下半身/背景噪声干扰；合成测试可传 1.0
        做全图搜索。
    """
    motion = np.zeros_like(frames[0], dtype=np.float64)
    for a, b in zip(frames[:-1], frames[1:]):
        motion += np.abs(a.astype(np.float64) - b.astype(np.float64))
    motion /= len(frames) - 1  # 平均帧间差异

    h, w = motion.shape

    # 窗口尺寸：画面宽高的合理比例，至少 4px，且不超过画面尺寸
    win_w = int(max(4, min(w, round(w * window_w_frac))))
    win_h = int(max(4, min(h, round(h * window_h_frac))))
    win_w = min(win_w, w)
    win_h = min(win_h, h)

    def _locate(m: np.ndarray) -> tuple[int, int] | None:
        mh, mw = m.shape
        if mh < win_h or mw < win_w:
            return None
        # 二维前缀和：motion 窗口积分
        ps = np.zeros((mh + 1, mw + 1), dtype=np.float64)
        np.cumsum(m, axis=0, out=ps[1:, 1:])
        np.cumsum(ps, axis=1, out=ps)
        # 每个窗口 (i, j)~(i+win_h, j+win_w) 的和
        a = ps[:-win_h, :-win_w]
        b = ps[win_h:, : -win_w]
        c = ps[: -win_h, win_w:]
        d = ps[win_h:, win_w:]
        sums = a + d - b - c
        idx = int(np.argmax(sums))
        by = idx // sums.shape[1]
        bx = idx % sums.shape[1]
        # 返回窗口左上角
        return (bx, by)

    pos = _locate(motion[: int(h * upper_limit), :]) if upper_limit > 0 else None
    if pos is None:  # 限制范围内无有效运动，回退到全图搜索
        pos = _locate(motion)
        if pos is None:
            return (0, 0, win_w, win_h)
    x, y = pos
    return (int(x), int(y), win_w, win_h)


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
