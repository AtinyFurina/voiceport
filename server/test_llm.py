"""llm.py 单元测试：mock，不真实调用 API。"""
import llm


def test_deepseek_chat(monkeypatch):
    captured = {}

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "改好的文本"}}]}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return FakeResp()

    monkeypatch.setattr(llm.requests, "post", fake_post)
    c = llm.DeepseekLlm("sk-ds", model="deepseek-chat")
    out = c.chat([{"role": "user", "content": "hi"}])
    assert out == "改好的文本"
    assert captured["url"] == "https://api.deepseek.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer sk-ds"
    assert captured["json"]["model"] == "deepseek-chat"
    assert captured["json"]["messages"] == [{"role": "user", "content": "hi"}]
    assert captured["json"]["stream"] is False


def test_get_llm(monkeypatch):
    monkeypatch.setattr(llm.config, "deepseek_model", "deepseek-chat")
    assert isinstance(llm.get_llm(), llm.DeepseekLlm)
