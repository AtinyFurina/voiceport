"""stt.py 单元测试：只验证请求构造与签名结构，不真实调用 API。"""
import base64
import io
import wave

import stt


def test_pcm_to_wav():
    pcm = b"\x00\x00" * 160  # 160 个 16bit 样本
    wav_bytes = stt.pcm_to_wav(pcm, rate=16000)
    with wave.open(io.BytesIO(wav_bytes), "rb") as w:
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.getframerate() == 16000
        assert w.readframes(w.getnframes()) == pcm


def test_siliconflow_transcribe(monkeypatch):
    captured = {}

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"text": "  你好世界  "}

    def fake_post(url, headers=None, data=None, files=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["data"] = data
        captured["files"] = files
        return FakeResp()

    monkeypatch.setattr(stt.requests, "post", fake_post)
    p = stt.SiliconflowStt("sk-test", "FunAudioLLM/SenseVoiceSmall")
    assert p.transcribe(b"\x00\x00" * 800) == "你好世界"
    assert captured["url"] == "https://api.siliconflow.cn/v1/audio/transcriptions"
    assert captured["headers"] == {"Authorization": "Bearer sk-test"}
    assert captured["data"] == {"model": "FunAudioLLM/SenseVoiceSmall"}
    assert "file" in captured["files"]
    assert captured["files"]["file"][0] == "audio.wav"


def test_iflytek_build_url():
    p = stt.IflytekStt("appid123", "apikey", "apisecret")
    url = p._build_url()
    assert url.startswith("wss://iat-api.xfyun.cn/v2/iat?authorization=")
    query = url.split("?", 1)[1]
    params = dict(kv.split("=", 1) for kv in query.split("&"))
    assert "authorization" in params and "date" in params
    assert params["host"] == "iat-api.xfyun.cn"
    decoded = base64.b64decode(params["authorization"]).decode()
    assert 'api_key="apikey"' in decoded
    assert "hmac-sha256" in decoded


def test_iflytek_frame():
    p = stt.IflytekStt("appid123", "apikey", "apisecret")
    f = p._frame(0, b"\x01\x02")
    assert f["common"]["app_id"] == "appid123"
    assert f["data"]["status"] == 0
    assert f["data"]["format"] == "audio/L16;rate=16000"
    assert base64.b64decode(f["data"]["audio"]) == b"\x01\x02"


def test_get_stt_factory(monkeypatch):
    monkeypatch.setattr(stt.config, "stt_provider", "siliconflow")
    assert isinstance(stt.get_stt(), stt.SiliconflowStt)
    monkeypatch.setattr(stt.config, "stt_provider", "iflytek")
    assert isinstance(stt.get_stt(), stt.IflytekStt)
