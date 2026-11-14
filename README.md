<p align="center">
  <img src="packaging/steamos-isomounttool.svg" width="128" alt="SteamOS ISO Mount Tool icon">
</p>

<h1 align="center">SteamOS ISO Mount Tool</h1>

<p align="center">
  Mount up to <b>4 ISO images</b> on SteamOS and run their Windows installers <b>directly with Proton</b> – no sudo, no terminal, no adding <code>setup.exe</code> to Steam by hand.<br>
  <i>Created by Dominic Lesina x Claude</i>
</p>

<p align="center">
  <img src="docs/screenshot-isos.png" width="820" alt="Screenshot">
</p>

---

## Features

- 💿 **Mount & eject ISOs** – up to 4 at the same time, via button, click on a free slot or **drag & drop**
- 🎮 **Run installers with Proton** – one click on **Run installer** starts `setup.exe` (or the `autorun.inf` target) from the ISO with Proton
- 🚀 **Newest Proton automatically** – Proton Experimental if installed, otherwise the highest version (official or GE-Proton). Any installed version can be picked
- 🧠 **No more RAM-limit crashes** – launch options work like in Steam, default: `WINE_LARGE_ADDRESS_AWARE=1 %command%`
- 🗂️ **One prefix per game** – stored in `~/Games/IsoMountTool/<game>`
- 💽 **Disc swapping** – slot 1–4 are drives **D:–G:** inside every prefix (marked as CD-ROM). When the installer asks for disc 2, eject disc 1 and mount disc 2 into the same slot
- ▶️ **Games & prefixes page** – start the installed game, run any program in its prefix, open drive C:, delete a prefix
- 🌐 **German & English**
- 🔄 **Auto update** – checks this repository for new releases on start and asks whether to update or keep the current version (can be turned off)
- 🔐 **No root** – mounting uses `udisksctl`, the same way Dolphin mounts drives
- 📦 **Everything included** – the AppImage bundles its own Python and Qt

## Requirements

- SteamOS 3.x in **Desktop Mode** (also works on most other Linux desktops)
- For installers: Steam with at least one Proton version (e.g. *Proton Experimental*: Steam → Library → Tools) or GE-Proton (e.g. via ProtonUp-Qt)

## Installation

1. Download the latest `SteamOS-IsoMountTool-x.y.z-x86_64.AppImage` from the [Releases page](https://github.com/elkarbeenus/SteamOS-IsoMountTool/releases/latest).
2. Move it to a folder in your home directory, e.g. `~/Applications` (needed for the auto update).
3. Right-click → **Properties** → **Permissions** → tick **Is executable**.
4. Double-click it to start.

## Installing a game from an ISO

1. **Mount** the ISO (click a free slot or drag the `.iso` onto the window).
2. Click **Run installer** on the slot.
3. Check the dialog:
   - **Program** – the installer the tool found (or choose another `.exe`)
   - **Game / prefix** – the name of the game. Use the same name for every disc of a game
   - **Proton version** – *Automatic* uses the newest one
   - **Launch options** – `WINE_LARGE_ADDRESS_AWARE=1 %command%` by default, same syntax as in Steam
4. Click **Start** and install the game as usual (to `C:\` inside the prefix).
5. **Multiple discs?** When the installer asks for the next disc: eject the ISO in the tool and mount the next one into the same slot – it keeps the same drive letter.
6. Afterwards, open **Games & prefixes** → **Run program…** and choose the game's `.exe` once. From then on **Play** starts it.

Logs of every run are stored in `~/.local/share/steamos-isomounttool/logs/`.

## Command line

```bash
./SteamOS-IsoMountTool.AppImage --mount ~/Downloads/game.iso   # mount
./SteamOS-IsoMountTool.AppImage --list                         # list mounted ISOs (slot, drive, path)
./SteamOS-IsoMountTool.AppImage --eject ~/Downloads/game.iso   # eject (ISO path or /dev/loopN)
./SteamOS-IsoMountTool.AppImage --eject-all                    # eject all
./SteamOS-IsoMountTool.AppImage --list-proton                  # Proton versions found
./SteamOS-IsoMountTool.AppImage --check-update                 # check for updates
./SteamOS-IsoMountTool.AppImage --lang en                      # set language (de|en)
./SteamOS-IsoMountTool.AppImage --no-update-check              # skip the update check on start
```

## How it works

- **Mounting:** `udisksctl loop-setup --read-only` + `udisksctl mount`. Mounted ISOs are found through the loop devices, so ISOs mounted another way count toward the limit of 4 too.
- **Proton:** Proton is started the way Steam does it: `STEAM_COMPAT_DATA_PATH` points to the game's prefix, and Proton runs inside the Steam Linux Runtime it asks for (`_v2-entry-point`). Your launch options are applied like in Steam (`VAR=value … %command% args`).
- **Drive letters:** `~/.local/share/steamos-isomounttool/drives/d…g` always point to the ISO in slot 1–4. Every prefix links `D:`–`G:` there and marks them as CD-ROM drives, so discs can be swapped while an installer runs.

Settings: `~/.config/steamos-isomounttool/config.json`

## Troubleshooting

- **“Could not eject … still in use”** – close the installer or Dolphin windows that still use files from the ISO.
- **The installer does not start** – open the log (button in the app). Try another Proton version, or turn off *Steam Linux Runtime* in the settings.
- **No Proton found** – install *Proton Experimental* in Steam (Library → Tools) or GE-Proton, then click **Rescan** in the settings.
- **The update check fails** – you are offline or GitHub can't be reached; the tool still works.

## Building from source

```bash
git clone https://github.com/elkarbeenus/SteamOS-IsoMountTool.git
cd SteamOS-IsoMountTool
python3 -m unittest discover -s tests   # core tests
./build.sh                              # → dist/SteamOS-IsoMountTool-<version>-x86_64.AppImage (needs internet)
```

## Releasing (maintainers)

1. Bump the version in `VERSION` and add a new section to `CHANGELOG.md` (`## [x.y.z] – date`).
2. Commit and push to `main`.
3. GitHub Actions runs the tests, builds the AppImage and, if there is no release for that version yet, creates the tag `vx.y.z` and publishes the release, using that version's CHANGELOG section as release notes. Installed copies pick the update up through the auto update.

## Credits

**Created by Dominic Lesina x Claude**
