"""Unit tests for the core logic (no Qt needed). Run: python3 -m unittest discover -s tests"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from isomounttool import core, demo  # noqa: E402


class CoreTests(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)
        self.tmp = tempfile.TemporaryDirectory()
        self.env = demo.create_demo_env(self.tmp.name)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)
        self.tmp.cleanup()

    def test_isos_slots_and_drive_links(self):
        isos = core.current_isos()
        self.assertEqual([m.slot for m in isos], [0, 1])
        self.assertEqual(isos[0].drive_letter, "D")
        self.assertTrue(isos[0].mountpoint.endswith("NFS_DISC1"))
        self.assertEqual(os.readlink(os.path.join(core.drives_dir(), "d")), isos[0].mountpoint)
        self.assertEqual(os.readlink(os.path.join(core.drives_dir(), "e")), isos[1].mountpoint)
        self.assertFalse(os.path.lexists(os.path.join(core.drives_dir(), "f")))

    def test_slot_stays_stable_after_eject(self):
        core.current_isos()
        # simulate ejecting slot 1 (loop0)
        import shutil
        shutil.rmtree(os.path.join(self.env["ISOMOUNT_SYSBLOCK"], "loop0"))
        with open(self.env["ISOMOUNT_PROC_MOUNTS"]) as f:
            lines = [l for l in f if not l.startswith("/dev/loop0 ")]
        with open(self.env["ISOMOUNT_PROC_MOUNTS"], "w") as f:
            f.writelines(lines)
        isos = core.current_isos()
        self.assertEqual(len(isos), 1)
        self.assertEqual(isos[0].slot, 1)          # Anno stays in slot 2 / drive E:
        self.assertFalse(os.path.lexists(os.path.join(core.drives_dir(), "d")))

    def test_mount_space_decoding(self):
        p = self.env["ISOMOUNT_PROC_MOUNTS"]
        with open(p, "a") as f:
            f.write("/dev/loop0p1 /run/media/deck/My\\040Game iso9660 ro 0 0\n")
        self.assertIn("/run/media/deck/My Game", core.mountpoints_of("/dev/loop0"))
        self.assertNotIn("/run/media/deck/My Game", core.mountpoints_of("/dev/loop1"))

    def test_find_installers_autorun_first(self):
        mp = core.current_isos()[0].mountpoint
        found = core.find_installers(mp)
        self.assertEqual(os.path.basename(found[0]), "SETUP.EXE")
        self.assertIn(os.path.join(mp, "tools", "dxsetup.exe"), found)

    def test_proton_discovery_and_auto_pick(self):
        tools = core.find_protons()
        names = [t.name for t in tools]
        self.assertEqual(names[0], "Proton - Experimental")
        self.assertIn("GE-Proton10-25", names)
        self.assertEqual(core.pick_proton(tools).name, "Proton - Experimental")
        ge = next(t for t in tools if t.kind == "ge")
        self.assertEqual(core.pick_proton(tools, ge.path).name, "GE-Proton10-25")
        p10 = next(t for t in tools if t.name == "Proton 10.0")
        self.assertTrue(core.runtime_for(p10).endswith("SteamLinuxRuntime_sniper"))
        self.assertEqual(core.runtime_for(ge), "")
        # without experimental the highest version wins
        rest = [t for t in tools if t.kind != "experimental"]
        self.assertIn(core.pick_proton(rest).name, ("GE-Proton10-25", "Proton 10.0"))

    def test_parse_launch_options(self):
        env, wrap, args = core.parse_launch_options("WINE_LARGE_ADDRESS_AWARE=1 %command%")
        self.assertEqual(env, {"WINE_LARGE_ADDRESS_AWARE": "1"})
        self.assertEqual((wrap, args), ([], []))
        env, wrap, args = core.parse_launch_options("A=1 B='x y' gamemoderun %command% -windowed")
        self.assertEqual(env, {"A": "1", "B": "x y"})
        self.assertEqual(wrap, ["gamemoderun"])
        self.assertEqual(args, ["-windowed"])
        env, wrap, args = core.parse_launch_options("DXVK_HUD=1 -nointro")
        self.assertEqual((env, wrap, args), ({"DXVK_HUD": "1"}, [], ["-nointro"]))

    def test_build_launch(self):
        cfg = core.Config()
        isos = core.current_isos()
        tool = core.pick_proton(core.find_protons())
        prefix = core.get_prefix(cfg, "Need for Speed")
        exe = core.find_installers(isos[0].mountpoint)[0]
        win = core.windows_path_for(exe, isos)
        self.assertEqual(win, "D:\\SETUP.EXE")
        cmd, env, cwd = core.build_launch(exe, prefix, tool, cfg, isos, win)
        self.assertTrue(cmd[0].endswith("_v2-entry-point"))
        self.assertEqual(cmd[1:3], ["--verb=waitforexitandrun", "--"])
        self.assertEqual(cmd[-2:], ["waitforexitandrun", "D:\\SETUP.EXE"])
        self.assertEqual(env["WINE_LARGE_ADDRESS_AWARE"], "1")
        self.assertEqual(env["STEAM_COMPAT_DATA_PATH"], prefix.path)
        self.assertEqual(cwd, isos[0].mountpoint)
        self.assertIn(isos[0].mountpoint, env["STEAM_COMPAT_MOUNTS"].split(":"))
        cmd, env, _ = core.build_launch(exe, prefix, tool, cfg, isos, use_runtime=False, launch_options="")
        self.assertTrue(cmd[0].endswith("/proton"))
        self.assertNotIn("WINE_LARGE_ADDRESS_AWARE", env)

    def test_clean_env_strips_appimage_vars(self):
        os.environ["APPIMAGE"] = "/x.AppImage"
        os.environ["PYTHONHOME"] = "/tmp/py"
        os.environ["ISOMT_ORIG_LD_LIBRARY_PATH"] = "/orig"
        os.environ["LD_LIBRARY_PATH"] = "/appdir/lib:/orig"
        env = core.clean_env()
        self.assertNotIn("APPIMAGE", env)
        self.assertNotIn("PYTHONHOME", env)
        self.assertEqual(env["LD_LIBRARY_PATH"], "/orig")
        self.assertNotIn("ISOMT_ORIG_LD_LIBRARY_PATH", env)

    def test_prefix_drive_links_and_registry(self):
        core.current_isos()
        cfg = core.Config()
        prefix = core.get_prefix(cfg, "Anno 1602")
        user_link = os.path.join(prefix.pfx, "dosdevices", "g:")
        os.symlink(self.tmp.name, user_link)            # user's own link must stay
        self.assertFalse(core.link_prefix_drives(prefix))
        self.assertEqual(os.readlink(os.path.join(prefix.pfx, "dosdevices", "d:")),
                         os.path.join(core.drives_dir(), "d"))
        self.assertEqual(os.readlink(user_link), self.tmp.name)
        with open(os.path.join(prefix.pfx, "system.reg")) as f:
            reg = f.read()
        self.assertIn("[Software\\\\Wine\\\\Drives]", reg)
        self.assertIn('"d:"="cdrom"', reg)
        # running again updates instead of duplicating
        core.set_cdrom_registry(os.path.join(prefix.pfx, "system.reg"))
        with open(os.path.join(prefix.pfx, "system.reg")) as f:
            self.assertEqual(f.read().count('"d:"="cdrom"'), 1)

    def test_unlink_prefix_drives_restores_steam_like_prefix(self):
        core.current_isos()
        prefix = core.get_prefix(core.Config(), "Anno 1602")
        core.link_prefix_drives(prefix)
        dos = os.path.join(prefix.pfx, "dosdevices")
        os.symlink("/", os.path.join(dos, "z:"))
        self.assertTrue(core.unlink_prefix_drives(prefix))
        self.assertFalse(os.path.lexists(os.path.join(dos, "d:")))
        self.assertEqual(os.readlink(os.path.join(dos, "z:")), "/")      # untouched
        with open(os.path.join(prefix.pfx, "system.reg")) as f:
            self.assertNotIn("cdrom", f.read())
        self.assertFalse(core.unlink_prefix_drives(prefix))

    def test_default_launch_is_steam_like(self):
        cfg = core.Config()
        self.assertFalse(cfg["drive_letters"])
        isos = core.current_isos()
        tool = core.pick_proton(core.find_protons())
        exe = core.find_installers(isos[0].mountpoint)[0]
        cmd, env, cwd = core.build_launch(exe, core.get_prefix(cfg, "X"), tool, cfg, isos)
        self.assertEqual(cmd[-1], exe)                    # unix path, like Steam
        self.assertEqual(cwd, os.path.dirname(exe))
        self.assertNotIn("STEAM_COMPAT_LIBRARY_PATHS", env)
        self.assertEqual(env["SteamAppId"], "0")

    def test_export_to_lakuen(self):
        cfg = core.Config()
        prefix = core.get_prefix(cfg, "Need for Speed")
        exe = prefix.meta["last_exe"]
        lk = os.path.join(self.env["XDG_DATA_HOME"], core.LAKUEN_ID)
        with self.assertRaises(core.MountError) as cm:
            core.export_to_lakuen(prefix, exe, prefix.name, core.DEFAULT_LAUNCH_OPTIONS)
        self.assertEqual(cm.exception.key, "err_lakuen_missing")
        os.makedirs(lk)
        import json
        with open(os.path.join(lk, "library.json"), "w") as f:
            json.dump({"version": 1, "games": [{"id": "x1", "name": "Other"}], "collections": [{"id": "c"}]}, f)
        os.environ["ISOMT_PROC"] = os.path.join(self.tmp.name, "noproc")
        self.assertEqual(core.export_to_lakuen(prefix, exe, prefix.name, "WINE_LARGE_ADDRESS_AWARE=1 %command% -w",
                                               "/p/Proton 11.0"), "added")
        with open(os.path.join(lk, "library.json")) as f:
            lib = json.load(f)
        self.assertEqual(len(lib["games"]), 2)
        self.assertEqual(lib["collections"], [{"id": "c"}])
        g = lib["games"][1]
        self.assertEqual((g["path"], g["kind"], g["prefix"], g["runner"], g["proton"]),
                         (exe, "exe", prefix.path, "slr", "/p/Proton 11.0"))
        self.assertEqual(g["env"], {"WINE_LARGE_ADDRESS_AWARE": "1"})
        self.assertEqual(g["args"], "-w")
        self.assertEqual(core.export_to_lakuen(prefix, exe, prefix.name, ""), "updated")
        with open(os.path.join(lk, "library.json")) as f:
            self.assertEqual(len(json.load(f)["games"]), 2)
        # running launcher is detected
        fake = os.path.join(self.tmp.name, "proc", "4242")
        os.makedirs(fake)
        with open(os.path.join(fake, "cmdline"), "wb") as f:
            f.write(b"/tmp/.mount_Lakuen/usr/bin/lakuenlauncher\0")
        os.environ["ISOMT_PROC"] = os.path.join(self.tmp.name, "proc")
        self.assertTrue(core.lakuen_running())
        with self.assertRaises(core.MountError) as cm:
            core.export_to_lakuen(prefix, exe, prefix.name, "")
        self.assertEqual(cm.exception.key, "err_lakuen_running")

    def test_registry_existing_section(self):
        reg = os.path.join(self.tmp.name, "system.reg")
        with open(reg, "w") as f:
            f.write('WINE REGISTRY Version 2\n\n[Software\\\\Wine\\\\Drives] 123\n#time=1\n"c:"="hd"\n"d:"="hd"\n\n[Other] 1\n"x"="y"\n')
        core.set_cdrom_registry(reg)
        with open(reg) as f:
            txt = f.read()
        self.assertIn('"c:"="hd"', txt)
        self.assertIn('"d:"="cdrom"', txt)
        self.assertNotIn('"d:"="hd"', txt)
        self.assertIn('"g:"="cdrom"\n\n[Other] 1', txt)

    def test_prefixes(self):
        cfg = core.Config()
        names = [p.name for p in core.list_prefixes(cfg)]
        self.assertEqual(names, ["Anno 1602", "Need for Speed"])
        self.assertEqual(core.safe_name("  ../a/b:c  "), "a b c")

    def test_versions(self):
        self.assertTrue(core.version_gt("2.0.0", "1.0.0"))
        self.assertTrue(core.version_gt("v1.10.0", "1.9.9"))
        self.assertFalse(core.version_gt("1.0.0", "1.0.0"))
        self.assertTrue(core.version_gt("1.0.0", "1.0.0-dev"))

    def test_config_migration(self):
        os.makedirs(core.config_dir(), exist_ok=True)
        with open(os.path.join(core.config_dir(), "config"), "w") as f:
            f.write("UI_LANG=de\nAUTO_UPDATE=0\nLAST_DIR=/tmp\n")
        cfg = core.Config()
        self.assertEqual((cfg["language"], cfg["auto_update"], cfg["last_dir"]), ("de", False, "/tmp"))
        cfg.save()
        self.assertEqual(core.Config()["language"], "de")


class MountTests(unittest.TestCase):
    """mount/eject against a fake udisksctl."""

    def setUp(self):
        self._env = dict(os.environ)
        self.tmp = tempfile.TemporaryDirectory()
        self.env = demo.create_demo_env(self.tmp.name, isos=(), with_prefix=False)
        bindir = os.path.join(self.tmp.name, "bin")
        os.makedirs(bindir)
        media = os.path.join(self.tmp.name, "media")
        script = f"""#!/bin/bash
