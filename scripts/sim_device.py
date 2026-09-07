"""模拟设备端：用于无硬件联调，验证 WebSocket 协议链路。

用法: python scripts/sim_device.py [uri]
默认连 ws://127.0.0.1:8765，发 hello → 收 welcome → 发 ping → 收 pong。
"""
import asyncio
import json
import sys
import uuid

import websockets


async def main(uri: str) -> None:
    device_id = str(uuid.uuid4())
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "hello", "ver": "1.0", "device_id": device_id}))
        print("device ->", "hello", device_id)
        print("server <-", await ws.recv())

        await ws.send(json.dumps({"type": "ping"}))
        print("device ->", "ping")
        print("server <-", await ws.recv())

        # 发一个未处理类型，验证错误回显
        await ws.send(json.dumps({"type": "audio_start"}))
        print("server <-", await ws.recv())


if __name__ == "__main__":
    uri = sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:8765/ws"
    asyncio.run(main(uri))
