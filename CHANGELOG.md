# Changelog

All notable changes to this project are documented here.

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
