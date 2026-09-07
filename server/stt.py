"""STT provider 抽象与实现。

- SiliconflowStt：硅基流动 SenseVoice，OpenAI 兼容 /v1/audio/transcriptions。
- IflytekStt：讯飞语音听写（流式版），WebSocket + HMAC-SHA256 签名。

注意：签名算法与返回结构按公开文档实现；真实调用需配置对应 API key 后实测。
"""
import asyncio
import base64
import datetime
import hashlib
import hmac
import io
import json
import wave
from abc import ABC, abstractmethod

import requests
import websockets

from config import config


def pcm_to_wav(pcm: bytes, rate: int = 16000, channels: int = 1, sampwidth: int = 2) -> bytes:
    """给 raw PCM 加 WAV 头，用于 multipart 上传。"""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(sampwidth)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


class SttProvider(ABC):
    """16kHz/16bit/mono little-endian PCM -> 文本。"""

    @abstractmethod
    def transcribe(self, pcm16k: bytes) -> str: ...


class SiliconflowStt(SttProvider):
    """硅基流动 SenseVoice（OpenAI 兼容 /audio/transcriptions）。"""

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.siliconflow.cn/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def transcribe(self, pcm16k: bytes) -> str:
        wav = pcm_to_wav(pcm16k)
        r = requests.post(
            f"{self.base_url}/audio/transcriptions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            data={"model": self.model},
            files={"file": ("audio.wav", wav, "audio/wav")},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["text"].strip()


class IflytekStt(SttProvider):
    """讯飞语音听写（流式版）。文档：https://www.xfyun.cn/doc/asr/voicedictation/API.html"""

    HOST = "iat-api.xfyun.cn"
    PATH = "/v2/iat"
    _CHUNK = 1280  # 每帧音频字节数（约 40ms @16kHz）

    def __init__(self, appid: str, api_key: str, api_secret: str):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret

    def _build_url(self) -> str:
        date = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        signature_origin = f"host: {self.HOST}\ndate: {date}\nGET {self.PATH} HTTP/1.1"
        signature = base64.b64encode(
            hmac.new(self.api_secret.encode(), signature_origin.encode(), hashlib.sha256).digest()
        ).decode()
        authorization_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature}"'
        )
        authorization = base64.b64encode(authorization_origin.encode()).decode()
        return (
            f"wss://{self.HOST}{self.PATH}"
            f"?authorization={authorization}&date={date}&host={self.HOST}"
        )

    def _frame(self, status: int, pcm_chunk: bytes) -> dict:
        return {
            "common": {"app_id": self.appid},
            "business": {"language": "zh_cn", "domain": "iat", "accent": "mandarin"},
            "data": {
                "status": status,
                "format": "audio/L16;rate=16000",
                "encoding": "raw",
                "audio": base64.b64encode(pcm_chunk).decode(),
            },
        }

    def transcribe(self, pcm16k: bytes) -> str:
        if not pcm16k:
            return ""
        frames = [pcm16k[i : i + self._CHUNK] for i in range(0, len(pcm16k), self._CHUNK)]
        return asyncio.run(self._run(frames))

    async def _run(self, frames: list[bytes]) -> str:
        words: list[str] = []
        url = self._build_url()

        async def send(ws: websockets.WebSocketClientProtocol) -> None:
            for idx, chunk in enumerate(frames):
                status = 0 if idx == 0 else (2 if idx == len(frames) - 1 else 1)
                await ws.send(json.dumps(self._frame(status, chunk)))

        async def recv(ws: websockets.WebSocketClientProtocol) -> None:
            while True:
                resp = json.loads(await ws.recv())
                if resp.get("code") != 0:
                    raise RuntimeError(f"iflytek error {resp.get('code')}: {resp.get('message')}")
                data = resp.get("data", {})
                for ws_item in data.get("result", {}).get("ws", []):
                    for cw in ws_item.get("cw", []):
                        words.append(cw.get("w", ""))
                if data.get("status") == 2:
                    break

        async with websockets.connect(url, ping_interval=None) as ws:
            await asyncio.gather(send(ws), recv(ws))

        return "".join(words)


def get_stt() -> SttProvider:
    """按 config.stt_provider 返回 STT 实例。"""
    if config.stt_provider == "siliconflow":
        return SiliconflowStt(config.siliconflow_api_key, config.siliconflow_stt_model)
    return IflytekStt(config.iflytek_appid, config.iflytek_api_key, config.iflytek_api_secret)
