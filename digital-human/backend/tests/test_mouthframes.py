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
    # 闪烁块在 y=25~35（图高 40 的 62%~87%），属于下半部分，因此需传
    # upper_limit=1.0 做全图搜索，验证密度峰值能定位到该块。
    x, y, w, h = find_motion_bbox(frames, upper_limit=1.0)
    # 窗口尺寸 > 0 且不超出画面
    assert 0 < w <= 60 and 0 < h <= 40
    # bbox 中心落在闪烁块中心 (30, 25) 附近
    cx, cy = x + w / 2, y + h / 2
    assert abs(cx - 25.0) <= 5
    assert abs(cy - 30.0) <= 5
