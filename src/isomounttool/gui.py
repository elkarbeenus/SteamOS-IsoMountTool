"""Graphical interface (Qt / PySide6) of SteamOS ISO Mount Tool.

Created by Dominic Lesina x Claude
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import time
import traceback

from PySide6.QtCore import QByteArray, QSize, Qt, QThread, QTimer, Signal, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QProgressDialog,
    QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QTextBrowser, QVBoxLayout, QWidget,
)

from . import core
from .i18n import Translator

# =============================================================================
#  Look & feel
# =============================================================================
C = {
    "bg": "#0e141b", "side": "#121a23", "card": "#18212c", "card2": "#1e2936", "border": "#2a3747",
    "accent": "#1a9fff", "accent_h": "#47b2ff", "text": "#e8eef4", "muted": "#8d9bab",
    "danger": "#ff5d5d", "ok": "#4cc38a",
}

QSS = f"""
* {{ font-size: 11pt; color: {C['text']}; }}
QMainWindow, QDialog, #Content {{ background: {C['bg']}; }}
#Sidebar {{ background: {C['side']}; border-right: 1px solid {C['border']}; }}
#AppName {{ font-size: 14pt; font-weight: 700; }}
#Small {{ color: {C['muted']}; font-size: 9pt; }}
#Title {{ font-size: 22pt; font-weight: 700; }}
#Sub, #Muted {{ color: {C['muted']}; }}
#SectionTitle {{ font-size: 13pt; font-weight: 700; }}
#NavButton {{
    text-align: left; padding: 12px 16px; border: none; border-radius: 10px;
    background: transparent; font-size: 12pt; color: {C['muted']};
}}
#NavButton:hover {{ background: {C['card']}; color: {C['text']}; }}
#NavButton:checked {{ background: {C['card2']}; color: {C['text']}; font-weight: 700; }}
#Card {{ background: {C['card']}; border: 1px solid {C['border']}; border-radius: 16px; }}
#Card[empty="true"] {{ background: transparent; border: 2px dashed {C['border']}; }}
#Card[empty="true"]:hover {{ border-color: {C['accent']}; background: rgba(26,159,255,0.06); }}
#Card[drop="true"] {{ border: 2px solid {C['accent']}; background: rgba(26,159,255,0.10); }}
#CardTitle {{ font-size: 14pt; font-weight: 700; }}
#Badge {{
    background: {C['card2']}; border: 1px solid {C['border']}; border-radius: 10px;
    padding: 3px 10px; color: {C['muted']}; font-size: 9pt; font-weight: 600;
}}
#DriveBadge {{
    background: rgba(26,159,255,0.15); border-radius: 10px; padding: 3px 10px;
    color: {C['accent_h']}; font-size: 10pt; font-weight: 700;
}}
QPushButton {{
    background: {C['card2']}; border: 1px solid {C['border']}; border-radius: 10px;
    padding: 9px 16px; font-weight: 600;
}}
QPushButton:hover {{ border-color: {C['accent']}; }}
QPushButton:pressed {{ background: {C['border']}; }}
QPushButton:disabled {{ color: #5b6878; border-color: {C['card2']}; }}
QPushButton#Primary {{ background: {C['accent']}; border: 1px solid {C['accent']}; color: white; }}
QPushButton#Primary:hover {{ background: {C['accent_h']}; border-color: {C['accent_h']}; }}
QPushButton#Primary:disabled {{ background: #2b4a66; border-color: #2b4a66; color: #9fb3c6; }}
QPushButton#Danger {{ color: {C['danger']}; }}
QPushButton#Danger:hover {{ border-color: {C['danger']}; }}
QPushButton#Update {{ background: rgba(76,195,138,0.15); border: 1px solid {C['ok']}; color: {C['ok']}; }}
QLineEdit, QComboBox {{
    background: {C['bg']}; border: 1px solid {C['border']}; border-radius: 8px; padding: 8px 10px;
    selection-background-color: {C['accent']};
}}
QLineEdit:focus, QComboBox:focus {{ border-color: {C['accent']}; }}
QComboBox QAbstractItemView {{
    background: {C['card']}; border: 1px solid {C['border']}; selection-background-color: {C['accent']};
}}
QListWidget {{
    background: {C['bg']}; border: 1px solid {C['border']}; border-radius: 10px; padding: 4px; outline: 0;
}}
QListWidget::item {{ padding: 8px; border-radius: 6px; }}
QListWidget::item:selected {{ background: {C['accent']}; color: white; }}
QListWidget::item:hover:!selected {{ background: {C['card2']}; }}
QCheckBox {{ spacing: 10px; }}
QCheckBox::indicator {{
    width: 20px; height: 20px; border-radius: 5px; border: 1px solid {C['border']}; background: {C['bg']};
}}
QCheckBox::indicator:checked {{ background: {C['accent']}; border-color: {C['accent']}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px; }}
QScrollBar::handle:vertical {{ background: {C['border']}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QTextBrowser {{ background: {C['bg']}; border: 1px solid {C['border']}; border-radius: 10px; padding: 8px; }}
#RunningBar {{ background: rgba(26,159,255,0.10); border: 1px solid {C['accent']}; border-radius: 12px; }}
#Toast {{
    background: {C['card2']}; border: 1px solid {C['accent']}; border-radius: 12px;
    padding: 12px 20px; font-weight: 600;
}}
QMessageBox QLabel {{ min-width: 360px; }}
QToolTip {{ background: {C['card2']}; color: {C['text']}; border: 1px solid {C['border']}; }}
"""

_SVG = {
    "disc": '<circle cx="12" cy="12" r="9.5"/><circle cx="12" cy="12" r="2.5"/><path d="M12 5.5a6.5 6.5 0 0 1 6.5 6.5"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "eject": '<path d="M12 5l7 8H5z" fill="COLOR"/><path d="M5 18h14"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "play": '<path d="M8 5.5v13l11-6.5z" fill="COLOR"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    "info": '<circle cx="12" cy="12" r="9.5"/><path d="M12 11v6M12 7.5v.5"/>',
    "game": '<rect x="2.5" y="7" width="19" height="11" rx="5"/><path d="M7 11v3M5.5 12.5h3"/><circle cx="16" cy="11.5" r="1" fill="COLOR"/><circle cx="18" cy="13.5" r="1" fill="COLOR"/>',
    "trash": '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3"/>',
    "refresh": '<path d="M20 11a8 8 0 0 0-14.6-4.5M4 4v4h4M4 13a8 8 0 0 0 14.6 4.5M20 20v-4h-4"/>',
    "download": '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
    "file": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>',
    "log": '<path d="M5 4h14v16H5z"/><path d="M8 8h8M8 12h8M8 16h5"/>',
}


def svg_pixmap(name: str, color: str = "#e8eef4", size: int = 24) -> QPixmap:
    body = _SVG[name].replace("COLOR", color)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
           f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{body}</svg>')
    ratio = 2
    pm = QPixmap(size * ratio, size * ratio)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    QSvgRenderer(QByteArray(svg.encode())).render(p)
    p.end()
    pm.setDevicePixelRatio(ratio)
    return pm


def svg_icon(name: str, color: str = "#e8eef4", size: int = 24) -> QIcon:
    return QIcon(svg_pixmap(name, color, size))


def app_icon_pixmap(size: int) -> QPixmap:
    here = os.path.dirname(os.path.abspath(__file__))
    for p in (os.path.join(here, "icon.svg"),
              os.path.join(here, "..", "..", "packaging", "steamos-isomounttool.svg")):
        if os.path.isfile(p):
            pm = QPixmap(size * 2, size * 2)
            pm.fill(Qt.transparent)
            painter = QPainter(pm)
            QSvgRenderer(p).render(painter)
            painter.end()
            pm.setDevicePixelRatio(2)
            return pm
    return svg_pixmap("disc", C["accent"], size)


def button(text: str, icon: str | None = None, kind: str = "", color: str | None = None) -> QPushButton:
    b = QPushButton(text.replace("&", "&&"))
    if kind:
        b.setObjectName(kind)
    if icon:
        col = color or ("#ffffff" if kind == "Primary" else C["danger"] if kind == "Danger" else C["text"])
        b.setIcon(svg_icon(icon, col, 18))
        b.setIconSize(QSize(18, 18))
    b.setCursor(Qt.PointingHandCursor)
    return b


def label(text: str = "", name: str = "", wrap: bool = False) -> QLabel:
    lab = QLabel(text)
    if name:
        lab.setObjectName(name)
    lab.setWordWrap(wrap)
    return lab


class ElidedLabel(QLabel):
    def __init__(self, text: str = "", name: str = "", mode=Qt.ElideMiddle):
        super().__init__()
        self._full = text
        self._mode = mode
        if name:
            self.setObjectName(name)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setMinimumWidth(40)
        self.setText(text)

    def setText(self, text):  # noqa: N802
        self._full = text
        self.setToolTip(text)
        self._update()

    def resizeEvent(self, e):  # noqa: N802
        super().resizeEvent(e)
        self._update()

    def _update(self):
        super().setText(self.fontMetrics().elidedText(self._full, self._mode, max(40, self.width())))


def repolish(w: QWidget):
    w.style().unpolish(w)
    w.style().polish(w)
    w.update()


# =============================================================================
#  Background work
# =============================================================================
class Task(QThread):
    done = Signal(object, object)          # result, exception

    def __init__(self, fn, *args, parent=None):
        super().__init__(parent)
        self.fn, self.args = fn, args

    def run(self):
        try:
            self.done.emit(self.fn(*self.args), None)
        except Exception as e:  # noqa: BLE001
            self.done.emit(None, e)


class GameRunner(QThread):
    status = Signal(str)
    finished_run = Signal(int, str)

    def __init__(self, t: Translator, cfg: dict, exe: str, prefix: core.Prefix, tool: core.ProtonTool,
                 launch_options: str, use_runtime: bool, from_iso: bool, parent=None):
        super().__init__(parent)
        self.t, self.cfg, self.exe, self.prefix, self.tool = t, cfg, exe, prefix, tool
        self.launch_options, self.use_runtime, self.from_iso = launch_options, use_runtime, from_iso
        stamp = time.strftime("%Y%m%d-%H%M%S")
        self.log_path = os.path.join(core.logs_dir(), f"{core.safe_name(prefix.name)}-{stamp}.log")

    @property
    def exe_name(self) -> str:
        return os.path.basename(self.exe)

    def run(self):
        code = -1
        try:
            os.makedirs(core.logs_dir(), exist_ok=True)
            os.makedirs(self.prefix.path, exist_ok=True)
            with open(self.log_path, "w", encoding="utf-8", errors="replace") as log:
                log.write(f"{core.APP_NAME} {core.app_version()}\nProton: {self.tool.name} ({self.tool.path})\n"
                          f"Prefix: {self.prefix.path}\nProgram: {self.exe}\n\n")
                log.flush()
                if not self.prefix.initialized:
                    self.status.emit(self.t("st_preparing", name=self.prefix.name))
                    cmd, env, cwd = core.init_command(self.prefix, self.tool, self.cfg, self.use_runtime)
                    log.write("$ " + " ".join(cmd) + "\n")
                    log.flush()
                    try:
                        subprocess.run(cmd, env=env, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, timeout=600)
                    except subprocess.TimeoutExpired:
                        log.write("prefix init timed out\n")
                linked = core.link_prefix_drives(self.prefix)
                isos = core.current_isos()
                win = core.windows_path_for(self.exe, isos) if (self.from_iso and linked) else ""
                cmd, env, cwd = core.build_launch(self.exe, self.prefix, self.tool, self.cfg, isos, win,
                                                  self.launch_options, self.use_runtime)
                log.write("\n$ " + " ".join(cmd) + "\n")
                log.write("env: " + " ".join(f"{k}={v}" for k, v in sorted(env.items())
                                             if k.startswith(("STEAM_COMPAT", "PROTON", "WINE", "DXVK"))) + "\n\n")
                log.flush()
                self.prefix.meta.update({"name": self.prefix.name, "proton": self.tool.name,
                                         "proton_path": self.tool.path, "last_run": int(time.time())})
                self.prefix.save_meta()
                self.status.emit(self.t("st_running", exe=self.exe_name, name=self.prefix.name))
                code = subprocess.run(cmd, env=env, cwd=cwd, stdout=log, stderr=subprocess.STDOUT).returncode
                log.write(f"\nexit code: {code}\n")
        except Exception:  # noqa: BLE001
            try:
                with open(self.log_path, "a", encoding="utf-8") as log:
                    log.write(traceback.format_exc())
            except OSError:
                pass
        self.finished_run.emit(code, self.log_path)


# =============================================================================
#  Widgets
# =============================================================================
def _iso_from_mime(mime) -> str:
    if mime.hasUrls():
        for u in mime.urls():
            p = u.toLocalFile()
            if p.lower().endswith(".iso"):
                return p
    return ""


class SlotCard(QFrame):
    mount_requested = Signal(int, str)       # slot, path ('' = ask)
    eject_requested = Signal(object)
    open_requested = Signal(object)
    install_requested = Signal(object)

    def __init__(self, t: Translator, slot: int):
        super().__init__()
        self.t, self.slot, self.iso = t, slot, None
        self.setObjectName("Card")
        self.setAcceptDrops(True)
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stack = QStackedWidget(self)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.addWidget(self.stack)

        # --- empty ---
        empty = QWidget()
        el = QVBoxLayout(empty)
        el.addStretch(1)
        ic = QLabel()
        ic.setPixmap(svg_pixmap("plus", C["accent"], 44))
        ic.setAlignment(Qt.AlignCenter)
        el.addWidget(ic)
        t1 = label(f"{t('slot', n=slot + 1)} · {t('slot_empty')}", "CardTitle")
        t1.setAlignment(Qt.AlignCenter)
        el.addWidget(t1)
        t2 = label(t("slot_empty_hint") + f"  ·  {t('drive', l=core.DRIVE_LETTERS[slot].upper())}", "Muted")
        t2.setAlignment(Qt.AlignCenter)
        el.addWidget(t2)
        el.addStretch(1)
        self.stack.addWidget(empty)

        # --- mounted ---
        full = QWidget()
        fl = QVBoxLayout(full)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(10)
        top = QHBoxLayout()
        top.setSpacing(14)
        disc = QLabel()
        disc.setPixmap(svg_pixmap("disc", C["accent"], 52))
        disc.setFixedSize(56, 56)
        top.addWidget(disc, 0, Qt.AlignTop)
        names = QVBoxLayout()
        names.setSpacing(4)
        self.title = ElidedLabel("", "CardTitle", Qt.ElideRight)
        names.addWidget(self.title)
        self.file = ElidedLabel("", "Muted")
        names.addWidget(self.file)
        top.addLayout(names, 1)
        badges = QVBoxLayout()
        badges.setSpacing(6)
        self.slot_badge = label(t("slot", n=slot + 1), "Badge")
        self.drive_badge = label("", "DriveBadge")
        for b in (self.slot_badge, self.drive_badge):
            b.setAlignment(Qt.AlignCenter)
            badges.addWidget(b, 0, Qt.AlignRight)
        badges.addStretch(1)
        top.addLayout(badges)
        fl.addLayout(top)
        self.path = ElidedLabel("", "Muted")
        fl.addWidget(self.path)
        self.installer = ElidedLabel("", "Sub", Qt.ElideRight)
        fl.addWidget(self.installer)
        self.running = label("", "Sub")
        self.running.setStyleSheet(f"color: {C['accent_h']}; font-weight: 600;")
        self.running.hide()
        fl.addWidget(self.running)
        fl.addStretch(1)
        row = QHBoxLayout()
        row.setSpacing(10)
        self.btn_install = button(t("btn_install"), "play", "Primary")
        self.btn_open = button(t("btn_open"), "folder")
        self.btn_eject = button(t("btn_eject"), "eject", "Danger")
        self.btn_install.clicked.connect(lambda: self.install_requested.emit(self.iso))
        self.btn_open.clicked.connect(lambda: self.open_requested.emit(self.iso))
        self.btn_eject.clicked.connect(lambda: self.eject_requested.emit(self.iso))
        self.btn_install.setMinimumWidth(190)
        row.addWidget(self.btn_install, 1)
        row.addWidget(self.btn_open)
        row.addWidget(self.btn_eject)
        fl.addLayout(row)
        self.stack.addWidget(full)
        self.set_iso(None)

    def set_iso(self, iso: core.IsoMount | None, running_text: str = ""):
        self.iso = iso
        if iso is None:
            self.stack.setCurrentIndex(0)
            self.setProperty("empty", True)
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.stack.setCurrentIndex(1)
            self.setProperty("empty", False)
            self.setCursor(Qt.ArrowCursor)
            self.title.setText(iso.label)
            self.file.setText(iso.name)
            self.drive_badge.setText(self.t("drive", l=iso.drive_letter) if iso.drive_letter else "")
            self.drive_badge.setVisible(bool(iso.drive_letter))
            self.path.setText(iso.mountpoint or self.t("not_mounted"))
            found = core.find_installers(iso.mountpoint) if iso.mountpoint else []
            self.installer.setText(self.t("installer_found", exe=os.path.relpath(found[0], iso.mountpoint))
                                   if found else self.t("installer_none"))
            self.btn_install.setEnabled(bool(iso.mountpoint))
            self.btn_open.setEnabled(bool(iso.mountpoint))
            self.running.setText(running_text)
            self.running.setVisible(bool(running_text))
        repolish(self)

    def mousePressEvent(self, e):  # noqa: N802
        if self.iso is None and e.button() == Qt.LeftButton:
            self.mount_requested.emit(self.slot, "")
        super().mousePressEvent(e)

    def dragEnterEvent(self, e):  # noqa: N802
        if self.iso is None and _iso_from_mime(e.mimeData()):
            e.acceptProposedAction()
            self.setProperty("drop", True)
            repolish(self)

    def dragLeaveEvent(self, e):  # noqa: N802
        self.setProperty("drop", False)
        repolish(self)

    def dropEvent(self, e):  # noqa: N802
        self.setProperty("drop", False)
        repolish(self)
        p = _iso_from_mime(e.mimeData())
        if p:
            e.acceptProposedAction()
            self.mount_requested.emit(self.slot, p)


class Header(QWidget):
    def __init__(self, title: str, sub: str = ""):
        super().__init__()
        self.lay = QHBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        col = QVBoxLayout()
        col.setSpacing(4)
        self.title = label(title, "Title")
        self.sub = label(sub, "Sub", wrap=True)
        col.addWidget(self.title)
        col.addWidget(self.sub)
        self.lay.addLayout(col, 1)

    def add(self, w):
        self.lay.addWidget(w, 0, Qt.AlignBottom)


class IsoPage(QWidget):
    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win, t = win, win.t
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 32, 36, 28)
        lay.setSpacing(22)
        self.header = Header(t("isos_title"))
        self.btn_mount = button(t("btn_mount"), "plus", "Primary")
        self.btn_eject_all = button(t("btn_eject_all"), "eject")
        self.btn_mount.clicked.connect(lambda: win.mount_dialog(None))
        self.btn_eject_all.clicked.connect(win.eject_all)
        self.header.add(self.btn_eject_all)
        self.header.add(self.btn_mount)
        lay.addWidget(self.header)

        self.running_bar = QFrame()
        self.running_bar.setObjectName("RunningBar")
        rb = QHBoxLayout(self.running_bar)
        rb.setContentsMargins(16, 10, 12, 10)
        ic = QLabel()
        ic.setPixmap(svg_pixmap("play", C["accent_h"], 20))
        rb.addWidget(ic)
        self.running_text = label("", "")
        self.running_text.setStyleSheet("font-weight: 600;")
        rb.addWidget(self.running_text, 1)
        self.btn_log = button(t("btn_open_log"), "log")
        self.btn_log.clicked.connect(win.open_last_log)
        rb.addWidget(self.btn_log)
        self.running_bar.hide()
        lay.addWidget(self.running_bar)

        grid = QGridLayout()
        grid.setSpacing(18)
        self.cards = []
        for i in range(core.MAX_ISOS):
            c = SlotCard(t, i)
            c.mount_requested.connect(lambda slot, path: win.mount_dialog(slot, path))
            c.eject_requested.connect(win.eject_iso)
            c.open_requested.connect(lambda iso: core.open_path(iso.mountpoint))
            c.install_requested.connect(win.install_dialog)
            grid.addWidget(c, i // 2, i % 2)
            self.cards.append(c)
        lay.addLayout(grid, 1)

    def update_isos(self, isos: list[core.IsoMount], running: dict):
        t = self.win.t
        by_slot = {m.slot: m for m in isos}
        for i, card in enumerate(self.cards):
            m = by_slot.get(i)
            card.set_iso(m, running.get(m.loop, "") if m else "")
        self.header.sub.setText(t("isos_sub", n=len(isos), max=core.MAX_ISOS))
        self.btn_mount.setEnabled(len(isos) < core.MAX_ISOS)
        self.btn_eject_all.setEnabled(bool(isos))

    def set_running(self, text: str):
        self.running_text.setText(text)
        self.running_bar.setVisible(bool(text))


class LaunchDialog(QDialog):
    def __init__(self, win: "MainWindow", iso: core.IsoMount | None = None, prefix: core.Prefix | None = None,
                 exe: str = ""):
        super().__init__(win)
        self.win, t = win, win.t
        self.setWindowTitle(t("launch_title"))
        self.setMinimumSize(760, 700)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)
        lay = QVBoxLayout(body)
        lay.setContentsMargins(28, 24, 28, 8)
        lay.setSpacing(8)
        head = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(svg_pixmap("play", C["accent"], 34))
        head.addWidget(ic)
        title_text = t("launch_header", iso=iso.label) if iso else t("launch_title")
        head.addWidget(label(title_text, "Title"), 1)
        lay.addLayout(head)

        lay.addWidget(label(t("launch_exe"), "SectionTitle"))
        self.exe_list = QListWidget()
        self.exe_list.setMinimumHeight(120)
        self.exe_list.setMaximumHeight(130)
        base = iso.mountpoint if iso else ""
        exes = core.find_installers(base) if iso else ([exe] if exe else [])
        for p in exes:
            item = QListWidgetItem(svg_icon("file", C["muted"], 18), os.path.relpath(p, base) if base else p)
            item.setData(Qt.UserRole, p)
            self.exe_list.addItem(item)
        if self.exe_list.count():
            self.exe_list.setCurrentRow(0)
        lay.addWidget(self.exe_list)
        row = QHBoxLayout()
        self.no_exe = label(t("launch_no_exe") if not exes else "", "Muted", wrap=True)
        row.addWidget(self.no_exe, 1)
        browse = button(t("launch_browse"), "folder")
        browse.clicked.connect(lambda: self._browse(base or (prefix.drive_c if prefix else core.home())))
        row.addWidget(browse)
        lay.addLayout(row)

        lay.addSpacing(6)
        lay.addWidget(label(t("launch_prefix"), "SectionTitle"))
        self.prefix_box = QComboBox()
        self.prefix_box.setEditable(True)
        names = [p.name for p in core.list_prefixes(win.cfg)]
        self.prefix_box.addItems(names)
        suggested = prefix.name if prefix else suggest_prefix_name(iso.name if iso else "")
        self.prefix_box.setCurrentText(suggested)
        self.prefix_box.setEnabled(prefix is None)
        lay.addWidget(self.prefix_box)
        lay.addWidget(label(t("launch_prefix_hint"), "Muted", wrap=True))

        lay.addSpacing(6)
        lay.addWidget(label(t("launch_proton"), "SectionTitle"))
        self.proton_box = proton_combo(win, (prefix.meta.get("proton_path") if prefix else "") or win.cfg["proton"])
        lay.addWidget(self.proton_box)

        lay.addSpacing(6)
        lay.addWidget(label(t("launch_options"), "SectionTitle"))
        orow = QHBoxLayout()
        self.options = QLineEdit(win.cfg.get("launch_options", core.DEFAULT_LAUNCH_OPTIONS))
        orow.addWidget(self.options, 1)
        reset = button(t("launch_reset"), "refresh")
        reset.clicked.connect(lambda: self.options.setText(core.DEFAULT_LAUNCH_OPTIONS))
        orow.addWidget(reset)
        lay.addLayout(orow)
        lay.addWidget(label(t("launch_options_hint"), "Muted", wrap=True))
        lay.addSpacing(6)

        self.runtime = QCheckBox(t("launch_runtime"))
        self.runtime.setChecked(bool(win.cfg.get("use_runtime", True)))
        lay.addWidget(self.runtime)
        lay.addStretch(1)

        btns = QHBoxLayout()
        btns.setContentsMargins(28, 8, 28, 22)
        btns.addStretch(1)
        cancel = button(t("cancel"))
        cancel.clicked.connect(self.reject)
        self.start = button(t("launch_start"), "play", "Primary")
        self.start.setDefault(True)
        self.start.clicked.connect(self._accept)
        self.start.setEnabled(bool(win.protons))
        btns.addWidget(cancel)
        btns.addWidget(self.start)
        outer.addLayout(btns)

    def _browse(self, start_dir: str):
        path, _ = QFileDialog.getOpenFileName(self, self.win.t("launch_browse"), start_dir,
                                              "Windows (*.exe *.EXE *.msi *.MSI *.bat);;* (*)")
        if path:
            item = QListWidgetItem(svg_icon("file", C["muted"], 18), path)
            item.setData(Qt.UserRole, path)
            self.exe_list.insertItem(0, item)
            self.exe_list.setCurrentRow(0)
            self.no_exe.setText("")

    def _accept(self):
        t = self.win.t
        if not self.exe_list.currentItem():
            QMessageBox.warning(self, t("error"), t("err_need_exe"))
            return
        if not core.safe_name(self.prefix_box.currentText()).strip() or not self.prefix_box.currentText().strip():
            QMessageBox.warning(self, t("error"), t("err_need_prefix"))
            return
        self.accept()

    def values(self) -> dict:
        return {
            "exe": self.exe_list.currentItem().data(Qt.UserRole),
            "prefix": self.prefix_box.currentText().strip(),
            "proton": self.proton_box.currentData() or "auto",
            "options": self.options.text().strip(),
            "runtime": self.runtime.isChecked(),
        }


def suggest_prefix_name(iso_name: str) -> str:
    n = os.path.splitext(os.path.basename(iso_name))[0]
    n = re.sub(r"[_.]+", " ", n)
    n = re.sub(r"[\s\-–(\[]*\b(disc|disk|cd|dvd)\s*\d+\b[)\]]*", "", n, flags=re.IGNORECASE)
    return core.safe_name(n.strip(" -–"))


def proton_combo(win: "MainWindow", current: str) -> QComboBox:
    box = QComboBox()
    t = win.t
    if not win.protons:
        box.addItem(t("proton_none"), "auto")
        box.setEnabled(False)
        return box
    box.addItem(t("proton_auto", name=core.pick_proton(win.protons).name), "auto")
    for tool in win.protons:
        box.addItem(tool.name, tool.path)
    idx = 0
    for i in range(box.count()):
        if current and (box.itemData(i) == current or box.itemText(i) == current):
            idx = i
            break
    box.setCurrentIndex(idx)
    return box


class PrefixCard(QFrame):
    def __init__(self, win: "MainWindow", prefix: core.Prefix):
        super().__init__()
        self.setObjectName("Card")
        t = win.t
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(16)
        ic = QLabel()
        ic.setPixmap(svg_pixmap("game", C["accent"], 44))
        lay.addWidget(ic, 0, Qt.AlignTop)
        col = QVBoxLayout()
        col.setSpacing(4)
        col.addWidget(ElidedLabel(prefix.name, "CardTitle", Qt.ElideRight))
        exe = prefix.meta.get("last_exe", "")
        has_exe = bool(exe) and os.path.isfile(exe)
        info = t("game_exe", exe=os.path.basename(exe)) if has_exe else t("game_no_exe")
        col.addWidget(label(info, "Sub", wrap=True))
        extra = prefix.path + (f"  ·  {prefix.meta['proton']}" if prefix.meta.get("proton") else "")
        col.addWidget(ElidedLabel(extra, "Muted"))
        lay.addLayout(col, 1)
        btns = QGridLayout()
        btns.setSpacing(8)
        play = button(t("btn_play"), "play", "Primary")
        play.setEnabled(has_exe)
        play.clicked.connect(lambda: win.run_in_prefix(prefix, exe))
        run = button(t("btn_run_exe"), "file")
        run.clicked.connect(lambda: win.pick_and_run_in_prefix(prefix))
        openc = button(t("btn_open_c"), "folder")
        openc.clicked.connect(lambda: core.open_path(prefix.drive_c if os.path.isdir(prefix.drive_c) else prefix.path))
        delete = button(t("btn_delete"), "trash", "Danger")
        delete.clicked.connect(lambda: win.delete_prefix(prefix))
        btns.addWidget(play, 0, 0)
        btns.addWidget(run, 0, 1)
        btns.addWidget(openc, 1, 0)
        btns.addWidget(delete, 1, 1)
        lay.addLayout(btns)


class GamesPage(QWidget):
    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win = win
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 32, 36, 28)
        lay.setSpacing(18)
        self.header = Header(win.t("games_title"))
        lay.addWidget(self.header)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        lay.addWidget(self.scroll, 1)
        self.refresh()

    def refresh(self):
        t = self.win.t
        self.header.sub.setText(t("games_sub", path=core.prefix_base(self.win.cfg)))
        inner = QWidget()
        col = QVBoxLayout(inner)
        col.setContentsMargins(0, 0, 8, 0)
        col.setSpacing(14)
        prefixes = core.list_prefixes(self.win.cfg)
        if not prefixes:
            e = label(t("games_empty"), "Sub", wrap=True)
            e.setAlignment(Qt.AlignCenter)
            col.addStretch(1)
            col.addWidget(e)
        for p in prefixes:
            col.addWidget(PrefixCard(self.win, p))
        col.addStretch(1)
        self.scroll.setWidget(inner)


class SettingsPage(QWidget):
    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win, t, cfg = win, win.t, win.cfg
        outer = QVBoxLayout(self)
        outer.setContentsMargins(36, 32, 36, 28)
        outer.setSpacing(18)
        outer.addWidget(Header(t("set_title")))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll, 1)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(16)
        scroll.setWidget(inner)

        # general
        gen, gl = self._card(t("set_section_general"), "gear")
        r = QHBoxLayout()
        r.addWidget(label(t("set_language")), 1)
        self.lang = QComboBox()
        self.lang.addItem(t("lang_system"), "")
        self.lang.addItem("Deutsch", "de")
        self.lang.addItem("English", "en")
        self.lang.setCurrentIndex(max(0, self.lang.findData(cfg.get("language", ""))))
        self.lang.currentIndexChanged.connect(self._lang_changed)
        self.lang.setMinimumWidth(260)
        r.addWidget(self.lang)
        gl.addLayout(r)
        r = QHBoxLayout()
        self.autoupd = QCheckBox(t("set_autoupdate"))
        self.autoupd.setChecked(bool(cfg.get("auto_update", True)))
        self.autoupd.toggled.connect(lambda v: self._set("auto_update", bool(v)))
        r.addWidget(self.autoupd, 1)
        chk = button(t("set_check_now"), "download")
        chk.clicked.connect(lambda: win.check_updates(manual=True))
        r.addWidget(chk)
        gl.addLayout(r)
        lay.addWidget(gen)

        # proton
        pro, pl = self._card(t("set_section_proton"), "game")
        r = QHBoxLayout()
        r.addWidget(label(t("set_proton")), 1)
        self.proton = proton_combo(win, cfg.get("proton", "auto"))
        self.proton.setMinimumWidth(320)
        self.proton.currentIndexChanged.connect(lambda _: self._set("proton", self.proton.currentData() or "auto"))
        r.addWidget(self.proton)
        pl.addLayout(r)
        r = QHBoxLayout()
        r.addWidget(label(t("set_protons_found", n=len(win.protons)), "Muted"), 1)
        rescan = button(t("set_rescan"), "refresh")
        rescan.clicked.connect(win.rescan_protons)
        r.addWidget(rescan)
        pl.addLayout(r)
        self.rt = QCheckBox(t("set_runtime"))
        self.rt.setChecked(bool(cfg.get("use_runtime", True)))
        self.rt.toggled.connect(lambda v: self._set("use_runtime", bool(v)))
        pl.addWidget(self.rt)
        self.log = QCheckBox(t("set_log"))
        self.log.setChecked(bool(cfg.get("proton_log", False)))
        self.log.toggled.connect(lambda v: self._set("proton_log", bool(v)))
        pl.addWidget(self.log)
        pl.addWidget(label(t("set_options")))
        r = QHBoxLayout()
        self.opts = QLineEdit(cfg.get("launch_options", core.DEFAULT_LAUNCH_OPTIONS))
        self.opts.editingFinished.connect(lambda: self._set("launch_options", self.opts.text().strip()))
        r.addWidget(self.opts, 1)
        reset = button(t("launch_reset"), "refresh")
        reset.clicked.connect(self._reset_opts)
        r.addWidget(reset)
        pl.addLayout(r)
        pl.addWidget(label(t("launch_options_hint"), "Muted", wrap=True))
        pl.addWidget(label(t("set_prefix_base")))
        r = QHBoxLayout()
        self.base = ElidedLabel(core.prefix_base(cfg), "Sub")
        r.addWidget(self.base, 1)
        ch = button(t("set_choose"), "folder")
        ch.clicked.connect(self._choose_base)
        r.addWidget(ch)
        pl.addLayout(r)
        lay.addWidget(pro)
        lay.addStretch(1)

    def _card(self, title: str, icon: str):
        card = QFrame()
        card.setObjectName("Card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(22, 18, 22, 20)
        lay.setSpacing(12)
        h = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(svg_pixmap(icon, C["accent"], 22))
        h.addWidget(ic)
        h.addWidget(label(title, "SectionTitle"), 1)
        lay.addLayout(h)
        return card, lay

    def _set(self, key, value):
        self.win.cfg[key] = value
        self.win.cfg.save()

    def _reset_opts(self):
        self.opts.setText(core.DEFAULT_LAUNCH_OPTIONS)
        self._set("launch_options", core.DEFAULT_LAUNCH_OPTIONS)

    def _choose_base(self):
        d = QFileDialog.getExistingDirectory(self, self.win.t("set_prefix_base"), core.prefix_base(self.win.cfg))
        if d:
            self._set("prefix_base", d)
            self.base.setText(d)
            self.win.games_page.refresh()

    def _lang_changed(self, _):
        self._set("language", self.lang.currentData() or "")
        QTimer.singleShot(0, lambda: self.win.rebuild(page=2))


class AboutPage(QWidget):
    def __init__(self, win: "MainWindow"):
        super().__init__()
        t = win.t
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 32, 36, 28)
        lay.addStretch(1)
        ic = QLabel()
        ic.setPixmap(app_icon_pixmap(128))
        ic.setAlignment(Qt.AlignCenter)
        lay.addWidget(ic)
        for text, name in ((core.APP_NAME, "Title"), (t("version", v=core.app_version()), "Sub")):
            lab = label(text, name)
            lab.setAlignment(Qt.AlignCenter)
            lay.addWidget(lab)
        lay.addSpacing(12)
        d = label(t("about_text", max=core.MAX_ISOS), "", wrap=True)
        d.setAlignment(Qt.AlignCenter)
        d.setFixedWidth(640)
        d.setMinimumHeight(d.heightForWidth(640) + 6)
        lay.addWidget(d, 0, Qt.AlignHCenter)
        lay.addSpacing(10)
        cr = label(t("about_credits"), "SectionTitle")
        cr.setAlignment(Qt.AlignCenter)
        lay.addWidget(cr)
        lay.addSpacing(14)
        gh = button(t("btn_github"), "info")
        gh.clicked.connect(lambda: core.open_path(core.REPO_URL))
        lay.addWidget(gh, 0, Qt.AlignCenter)
        lay.addStretch(2)


class Toast(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_text(self, text: str, ms: int = 3500):
        self.setText(text)
        self.adjustSize()
        p = self.parentWidget()
        self.move((p.width() - self.width()) // 2 + 115, p.height() - self.height() - 28)
        self.raise_()
        self.show()
        self._timer.start(ms)


class UpdateDialog(QDialog):
    def __init__(self, win: "MainWindow", info: dict):
        super().__init__(win)
        t = win.t
        self.setWindowTitle(t("upd_title"))
        self.setMinimumSize(620, 480)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(12)
        h = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(svg_pixmap("download", C["ok"], 34))
        h.addWidget(ic)
        h.addWidget(label(t("upd_title"), "Title"), 1)
        lay.addLayout(h)
        lay.addWidget(label(t("upd_text", new=info["version"], old=core.app_version()), "Sub", wrap=True))
        lay.addWidget(label(t("upd_notes"), "SectionTitle"))
        notes = QTextBrowser()
        notes.setOpenExternalLinks(True)
        notes.setMarkdown(info.get("notes") or "-")
        lay.addWidget(notes, 1)
        row = QHBoxLayout()
        row.addStretch(1)
        later = button(t("upd_later"))
        later.clicked.connect(self.reject)
        now = button(t("upd_now"), "download", "Primary")
        now.clicked.connect(self.accept)
        now.setDefault(True)
        row.addWidget(later)
        row.addWidget(now)
        lay.addLayout(row)


# =============================================================================
#  Main window
# =============================================================================
class MainWindow(QMainWindow):
    def __init__(self, cfg: core.Config, check_updates: bool = True):
        super().__init__()
        self.cfg = cfg
        self.t = Translator(cfg.get("language") or core.system_language())
        self.protons = core.find_protons()
        self.tasks: list[QThread] = []
        self.runners: list[GameRunner] = []
        self.last_log = ""
        self.update_info = None
        self._iso_state = None
        self.isos: list[core.IsoMount] = []
        self.setWindowTitle(core.APP_NAME)
        self.setWindowIcon(QIcon(app_icon_pixmap(64)))
        self.resize(1200, 780)
        self.setMinimumSize(980, 660)
        self.setAcceptDrops(True)
        self.build()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)
        self.refresh(force=True)
        if check_updates and cfg.get("auto_update", True):
            QTimer.singleShot(1200, lambda: self.check_updates(manual=False))

    # ----- UI construction ----------------------------------------------------
    def build(self, page: int = 0):
        t = self.t
        central = QWidget()
        central.setObjectName("Content")
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        side = QFrame()
        side.setObjectName("Sidebar")
        side.setFixedWidth(250)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(16, 22, 16, 18)
        sl.setSpacing(6)
        logo = QHBoxLayout()
        lg = QLabel()
        lg.setPixmap(app_icon_pixmap(46))
        logo.addWidget(lg)
        nm = QVBoxLayout()
        nm.setSpacing(0)
        nm.addWidget(label("SteamOS", "Small"))
        nm.addWidget(label("ISO Mount Tool", "AppName"))
        logo.addLayout(nm, 1)
        sl.addLayout(logo)
        sl.addSpacing(22)
        self.nav = []
        for i, (key, icon) in enumerate((("nav_isos", "disc"), ("nav_games", "game"),
                                         ("nav_settings", "gear"), ("nav_about", "info"))):
            b = button(t(key), icon)
            b.setObjectName("NavButton")
            b.setCheckable(True)
            b.setIconSize(QSize(22, 22))
            b.setIcon(svg_icon(icon, C["text"], 22))
            b.clicked.connect(lambda _=False, i=i: self.show_page(i))
            sl.addWidget(b)
            self.nav.append(b)
        sl.addStretch(1)
        self.update_btn = button("", "download", "Update", C["ok"])
        self.update_btn.clicked.connect(lambda: self.offer_update(self.update_info))
        self.update_btn.hide()
        sl.addWidget(self.update_btn)
        sl.addWidget(label(t("version", v=core.app_version()), "Small"))
        sl.addWidget(label(t("about_credits"), "Small", wrap=True))
        root.addWidget(side)

        self.pages = QStackedWidget()
        self.iso_page = IsoPage(self)
        self.games_page = GamesPage(self)
        self.settings_page = SettingsPage(self)
        self.about_page = AboutPage(self)
        for p in (self.iso_page, self.games_page, self.settings_page, self.about_page):
            self.pages.addWidget(p)
        root.addWidget(self.pages, 1)
        self.setCentralWidget(central)
        self.toast = Toast(central)
        if self.update_info:
            self._show_update_badge()
        self.show_page(page)
        self._iso_state = None

    def rebuild(self, page: int = 0):
        self.t = Translator(self.cfg.get("language") or core.system_language())
        self.build(page)
        self.refresh(force=True)
        self._update_running()

    def show_page(self, i: int):
        self.pages.setCurrentIndex(i)
        for j, b in enumerate(self.nav):
            b.setChecked(i == j)
        if i == 1:
            self.games_page.refresh()

    # ----- state ------------------------------------------------------------------
    def refresh(self, force: bool = False):
        try:
            isos = core.current_isos()
        except Exception:  # noqa: BLE001
            isos = []
        state = tuple((m.loop, m.iso, tuple(m.mountpoints), m.slot) for m in isos)
        if force or state != self._iso_state:
            self._iso_state = state
            self.isos = isos
            self.iso_page.update_isos(isos, self._running_by_loop())

    def _running_by_loop(self) -> dict:
        out = {}
        for r in self.runners:
            for m in self.isos:
                mp = m.mountpoint
                if mp and r.exe.startswith(mp.rstrip("/") + "/"):
                    out[m.loop] = self.t("running_on", exe=r.exe_name)
        return out

    def _update_running(self):
        texts = [getattr(r, "status_text", "") for r in self.runners]
        self.iso_page.set_running(" · ".join(x for x in texts if x))
        self.iso_page.update_isos(self.isos, self._running_by_loop())

    def notify(self, text: str):
        self.toast.show_text(text)

    def error(self, text: str, detail: str = ""):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(self.t("error"))
        box.setText(text)
        if detail:
            box.setDetailedText(detail)
        box.exec()

    def ask(self, text: str) -> bool:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle(core.APP_NAME)
        box.setText(text)
        yes = box.addButton(self.t("yes"), QMessageBox.YesRole)
        box.addButton(self.t("no"), QMessageBox.NoRole)
        box.exec()
        return box.clickedButton() is yes

    def _start_task(self, fn, *args, done=None):
        task = Task(fn, *args, parent=self)

        def finish(res, exc):
            if task in self.tasks:
                self.tasks.remove(task)
            if done:
                done(res, exc)
            self.refresh(force=True)

        task.done.connect(finish)
        self.tasks.append(task)
        task.start()

    def _mount_error(self, e: Exception):
        if isinstance(e, core.AlreadyMounted):
            self.notify(self.t(e.key, **e.fmt).replace("\n", " "))
        elif isinstance(e, core.MountError):
            self.error(self.t(e.key, **e.fmt), e.detail)
        else:
            self.error(str(e), traceback.format_exc())

    # ----- ISO actions ----------------------------------------------------------
    def mount_dialog(self, slot: int | None, path: str = ""):
        if not path:
            start = self.cfg.get("last_dir") or os.path.join(core.home(), "Downloads")
            if not os.path.isdir(start):
                start = core.home()
            path, _ = QFileDialog.getOpenFileName(self, self.t("pick_iso"), start,
                                                  f"{self.t('iso_filter')};;* (*)")
            if not path:
                return
        self.cfg["last_dir"] = os.path.dirname(path)
        self.cfg.save()
        self.setCursor(Qt.WaitCursor)

        def done(res, exc):
            self.unsetCursor()
            if exc:
                self._mount_error(exc)
            elif res:
                self.notify(self.t("mounted_toast", name=res.name, l=res.drive_letter))

        self._start_task(core.mount_iso, path, slot, done=done)

    def eject_iso(self, iso: core.IsoMount):
        def done(_, exc):
            if exc:
                self._mount_error(exc)
            else:
                self.notify(self.t("ejected_toast", name=iso.name))

        self._start_task(core.eject, iso.loop, done=done)

    def eject_all(self):
        isos = list(self.isos)
        if not isos:
            return
        if not self.ask(self.t("confirm_eject_all", n=len(isos))):
            return

        def work():
            errors = []
            for m in isos:
                try:
                    core.eject(m.loop)
                except core.MountError as e:
                    errors.append(f"{m.name}: {e.detail}")
            if errors:
                raise core.MountError("err_eject", "\n".join(errors))

        self._start_task(work, done=lambda _, exc: self._mount_error(exc) if exc else None)

    def dragEnterEvent(self, e):  # noqa: N802
        if _iso_from_mime(e.mimeData()):
            e.acceptProposedAction()

    def dropEvent(self, e):  # noqa: N802
        p = _iso_from_mime(e.mimeData())
        if p:
            self.mount_dialog(None, p)

    # ----- Proton ------------------------------------------------------------------
    def rescan_protons(self):
        self.protons = core.find_protons()
        self.rebuild(page=self.pages.currentIndex())
        self.notify(self.t("set_protons_found", n=len(self.protons)))

    def _tool(self, choice: str) -> core.ProtonTool | None:
        return core.pick_proton(self.protons, choice or "auto")

    def install_dialog(self, iso: core.IsoMount):
        if not self.protons:
            self.protons = core.find_protons()
        if not self.protons:
            self.error(self.t("err_no_proton"))
            return
        dlg = LaunchDialog(self, iso=iso)
        if dlg.exec() != QDialog.Accepted:
            return
        v = dlg.values()
        prefix = core.get_prefix(self.cfg, v["prefix"])
        self._run(v["exe"], prefix, self._tool(v["proton"]), v["options"], v["runtime"], from_iso=True)

    def pick_and_run_in_prefix(self, prefix: core.Prefix):
        if not self.protons:
            self.error(self.t("err_no_proton"))
            return
        start = prefix.drive_c if os.path.isdir(prefix.drive_c) else prefix.path
        exe, _ = QFileDialog.getOpenFileName(self, self.t("pick_game_exe"), start,
                                             "Windows (*.exe *.EXE *.msi *.MSI *.bat);;* (*)")
        if not exe:
            return
        if not os.path.basename(exe).lower().startswith("unins"):
            prefix.meta["last_exe"] = exe
            prefix.save_meta()
        self.run_in_prefix(prefix, exe)
        self.games_page.refresh()

    def run_in_prefix(self, prefix: core.Prefix, exe: str):
        if not exe or not os.path.isfile(exe):
            return
        tool = self._tool(prefix.meta.get("proton_path") or self.cfg.get("proton", "auto"))
        if not tool:
            self.error(self.t("err_no_proton"))
            return
        self._run(exe, prefix, tool, self.cfg.get("launch_options", core.DEFAULT_LAUNCH_OPTIONS),
                  bool(self.cfg.get("use_runtime", True)), from_iso=False)

    def _run(self, exe, prefix, tool, options, use_runtime, from_iso):
        r = GameRunner(self.t, self.cfg, exe, prefix, tool, options, use_runtime, from_iso, parent=self)
        r.status_text = ""

        def on_status(text):
            r.status_text = text
            self._update_running()

        def on_done(code, log_path):
            self.last_log = log_path
            if r in self.runners:
                self.runners.remove(r)
            self._update_running()
            self.games_page.refresh()
            self._finished_dialog(r.exe_name, code, log_path, from_iso)

        r.status.connect(on_status)
        r.finished_run.connect(on_done)
        self.runners.append(r)
        self.last_log = r.log_path
        r.start()
        self.show_page(0)
        self.notify(self.t("st_running", exe=r.exe_name, name=prefix.name))

    def _finished_dialog(self, exe_name, code, log_path, from_iso):
        t = self.t
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle(t("finished_title"))
        box.setText(t("finished_text", exe=exe_name, code=code) if from_iso else t("st_finished", exe=exe_name))
        games = box.addButton(t("btn_show_games"), QMessageBox.AcceptRole) if from_iso else None
        logb = box.addButton(t("btn_open_log"), QMessageBox.ActionRole)
        box.addButton(t("ok"), QMessageBox.RejectRole)
        box.exec()
        if games is not None and box.clickedButton() is games:
            self.show_page(1)
        elif box.clickedButton() is logb:
            core.open_path(log_path)

    def open_last_log(self):
        if self.last_log:
            core.open_path(self.last_log)

    def delete_prefix(self, prefix: core.Prefix):
        if not self.ask(self.t("confirm_delete", name=prefix.name, path=prefix.path)):
            return
        try:
            core.delete_prefix(prefix)
        except OSError as e:
            self.error(str(e))
        self.games_page.refresh()

    # ----- updates -------------------------------------------------------------------
    def check_updates(self, manual: bool):
        def done(info, exc):
            if exc or not info:
                if manual:
                    self.error(self.t("upd_fail_check"))
                return
            if core.version_gt(info["version"], core.app_version()):
                self.update_info = info
                self._show_update_badge()
                self.offer_update(info)
            elif manual:
                QMessageBox.information(self, core.APP_NAME, self.t("upd_none", v=core.app_version()))

        self._start_task(core.fetch_latest_release, done=done)

    def _show_update_badge(self):
        self.update_btn.setText(self.t("upd_badge", v=self.update_info["version"]))
        self.update_btn.show()

    def offer_update(self, info):
        if not info:
            return
        if UpdateDialog(self, info).exec() != QDialog.Accepted:
            return
        target = core.can_self_update()
        if not target or not info.get("url"):
            QMessageBox.information(self, core.APP_NAME, self.t("upd_manual"))
            QDesktopServices.openUrl(QUrl(info.get("page") or core.REPO_URL))
            return
        prog = QProgressDialog(self.t("upd_downloading"), "", 0, 0, self)
        prog.setCancelButton(None)
        prog.setWindowTitle(self.t("upd_title"))
        prog.setWindowModality(Qt.WindowModal)
        prog.setMinimumDuration(0)
        prog.show()

        def done(ok, exc):
            prog.close()
            if exc or not ok:
                self.error(self.t("upd_fail_dl"))
                return
            QMessageBox.information(self, core.APP_NAME, self.t("upd_done", v=info["version"]))
            subprocess.Popen([target, "--no-update-check"], env=core.clean_env(), start_new_session=True)
            QApplication.instance().quit()

        self._start_task(core.download_update, info["url"], target, done=done)

    def closeEvent(self, e):  # noqa: N802
        self.timer.stop()
        super().closeEvent(e)


# =============================================================================
#  Start
# =============================================================================
def _prepare_qt_env():
    if not os.environ.get("QT_QPA_PLATFORM"):
        os.environ["ISOMT_ORIG_QT_QPA_PLATFORM"] = ""     # removed again for child processes
        os.environ["QT_QPA_PLATFORM"] = "xcb;wayland" if os.environ.get("DISPLAY") else "wayland;xcb"


def make_app() -> QApplication:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(core.APP_NAME)
    app.setDesktopFileName(core.APP_ID)
    app.setStyle("Fusion")
    pal = QPalette()
    for role, col in ((QPalette.Window, C["bg"]), (QPalette.WindowText, C["text"]), (QPalette.Base, C["bg"]),
                      (QPalette.AlternateBase, C["card"]), (QPalette.Text, C["text"]), (QPalette.Button, C["card2"]),
                      (QPalette.ButtonText, C["text"]), (QPalette.Highlight, C["accent"]),
                      (QPalette.HighlightedText, "#ffffff"), (QPalette.ToolTipBase, C["card2"]),
                      (QPalette.ToolTipText, C["text"]), (QPalette.PlaceholderText, C["muted"])):
        pal.setColor(role, QColor(col))
    app.setPalette(pal)
    qss = QSS
    try:
        check = os.path.join(core.data_dir(), "ui", "check.svg")
        os.makedirs(os.path.dirname(check), exist_ok=True)
        with open(check, "w", encoding="utf-8") as f:
            f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#ffffff" '
                    'stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>')
        qss += "QCheckBox::indicator:checked { image: url(%s); }" % check.replace("\\", "/")
    except OSError:
        pass
    app.setStyleSheet(qss)
    return app


def run(cfg: core.Config, check_updates: bool = True) -> int:
    _prepare_qt_env()
    app = make_app()
    win = MainWindow(cfg, check_updates)
    win.show()
    return app.exec()


def make_screenshots(out_dir: str) -> int:
    """Renders all screens with demo data (used by CI to check the UI)."""
    os.makedirs(out_dir, exist_ok=True)
    errors = []
    tmp = tempfile.mkdtemp(prefix="isomt-shots-")
    from . import demo
    demo.create_demo_env(tmp)
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = make_app()

    def snap(widget, name):
        try:
            for _ in range(5):
                app.processEvents()
            widget.grab().save(os.path.join(out_dir, name + ".png"))
            print("saved", name)
        except Exception:  # noqa: BLE001
            errors.append(f"{name}:\n{traceback.format_exc()}")

    try:
        for lang in ("de", "en"):
            cfg = core.Config()
            cfg["language"] = lang
            cfg.save()
            win = MainWindow(cfg, check_updates=False)
            win.resize(1280, 800)
            win.show()
            snap(win, f"{lang}_1_isos")
            win.notify(win.t("mounted_toast", name="Anno 1602.iso", l="E"))
            snap(win, f"{lang}_1b_toast")
            win.toast.hide()
            dlg = LaunchDialog(win, iso=win.isos[0])
            dlg.show()
            snap(dlg, f"{lang}_2_launch")
            dlg.close()
            r = GameRunner(win.t, cfg, os.path.join(win.isos[0].mountpoint, "SETUP.EXE"),
                           core.get_prefix(cfg, "Need for Speed"), win.protons[0], "", True, True)
            r.status_text = win.t("st_running", exe="SETUP.EXE", name="Need for Speed")
            win.runners.append(r)
            win._update_running()
            snap(win, f"{lang}_3_running")
            win.runners.clear()
            win._update_running()
            for i, n in ((1, "4_games"), (2, "5_settings"), (3, "6_about")):
                win.show_page(i)
                snap(win, f"{lang}_{n}")
            upd = UpdateDialog(win, {"version": "2.1.0", "notes": "### Added\n- Something new\n- Another fix"})
            upd.show()
            snap(upd, f"{lang}_7_update")
            upd.close()
            win.close()
        # empty state
        for d in os.listdir(os.environ["ISOMOUNT_SYSBLOCK"]):
            import shutil
            shutil.rmtree(os.path.join(os.environ["ISOMOUNT_SYSBLOCK"], d))
        win = MainWindow(core.Config(), check_updates=False)
        win.resize(1280, 800)
        win.show()
        snap(win, "en_0_empty")
        win.resize(1280, 800)
        win.close()
    except Exception:  # noqa: BLE001
        errors.append(traceback.format_exc())
    with open(os.path.join(out_dir, "errors.txt"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(errors) if errors else "OK\n")
    print("\n".join(errors) if errors else "screenshots OK")
    return 1 if errors else 0
