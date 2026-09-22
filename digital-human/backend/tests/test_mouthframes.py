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
