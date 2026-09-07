"""provision.py 单元测试：mock BleakClient，不真实访问蓝牙。"""
import asyncio

import provision


class FakeClient:
    def __init__(self, address):
        self.address = address
        self.writes = []
        self.status = b"\x01"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def write_gatt_char(self, uuid, data):
        self.writes.append((uuid, data))

    async def read_gatt_char(self, uuid):
        return self.status


def test_provision_writes(monkeypatch):
    fake = FakeClient("AA:BB:CC")
    monkeypatch.setattr(provision, "BleakClient", lambda addr: fake)
    monkeypatch.setattr(provision, "get_local_ip", lambda: "192.168.1.10")

    status = asyncio.run(
        provision.provision("AA:BB:CC", "wifi", "pass123", pc_ip="192.168.1.10", pc_port=8765)
    )
    assert status == b"\x01"
    writes = dict(fake.writes)
    assert writes[provision.CHAR_SSID] == b"wifi"
    assert writes[provision.CHAR_PASSWORD] == b"pass123"
    assert writes[provision.CHAR_PC_IP] == b"192.168.1.10"
    assert writes[provision.CHAR_PC_PORT] == (8765).to_bytes(2, "little")


def test_provision_uses_config_port(monkeypatch):
    fake = FakeClient("AA:BB:CC")
    monkeypatch.setattr(provision, "BleakClient", lambda addr: fake)
    monkeypatch.setattr(provision, "get_local_ip", lambda: "10.0.0.1")
    monkeypatch.setattr(provision.config, "port", 9999)

    asyncio.run(provision.provision("AA:BB:CC", "w", "p"))
    writes = dict(fake.writes)
    assert writes[provision.CHAR_PC_PORT] == (9999).to_bytes(2, "little")
