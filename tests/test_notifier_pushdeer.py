import asyncio

import pytest

from src.core import notifier
from src.core.notifier import CHANNEL_TYPES, NotifierManager


class _FakeResponse:
    def __init__(self, data: dict):
        self._data = data

    def json(self):
        return self._data


class _FakeAsyncClient:
    response_data = {"code": 0, "message": "success"}
    calls: list[dict] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, *, data=None, timeout=None):
        self.calls.append({"url": url, "data": data, "timeout": timeout})
        return _FakeResponse(self.response_data)


def test_channel_types_include_pushdeer():
    assert CHANNEL_TYPES["pushdeer"] == {
        "label": "PushDeer",
        "fields": ["tokenid"],
    }


def test_send_pushdeer_success(monkeypatch):
    _FakeAsyncClient.calls = []
    _FakeAsyncClient.response_data = {"code": 0, "message": "success"}
    monkeypatch.setattr(notifier.httpx, "AsyncClient", _FakeAsyncClient)

    mgr = NotifierManager()
    asyncio.run(
        mgr._send_pushdeer(
            {"tokenid": "PDU_test"},
            "测试标题",
            "正文内容",
        )
    )

    assert _FakeAsyncClient.calls == [
        {
            "url": "https://api2.pushdeer.com/message/push",
            "data": {
                "pushkey": "PDU_test",
                "text": "测试标题\n\n正文内容",
            },
            "timeout": 30,
        }
    ]


def test_send_pushdeer_failure(monkeypatch):
    _FakeAsyncClient.calls = []
    _FakeAsyncClient.response_data = {"code": 1, "message": "bad token"}
    monkeypatch.setattr(notifier.httpx, "AsyncClient", _FakeAsyncClient)

    mgr = NotifierManager()
    with pytest.raises(RuntimeError, match="bad token"):
        asyncio.run(mgr._send_pushdeer({"tokenid": "PDU_bad"}, "标题", "正文"))
