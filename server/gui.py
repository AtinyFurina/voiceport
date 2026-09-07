"""原生桌面 GUI（PySide6，Linear 极简暗色风）：服务控制 + API 配置 + 历史记录 + 偏好管理。"""
import asyncio
import json
import logging
import plistlib
import platform
import sys
import threading
import time
from pathlib import Path

if platform.system() == "Windows":
    import winreg  # Windows 专用（macOS 无此模块）

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox, QPushButton,
    QStackedWidget, QStyle, QSystemTrayIcon, QTabWidget, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget, QFormLayout,
)

from config import config
from history import History

log = logging.getLogger("gui")

CONFIG_FILE = Path.home() / ".passport" / "config.json"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "VoicePort"
_IS_MAC = platform.system() == "Darwin"
_LAUNCH_AGENT = Path.home() / "Library" / "LaunchAgents" / "com.voiceport.plist"

# --- 配色 Token ---
BG = "#0f1115"
SURFACE = "#161a20"
SURFACE2 = "#1e232b"
BORDER = "#262b33"
TEXT = "#e8eaed"
MUTED = "#9aa3ad"
FAINT = "#5c656f"
ACCENT = "#6c8cff"
ACCENT_SOFT = "rgba(108,140,255,0.10)"
SUCCESS = "#3fb950"
DANGER = "#f85149"

QSS = f"""
QWidget {{ background: {BG}; color: {TEXT}; font-size: 14px; font-family: 'Segoe UI','Microsoft YaHei'; }}
QLabel, QCheckBox {{ background: transparent; }}
QListWidget {{ background: transparent; border: none; color: {MUTED}; outline: none; }}
QListWidget::item {{ height: 42px; padding-left: 12px; border-radius: 8px; margin: 2px 8px; }}
QListWidget::item:hover {{ background: {SURFACE2}; color: {TEXT}; }}
QListWidget::item:selected {{ background: {ACCENT_SOFT}; color: {TEXT}; font-weight: 500; }}
QPushButton {{ height: 38px; padding: 0 22px; border: none; border-radius: 10px; font-weight: 600; }}
QPushButton#primary {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #6c8cff, stop:1 #5b7cfa); color:#fff; }}
QPushButton#primary:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #7b9bff, stop:1 #6f8cff); }}
QPushButton#secondary {{ background: transparent; border: 1px solid {BORDER}; color: {TEXT}; }}
QPushButton#secondary:hover {{ background: {SURFACE2}; }}
QPushButton#danger {{ background: transparent; border: 1px solid rgba(248,81,73,.4); color: {DANGER}; }}
QPushButton#danger:hover {{ background: rgba(248,81,73,.10); }}
QLineEdit, QComboBox {{ min-height: 36px; padding: 0 12px; background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}
QLineEdit:focus, QComboBox:focus {{ border-color: {ACCENT}; }}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{ background: {SURFACE2}; border: 1px solid {BORDER}; selection-background-color: {ACCENT_SOFT}; }}
QFrame.card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}
QLabel.page-title {{ font-size: 20px; font-weight: 600; }}
QLabel.page-sub {{ color: {MUTED}; font-size: 13px; }}
QLabel.card-title {{ color: {FAINT}; font-size: 12px; font-weight: 600; letter-spacing: .5px; }}
QLabel.metric-val {{ font-size: 17px; font-weight: 600; }}
QLabel.metric-label {{ color: {FAINT}; font-size: 12px; }}
QLabel.hint {{ color: {FAINT}; font-size: 12px; }}
QTableWidget {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; alternate-background-color: {SURFACE2}; gridline-color: {BORDER}; }}
QTableWidget::item {{ padding: 6px; }}
QHeaderView::section {{ background: {SURFACE2}; color: {MUTED}; border: none; padding: 8px; }}
QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 8px; }}
QTabBar::tab {{ background: {SURFACE}; padding: 8px 18px; }}
QTabBar::tab:selected {{ background: {SURFACE2}; color: {TEXT}; font-weight: 600; }}
QTextEdit {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; padding: 10px; }}
QScrollBar:vertical {{ background: transparent; width: 8px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 4px; min-height: 24px; }}
"""


