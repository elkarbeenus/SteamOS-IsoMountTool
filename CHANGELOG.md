# Changelog

All notable changes to this project are documented here.

## [2.2.0] – 2026-11-14

Now also for Windows 🪟

### Added
- **Windows version** (`SteamOS-IsoMountTool-x.y.z-windows-x64.exe`, Windows 10/11 64-bit) – a single .exe, nothing to install
  - Mounts ISOs with Windows' built-in ISO support (same as right-click → *Mount*), up to 4 at the same time, each with its real drive letter
  - **Run installer** starts the installer directly; if it needs administrator rights, Windows asks via UAC
  - **Games** page: choose the installed game's .exe once, then start it with **Play**, open its folder, or send it to LakuenLauncher. *Remove* only removes the entry from the list – the installed game stays
  - Auto update downloads the new .exe and restarts the tool
  - Same interface, German & English
- Releases now contain both the AppImage (SteamOS/Linux) and the Windows .exe

### Changed
- Slightly slimmer buttons on the ISO cards so “Run installer” always fits

## [2.1.0] – 2026-11-14

### Added
- **“Send to LakuenLauncher”** on the *Games & prefixes* page: adds the installed game to the LakuenLauncher library in one click – with the same prefix (filled into the game's prefix setting), the same Proton version, Steam Linux Runtime and your launch options (`WINE_LARGE_ADDRESS_AWARE=1`). If no game `.exe` was chosen yet, the tool asks for it first
- Sending a game again updates the existing entry instead of creating a duplicate
- A backup of the LakuenLauncher library is written before every change; if the launcher is running, the tool asks you to close it first so it doesn't overwrite the library

## [2.0.1] – 2026-11-14

### Fixed
- **Installers did not start** (“could not open working directory D:\\”, exit code 1): the installer is now started exactly like Steam does it – with its normal Linux path and without extra drive letters. The installer window opens and you install as usual
- Prefixes created with 2.0.0 are repaired automatically: the drive links D:–G: are removed on the next start
- No extra prefix preparation run any more – Proton creates the prefix itself, like under Steam
- Removed `STEAM_COMPAT_LIBRARY_PATHS` (caused “unable to use parent for game drive” warnings) and set the app id variables Proton expects

### Changed
- Drive letters D:–G: for mounted ISOs are now an **experimental option** in the settings (off by default)

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
