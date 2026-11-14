"""Entry point: graphical UI without options, command line mode with options.

Created by Dominic Lesina x Claude
"""

import argparse
import sys

from . import core
from .i18n import Translator


def _tr(cfg) -> Translator:
    return Translator(cfg.get("language") or core.system_language())


def _err(t, e: core.MountError) -> str:
    msg = t(e.key, **e.fmt)
    return f"{msg}\n{e.detail}" if e.detail else msg


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog=core.APP_ID,
        description=f"{core.APP_NAME} {core.app_version()} – Created by Dominic Lesina x Claude. "
                    "Without options the graphical interface is started.")
    p.add_argument("--mount", metavar="FILE.iso", help=f"mount an ISO file (max. {core.MAX_ISOS} at the same time)")
    p.add_argument("--eject", metavar="FILE|LOOP", help="eject a mounted ISO (ISO path or /dev/loopN)")
    p.add_argument("--eject-all", action="store_true", help="eject all mounted ISOs")
    p.add_argument("--list", action="store_true", help="list mounted ISOs")
    p.add_argument("--list-proton", action="store_true", help="list the Proton versions found")
    p.add_argument("--check-update", action="store_true", help="check for a new release")
    p.add_argument("--lang", choices=["de", "en"], help="set the language (saved)")
    p.add_argument("--no-update-check", action="store_true", help="skip the update check on start")
    p.add_argument("--version", action="version", version=f"{core.APP_NAME} {core.app_version()}")
    p.add_argument("--screenshots", metavar="DIR", help=argparse.SUPPRESS)
    a = p.parse_args(argv)

    cfg = core.Config()
    if a.lang:
        cfg["language"] = a.lang
        cfg.save()
    t = _tr(cfg)

    try:
        if a.list:
            for m in core.current_isos():
                print(f"{m.slot + 1}\t{m.drive_letter}:\t{m.loop}\t{m.iso}\t{m.mountpoint}")
            return 0
        if a.list_proton:
            for tool in core.find_protons():
                rt = core.runtime_for(tool)
                print(f"{tool.name}\t{tool.kind}\t{tool.path}\t{'runtime: ' + rt if rt else 'no runtime'}")
            return 0
        if a.mount:
            m = core.mount_iso(a.mount)
            print(t("mounted_toast", name=m.name, l=m.drive_letter) + f"\n{m.mountpoint}")
            return 0
        if a.eject:
            target = a.eject
            loop = target if target.startswith("/dev/loop") else ""
            if not loop:
                import os
                real = os.path.realpath(target)
                loop = next((m.loop for m in core.current_isos() if m.iso == real), "")
            if not loop:
                print(t("nothing_mounted"), file=sys.stderr)
                return 1
            core.eject(loop)
            print(t("ejected_toast", name=target))
            return 0
        if a.eject_all:
            rc = 0
            for m in core.current_isos():
                try:
                    core.eject(m.loop)
                    print(t("ejected_toast", name=m.name))
                except core.MountError as e:
                    print(_err(t, e), file=sys.stderr)
                    rc = 1
            return rc
        if a.check_update:
            info = core.fetch_latest_release()
            if not info:
                print(t("upd_fail_check"), file=sys.stderr)
                return 1
            if core.version_gt(info["version"], core.app_version()):
                print(t("upd_text", new=info["version"], old=core.app_version()))
                print(info["page"])
            else:
                print(t("upd_none", v=core.app_version()))
            return 0
    except core.MountError as e:
        print(_err(t, e), file=sys.stderr)
        return 1

    try:
        from . import gui
    except ImportError as e:
        print(f"The graphical interface is not available ({e}). Use --help for the command line mode.",
              file=sys.stderr)
        return 1
    if a.screenshots:
        return gui.make_screenshots(a.screenshots)
    return gui.run(cfg, check_updates=not a.no_update_check)


if __name__ == "__main__":
    sys.exit(main())
