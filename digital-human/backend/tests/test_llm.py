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
