"""服务端配置。密钥优先级：环境变量 > ~/.passport/config.json > 空。

config.json 由 config_gui.py（程序内输入框）写入，禁止把密钥硬编码进代码或入库。
"""
import json
import os
import socket
import uuid
from dataclasses import dataclass
from pathlib import Path

_PASSPORT_DIR = Path.home() / ".passport"
_CONFIG_FILE = _PASSPORT_DIR / "config.json"


def _load_or_create_server_id() -> str:
    path = _PASSPORT_DIR / "server_id"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    _PASSPORT_DIR.mkdir(parents=True, exist_ok=True)
    sid = str(uuid.uuid4())
    path.write_text(sid, encoding="utf-8")
    return sid


def _load_config_file() -> dict:
    try:
        if _CONFIG_FILE.exists():
            return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _env_or_file(name: str, key: str, default: str = "") -> str:
    return os.environ.get(name) or _FILE_CFG.get(key, default)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return int(raw) if raw else default


_FILE_CFG = _load_config_file()


@dataclass
class Config:
    # --- 网络 ---
    bind_host: str = "0.0.0.0"
    port: int = _env_int("PASSPORT_PORT", 8765)
    host: str = socket.gethostname()
    server_id: str = _load_or_create_server_id()

    # --- STT ---
    stt_provider: str = os.environ.get("PASSPORT_STT_PROVIDER", "iflytek")  # iflytek | siliconflow
    iflytek_appid: str = _env_or_file("IFLYTEK_APPID", "iflytek_appid")
    iflytek_api_key: str = _env_or_file("IFLYTEK_API_KEY", "iflytek_api_key")
    iflytek_api_secret: str = _env_or_file("IFLYTEK_API_SECRET", "iflytek_api_secret")
    siliconflow_api_key: str = _env_or_file("SILICONFLOW_API_KEY", "siliconflow_api_key")
    siliconflow_stt_model: str = os.environ.get(
        "SILICONFLOW_STT_MODEL", "FunAudioLLM/SenseVoiceSmall"
    )

    # --- LLM ---
    deepseek_api_key: str = _env_or_file("DEEPSEEK_API_KEY", "deepseek_api_key")
    deepseek_model: str = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    deepseek_base_url: str = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    # --- 注入 ---
    inject_backend: str = os.environ.get("PASSPORT_INJECT_BACKEND", "sendinput")  # sendinput | tsf

    # --- 历史/偏好 ---
    db_path: str = os.environ.get("PASSPORT_DB", str(_PASSPORT_DIR / "history.db"))
    preference_batch: int = _env_int("PASSPORT_PREF_BATCH", 20)


config = Config()
