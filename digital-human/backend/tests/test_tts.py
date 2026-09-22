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
