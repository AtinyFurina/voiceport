"""BLE 配网客户端：扫描设备 → 写入 Wi-Fi 凭证 + 服务端地址 → 读连接状态。

GATT UUID 与固件侧（firmware/wifi_prov.c）保持一致。
"""
import asyncio

from bleak import BleakClient, BleakScanner

from config import config
from mdns_adv import get_local_ip

SERVICE_UUID = "a3f0a5b1-0000-4a5b-9c1d-2e3f4a5b6c7d"
CHAR_SSID = "a3f0a5b1-0001-4a5b-9c1d-2e3f4a5b6c7d"
CHAR_PASSWORD = "a3f0a5b1-0002-4a5b-9c1d-2e3f4a5b6c7d"
CHAR_PC_IP = "a3f0a5b1-0003-4a5b-9c1d-2e3f4a5b6c7d"
CHAR_PC_PORT = "a3f0a5b1-0004-4a5b-9c1d-2e3f4a5b6c7d"
CHAR_SERVER_ID = "a3f0a5b1-0005-4a5b-9c1d-2e3f4a5b6c7d"
CHAR_STATUS = "a3f0a5b1-0006-4a5b-9c1d-2e3f4a5b6c7d"


async def scan_devices(timeout: float = 10.0) -> list[tuple[str, str]]:
    found = await BleakScanner.discover(timeout=timeout)
    return [(d.address, d.name or d.address) for d in found]


async def provision(
    address: str,
    ssid: str,
    password: str,
    pc_ip: str | None = None,
    pc_port: int | None = None,
) -> bytes:
    ip = pc_ip or get_local_ip()
    port = pc_port or config.port
    async with BleakClient(address) as client:
        await client.write_gatt_char(CHAR_SSID, ssid.encode("utf-8"))
        await client.write_gatt_char(CHAR_PASSWORD, password.encode("utf-8"))
        await client.write_gatt_char(CHAR_PC_IP, ip.encode("utf-8"))
        await client.write_gatt_char(CHAR_PC_PORT, int(port).to_bytes(2, "little"))
        await client.write_gatt_char(CHAR_SERVER_ID, config.server_id.encode("utf-8"))
        return await client.read_gatt_char(CHAR_STATUS)


async def _cli() -> None:
    print("扫描 BLE 设备…")
    devices = await scan_devices()
    if not devices:
        print("未发现设备")
        return
    for i, (addr, name) in enumerate(devices):
        print(f"[{i}] {name} ({addr})")
    idx = int(input("选择设备序号: "))
    ssid = input("Wi-Fi SSID: ")
    password = input("Wi-Fi 密码: ")
    addr, name = devices[idx]
    status = await provision(addr, ssid, password)
    print(f"配网完成，status={status.hex()} (1=已连网, 2=失败)")


if __name__ == "__main__":
    asyncio.run(_cli())
