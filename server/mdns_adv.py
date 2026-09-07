"""mDNS 广播：_passport._tcp.local，TXT 记录 server_id/host/port。"""
import logging
import socket

from zeroconf import NonUniqueNameException, ServiceInfo, Zeroconf

log = logging.getLogger("mdns")

SERVICE_TYPE = "_passport._tcp.local."


def get_local_ip() -> str:
    """获取本机局域网 IP（用 UDP 探测路由，不真正发包）。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


class MdnsAdvertiser:
    def __init__(self, host: str, port: int, server_id: str):
        self.zc = Zeroconf()
        base = f"passport-{server_id[:8]}"
        self.info = ServiceInfo(
            SERVICE_TYPE,
            f"{base}.{SERVICE_TYPE}",
            addresses=[socket.inet_aton(get_local_ip())],
            port=port,
            properties={"server_id": server_id, "host": host, "port": str(port)},
            server=f"{base}.local.",
        )

    def start(self) -> None:
        try:
            self.zc.register_service(self.info)
            log.info("mDNS 广播: %s", self.info.name)
        except NonUniqueNameException:
            log.warning("mDNS 服务名冲突（多实例/残留），跳过广播，不影响核心功能")

    def stop(self) -> None:
        self.zc.unregister_service(self.info)
        self.zc.close()
