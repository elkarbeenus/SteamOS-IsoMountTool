"""German / English texts. Created by Dominic Lesina x Claude."""

STRINGS = {
    # navigation
    "nav_isos": ("ISOs", "ISOs"),
    "nav_games": ("Spiele & Präfixe", "Games & prefixes"),
    "nav_settings": ("Einstellungen", "Settings"),
    "nav_about": ("Über", "About"),

    # ISO page
    "isos_title": ("Deine ISOs", "Your ISOs"),
    "isos_sub": ("{n} von {max} Slots belegt · ISO einfach hierher ziehen oder auf einen freien Slot klicken",
                 "{n} of {max} slots used · drag an ISO here or click a free slot"),
    "btn_mount": ("ISO einbinden", "Mount ISO"),
    "btn_eject_all": ("Alle auswerfen", "Eject all"),
    "slot": ("Slot {n}", "Slot {n}"),
    "slot_empty": ("Frei", "Empty"),
    "slot_empty_hint": ("Klicken, um eine ISO einzubinden", "Click to mount an ISO"),
    "drive": ("Laufwerk {l}:", "Drive {l}:"),
    "btn_install": ("Installer starten", "Run installer"),
    "btn_open": ("Öffnen", "Open"),
    "btn_eject": ("Auswerfen", "Eject"),
    "installer_found": ("Installer gefunden: {exe}", "Installer found: {exe}"),
    "installer_none": ("Kein Installer gefunden – im Dialog eine .exe wählen", "No installer found – choose an .exe in the dialog"),
    "not_mounted": ("nicht eingehängt", "not mounted"),
    "running_on": ("Läuft: {exe}", "Running: {exe}"),

    # launch dialog
    "launch_title": ("Mit Proton starten", "Run with Proton"),
    "launch_header": ("Installer von „{iso}“ starten", "Run installer from “{iso}”"),
    "launch_exe": ("Programm (.exe)", "Program (.exe)"),
    "launch_browse": ("Andere .exe wählen…", "Choose another .exe…"),
    "launch_no_exe": ("Auf dieser ISO wurde keine .exe gefunden. Wähle eine Datei aus.",
                      "No .exe was found on this ISO. Please choose a file."),
    "launch_prefix": ("Spiel / Präfix", "Game / prefix"),
    "launch_prefix_hint": ("Für mehrere Discs eines Spiels immer denselben Präfix wählen.",
                           "Use the same prefix for all discs of a game."),
    "launch_proton": ("Proton-Version", "Proton version"),
    "launch_options": ("Startoptionen (wie in Steam)", "Launch options (like in Steam)"),
    "launch_options_hint": ("Standard: WINE_LARGE_ADDRESS_AWARE=1 %command% – verhindert, dass große Installer ins RAM-Limit laufen.",
                            "Default: WINE_LARGE_ADDRESS_AWARE=1 %command% – keeps big installers from hitting the RAM limit."),
    "launch_reset": ("Standard", "Default"),
    "launch_runtime": ("Steam Linux Runtime verwenden (empfohlen)", "Use Steam Linux Runtime (recommended)"),
    "launch_start": ("Starten", "Start"),
    "cancel": ("Abbrechen", "Cancel"),
    "proton_auto": ("Automatisch – {name}", "Automatic – {name}"),
    "proton_none": ("Kein Proton gefunden", "No Proton found"),
    "err_no_proton": ("Es wurde keine Proton-Version gefunden.\n\nInstalliere in Steam z. B. „Proton Experimental“ (Bibliothek → Werkzeuge) oder GE-Proton (z. B. mit ProtonUp-Qt).",
                      "No Proton version was found.\n\nInstall e.g. “Proton Experimental” in Steam (Library → Tools) or GE-Proton (e.g. with ProtonUp-Qt)."),
    "err_need_exe": ("Bitte wähle eine .exe aus.", "Please choose an .exe file."),
    "err_need_prefix": ("Bitte gib einen Namen für das Spiel / den Präfix ein.", "Please enter a name for the game / prefix."),

    # running
    "st_preparing": ("Präfix „{name}“ wird vorbereitet…", "Preparing prefix “{name}”…"),
    "st_running": ("{exe} läuft (Präfix „{name}“)", "{exe} is running (prefix “{name}”)"),
    "st_finished": ("{exe} wurde beendet.", "{exe} has exited."),
    "finished_title": ("Programm beendet", "Program finished"),
    "finished_text": ("„{exe}“ wurde beendet (Code {code}).\n\nIm Bereich „Spiele & Präfixe“ kannst du das installierte Spiel jetzt starten.",
                      "“{exe}” has exited (code {code}).\n\nYou can now start the installed game in “Games & prefixes”."),
    "btn_show_games": ("Zu Spiele & Präfixe", "Go to games & prefixes"),
    "btn_open_log": ("Log öffnen", "Open log"),
    "ok": ("OK", "OK"),
    "close": ("Schließen", "Close"),

    # games / prefixes page
    "games_title": ("Spiele & Präfixe", "Games & prefixes"),
    "games_sub": ("Jedes Spiel bekommt einen eigenen Proton-Präfix in {path}",
                  "Every game gets its own Proton prefix in {path}"),
    "games_empty": ("Noch keine Präfixe. Starte einen Installer von einer ISO – der Präfix wird automatisch angelegt.",
                    "No prefixes yet. Run an installer from an ISO – the prefix is created automatically."),
    "btn_play": ("Spielen", "Play"),
    "btn_run_exe": ("Programm starten…", "Run program…"),
    "btn_open_c": ("Laufwerk C: öffnen", "Open drive C:"),
    "btn_delete": ("Löschen", "Delete"),
    "game_exe": ("Spiel: {exe}", "Game: {exe}"),
    "game_no_exe": ("Noch kein Spiel gewählt – „Programm starten…“ und die Spiel-.exe auswählen.",
                    "No game chosen yet – use “Run program…” and pick the game's .exe."),
    "pick_game_exe": ("Spiel- oder Programmdatei wählen", "Choose game or program file"),
    "confirm_delete": ("Präfix „{name}“ wirklich löschen?\n\nDas installierte Spiel und alle Spielstände darin werden gelöscht!\n\n{path}",
                       "Really delete prefix “{name}”?\n\nThe installed game and all save games in it will be deleted!\n\n{path}"),
    "remember_exe": ("Als Spiel für „Spielen“ merken", "Remember as game for “Play”"),

    # settings
    "set_title": ("Einstellungen", "Settings"),
    "set_language": ("Sprache", "Language"),
    "lang_system": ("Systemsprache", "System language"),
    "set_autoupdate": ("Beim Start nach Updates suchen", "Check for updates on start"),
    "set_check_now": ("Jetzt nach Updates suchen", "Check for updates now"),
    "set_proton": ("Standard-Proton", "Default Proton"),
    "set_runtime": ("Proton in der Steam Linux Runtime starten (empfohlen)", "Run Proton inside the Steam Linux Runtime (recommended)"),
    "set_log": ("Proton-Log schreiben (zur Fehlersuche)", "Write Proton log (for troubleshooting)"),
    "set_prefix_base": ("Ordner für Präfixe", "Folder for prefixes"),
    "set_choose": ("Ändern…", "Change…"),
    "set_options": ("Standard-Startoptionen", "Default launch options"),
    "set_section_general": ("Allgemein", "General"),
    "set_section_proton": ("Proton", "Proton"),
    "set_protons_found": ("{n} Proton-Version(en) gefunden", "{n} Proton version(s) found"),
    "set_rescan": ("Neu suchen", "Rescan"),

    # about
    "about_text": ("Bis zu {max} ISO-Abbilder unter SteamOS einbinden, auswerfen und Installer direkt mit Proton starten – ganz ohne sudo.",
                   "Mount and eject up to {max} ISO images on SteamOS and run installers directly with Proton – no sudo needed."),
    "about_credits": ("Erstellt von Dominic Lesina x Claude", "Created by Dominic Lesina x Claude"),
    "version": ("Version {v}", "Version {v}"),
    "btn_github": ("GitHub öffnen", "Open GitHub"),

    # mounting / errors
    "pick_iso": ("ISO-Datei auswählen", "Choose an ISO file"),
    "iso_filter": ("ISO-Abbilder (*.iso *.ISO)", "ISO images (*.iso *.ISO)"),
    "err_no_udisks": ("„udisksctl“ wurde nicht gefunden. Es wird benötigt, um ISOs ohne Root-Rechte einzubinden.",
                      "“udisksctl” was not found. It is required to mount ISOs without root rights."),
    "err_not_found": ("Datei nicht gefunden:\n{path}", "File not found:\n{path}"),
    "err_not_iso": ("Das ist keine .iso-Datei:\n{path}", "This is not an .iso file:\n{path}"),
    "err_already": ("Diese ISO ist bereits eingebunden:\n{path}", "This ISO is already mounted:\n{path}"),
    "err_limit": ("Es können höchstens {max} ISOs gleichzeitig eingebunden sein.\nBitte wirf zuerst eine aus.",
                  "You can mount at most {max} ISOs at the same time.\nPlease eject one first."),
    "err_loop": ("Die ISO konnte nicht als Loop-Gerät eingerichtet werden.", "Could not set up the ISO as a loop device."),
    "err_mount": ("Die ISO konnte nicht eingebunden werden.", "The ISO could not be mounted."),
    "err_eject": ("Die ISO konnte nicht ausgeworfen werden.\nWird sie noch von einem Programm oder Dateimanager-Fenster benutzt? Schließe es und versuche es erneut.",
                  "The ISO could not be ejected.\nIs a program or file manager window still using it? Close it and try again."),
    "mounted_toast": ("„{name}“ eingebunden als Laufwerk {l}:", "“{name}” mounted as drive {l}:"),
    "ejected_toast": ("„{name}“ ausgeworfen", "“{name}” ejected"),
    "confirm_eject_all": ("Alle {n} eingebundenen ISOs auswerfen?", "Eject all {n} mounted ISOs?"),
    "nothing_mounted": ("Es ist keine ISO eingebunden.", "No ISO is mounted."),
    "yes": ("Ja", "Yes"),
    "no": ("Nein", "No"),
    "error": ("Fehler", "Error"),
    "details": ("Details", "Details"),

    # updates
    "upd_title": ("Update verfügbar", "Update available"),
    "upd_text": ("Version {new} ist verfügbar (installiert: {old}).", "Version {new} is available (installed: {old})."),
    "upd_notes": ("Neuerungen", "What's new"),
    "upd_now": ("Jetzt aktualisieren", "Update now"),
    "upd_later": ("Alte Version behalten", "Keep current version"),
    "upd_none": ("Du verwendest die neueste Version ({v}).", "You are using the latest version ({v})."),
    "upd_fail_check": ("Konnte nicht nach Updates suchen. Bist du online?", "Could not check for updates. Are you online?"),
    "upd_downloading": ("Update wird heruntergeladen…", "Downloading update…"),
    "upd_fail_dl": ("Das Update konnte nicht heruntergeladen werden.", "The update could not be downloaded."),
    "upd_done": ("Auf Version {v} aktualisiert. Das Tool startet jetzt neu.", "Updated to version {v}. The tool will now restart."),
    "upd_manual": ("Diese Kopie kann sich nicht selbst aktualisieren (läuft nicht als AppImage oder keine Schreibrechte). Die Release-Seite wird geöffnet.",
                   "This copy cannot update itself (not running as AppImage or no write permission). The release page will be opened."),
    "upd_badge": ("Update {v} verfügbar", "Update {v} available"),
}


class Translator:
    def __init__(self, lang: str = "en"):
        self.lang = lang if lang in ("de", "en") else "en"

    def __call__(self, key: str, **fmt) -> str:
        pair = STRINGS.get(key)
        if pair is None:
            text = key
        else:
            text = pair[0] if self.lang == "de" else pair[1]
        if fmt:
            try:
                text = text.format(**fmt)
            except (KeyError, IndexError, ValueError):
                pass
        return text