S="$ISOMOUNT_SYSBLOCK"; M="$ISOMOUNT_PROC_MOUNTS"
case "$1" in
 loop-setup) f="${{@: -1}}"; for n in 0 1 2 3 4 5 6 7; do [ -d "$S/loop$n" ] || {{ mkdir -p "$S/loop$n/loop"; echo "$f" > "$S/loop$n/loop/backing_file"; echo "Mapped file $f as /dev/loop$n."; exit 0; }}; done; exit 1;;
 mount) d="${{@: -1}}"; n=$(basename "$(cat "$S/${{d#/dev/}}/loop/backing_file")" .iso); mkdir -p "{media}/$n"; echo "$d {media}/${{n// /\\\\040}} iso9660 ro 0 0" >> "$M"; echo "Mounted $d";;
 unmount) d="${{@: -1}}"; [ -e "{self.tmp.name}/BUSY" ] && {{ echo "target is busy" >&2; exit 1; }}; grep -v "^$d " "$M" > "$M.n"; mv "$M.n" "$M";;
 loop-delete) d="${{@: -1}}"; rm -rf "$S/${{d#/dev/}}";;
esac
"""
        with open(os.path.join(bindir, "udisksctl"), "w") as f:
            f.write(script)
        with open(os.path.join(bindir, "lsblk"), "w") as f:
            f.write('#!/bin/bash\necho "${@: -1} "\n')
        for n in ("udisksctl", "lsblk"):
            os.chmod(os.path.join(bindir, n), 0o755)
        os.environ["PATH"] = bindir + ":" + os.environ["PATH"]
        self.dl = os.path.join(self.env["HOME"], "Downloads")
        os.makedirs(self.dl, exist_ok=True)
        for n in ("My Game.iso", "b.iso", "c.ISO", "d.iso", "e.iso", "x.txt"):
            open(os.path.join(self.dl, n), "w").close()
        core.time.sleep = lambda s: None

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)
        self.tmp.cleanup()

    def test_mount_limit_eject(self):
        m = core.mount_iso(os.path.join(self.dl, "My Game.iso"))
        self.assertEqual((m.slot, m.drive_letter), (0, "D"))
        self.assertTrue(m.mountpoint.endswith("My Game"))
        with self.assertRaises(core.AlreadyMounted):
            core.mount_iso(os.path.join(self.dl, "My Game.iso"))
        for n in ("b.iso", "c.ISO", "d.iso"):
            core.mount_iso(os.path.join(self.dl, n))
        with self.assertRaises(core.MountError) as cm:
            core.mount_iso(os.path.join(self.dl, "e.iso"))
        self.assertEqual(cm.exception.key, "err_limit")
        with self.assertRaises(core.MountError) as cm:
            core.mount_iso(os.path.join(self.dl, "x.txt"))
        self.assertEqual(cm.exception.key, "err_not_iso")

        open(os.path.join(self.tmp.name, "BUSY"), "w").close()
        with self.assertRaises(core.MountError) as cm:
            core.eject(m.loop)
        self.assertEqual(cm.exception.key, "err_eject")
        os.remove(os.path.join(self.tmp.name, "BUSY"))
        core.eject(m.loop)
        isos = core.current_isos()
        self.assertEqual(sorted(i.slot for i in isos), [1, 2, 3])
        # disc swap: the next ISO goes into the freed slot 1 / drive D:
        m2 = core.mount_iso(os.path.join(self.dl, "e.iso"))
        self.assertEqual(m2.drive_letter, "D")
        self.assertEqual(os.readlink(os.path.join(core.drives_dir(), "d")), m2.mountpoint)


class WindowsLogicTests(unittest.TestCase):
    """Windows code paths, simulated on Linux (PowerShell calls are faked)."""

    def setUp(self):
        self._env = dict(os.environ)
        self.tmp = tempfile.TemporaryDirectory()
        core.IS_WINDOWS = True
        self.env = demo.create_demo_env(self.tmp.name)
        self.calls = []
        self._run = core.run

        def fake_run(cmd, timeout=60, extra_env=None):
            script = cmd[-1]
            self.calls.append((script, extra_env or {}))
            if "Mount-DiskImage" in script:
                path = extra_env["ISOMT_PATH"]
                with open(self.env["ISOMT_DEMO_WIN"]) as f:
                    rows = json.load(f)
                rows.append({"image": path, "letter": "H", "mount": self.tmp.name})
                with open(self.env["ISOMT_DEMO_WIN"], "w") as f:
                    json.dump(rows, f)
                return 0, "LETTER=H\n"
            if "Dismount-DiskImage" in script:
                with open(self.env["ISOMT_DEMO_WIN"]) as f:
                    rows = [r for r in json.load(f) if r["image"] != extra_env["ISOMT_PATH"]]
                with open(self.env["ISOMT_DEMO_WIN"], "w") as f:
                    json.dump(rows, f)
                return 0, "OK"
            return 1, ""

        core.run = fake_run

    def tearDown(self):
        core.IS_WINDOWS = False
        core.run = self._run
        os.environ.clear()
        os.environ.update(self._env)
        self.tmp.cleanup()

    def test_paths(self):
        self.assertTrue(core.config_dir().startswith(self.env["APPDATA"]))
        self.assertTrue(core.data_dir().startswith(self.env["LOCALAPPDATA"]))
        self.assertTrue(core.lakuen_dir().startswith(self.env["APPDATA"]))
        self.assertTrue(core.prefix_base({}).startswith(self.env["LOCALAPPDATA"]))

    def test_list_mount_eject(self):
        isos = core.current_isos()
        self.assertEqual([(m.slot, m.drive_letter, m.label) for m in isos],
                         [(0, "D", "Need for Speed Disc 1"), (1, "E", "Anno 1602")])
        self.assertTrue(core.find_installers(isos[0].mountpoint))
        new = os.path.join(self.env["HOME"], "Downloads", "x.iso")
        open(new, "w").close()
        m = core.mount_iso(new)
        self.assertEqual((m.drive_letter, m.slot), ("H", 2))
        self.assertEqual(self.calls[-1][1]["ISOMT_PATH"], new)
        with self.assertRaises(core.AlreadyMounted):
            core.mount_iso(new)
        core.eject(m.loop)
        self.assertEqual(len(core.current_isos()), 2)

    def test_games_and_lakuen_export(self):
        cfg = core.Config()
        names = [p.name for p in core.list_prefixes(cfg)]
        self.assertEqual(names, ["Anno 1602", "Need for Speed"])
        prefix = core.get_prefix(cfg, "Need for Speed")
        os.makedirs(core.lakuen_dir())
        os.environ["ISOMT_PROC"] = os.path.join(self.tmp.name, "noproc")
        core.export_to_lakuen(prefix, prefix.meta["last_exe"], prefix.name, core.DEFAULT_LAUNCH_OPTIONS, "/x")
        with open(os.path.join(core.lakuen_dir(), "library.json")) as f:
            g = json.load(f)["games"][0]
        self.assertEqual((g["runner"], g["proton"], g["prefix"], g["env"]), ("default", "default", "", {}))


if __name__ == "__main__":
    unittest.main()
