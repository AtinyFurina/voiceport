"""服务端：只保留设备 WebSocket 连接（无 HTTP/Web 界面）。"""
import asyncio
import json
import logging

from aiohttp import WSMsgType, web

from config import config
from controller import Session
from history import History
from mdns_adv import MdnsAdvertiser

log = logging.getLogger("ws_server")
history = History()
sessions: dict[str, Session] = {}


async def ws_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    device_id = None
    session: Session | None = None
    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
            except json.JSONDecodeError:
                await ws.send_str(
                    json.dumps({"type": "status", "state": "error", "msg": "bad json"})
                )
                continue
            if data.get("type") == "hello":
                device_id = data.get("device_id")
                session = Session(device_id, ws.send_str, history)
                sessions[device_id] = session
                await ws.send_str(
                    json.dumps(
                        {"type": "welcome", "server_id": config.server_id, "host": config.host}
                    )
                )
                continue
            if session is None:
                await ws.send_str(
                    json.dumps({"type": "status", "state": "error", "msg": "hello required"})
                )
                continue
            await session.handle(data)
        elif msg.type == WSMsgType.BINARY:
            if session is not None:
                await session.on_audio(msg.data)
        elif msg.type == WSMsgType.ERROR:
            break
    if device_id:
        sessions.pop(device_id, None)
    return ws


async def main() -> None:
    advertiser = MdnsAdvertiser(config.host, config.port, config.server_id)
    try:
        advertiser.start()
    except Exception as exc:  # noqa: BLE001
        log.warning("mDNS start failed: %s", exc)

    app = web.Application()
    app.router.add_get("/ws", ws_handler)

    log.info("服务端启动: ws://localhost:%s/ws (设备)", config.port)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.bind_host, config.port)
    await site.start()
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
