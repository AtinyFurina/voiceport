"""config.py 单元测试：验证 config.json 读取与优先级（环境变量 > 文件）。"""
import json

import config as C


def test_load_config_file(tmp_path, monkeypatch):
    f = tmp_path / "c.json"
    f.write_text(json.dumps({"deepseek_api_key": "sk-file"}), encoding="utf-8")
    monkeypatch.setattr(C, "_CONFIG_FILE", f)
    assert C._load_config_file() == {"deepseek_api_key": "sk-file"}


def test_load_config_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "_CONFIG_FILE", tmp_path / "nope.json")
    assert C._load_config_file() == {}


def test_env_priority_over_file(monkeypatch):
    monkeypatch.setattr(C, "_FILE_CFG", {"iflytek_appid": "from_file"})
    monkeypatch.delenv("IFLYTEK_APPID", raising=False)
    assert C._env_or_file("IFLYTEK_APPID", "iflytek_appid") == "from_file"
    monkeypatch.setenv("IFLYTEK_APPID", "from_env")
    assert C._env_or_file("IFLYTEK_APPID", "iflytek_appid") == "from_env"
