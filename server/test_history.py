"""history.py 单元测试：用临时 SQLite，不真实调用 LLM。"""
import history


def test_add_and_recent_isolated(tmp_path):
    h = history.History(str(tmp_path / "test.db"))
    h.add("dev1", "草稿A", "最终A", "窗口A")
    h.add("dev2", "草稿B", "最终B", "窗口B")
    rows = h.recent("dev1")
    assert len(rows) == 1
    assert rows[0] == ("草稿A", "最终A", "窗口A")


def test_summarize_preferences_empty(tmp_path, monkeypatch):
    h = history.History(str(tmp_path / "test.db"))
    assert h.summarize_preferences("dev-x") == ""


def test_summarize_preferences_calls_llm(tmp_path, monkeypatch):
    h = history.History(str(tmp_path / "test.db"))
    h.add("dev1", "草稿", "最终", "窗口")

    captured = {}

    class FakeLlm:
        def chat(self, messages):
            captured["messages"] = messages
            return "偏好要点"

    monkeypatch.setattr(history, "get_llm", lambda: FakeLlm())
    out = h.summarize_preferences("dev1")
    assert out == "偏好要点"
    assert captured["messages"][0]["role"] == "system"
    assert "草稿" in captured["messages"][1]["content"]
