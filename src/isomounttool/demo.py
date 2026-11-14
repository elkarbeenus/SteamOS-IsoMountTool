"""Fake SteamOS environment for tests and screenshots (no real mounting).

Created by Dominic Lesina x Claude
"""

import json
import os


def _w(path, text=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def create_demo_env(base: str, isos=(("Need for Speed Disc 1.iso", "NFS_DISC1"), ("Anno 1602.iso", "ANNO1602")),
                    with_prefix: bool = True) -> dict:
    """Builds a fake home with Steam, Proton versions, mounted ISOs and a prefix. Sets env vars."""
    home = os.path.join(base, "home")
    sysb = os.path.join(base, "sys")
    media = os.path.join(base, "run", "media", "deck")
    mounts = os.path.join(base, "mounts")
    os.makedirs(home, exist_ok=True)
    os.makedirs(sysb, exist_ok=True)

    steam = os.path.join(home, ".local", "share", "Steam")
    common = os.path.join(steam, "steamapps", "common")
    for name in ("Proton - Experimental", "Proton 9.0 (Beta)", "Proton 10.0"):
        _w(os.path.join(common, name, "proton"), "#!/usr/bin/env python3\n")
        _w(os.path.join(common, name, "toolmanifest.vdf"),
           '"manifest"\n{\n  "commandline" "/proton %verb%"\n  "require_tool_appid" "1628350"\n}\n')
    _w(os.path.join(common, "SteamLinuxRuntime_sniper", "_v2-entry-point"), "#!/bin/sh\n")
    _w(os.path.join(steam, "steamapps", "appmanifest_1628350.acf"),
       '"AppState"\n{\n  "appid" "1628350"\n  "installdir" "SteamLinuxRuntime_sniper"\n}\n')
    ge = os.path.join(steam, "compatibilitytools.d", "GE-Proton10-25")
    _w(os.path.join(ge, "proton"), "#!/usr/bin/env python3\n")
    _w(os.path.join(ge, "compatibilitytool.vdf"), '"compatibilitytools" { "compat_tools" { "GE-Proton10-25" {'
                                                  ' "display_name" "GE-Proton10-25" } } }\n')

    lines = []
    for i, (iso_name, label) in enumerate(isos):
        iso_path = os.path.join(home, "Downloads", iso_name)
        _w(iso_path, "")
        _w(os.path.join(sysb, f"loop{i}", "loop", "backing_file"), iso_path + "\n")
        mp = os.path.join(media, label)
        _w(os.path.join(mp, "autorun.inf"), "[autorun]\nopen=SETUP.EXE /auto\nicon=game.ico\n")
        _w(os.path.join(mp, "SETUP.EXE"), "MZ")
        _w(os.path.join(mp, "tools", "dxsetup.exe"), "MZ")
        lines.append(f"/dev/loop{i} {mp.replace(' ', chr(92) + '040')} iso9660 ro,nosuid,nodev 0 0")
    _w(mounts, "\n".join(lines) + "\n")

    if with_prefix:
        pfx_root = os.path.join(home, "Games", "IsoMountTool")
        for name, exe in (("Need for Speed", "Program Files/EA Games/NFS/nfs.exe"), ("Anno 1602", "")):
            d = os.path.join(pfx_root, name)
            _w(os.path.join(d, "pfx", "system.reg"), "WINE REGISTRY Version 2\n")
            os.makedirs(os.path.join(d, "pfx", "dosdevices"), exist_ok=True)
            meta = '{"name": "%s"' % name
            if exe:
                full = os.path.join(d, "pfx", "drive_c", exe)
                _w(full, "MZ")
                meta += ', "last_exe": "%s"' % full
            meta += ', "proton": "GE-Proton10-25"}'
            _w(os.path.join(d, "isomounttool.json"), meta)

    from . import core
    win_rows = []
    for i, (iso_name, label) in enumerate(isos):
        win_rows.append({"image": os.path.join(home, "Downloads", iso_name), "letter": "DEFG"[i],
                         "mount": os.path.join(media, label)})
    _w(os.path.join(base, "win-images.json"), json.dumps(win_rows))
    if core.IS_WINDOWS and with_prefix:
        games = os.path.join(base, "localappdata", core.APP_ID, "games")
        for name, exe in (("Need for Speed", "Program Files/EA Games/NFS/nfs.exe"), ("Anno 1602", "")):
            meta = {"name": name}
            if exe:
                full = os.path.join(base, "C", exe)
                _w(full, "MZ")
                meta["last_exe"] = full
            _w(os.path.join(games, name, "isomounttool.json"), json.dumps(meta))

    env = {
        "APPDATA": os.path.join(base, "appdata"),
        "LOCALAPPDATA": os.path.join(base, "localappdata"),
        "ISOMT_DEMO_WIN": os.path.join(base, "win-images.json"),
        "HOME": home,
        "XDG_CONFIG_HOME": os.path.join(home, ".config"),
        "XDG_DATA_HOME": os.path.join(home, ".local", "share"),
        "ISOMOUNT_SYSBLOCK": sysb,
        "ISOMOUNT_PROC_MOUNTS": mounts,
        "ISOMT_STEAM_ROOT": steam,
    }
    os.environ.update(env)
    return env
