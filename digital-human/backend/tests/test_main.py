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
