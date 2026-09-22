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
