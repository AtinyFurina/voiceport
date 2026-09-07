"""修改阶段：用 LLM 把语音修改指令应用到草稿，返回修改后的完整文本。"""
from llm import DeepseekLlm, get_llm

SYSTEM_PROMPT = (
    "你是文本编辑助手。根据用户的修改指令修改给定草稿。要求：\n"
    "1) 只修改指令指定的部分，不改动其他内容；\n"
    "2) 保持未指定部分的原意与措辞；\n"
    "3) 只输出修改后的完整文本，不要任何解释、不要加引号或代码块；\n"
    "4) 若指令要求换行/另起一行，在对应位置使用换行符。"
)


class Editor:
    def __init__(self, llm: DeepseekLlm | None = None):
        self.llm = llm if llm is not None else get_llm()

    def apply_edit(self, draft: str, instruction: str) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"草稿：\n{draft}\n\n修改指令：{instruction}"},
        ]
        return self.llm.chat(messages).strip()
