"""editor.py 单元测试：mock LLM，不真实调用 API。"""
import editor


class FakeLlm:
    def __init__(self, out):
        self.out = out
        self.calls = []

    def chat(self, messages):
        self.calls.append(messages)
        return self.out


def test_apply_edit():
    fake = FakeLlm("把 hello 改成 world\n第二行")
    e = editor.Editor(fake)
    out = e.apply_edit("hello\n第一行", "把 hello 改成 world")
    assert out == "把 hello 改成 world\n第二行"

    msgs = fake.calls[0]
    assert msgs[0]["role"] == "system"
    assert "只修改" in msgs[0]["content"]
    assert msgs[1]["role"] == "user"
    assert "hello\n第一行" in msgs[1]["content"]
    assert "把 hello 改成 world" in msgs[1]["content"]


def test_apply_edit_strips():
    fake = FakeLlm("  结果  ")
    e = editor.Editor(fake)
    assert e.apply_edit("草稿", "指令") == "结果"
