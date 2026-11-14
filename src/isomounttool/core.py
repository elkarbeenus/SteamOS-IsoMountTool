"""Core logic of SteamOS ISO Mount Tool (standard library only).

Created by Dominic Lesina x Claude
https://github.com/elkarbeenus/SteamOS-IsoMountTool
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass, field

APP_ID = "steamos-isomounttool"
APP_NAME = "SteamOS ISO Mount Tool"
REPO = "elkarbeenus/SteamOS-IsoMountTool"
REPO_URL = f"https://github.com/{REPO}"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
MAX_ISOS = 4
DRIVE_LETTERS = ["d", "e", "f", "g"]          # slot 1..4 -> D: .. G: inside Proton prefixes
DEFAULT_LAUNCH_OPTIONS = "WINE_LARGE_ADDRESS_AWARE=1 %command%"
PREFIX_META = "isomounttool.json"
IS_WINDOWS = sys.platform == "win32"
_NO_WINDOW = 0x08000000                       # CREATE_NO_WINDOW (Windows)


# =============================================================================
#  Version / paths
# =============================================================================
def _here() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def app_version() -> str:
    for p in (os.path.join(_here(), "VERSION"), os.path.join(_here(), "..", "..", "VERSION")):
        try:
            with open(p, encoding="utf-8") as f:
                v = f.read().strip()
                if v:
                    return v
        except OSError:
            pass
    return "0.0.0-dev"


def home() -> str:
    return os.path.expanduser("~")


def config_dir() -> str:
    if IS_WINDOWS:
        return os.path.join(os.environ.get("APPDATA") or os.path.join(home(), "AppData", "Roaming"), APP_ID)
    return os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.join(home(), ".config"), APP_ID)


def data_dir() -> str:
    if IS_WINDOWS:
        return os.path.join(os.environ.get("LOCALAPPDATA") or os.path.join(home(), "AppData", "Local"), APP_ID)
    return os.path.join(os.environ.get("XDG_DATA_HOME") or os.path.join(home(), ".local", "share"), APP_ID)


def drives_dir() -> str:
    return os.path.join(data_dir(), "drives")


def logs_dir() -> str:
    return os.path.join(data_dir(), "logs")


# =============================================================================
#  Config
# =============================================================================
DEFAULT_CONFIG = {
    "language": "",            # "" = follow system, "de", "en"
    "auto_update": True,
    "last_dir": "",
    "proton": "auto",          # "auto" or path of a Proton directory
    "use_runtime": True,       # run Proton inside the Steam Linux Runtime when available
    "proton_log": False,
    "prefix_base": "",         # "" = ~/Games/IsoMountTool
    "launch_options": DEFAULT_LAUNCH_OPTIONS,
    "drive_letters": False,    # experimental: map slots to D:..G: inside prefixes
}


class Config(dict):
    def __init__(self):
        super().__init__(DEFAULT_CONFIG)
        self.path = os.path.join(config_dir(), "config.json")
        self.load()

    def load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for k, v in data.items():
                    if k in DEFAULT_CONFIG and type(v) is type(DEFAULT_CONFIG[k]):
                        self[k] = v
            return
        except (OSError, ValueError):
            pass
        # migrate the key=value config of v1.x
        legacy = os.path.join(config_dir(), "config")
        try:
            with open(legacy, encoding="utf-8") as f:
                for line in f:
                    k, _, v = line.strip().partition("=")
                    if k == "UI_LANG" and v in ("de", "en"):
                        self["language"] = v
                    elif k == "AUTO_UPDATE" and v in ("0", "1"):
                        self["auto_update"] = v == "1"
                    elif k == "LAST_DIR" and v:
                        self["last_dir"] = v
        except OSError:
            pass

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(dict(self), f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
        except OSError:
            pass


def system_language() -> str:
    loc = os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or ""
    return "de" if loc.lower().startswith("de") else "en"


# =============================================================================
#  Environment for child processes
# =============================================================================
_APPIMAGE_VARS = ("APPDIR", "APPIMAGE", "ARGV0", "OWD")
_STRIP_VARS = ("PYTHONHOME", "PYTHONPATH", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "QML2_IMPORT_PATH")


def clean_env(extra: dict | None = None) -> dict:
    """Environment for external programs, without anything coming from our AppImage."""
    env = dict(os.environ)
    for k in _APPIMAGE_VARS + _STRIP_VARS:
        env.pop(k, None)
    # restore values AppRun saved before changing them (if any)
    for k in list(env):
        if k.startswith("ISOMT_ORIG_"):
            name = k[len("ISOMT_ORIG_"):]
            if env[k]:
                env[name] = env[k]
            else:
                env.pop(name, None)
            env.pop(k, None)
    if extra:
        env.update(extra)
    return env


def _popen_kwargs() -> dict:
    return {"creationflags": _NO_WINDOW} if IS_WINDOWS else {}


def run(cmd: list[str], timeout: float | None = 60, extra_env: dict | None = None) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                           encoding="utf-8", errors="replace",
                           env=clean_env(extra_env), timeout=timeout, **_popen_kwargs())
        return p.returncode, p.stdout or ""
    except FileNotFoundError:
        return 127, f"{cmd[0]}: not found"
    except subprocess.TimeoutExpired:
        return 124, f"{cmd[0]}: timeout"


def open_path(path: str):
    if IS_WINDOWS:
        try:
            os.startfile(path)  # noqa: S606  (Windows only)
            return True
        except OSError:
            return False
    for opener in ("xdg-open", "dolphin", "nautilus"):
        if shutil.which(opener):
            subprocess.Popen([opener, path], env=clean_env(), stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
            return True
    return False


# =============================================================================
#  ISO / loop devices
# =============================================================================
def _sys_block() -> str:
    return os.environ.get("ISOMOUNT_SYSBLOCK", "/sys/block")


def _proc_mounts() -> str:
    return os.environ.get("ISOMOUNT_PROC_MOUNTS", "/proc/mounts")


def _decode_mount_field(s: str) -> str:
    return re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), s)


def _loop_num(dev: str) -> int:
    m = re.search(r"(\d+)$", dev)
    return int(m.group(1)) if m else 0


def list_iso_loops() -> list[tuple[str, str]]:
    """[(\"/dev/loopN\", \"/path/file.iso\")] for every loop device backed by an .iso file."""
    out = []
    base = _sys_block()
    try:
        names = os.listdir(base)
    except OSError:
        return out
    for name in names:
        if not name.startswith("loop"):
            continue
        try:
            with open(os.path.join(base, name, "loop", "backing_file"), encoding="utf-8",
                      errors="surrogateescape") as f:
                bf = f.read().strip()
        except OSError:
            continue
        if bf.endswith(" (deleted)"):
            bf = bf[: -len(" (deleted)")]
        if bf.lower().endswith(".iso"):
            out.append((f"/dev/{name}", bf))
    out.sort(key=lambda t: _loop_num(t[0]))
    return out


def mount_table() -> list[tuple[str, str]]:
    rows = []
    try:
        with open(_proc_mounts(), encoding="utf-8", errors="surrogateescape") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    rows.append((_decode_mount_field(parts[0]), _decode_mount_field(parts[1])))
    except OSError:
        pass
    return rows


def _belongs(src: str, loop: str) -> bool:
    return src == loop or src.startswith(loop + "p")


def mount_sources_of(loop: str) -> list[str]:
    return [s for s, _ in mount_table() if _belongs(s, loop)]


def mountpoints_of(loop: str) -> list[str]:
    return [t for s, t in mount_table() if _belongs(s, loop)]


@dataclass
class IsoMount:
    loop: str
    iso: str
    mountpoints: list[str] = field(default_factory=list)
    slot: int = -1
    win_letter: str = ""          # real drive letter on Windows

    @property
    def name(self) -> str:
        return os.path.basename(self.iso)

    @property
    def mountpoint(self) -> str:
        return self.mountpoints[0] if self.mountpoints else ""

    @property
    def label(self) -> str:
        mp = self.mountpoint
        if self.win_letter or not mp:
            return os.path.splitext(self.name)[0]
        return os.path.basename(mp.rstrip("/")) or os.path.splitext(self.name)[0]

    @property
    def drive_letter(self) -> str:
        if self.win_letter:
            return self.win_letter.upper()
        return DRIVE_LETTERS[self.slot].upper() if 0 <= self.slot < len(DRIVE_LETTERS) else ""


# --- slots (stable positions 1..4, used for the drive letters) ---------------
def _slots_file() -> str:
    return os.path.join(data_dir(), "slots.json")


def _load_slots() -> dict[int, str]:
    try:
        with open(_slots_file(), encoding="utf-8") as f:
            data = json.load(f)
        return {int(k): v for k, v in data.items() if str(k).isdigit()}
    except (OSError, ValueError, AttributeError):
        return {}


def _save_slots(slots: dict[int, str]):
    try:
        os.makedirs(data_dir(), exist_ok=True)
        with open(_slots_file(), "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in slots.items()}, f)
    except OSError:
        pass


def current_isos(preferred: dict[str, int] | None = None) -> list[IsoMount]:
    """All mounted ISOs with their slot. Keeps slot positions stable between calls."""
    if IS_WINDOWS:
        isos = [IsoMount(img, img, [mnt], win_letter=letter) for img, letter, mnt in win_list_images()]
    else:
        isos = [IsoMount(loop, iso, mountpoints_of(loop)) for loop, iso in list_iso_loops()]
    slots = _load_slots()
    present = {m.iso for m in isos}
    new_slots = {s: p for s, p in slots.items() if p in present and 0 <= s < MAX_ISOS}
    by_iso = {p: s for s, p in new_slots.items()}
    for m in isos:
        if m.iso in by_iso:
            m.slot = by_iso[m.iso]
    for m in isos:
        if m.slot >= 0:
            continue
        want = (preferred or {}).get(m.iso)
        free = [s for s in range(MAX_ISOS) if s not in new_slots]
        if not free:
            break
        s = want if want in free else free[0]
        m.slot = s
        new_slots[s] = m.iso
    if new_slots != slots:
        _save_slots(new_slots)
    if not IS_WINDOWS:
        sync_drive_links(isos)
    return isos


# --- Windows: built-in ISO mounting (Mount-DiskImage) --------------------------
_PS_LIST = r"""$ErrorActionPreference = 'SilentlyContinue'
$r = @(Get-Volume | Where-Object { $_.DriveType -eq 'CD-ROM' -and $_.DriveLetter } | ForEach-Object {
  $img = Get-DiskImage -Volume $_
  if ($img -and $img.ImagePath) { [pscustomobject]@{ image = [string]$img.ImagePath; letter = [string]$_.DriveLetter } }
})
ConvertTo-Json -InputObject $r -Compress"""

_PS_MOUNT = r"""$ErrorActionPreference = 'Stop'
$img = Mount-DiskImage -ImagePath $env:ISOMT_PATH -StorageType ISO -PassThru
$letter = ''
for ($i = 0; $i -lt 20 -and -not $letter; $i++) {
  Start-Sleep -Milliseconds 250
  $letter = [string](Get-DiskImage -ImagePath $env:ISOMT_PATH | Get-Volume).DriveLetter
}
Write-Output "LETTER=$letter" """

_PS_EJECT = r"""$ErrorActionPreference = 'Stop'
Dismount-DiskImage -ImagePath $env:ISOMT_PATH | Out-Null
Write-Output 'OK'"""


def powershell(script: str, extra_env: dict | None = None, timeout: float | None = 60) -> tuple[int, str]:
    return run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                "-Command", script], timeout=timeout, extra_env=extra_env)


def win_list_images() -> list[tuple[str, str, str]]:
    """[(iso path, drive letter, mount path)] of mounted ISO images on Windows."""
    demo = os.environ.get("ISOMT_DEMO_WIN")
    if demo:
        try:
            with open(demo, encoding="utf-8") as f:
                rows = json.load(f)
        except (OSError, ValueError):
            rows = []
    else:
        rc, out = powershell(_PS_LIST, timeout=30)
        try:
            rows = json.loads(out.strip() or "[]") if rc == 0 else []
        except ValueError:
            rows = []
        if isinstance(rows, dict):
            rows = [rows]
    result = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        img, letter = str(r.get("image", "")), str(r.get("letter", "")).strip(":")
        if img.lower().endswith(".iso") and letter:
            result.append((img, letter.upper(), r.get("mount") or f"{letter.upper()}:\\"))
    return result


def sync_drive_links(isos: list[IsoMount]):
    """~/.local/share/<app>/drives/<letter> -> mount point of the ISO in that slot.

    Proton prefixes link D:..G: to these paths, so discs can be swapped while an
    installer is running (eject disc 1, mount disc 2 into the same slot)."""
    d = drives_dir()
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        return
    targets = {m.slot: m.mountpoint for m in isos if 0 <= m.slot < len(DRIVE_LETTERS) and m.mountpoint}
    for i, letter in enumerate(DRIVE_LETTERS):
        link = os.path.join(d, letter)
        target = targets.get(i)
        try:
            if target:
                if os.path.islink(link) and os.readlink(link) == target:
                    continue
                tmp = link + ".tmp"
                if os.path.lexists(tmp):
                    os.remove(tmp)
                os.symlink(target, tmp)
                os.replace(tmp, link)
            elif os.path.lexists(link):
                os.remove(link)
        except OSError:
            pass


class MountError(Exception):
    def __init__(self, key: str, detail: str = "", **fmt):
        super().__init__(key)
        self.key = key
        self.detail = detail.strip()
        self.fmt = fmt


class AlreadyMounted(MountError):
    pass


def udisks_available() -> bool:
    return IS_WINDOWS or shutil.which("udisksctl") is not None


def mount_iso(path: str, slot: int | None = None) -> IsoMount:
    if not udisks_available():
        raise MountError("err_no_udisks")
    if not os.path.isfile(path):
        raise MountError("err_not_found", path=path)
    iso = os.path.realpath(path)
    if not iso.lower().endswith(".iso"):
        raise MountError("err_not_iso", path=iso)
    if IS_WINDOWS:
        return _mount_iso_windows(iso, slot)
    loops = list_iso_loops()
    for loop, bf in loops:
        if bf == iso:
            raise AlreadyMounted("err_already", path=iso)
    if len(loops) >= MAX_ISOS:
        raise MountError("err_limit", max=MAX_ISOS)

    rc, out = run(["udisksctl", "loop-setup", "--read-only", "--file", iso])
    m = re.search(r"/dev/loop\d+", out)
    if rc != 0 or not m:
        raise MountError("err_loop", out)
    loop = m.group(0)

    for _ in range(4):                       # desktops may auto-mount new devices
        if mountpoints_of(loop):
            break
        time.sleep(0.5)

    errors = ""
    if not mountpoints_of(loop):
        rc, out = run(["lsblk", "-nrpo", "NAME,FSTYPE", loop])
        targets = []
        if rc == 0:
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[1]:
                    targets.append(parts[0])
        for dev in targets or [loop]:
            rc, out = run(["udisksctl", "mount", "--block-device", dev])
            if rc != 0:
                errors += out + "\n"

    if not mountpoints_of(loop):
        run(["udisksctl", "loop-delete", "--block-device", loop])
        raise MountError("err_mount", errors)

    preferred = {iso: slot} if slot is not None else None
    for mnt in current_isos(preferred):
        if mnt.loop == loop:
            return mnt
    return IsoMount(loop, iso, mountpoints_of(loop))


def _mount_iso_windows(iso: str, slot: int | None) -> IsoMount:
    images = win_list_images()
    if any(os.path.normcase(img) == os.path.normcase(iso) for img, _, _ in images):
        raise AlreadyMounted("err_already", path=iso)
    if len(images) >= MAX_ISOS:
        raise MountError("err_limit", max=MAX_ISOS)
    rc, out = powershell(_PS_MOUNT, {"ISOMT_PATH": iso}, timeout=90)
    m = re.search(r"LETTER=([A-Za-z])", out)
    if rc != 0 or not m:
        raise MountError("err_mount", out)
    preferred = {iso: slot} if slot is not None else None
    for mnt in current_isos(preferred):
        if os.path.normcase(mnt.iso) == os.path.normcase(iso):
            return mnt
    letter = m.group(1).upper()
    return IsoMount(iso, iso, [f"{letter}:\\"], win_letter=letter)


def eject(loop: str):
    if IS_WINDOWS:                         # on Windows `loop` is the ISO path
        rc, out = powershell(_PS_EJECT, {"ISOMT_PATH": loop}, timeout=60)
        current_isos()
        if rc != 0:
            raise MountError("err_eject", out)
        return
    errors = ""
    for src in mount_sources_of(loop):
        rc, out = run(["udisksctl", "unmount", "--block-device", src])
        if rc != 0:
            errors += out + "\n"
    if not errors:
        rc, out = run(["udisksctl", "loop-delete", "--block-device", loop])
        if rc != 0:
            errors += out + "\n"
    current_isos()
    if errors:
        raise MountError("err_eject", errors)


def find_installers(mountpoint: str) -> list[str]:
    """.exe files on the ISO, best candidates first (autorun.inf target, setup*, install*)."""
    if not mountpoint or not os.path.isdir(mountpoint):
        return []
    autorun_target = ""
    try:
        for entry in os.listdir(mountpoint):
            if entry.lower() == "autorun.inf":
                with open(os.path.join(mountpoint, entry), encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        k, _, v = line.strip().partition("=")
                        if k.strip().lower() == "open" and v.strip():
                            target = v.strip().strip('"')
                            low = target.lower()
                            if ".exe" in low:
                                target = target[: low.index(".exe") + 4]
                            autorun_target = target.replace("\\", "/").lstrip("/")
                            break
    except OSError:
        pass

    found = []

    def scan(d, depth):
        try:
            entries = sorted(os.listdir(d), key=str.lower)
        except OSError:
            return
        for e in entries:
            p = os.path.join(d, e)
            if os.path.isfile(p) and e.lower().endswith(".exe"):
                found.append(p)
            elif depth > 0 and os.path.isdir(p):
                scan(p, depth - 1)

    scan(mountpoint, 1)

    def resolve_ci(rel):
        cur = mountpoint
        for part in [x for x in rel.split("/") if x]:
            try:
                match = next((e for e in os.listdir(cur) if e.lower() == part.lower()), None)
            except OSError:
                return ""
            if not match:
                return ""
            cur = os.path.join(cur, match)
        return cur if os.path.isfile(cur) else ""

    auto = resolve_ci(autorun_target) if autorun_target else ""

    def rank(p):
        n = os.path.basename(p).lower()
        if auto and p == auto:
            return (0, n)
        if n.startswith("setup"):
            return (1, n)
        if n.startswith("install"):
            return (2, n)
        if os.path.dirname(p) == mountpoint:
            return (3, n)
        return (4, p.lower())

    if auto and auto not in found:
        found.append(auto)
    return sorted(set(found), key=rank)


# =============================================================================
#  Steam / Proton discovery
# =============================================================================
def steam_roots() -> list[str]:
    env = os.environ.get("ISOMT_STEAM_ROOT")
    cands = env.split(":") if env else [
        os.path.join(home(), ".local", "share", "Steam"),
        os.path.join(home(), ".steam", "steam"),
        os.path.join(home(), ".steam", "root"),
        os.path.join(home(), ".var", "app", "com.valvesoftware.Steam", "data", "Steam"),
    ]
    out, seen = [], set()
    for c in cands:
        if c and os.path.isdir(c):
            r = os.path.realpath(c)
            if r not in seen:
                seen.add(r)
                out.append(r)
    return out


def library_dirs() -> list[str]:
    out, seen = [], set()

    def add(p):
        if p and os.path.isdir(os.path.join(p, "steamapps")):
            r = os.path.realpath(p)
            if r not in seen:
                seen.add(r)
                out.append(r)

    for root in steam_roots():
        add(root)
        for vdf in (os.path.join(root, "steamapps", "libraryfolders.vdf"),
                    os.path.join(root, "config", "libraryfolders.vdf")):
            try:
                with open(vdf, encoding="utf-8", errors="ignore") as f:
                    for m in re.finditer(r'"path"\s+"([^"]+)"', f.read()):
                        add(m.group(1).replace("\\\\", "\\"))
            except OSError:
                pass
    return out


@dataclass
class ProtonTool:
    name: str
    path: str
    kind: str                 # "experimental", "official", "ge", "custom"
    version: tuple = ()
    runtime_appid: str = ""

    @property
    def script(self) -> str:
        return os.path.join(self.path, "proton")


def _version_of(name: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", name)[:3])


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def _tool_from_dir(d: str, compat: bool) -> ProtonTool | None:
    if not os.path.isfile(os.path.join(d, "proton")):
        return None
    base = os.path.basename(d.rstrip("/"))
    name = base
    if compat:
        m = re.search(r'"display_name"\s+"([^"]+)"', _read(os.path.join(d, "compatibilitytool.vdf")))
        if m:
            name = m.group(1)
    elif not base.lower().startswith("proton"):
        return None
    low = name.lower()
    if "experimental" in low:
        kind = "experimental"
    elif "ge-proton" in low or "proton-ge" in low or low.startswith("ge"):
        kind = "ge"
    elif compat:
        kind = "custom"
    else:
        kind = "official"
    m = re.search(r'"require_tool_appid"\s+"(\d+)"', _read(os.path.join(d, "toolmanifest.vdf")))
    return ProtonTool(name, os.path.realpath(d), kind, _version_of(name) if kind != "experimental" else (),
                      m.group(1) if m else "")


def sort_protons(tools: list[ProtonTool]) -> list[ProtonTool]:
    def key(t):
        exp = 1 if t.kind == "experimental" else 0
        hotfix = 0 if "hotfix" in t.name.lower() else 1
        return (exp, hotfix, t.version, 1 if t.kind == "ge" else 0, t.name)
    return sorted(tools, key=key, reverse=True)


def find_protons() -> list[ProtonTool]:
    tools, seen = [], set()

    def add(t):
        if t and t.path not in seen:
            seen.add(t.path)
            tools.append(t)

    for lib in library_dirs():
        common = os.path.join(lib, "steamapps", "common")
        try:
            for e in os.listdir(common):
                add(_tool_from_dir(os.path.join(common, e), compat=False))
        except OSError:
            pass
    for root in steam_roots():
        ct = os.path.join(root, "compatibilitytools.d")
        try:
            for e in os.listdir(ct):
                add(_tool_from_dir(os.path.join(ct, e), compat=True))
        except OSError:
            pass
    return sort_protons(tools)


def pick_proton(tools: list[ProtonTool], choice: str = "auto") -> ProtonTool | None:
    if not tools:
        return None
    if choice and choice != "auto":
        for t in tools:
            if t.path == choice or t.name == choice:
                return t
    return sort_protons(tools)[0]


_KNOWN_RUNTIMES = {"1628350": "SteamLinuxRuntime_sniper", "1391110": "SteamLinuxRuntime_soldier",
                   "4183110": "SteamLinuxRuntime_4"}


def runtime_for(tool: ProtonTool) -> str:
    """Directory of the Steam Linux Runtime the Proton version asks for ('' if none/not installed)."""
    if not tool.runtime_appid:
        return ""
    for lib in library_dirs():
        sa = os.path.join(lib, "steamapps")
        m = re.search(r'"installdir"\s+"([^"]+)"', _read(os.path.join(sa, f"appmanifest_{tool.runtime_appid}.acf")))
        names = [m.group(1)] if m else []
        if tool.runtime_appid in _KNOWN_RUNTIMES:
            names.append(_KNOWN_RUNTIMES[tool.runtime_appid])
        for n in names:
            d = os.path.join(sa, "common", n)
            if os.path.isfile(os.path.join(d, "_v2-entry-point")):
                return d
    return ""


# =============================================================================
#  Prefixes (one Wine/Proton prefix per game)
# =============================================================================
def prefix_base(cfg: dict) -> str:
    if IS_WINDOWS:                         # no prefixes on Windows: just the tool's game list
        return os.path.join(data_dir(), "games")
    return cfg.get("prefix_base") or os.path.join(home(), "Games", "IsoMountTool")


def safe_name(name: str) -> str:
    name = re.sub(r"[/\\:*?\"<>|\x00-\x1f]+", " ", name or "").strip().strip(".").strip()
    name = re.sub(r"\s+", " ", name)
    return name[:80] or "Game"


@dataclass
class Prefix:
    name: str
    path: str
    meta: dict = field(default_factory=dict)

    @property
    def pfx(self) -> str:
        return os.path.join(self.path, "pfx")

    @property
    def drive_c(self) -> str:
        return os.path.join(self.pfx, "drive_c")

    @property
    def initialized(self) -> bool:
        return os.path.isfile(os.path.join(self.pfx, "system.reg"))

    def save_meta(self):
        try:
            os.makedirs(self.path, exist_ok=True)
            with open(os.path.join(self.path, PREFIX_META), "w", encoding="utf-8") as f:
                json.dump(self.meta, f, indent=2, ensure_ascii=False)
        except OSError:
            pass


def load_prefix(path: str) -> Prefix:
    meta = {}
    try:
        with open(os.path.join(path, PREFIX_META), encoding="utf-8") as f:
            meta = json.load(f)
            if not isinstance(meta, dict):
                meta = {}
    except (OSError, ValueError):
        pass
    return Prefix(meta.get("name") or os.path.basename(path), path, meta)


def get_prefix(cfg: dict, name: str) -> Prefix:
    path = os.path.join(prefix_base(cfg), safe_name(name))
    p = load_prefix(path)
    if not p.meta.get("name"):
        p.meta["name"] = safe_name(name)
        p.name = p.meta["name"]
    return p


def list_prefixes(cfg: dict) -> list[Prefix]:
    base = prefix_base(cfg)
    out = []
    try:
        for e in sorted(os.listdir(base), key=str.lower):
            d = os.path.join(base, e)
            if os.path.isdir(d) and (os.path.isdir(os.path.join(d, "pfx")) or
                                     os.path.isfile(os.path.join(d, PREFIX_META))):
                out.append(load_prefix(d))
    except OSError:
        pass
    return out


def delete_prefix(prefix: Prefix):
    shutil.rmtree(prefix.path)


def set_cdrom_registry(system_reg: str, letters=DRIVE_LETTERS, remove: bool = False) -> bool:
    """Marks the given drive letters as CD-ROM drives (HKLM\\Software\\Wine\\Drives),
    or removes these entries again with remove=True."""
    try:
        with open(system_reg, encoding="utf-8", errors="surrogateescape") as f:
            text = f.read()
    except OSError:
        return False
    nl = "\n"
    lines = text.split(nl)
    header_re = re.compile(r"^\[Software\\\\Wine\\\\Drives\](\s+\d+)?\s*$", re.IGNORECASE)
    idx = next((i for i, l in enumerate(lines) if header_re.match(l)), None)
    wanted = {f'"{l}:"': f'"{l}:"="cdrom"' for l in letters}
    if remove:
        if idx is None:
            return True
        end = idx + 1
        while end < len(lines) and lines[end].strip() != "" and not lines[end].startswith("["):
            end += 1
        drop = {v.lower() for v in wanted.values()}
        lines[idx + 1:end] = [l for l in lines[idx + 1:end] if l.strip().lower() not in drop]
    elif idx is None:
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(f"[Software\\\\Wine\\\\Drives] {int(time.time())}")
        lines.extend(wanted.values())
        lines.append("")
    else:
        end = idx + 1
        while end < len(lines) and lines[end].strip() != "" and not lines[end].startswith("["):
            end += 1
        section = lines[idx + 1:end]
        done = set()
        for i, l in enumerate(section):
            for k, v in wanted.items():
                if l.lower().startswith(k.lower() + "="):
                    section[i] = v
                    done.add(k)
        section += [v for k, v in wanted.items() if k not in done]
        lines[idx + 1:end] = section
    new = nl.join(lines)
    if new == text:
        return True
    try:
        tmp = system_reg + ".isomt.tmp"
        with open(tmp, "w", encoding="utf-8", errors="surrogateescape") as f:
            f.write(new)
        os.replace(tmp, system_reg)
        return True
    except OSError:
        return False


def link_prefix_drives(prefix: Prefix) -> bool:
    """Links D:..G: in the prefix to our slot drive links and marks them as CD-ROM drives."""
    dosdevices = os.path.join(prefix.pfx, "dosdevices")
    if not os.path.isdir(dosdevices):
        return False
    ours = drives_dir()
    ok = True
    for letter in DRIVE_LETTERS:
        link = os.path.join(dosdevices, f"{letter}:")
        target = os.path.join(ours, letter)
        try:
            if os.path.islink(link):
                cur = os.readlink(link)
                if cur == target:
                    continue
                # only replace links that are ours, dangling or point to removable media
                if not (cur.startswith(ours) or not os.path.exists(link) or
                        cur.startswith(("/run/media/", "/media/", "/mnt/"))):
                    ok = False
                    continue
                os.remove(link)
            elif os.path.lexists(link):
                ok = False
                continue
            os.symlink(target, link)
        except OSError:
            ok = False
    set_cdrom_registry(os.path.join(prefix.pfx, "system.reg"))
    return ok


def unlink_prefix_drives(prefix: Prefix) -> bool:
    """Removes the D:..G: links this tool created (and their CD-ROM entries) from a prefix.

    Without them Proton behaves exactly like when the .exe is started from Steam."""
    dosdevices = os.path.join(prefix.pfx, "dosdevices")
    if not os.path.isdir(dosdevices):
        return False
    ours = drives_dir()
    removed = []
    for letter in DRIVE_LETTERS:
        link = os.path.join(dosdevices, f"{letter}:")
        try:
            if os.path.islink(link) and os.readlink(link).startswith(ours):
                os.remove(link)
                removed.append(letter)
        except OSError:
            pass
    if removed:
        set_cdrom_registry(os.path.join(prefix.pfx, "system.reg"), removed, remove=True)
    return bool(removed)


def windows_path_for(exe: str, isos: list[IsoMount]) -> str:
    """D:\\setup.exe if the exe lies on a mounted ISO with a drive letter, else ''."""
    for m in isos:
        mp = m.mountpoint
        if mp and m.drive_letter and (exe == mp or exe.startswith(mp.rstrip("/") + "/")):
            rel = os.path.relpath(exe, mp)
            return f"{m.drive_letter}:\\" + rel.replace("/", "\\")
    return ""


# =============================================================================
#  Launching with Proton
# =============================================================================
_ENV_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def parse_launch_options(opts: str) -> tuple[dict, list, list]:
    """Steam style launch options -> (env, wrapper command, extra arguments)."""
    try:
        tokens = shlex.split(opts or "")
    except ValueError:
        tokens = (opts or "").split()
    if "%command%" in tokens:
        i = tokens.index("%command%")
        before, after = tokens[:i], tokens[i + 1:]
    else:
        before = [t for t in tokens if _ENV_RE.match(t)]
        after = [t for t in tokens if not _ENV_RE.match(t)]
    env, wrapper = {}, []
    for t in before:
        if not wrapper and _ENV_RE.match(t):
            k, _, v = t.partition("=")
            env[k] = v
        else:
            wrapper.append(t)
    return env, wrapper, after


def build_launch(exe: str, prefix: Prefix, tool: ProtonTool, cfg: dict,
                 isos: list[IsoMount] | None = None, win_exe: str = "",
                 launch_options: str | None = None, use_runtime: bool | None = None):
    """Returns (cmd, env, cwd) to run `exe` in `prefix` with Proton `tool`."""
    isos = isos or []
    opts = cfg.get("launch_options", DEFAULT_LAUNCH_OPTIONS) if launch_options is None else launch_options
    opt_env, wrapper, args = parse_launch_options(opts)
    use_rt = cfg.get("use_runtime", True) if use_runtime is None else use_runtime
    runtime = runtime_for(tool) if use_rt else ""
    roots = steam_roots()
    exe_dir = os.path.dirname(exe) or home()

    mounts = []
    for p in ["/run/media", prefix_base(cfg), drives_dir(), exe_dir] + [m.mountpoint for m in isos]:
        if p and p not in mounts and os.path.isdir(p):
            mounts.append(p)

    env = clean_env()
    env.update({
        "STEAM_COMPAT_DATA_PATH": prefix.path,
        "STEAM_COMPAT_CLIENT_INSTALL_PATH": roots[0] if roots else prefix.path,
        "STEAM_COMPAT_INSTALL_PATH": exe_dir,
        "STEAM_COMPAT_TOOL_PATHS": ":".join([tool.path] + ([runtime] if runtime else [])),
        "STEAM_COMPAT_MOUNTS": ":".join(mounts),
        "STEAM_COMPAT_APP_ID": "0",
        "SteamAppId": "0",
        "SteamGameId": "0",
        "PROTON_VERB": "waitforexitandrun",
    })
    if cfg.get("proton_log"):
        env["PROTON_LOG"] = "1"
        env["PROTON_LOG_DIR"] = logs_dir()
    env.update(opt_env)

    target = win_exe or exe
    cmd = list(wrapper)
    if runtime:
        cmd += [os.path.join(runtime, "_v2-entry-point"), "--verb=waitforexitandrun", "--"]
    cmd += [tool.script, "waitforexitandrun", target] + args
    return cmd, env, exe_dir


def init_command(prefix: Prefix, tool: ProtonTool, cfg: dict, use_runtime: bool | None = None):
    """Command that only creates the prefix (runs wineboot)."""
    cmd, env, cwd = build_launch("wineboot", prefix, tool, cfg, launch_options="",
                                 use_runtime=use_runtime)
    env["STEAM_COMPAT_INSTALL_PATH"] = prefix.path
    return cmd, env, prefix.path


def run_windows_program(exe: str, args: list[str], log) -> int:
    """Runs an installer/game on Windows and waits for it. Asks for admin rights (UAC) if needed."""
    cwd = os.path.dirname(exe) or None
    try:
        return subprocess.run([exe] + args, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                              env=clean_env()).returncode
    except OSError as e:
        if getattr(e, "winerror", 0) != 740:          # 740 = elevation required
            raise
    log.write("Program needs administrator rights – asking via UAC\n")
    log.flush()
    script = ("$a = @{ FilePath = $env:ISOMT_PATH; WorkingDirectory = $env:ISOMT_CWD; Verb = 'RunAs'; "
              "Wait = $true; PassThru = $true }; if ($env:ISOMT_ARGS) { $a.ArgumentList = $env:ISOMT_ARGS }; "
              "$p = Start-Process @a; exit $p.ExitCode")
    rc, out = powershell(script, {"ISOMT_PATH": exe, "ISOMT_CWD": cwd or home(),
                                  "ISOMT_ARGS": subprocess.list2cmdline(args) if args else ""}, timeout=None)
    log.write(out)
    return rc


# =============================================================================
#  Updates
# =============================================================================
def _version_tuple(v: str) -> tuple:
    v = v.strip().lstrip("vV")
    main, _, pre = v.partition("-")
    nums = tuple(int(x) for x in re.findall(r"\d+", main)[:3])
    nums = nums + (0,) * (3 - len(nums))
    return nums + ((0,) if pre else (1,))


def version_gt(a: str, b: str) -> bool:
    try:
        return _version_tuple(a) > _version_tuple(b)
    except ValueError:
        return False


def fetch_latest_release(timeout: int = 8) -> dict | None:
    """{'tag':..., 'version':..., 'url': AppImage URL, 'notes':..., 'page':...} or None."""
    raw = None
    if shutil.which("curl"):
        rc, out = run(["curl", "-fsSL", "--max-time", str(timeout), "-H", "Accept: application/vnd.github+json",
                       "-H", f"User-Agent: {APP_ID}/{app_version()}", API_LATEST], timeout=timeout + 5)
        if rc == 0:
            raw = out
    if raw is None:
        try:
            req = urllib.request.Request(API_LATEST, headers={"Accept": "application/vnd.github+json",
                                                              "User-Agent": f"{APP_ID}/{app_version()}"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode("utf-8", "replace")
        except Exception:
            return None
    try:
        d = json.loads(raw)
    except ValueError:
        return None
    tag = d.get("tag_name") or ""
    if not tag:
        return None
    url = ""
    want = ".exe" if IS_WINDOWS else ".AppImage"
    for a in d.get("assets") or []:
        if str(a.get("name", "")).endswith(want):
            url = a.get("browser_download_url", "")
            break
    return {"tag": tag, "version": tag.lstrip("vV"), "url": url, "notes": d.get("body") or "",
            "page": d.get("html_url") or f"{REPO_URL}/releases/latest"}


def can_self_update() -> str:
    """Path of the running AppImage (Linux) or .exe (Windows) if it can be replaced, else ''."""
    if IS_WINDOWS:
        exe = sys.executable if getattr(sys, "frozen", False) else ""
        return exe if exe and os.access(os.path.dirname(exe), os.W_OK) else ""
    target = os.environ.get("APPIMAGE", "")
    if target and os.path.isfile(target) and os.access(target, os.W_OK) and \
            os.access(os.path.dirname(target), os.W_OK):
        return target
    return ""


def download_update(url: str, target: str) -> bool:
    tmp = f"{target}.update.{os.getpid()}"
    ok = False
    if shutil.which("curl"):
        rc, _ = run(["curl", "-fsSL", "--max-time", "900", "-o", tmp, url], timeout=930)
        ok = rc == 0
    if not ok:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": f"{APP_ID}/{app_version()}"})
            with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
                shutil.copyfileobj(r, f)
            ok = True
        except Exception:
            ok = False
    try:
        if ok:
            with open(tmp, "rb") as f:
                head = f.read(4)
            ok = head[:2] == b"MZ" if IS_WINDOWS else head == b"\x7fELF"
        if ok:
            if IS_WINDOWS:
                old = target + ".old"          # a running .exe can be renamed, not overwritten
                if os.path.exists(old):
                    os.remove(old)
                os.replace(target, old)
            else:
                os.chmod(tmp, 0o755)
            os.replace(tmp, target)
            return True
    except OSError:
        pass
    try:
        os.remove(tmp)
    except OSError:
        pass
    return False


# =============================================================================
#  LakuenLauncher export
# =============================================================================
LAKUEN_ID = "de.lakuen.launcher"


def lakuen_dir() -> str:
    if os.environ.get("ISOMT_LAKUEN_DIR"):
        return os.environ["ISOMT_LAKUEN_DIR"]
    if IS_WINDOWS:
        return os.path.join(os.environ.get("APPDATA") or os.path.join(home(), "AppData", "Roaming"), LAKUEN_ID)
    return os.path.join(os.environ.get("XDG_DATA_HOME") or os.path.join(home(), ".local", "share"), LAKUEN_ID)


def lakuen_installed() -> bool:
    return os.path.isdir(lakuen_dir())


def lakuen_running() -> bool:
    """True if a LakuenLauncher process is running (it would overwrite library.json on its next save)."""
    if IS_WINDOWS and not os.environ.get("ISOMT_PROC"):
        rc, out = run(["tasklist", "/FO", "CSV", "/NH"], timeout=20)
        return rc == 0 and "lakuenlauncher" in out.lower()
    proc = os.environ.get("ISOMT_PROC", "/proc")
    me = str(os.getpid())
    try:
        pids = [p for p in os.listdir(proc) if p.isdigit() and p != me]
    except OSError:
        return False
    for pid in pids:
        try:
            with open(os.path.join(proc, pid, "cmdline"), "rb") as f:
                cmd = f.read().replace(b"\0", b" ").decode("utf-8", "ignore").lower()
        except OSError:
            continue
        first = cmd.split(" ", 1)[0]
        if "lakuenlauncher" in os.path.basename(first) or "lakuenlauncher" in first.rsplit("/", 1)[-1]:
            return True
    return False


def _lakuen_uid() -> str:
    import random
    import string
    n = int(time.time() * 1000)
    digits = string.digits + string.ascii_lowercase
    out = ""
    while n:
        n, r = divmod(n, 36)
        out = digits[r] + out
    return out + "".join(random.choice(digits) for _ in range(6))


def export_to_lakuen(prefix: Prefix, exe: str, name: str, launch_options: str,
                     proton_path: str = "", use_runtime: bool = True) -> str:
    """Adds (or updates) the game in LakuenLauncher's library.json. Returns 'added' or 'updated'."""
    if not lakuen_installed():
        raise MountError("err_lakuen_missing")
    if lakuen_running():
        raise MountError("err_lakuen_running")
    path = os.path.join(lakuen_dir(), "library.json")
    lib = {"version": 1, "games": [], "collections": []}
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            raise MountError("err_lakuen_read", str(e))
        if isinstance(data, dict) and isinstance(data.get("games"), list):
            lib = data
        try:
            shutil.copy2(path, os.path.join(lakuen_dir(), f"library.isomounttool-backup-{int(time.time())}.json"))
        except OSError:
            pass

    env, wrapper, args = parse_launch_options(launch_options)
    if IS_WINDOWS:                          # games run natively on Windows
        env, wrapper = {}, []
    fields = {
        "name": name,
        "path": exe,
        "kind": "exe",
        "args": " ".join(shlex.quote(a) for a in args),
        "workdir": os.path.dirname(exe),
        "env": env,
        "runner": "default" if IS_WINDOWS else ("slr" if use_runtime else "proton"),
        "proton": "default" if IS_WINDOWS else (proton_path or "default"),
        "prefix": "" if IS_WINDOWS else prefix.path,
        "wrapper": " ".join(shlex.quote(w) for w in wrapper),
    }
    existing = None
    for g in lib["games"]:
        if isinstance(g, dict) and (g.get("path") == exe or
                                    (prefix.meta.get("lakuen_id") and g.get("id") == prefix.meta.get("lakuen_id"))):
            existing = g
            break
    if existing is not None:
        existing.update(fields)
        result, gid = "updated", existing.get("id")
    else:
        gid = _lakuen_uid()
        game = {
            "id": gid, **fields,
            "mangohud": None, "gamemode": None, "fsr": False, "preScript": "", "postScript": "",
            "art": {}, "favorite": False, "hidden": False, "collections": [],
            "notes": "Importiert aus SteamOS ISO Mount Tool", "addedAt": int(time.time() * 1000), "lastLaunch": 0,
        }
        lib["games"].append(game)
        result = "added"
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(lib, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except OSError as e:
        raise MountError("err_lakuen_write", str(e))
    prefix.meta["lakuen_id"] = gid
    prefix.save_meta()
    return result
