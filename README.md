<p align="center">
  <img src="packaging/steamos-isomounttool.svg" width="128" alt="SteamOS ISO Mount Tool icon">
</p>

<h1 align="center">SteamOS ISO Mount Tool</h1>

<p align="center">
  Mount and eject up to <b>4 ISO images</b> on SteamOS with a few clicks – no sudo, no password, no terminal.<br>
  <i>Created by Dominic Lesina x Claude</i>
</p>

---

## Features

- 💿 **Mount ISO files** – pick any `.iso` file with a file dialog, and it gets mounted read-only so you can open it in Dolphin
- ⏏️ **Eject ISOs** – eject one, several or all mounted ISOs at once
- 🔢 **Up to 4 ISOs** at the same time (the limit is intentional)
- 📂 **Open in file manager** – jump straight into a mounted ISO
- 🌐 **German & English** – follows your system language, and you can switch it in the menu
- 🔄 **Auto update** – on start the tool checks this repository for a new release and asks whether you want to update or keep your current version (can be turned off)
- 🔐 **No root required** – uses `udisksctl` (udisks2), the same way Dolphin mounts drives
- 🧰 **Command line mode** for scripts and Steam shortcuts

## Requirements

- SteamOS 3.x in **Desktop Mode** (also works on most other Linux desktops)
- `udisksctl`, plus `zenity` or `kdialog` – all preinstalled on SteamOS

## Installation

1. Download the latest `SteamOS-IsoMountTool-x.y.z-x86_64.AppImage` from the [Releases page](https://github.com/elkarbeenus/SteamOS-IsoMountTool/releases/latest).
2. Move it to a folder of your choice, e.g. `~/Applications`.
3. Make it executable: right-click → **Properties** → **Permissions** → tick **Is executable**
   (or in a terminal: `chmod +x SteamOS-IsoMountTool-*.AppImage`).
4. Double-click it to start.

> **Tip:** For the auto update to work, the AppImage has to be in a folder you can write to (e.g. inside your home folder).

## Usage

Start the AppImage and pick an option from the menu:

| Option | What it does |
|---|---|
| **Mount ISO…** | Choose an `.iso` file → it is mounted under `/run/media/<user>/<ISO label>` |
| **Eject ISO…** | Choose one or more mounted ISOs to eject |
| **Eject all ISOs** | Ejects every mounted ISO |
| **Open mounted ISO in file manager…** | Opens the mount folder in Dolphin |
| **Language** | Switches between German and English |
| **Auto update ON/OFF** | Turns the update check on start on or off |
| **Check for updates now** | Checks for a new release right away |

The menu always shows which ISOs are mounted and where.

### Command line

```bash
./SteamOS-IsoMountTool.AppImage --mount ~/Downloads/game.iso   # mount
./SteamOS-IsoMountTool.AppImage --list                         # list mounted ISOs
./SteamOS-IsoMountTool.AppImage --eject ~/Downloads/game.iso   # eject (path or /dev/loopN)
./SteamOS-IsoMountTool.AppImage --eject-all                    # eject all
./SteamOS-IsoMountTool.AppImage --check-update                 # check for updates
./SteamOS-IsoMountTool.AppImage --lang en                      # set language (de|en)
./SteamOS-IsoMountTool.AppImage --no-update-check              # skip update check on start
./SteamOS-IsoMountTool.AppImage --help
```

## How it works

1. `udisksctl loop-setup --read-only` attaches the ISO to a free loop device.
2. `udisksctl mount` mounts it (hybrid ISOs with partitions are supported).
3. On eject, it unmounts everything and removes the loop device with `udisksctl loop-delete`.

Mounted ISOs are found by checking which loop devices are backed by an `.iso` file. So the tool also sees ISOs you mounted another way, and they count toward the limit of 4.

Settings are stored in `~/.config/steamos-isomounttool/config`.

## Troubleshooting

- **"Could not eject … still in use"** – close every Dolphin window or program that is still opening files from the ISO, then try again.
- **An authentication prompt appears** – udisks asks for permission via polkit. On SteamOS in Desktop Mode this is normally allowed without a password for the active user.
- **The update check fails** – you are offline or GitHub can't be reached. The tool still works normally.

## Building from source

```bash
git clone https://github.com/elkarbeenus/SteamOS-IsoMountTool.git
cd SteamOS-IsoMountTool
./build.sh          # → dist/SteamOS-IsoMountTool-<version>-x86_64.AppImage
```

`build.sh` downloads `appimagetool` automatically if it is missing. The version comes from the `VERSION` file.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) – every release lists its changes.

## Credits

**Created by Dominic Lesina x Claude**
