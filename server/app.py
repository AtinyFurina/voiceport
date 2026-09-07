"""主程序：服务端（后台线程）+ 原生 GUI（PySide6）+ 日志写文件。"""
import logging
from pathlib import Path

import gui
from history import History

LOG_FILE = Path.home() / ".passport" / "server.log"


def setup_logging() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")],
    )


def main() -> None:
    setup_logging()
    log = logging.getLogger("main")
    log.info("passport 启动，日志文件: %s", LOG_FILE)

    server = gui.ServerThread()
    history = History()
    server.start()  # 服务端在后台线程跑
    gui.run_gui(server, history)
    log.info("退出")


if __name__ == "__main__":
    main()
