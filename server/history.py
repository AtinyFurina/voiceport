"""历史记录（SQLite，按 device_id 隔离）+ LLM 偏好总结。"""
import sqlite3
import time

from config import config
from llm import get_llm


class History:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or config.db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entries(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    draft_text TEXT NOT NULL,
                    final_text TEXT NOT NULL,
                    window_title TEXT NOT NULL DEFAULT '',
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS edits(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    draft_before TEXT NOT NULL,
                    instruction TEXT NOT NULL,
                    draft_after TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )

    def add(self, device_id: str, draft_text: str, final_text: str, window_title: str = "") -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO entries(device_id, draft_text, final_text, window_title, created_at)"
                " VALUES(?,?,?,?,?)",
                (device_id, draft_text, final_text, window_title, time.time()),
            )

    def add_edit(self, device_id: str, draft_before: str, instruction: str, draft_after: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO edits(device_id, draft_before, instruction, draft_after, created_at)"
                " VALUES(?,?,?,?,?)",
                (device_id, draft_before, instruction, draft_after, time.time()),
            )

    def recent(self, device_id: str, n: int = 20) -> list[tuple[str, str, str]]:
        with self._connect() as conn:
            if device_id:
                rows = conn.execute(
                    "SELECT draft_text, final_text, window_title FROM entries"
                    " WHERE device_id=? ORDER BY id DESC LIMIT ?",
                    (device_id, n),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT draft_text, final_text, window_title FROM entries"
                    " ORDER BY id DESC LIMIT ?",
                    (n,),
                ).fetchall()
        return list(rows)

    def recent_edits(self, device_id: str, n: int = 50) -> list[tuple[str, str, str]]:
        with self._connect() as conn:
            if device_id:
                rows = conn.execute(
                    "SELECT draft_before, instruction, draft_after FROM edits"
                    " WHERE device_id=? ORDER BY id DESC LIMIT ?",
                    (device_id, n),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT draft_before, instruction, draft_after FROM edits"
                    " ORDER BY id DESC LIMIT ?",
                    (n,),
                ).fetchall()
        return list(rows)

    def summarize_preferences(self, device_id: str) -> str:
        """用 LLM 总结最近输入偏好（原始识别 -> 最终发送）。"""
        entries = self.recent(device_id, config.preference_batch)
        if not entries:
            return ""
        samples = "\n".join(f"- {d} -> {f}（窗口:{w}）" for d, f, w in entries)
        llm = get_llm()
        return llm.chat(
            [
                {
                    "role": "system",
                    "content": "以下是用户的语音输入记录（原始识别 → 最终发送）。"
                    "总结用户的表达习惯、常用词、缩写与纠错偏好，用于优化后续识别。简洁输出要点。",
                },
                {"role": "user", "content": samples},
            ]
        ).strip()