def _resource_path(name: str) -> Path:
    """打包后资源在 sys._MEIPASS，开发期在源码目录。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / name


def load_cfg() -> dict:
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def save_cfg(cfg: dict) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def apply_keys(cfg: dict) -> None:
    for key in (
        "iflytek_appid", "iflytek_api_key", "iflytek_api_secret",
        "siliconflow_api_key", "deepseek_api_key",
    ):
        if cfg.get(key):
            setattr(config, key, cfg[key])


def _card(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    frame.setProperty("class", "card")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(20, 18, 20, 18)
    lay.setSpacing(14)
    if title:
        t = QLabel(title)
        t.setObjectName("card-title")
        lay.addWidget(t)
    return frame, lay


class ServerThread:
    def __init__(self):
        self.thread: threading.Thread | None = None

    def start(self) -> bool:
        if self.thread and self.thread.is_alive():
            return False
        import ws_server
        self.thread = threading.Thread(
            target=lambda: asyncio.run(ws_server.main()), daemon=True
        )
        self.thread.start()
        return True

    @property
    def running(self) -> bool:
        return bool(self.thread and self.thread.is_alive())


class ServiceControlPage(QWidget):
    def __init__(self, server: ServerThread, on_quit, on_tray):
        super().__init__()
        self.server = server
        self.on_quit = on_quit
        self.on_tray = on_tray
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(16)

        title = QLabel("服务控制")
        title.setObjectName("page-title")
        sub = QLabel("管理服务端运行状态与开机行为")
        sub.setObjectName("page-sub")
        outer.addWidget(title)
        outer.addWidget(sub)

        # 状态总览卡片
        card, lay = _card("运行状态")
        badge = QLabel("●  运行中")
        badge.setStyleSheet(f"color:{SUCCESS}; font-weight:600;")
        lay.addWidget(badge)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self._metric_labels = {}
        for label in ("server_id", "已连接设备", "注入后端"):
            box = QFrame()
            box.setStyleSheet(f"background:{SURFACE2}; border-radius:10px;")
            bl = QVBoxLayout(box)
            bl.setContentsMargins(14, 12, 14, 12)
            bl.setSpacing(4)
            l = QLabel(label)
            l.setObjectName("metric-label")
            v = QLabel("—")
            v.setObjectName("metric-val")
            bl.addWidget(l)
            bl.addWidget(v)
            metrics.addWidget(box)
            self._metric_labels[label] = v
        lay.addLayout(metrics)
        outer.addWidget(card)

        # 操作卡片
        card2, lay2 = _card("操作")
        btns = QHBoxLayout()
        btns.setSpacing(12)
        b_start = QPushButton("启动服务端")
        b_start.setObjectName("primary")
        b_start.clicked.connect(self._on_start)
        b_tray = QPushButton("最小化到托盘")
        b_tray.setObjectName("secondary")
        b_tray.clicked.connect(self.on_tray)
        b_quit = QPushButton("退出")
        b_quit.setObjectName("danger")
        b_quit.clicked.connect(self.on_quit)
        btns.addWidget(b_start)
        btns.addWidget(b_tray)
        btns.addWidget(b_quit)
        btns.addStretch()
        lay2.addLayout(btns)

        # 开机自启动开关
        row = QHBoxLayout()
        left = QVBoxLayout()
        ll = QLabel("开机自启动")
        lh = QLabel("登录 Windows 后自动运行")
        lh.setObjectName("hint")
        left.addWidget(ll)
        left.addWidget(lh)
        self.autostart = QCheckBox()
        self.autostart.setChecked(self._read_autostart())
        self.autostart.toggled.connect(self._on_autostart)
        row.addLayout(left)
        row.addStretch()
        row.addWidget(self.autostart, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay2.addLayout(row)
        outer.addWidget(card2)
        outer.addStretch()

    def _on_start(self):
        self.server.start()
        self.refresh()

    def refresh(self):
        import ws_server

        self._metric_labels["server_id"].setText(config.server_id[:8])
        devices = getattr(ws_server, "sessions", {})
        self._metric_labels["已连接设备"].setText(str(len(devices)))
        self._metric_labels["注入后端"].setText(
            "TSF" if config.inject_backend == "tsf" else "SendInput"
        )

    def _read_autostart(self) -> bool:
        if _IS_MAC:
            return _LAUNCH_AGENT.exists()
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, RUN_NAME)
            winreg.CloseKey(key)
            return True
        except OSError:
            return False

    def _on_autostart(self, checked: bool):
        if _IS_MAC:
            try:
                if checked:
                    _LAUNCH_AGENT.parent.mkdir(parents=True, exist_ok=True)
                    plist = {
                        "Label": "com.voiceport",
                        "ProgramArguments": [sys.executable],
                        "RunAtLoad": True,
                    }
                    with open(_LAUNCH_AGENT, "wb") as f:
                        plistlib.dump(plist, f)
                else:
                    _LAUNCH_AGENT.unlink(missing_ok=True)
            except OSError as exc:
                log.warning("autostart failed: %s", exc)
            return
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
            if checked:
                winreg.SetValueEx(key, RUN_NAME, 0, winreg.REG_SZ, sys.executable)
            else:
                try:
                    winreg.DeleteValue(key, RUN_NAME)
                except OSError:
                    pass
            winreg.CloseKey(key)
        except OSError as exc:
            log.warning("autostart failed: %s", exc)


class ApiConfigPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build()
        self.load()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(16)
        title = QLabel("API 配置")
        title.setObjectName("page-title")
        sub = QLabel("配置 STT 与 LLM 密钥，保存到 ~/.passport/config.json")
        sub.setObjectName("page-sub")
        outer.addWidget(title)
        outer.addWidget(sub)

        self.entries = {}

        # STT 分组
        card, lay = _card("语音识别 STT")
        form = QFormLayout()
        form.setSpacing(10)
        self.stt_provider = QComboBox()
        self.stt_provider.addItems(["iflytek", "siliconflow"])
        self.entries["stt_provider"] = self.stt_provider
        form.addRow("STT 引擎", self.stt_provider)
        for key, label in [
            ("iflytek_appid", "讯飞 AppID"),
            ("iflytek_api_key", "讯飞 API Key"),
            ("iflytek_api_secret", "讯飞 API Secret"),
        ]:
            e = QLineEdit()
            e.setEchoMode(QLineEdit.EchoMode.Password)
            self.entries[key] = e
            form.addRow(label, e)
        self.sf_key = QLineEdit()
        self.sf_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.entries["siliconflow_api_key"] = self.sf_key
        form.addRow("硅基流动 API Key", self.sf_key)
        lay.addLayout(form)
        outer.addWidget(card)

        # LLM 分组
        card2, lay2 = _card("大模型 LLM")
        form2 = QFormLayout()
        form2.setSpacing(10)
        self.ds_key = QLineEdit()
        self.ds_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.entries["deepseek_api_key"] = self.ds_key
        form2.addRow("DeepSeek API Key", self.ds_key)
        lay2.addLayout(form2)
        outer.addWidget(card2)

        b = QPushButton("保存密钥")
        b.setObjectName("primary")
        b.clicked.connect(self._on_save)
        outer.addWidget(b, alignment=Qt.AlignmentFlag.AlignLeft)
        outer.addStretch()

    def load(self):
        cfg = load_cfg()
        for key, w in self.entries.items():
            if isinstance(w, QComboBox):
                idx = w.findText(cfg.get(key, "iflytek"))
                w.setCurrentIndex(idx if idx >= 0 else 0)
            else:
                w.setText(cfg.get(key, ""))

    def _on_save(self):
        cfg = load_cfg()
        for key, w in self.entries.items():
            cfg[key] = w.currentText() if isinstance(w, QComboBox) else w.text().strip()
        save_cfg(cfg)
        apply_keys(cfg)
        QMessageBox.information(self, "已保存", "密钥已保存并生效")


class HistoryPage(QWidget):
    def __init__(self, history: History):
        super().__init__()
        self.history = history
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(16)
        title = QLabel("历史记录")
        title.setObjectName("page-title")
        sub = QLabel("语音输入与修改记录")
        sub.setObjectName("page-sub")
        outer.addWidget(title)
        outer.addWidget(sub)

        tabs = QTabWidget()
        self.entries_table = QTableWidget()
        self.edits_table = QTableWidget()
        tabs.addTab(self.entries_table, "输入记录")
        tabs.addTab(self.edits_table, "修改记录")
        outer.addWidget(tabs)
        self.refresh()

    def refresh(self):
        rows = self.history.recent("", n=200)
        self.entries_table.setColumnCount(3)
        self.entries_table.setHorizontalHeaderLabels(["原始识别", "最终发送", "窗口"])
        self.entries_table.setRowCount(len(rows))
        for i, (draft, final, win) in enumerate(rows):
            self.entries_table.setItem(i, 0, QTableWidgetItem(draft))
            self.entries_table.setItem(i, 1, QTableWidgetItem(final))
            self.entries_table.setItem(i, 2, QTableWidgetItem(win))
        self.entries_table.horizontalHeader().setStretchLastSection(True)
        self.entries_table.setAlternatingRowColors(True)
        self.entries_table.verticalHeader().setVisible(False)

        edits = self.history.recent_edits("", n=200)
        self.edits_table.setColumnCount(3)
        self.edits_table.setHorizontalHeaderLabels(["修改前", "修改指令", "修改后"])
        self.edits_table.setRowCount(len(edits))
        for i, (before, ins, after) in enumerate(edits):
            self.edits_table.setItem(i, 0, QTableWidgetItem(before))
            self.edits_table.setItem(i, 1, QTableWidgetItem(ins))
            self.edits_table.setItem(i, 2, QTableWidgetItem(after))
        self.edits_table.horizontalHeader().setStretchLastSection(True)
        self.edits_table.setAlternatingRowColors(True)
        self.edits_table.verticalHeader().setVisible(False)


class PreferencePage(QWidget):
    def __init__(self, history: History):
        super().__init__()
        self.history = history
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(16)
        title = QLabel("偏好管理")
        title.setObjectName("page-title")
        sub = QLabel("基于历史输入生成的表达偏好总结")
        sub.setObjectName("page-sub")
        outer.addWidget(title)
        outer.addWidget(sub)

        card, lay = _card("偏好总结")
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        lay.addWidget(self.text)
        outer.addWidget(card)
        b = QPushButton("生成偏好总结")
        b.setObjectName("primary")
        b.clicked.connect(self._on_generate)
        outer.addWidget(b, alignment=Qt.AlignmentFlag.AlignLeft)
        outer.addStretch()

    def _on_generate(self):
        self.text.setPlainText("生成中…")
        try:
            result = self.history.summarize_preferences("")
        except Exception as exc:  # noqa: BLE001
            result = f"生成失败: {exc}"
        self.text.setPlainText(result or "（暂无足够历史记录）")


class MainWindow(QMainWindow):
    def __init__(self, server: ServerThread, history: History):
        super().__init__()
        self.server = server
        self.history = history
        self.setWindowTitle("VoicePort")
        self.resize(920, 620)

        self.pages = QStackedWidget()
        self.service_page = ServiceControlPage(server, self._quit, self._to_tray)
        self.api_page = ApiConfigPage()
        self.history_page = HistoryPage(history)
        self.pref_page = PreferencePage(history)
        for p in (self.service_page, self.api_page, self.history_page, self.pref_page):
            self.pages.addWidget(p)

        self._build_nav()
        central = QWidget()
        hl = QHBoxLayout(central)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)
        hl.addWidget(self.nav_col)
        hl.addWidget(self.pages, stretch=1)
        self.setCentralWidget(central)
        self._build_tray()

    def _build_nav(self):
        self.nav_col = QWidget()
        self.nav_col.setFixedWidth(210)
        self.nav_col.setStyleSheet(f"background:{SURFACE}; border-right:1px solid {BORDER};")
        lay = QVBoxLayout(self.nav_col)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(4)

        brand = QWidget()
        bl = QHBoxLayout(brand)
        bl.setContentsMargins(4, 0, 0, 0)
        bl.setSpacing(10)
        logo = QLabel()
        pix = QPixmap(str(_resource_path("icon.png")))
        logo.setPixmap(pix.scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        name = QLabel("VoicePort")
        name.setStyleSheet("font-weight:600; font-size:15px;")
        bl.addWidget(logo)
        bl.addWidget(name)
        bl.addStretch()
        lay.addWidget(brand)

        self.nav = QListWidget()
        self.nav.setStyleSheet(f"QListWidget {{ background:transparent; border:none; color:{MUTED}; }}")
        style = self.style()
        items = [
            (style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), "服务控制"),
            (style.standardIcon(QStyle.StandardPixmap.SP_DriveNetIcon), "API 配置"),
            (style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), "历史记录"),
            (style.standardIcon(QStyle.StandardPixmap.SP_DialogYesButton), "偏好管理"),
        ]
        for icon, text in items:
            it = QListWidgetItem(icon, text)
            it.setSizeHint(it.sizeHint() + type(it.sizeHint())(0, 16))
            self.nav.addItem(it)
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.nav.setCurrentRow(0)
        lay.addWidget(self.nav, stretch=1)

    def _build_tray(self):
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(icon, self)
        menu = QMenu()
        a_show = menu.addAction("显示")
        a_show.triggered.connect(self._show)
        a_quit = menu.addAction("退出")
        a_quit.triggered.connect(self._quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self._show() if r == QSystemTrayIcon.ActivationReason.DoubleClick else None
        )
        self.tray.show()

    def _show(self):
        self.showNormal()
        self.activateWindow()

    def _to_tray(self):
        self.hide()
        self.tray.showMessage("VoicePort", "已最小化到系统托盘", QSystemTrayIcon.MessageIcon.Information, 2000)

    def _quit(self):
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self._to_tray()

    def refresh(self):
        self.service_page.refresh()
        self.history_page.refresh()


def run_gui(server: ServerThread, history: History) -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    app.setWindowIcon(QIcon(str(_resource_path("icon.png"))))
    win = MainWindow(server, history)
    win.show()
    win.refresh()
    app.exec()
