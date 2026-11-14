# Changelog

All notable changes to this project are documented here.

## [2.0.0] – 2026-11-14

Big update: a real graphical interface and Windows installers straight from the ISO with Proton 🎮

### Added
- **New graphical interface** (Qt) with a dark, SteamOS-style look: 4 large ISO slots, sidebar navigation, notifications
- **Drag & drop**: drop an `.iso` onto the window or a free slot to mount it
- **Run installers with Proton**: “Run installer” finds `setup.exe` / the `autorun.inf` target on the ISO and starts it with Proton – no more adding the `.exe` to Steam by hand
- Uses the **newest Proton** on your system automatically (Proton Experimental, otherwise the highest version incl. GE-Proton); any installed version can be chosen
- **Launch options like in Steam**, default `WINE_LARGE_ADDRESS_AWARE=1 %command%`, so big installers don't hit the RAM limit
- Proton runs inside the **Steam Linux Runtime** (like Steam does), can be turned off
- **One prefix per game** in `~/Games/IsoMountTool/<game>` – choose the same prefix for every disc of a game
- **Fixed drive letters**: slot 1–4 = drive D:–G: inside the prefix (marked as CD-ROM). **Swap discs during installation**: eject disc 1 and mount disc 2 into the same slot
- New **“Games & prefixes”** page: start the installed game (“Play”), run any program in the prefix, open drive C:, delete a prefix
- Log file for every run, can be opened from the app
- Settings page: language, auto update, default Proton, Steam Linux Runtime, Proton log, default launch options, prefix folder
- Update dialog shows the release notes
- New command line options `--list-proton`

### Changed
- Rewritten in Python; the AppImage bundles its own Python and Qt, nothing has to be installed
- Settings moved to `~/.config/steamos-isomounttool/config.json` (old settings are taken over)

## [1.0.0] – 2026-11-13

First release 🎉

### Added
- Mount `.iso` files via a file dialog (read-only, no root needed – uses `udisksctl`)
- Eject one, several or all mounted ISOs
- Limit of **4** ISOs mounted at the same time
- Main menu shows all mounted ISOs and where they are mounted
- Open a mounted ISO directly in the file manager
- German and English user interface (follows the system language, switchable in the menu)
- Auto update: checks GitHub for a new release on start and asks whether to update or keep the current version (can be turned off)
- Support for hybrid ISOs with partitions
- Command line options: `--mount`, `--eject`, `--eject-all`, `--list`, `--check-update`, `--lang`, `--no-update-check`
- zenity UI with kdialog fallback
