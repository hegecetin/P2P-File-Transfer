#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kolay Dosya Aktarımı — Windows 10/11
Gereksinim: python -m pip install --upgrade "magic-wormhole>=0.23.0"
Çalıştırma: python dosya_aktar.py
"""

import os
import re
import argparse
import sys
import site
import shutil
import queue
import threading
import subprocess
import tempfile
import time
import json
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = "Kolay Dosya Aktarımı"
CONFIG_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "KolayDosyaAktarimi"
CONFIG_FILE = CONFIG_DIR / "settings.json"
ACTIVITY_LOG_FILE = CONFIG_DIR / "islem_gunlugu.jsonl"

# Wormhole sürümleri arasında çıktı metni değişebildiğinden birden fazla biçim desteklenir.
CODE_PATTERNS = [
    re.compile(r"\b(?:wormhole\s+code(?:\s+is)?|allocated\s+code)\s*:\s*([0-9]+(?:-[a-zA-Z0-9]+){2,})", re.I),
    re.compile(r"\b([0-9]+(?:-[a-zA-Z0-9]+){2,})\b"),
]
VALID_CODE = re.compile(r"^[0-9]+(?:-[a-zA-Z0-9]+){2,}$")
PROGRESS_RE = re.compile(r"(?<!\d)(100|[1-9]?\d)%\s*\|")
SPEED_RE = re.compile(r"([\d.,]+)\s*(B/s|KB/s|MB/s|GB/s|KiB/s|MiB/s|GiB/s)", re.I)
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


TEXT = {
    "tr": {
        "subtitle": "Bilgisayarlar arasında kolay ve güvenli dosya aktarımı",
        "send_tab": "Dosya gönder", "receive_tab": "Dosya al",
        "settings": "Ayarlar", "source_title": "Gönderilecek dosya veya klasör",
        "choose_file": "Dosya seç", "choose_folder": "Klasör seç",
        "source_placeholder": "Bir dosya veya klasör seçin",
        "send": "Göndermeyi başlat", "code_title": "Tek kullanımlık aktarım kodu",
        "copy": "Kodu kopyala", "code_not_ready": "Kod henüz oluşturulmadı",
        "receive_code": "Gönderen bilgisayardaki kod",
        "destination": "Kayıt konumu", "browse": "Göz at", "receive": "Dosyayı al",
        "status_title": "Aktarım durumu", "ready": "Hazır · Bir işlem seçerek başlayın",
        "details": "İşlem ayrıntıları", "clear": "Temizle", "open_folder": "Alınan klasörü aç",
        "cancel": "Aktarımı iptal et", "language": "Uygulama dili",
        "language_hint": "Dil değişikliği anında uygulanır.",
        "performance": "Performans", "performance_hint": "Aktarım hızını bağlantı, karşı bilgisayar ve disk hızı belirler. Uygulama güvenli aktarım ayarlarını otomatik olarak korur.",
        "save": "Kaydet", "close": "Kapat", "choose_source": "Lütfen göndereceğiniz dosya veya klasörü seçin.",
        "bad_code": "Aktarım kodu geçersiz. Gönderen bilgisayardaki kodu aynen girin.",
        "starting": "Aktarım başlatılıyor…", "creating_code": "Tek kullanımlık kod oluşturuluyor…",
        "waiting": "Kod hazır · Alıcı kodu girene kadar bekleniyor",
        "connecting": "Gönderen bilgisayara bağlanılıyor…", "transferring": "Dosya aktarılıyor…",
        "verifying": "Aktarım doğrulanıyor…", "success": "Aktarım başarıyla tamamlandı",
        "failed": "Aktarım tamamlanamadı · Ayrıntıları kontrol edin", "cancelled": "Aktarım iptal edildi",
        "no_wormhole": "Magic Wormhole kurulu değil. İki bilgisayarda da şu komutu çalıştırın:\n\npython -m pip install --upgrade \"magic-wormhole>=0.23.0\"",
        "no_folder": "Alınan dosya klasörü bulunamadı.", "copy_done": "Kod panoya kopyalandı.",
        "select_error": "Dosya veya klasör bulunamadı.", "folder_note": "Her alım ayrı bir alt klasöre kaydedilir; mevcut dosyalar korunur.",
        "source_selected": "Seçildi", "speed": "Hız", "elapsed": "Süre",
        "log_started_send": "Gönderim başlatıldı: ", "log_started_receive": "Alım klasörü: ",
        "log_complete": "Aktarım tamamlandı.", "log_cancel": "İşlem kullanıcı tarafından iptal edildi.",
        "log_missing": "Alınan dosya bulunamadı.", "error": "Hata",
        "ask_cancel": "Aktarımı iptal edip çıkmak istiyor musunuz?", "busy_title": "Aktarım devam ediyor",
        "window_error": "Pencere açılamadı. Grafik masaüstü ortamı gerekli: ",
        "size": "Boyut", "unknown": "Bilinmiyor",
        "history": "İşlem günlüğü", "history_open": "Günlüğü aç",
        "history_empty": "Henüz kayıtlı işlem yok.",
        "history_saved": "İşlem günlüğü kaydedildi: ",
        "log_app_start": "Uygulama açıldı.", "log_app_close": "Uygulama kapatıldı.",
        "log_send_failed": "Gönderim başarısız.", "log_receive_failed": "Alım başarısız.",
    },
    "en": {
        "subtitle": "Easy and secure file transfers between computers",
        "send_tab": "Send files", "receive_tab": "Receive files",
        "settings": "Settings", "source_title": "File or folder to send",
        "choose_file": "Choose file", "choose_folder": "Choose folder",
        "source_placeholder": "Choose a file or folder",
        "send": "Start sending", "code_title": "One-time transfer code",
        "copy": "Copy code", "code_not_ready": "Code has not been created yet",
        "receive_code": "Code from the sending computer",
        "destination": "Save location", "browse": "Browse", "receive": "Receive files",
        "status_title": "Transfer status", "ready": "Ready · Choose an action to begin",
        "details": "Activity details", "clear": "Clear", "open_folder": "Open received folder",
        "cancel": "Cancel transfer", "language": "Application language",
        "language_hint": "Language changes apply immediately.",
        "performance": "Performance", "performance_hint": "Transfer speed depends on the network, the other computer, and disk speed. The app keeps secure transfer settings intact.",
        "save": "Save", "close": "Close", "choose_source": "Please choose a file or folder to send.",
        "bad_code": "Invalid transfer code. Enter the code exactly as shown on the sender's computer.",
        "starting": "Starting transfer…", "creating_code": "Creating one-time code…",
        "waiting": "Code ready · Waiting for the receiver to enter it",
        "connecting": "Connecting to sender…", "transferring": "Transferring files…",
        "verifying": "Verifying transfer…", "success": "Transfer completed successfully",
        "failed": "Transfer failed · Check the activity details", "cancelled": "Transfer cancelled",
        "no_wormhole": "Magic Wormhole is not installed. Run this command on both computers:\n\npython -m pip install --upgrade \"magic-wormhole>=0.23.0\"",
        "no_folder": "Received-file folder could not be found.", "copy_done": "Code copied to clipboard.",
        "select_error": "File or folder not found.", "folder_note": "Each receive operation uses a separate subfolder to protect existing files.",
        "source_selected": "Selected", "speed": "Speed", "elapsed": "Elapsed",
        "log_started_send": "Sending: ", "log_started_receive": "Receive folder: ",
        "log_complete": "Transfer completed.", "log_cancel": "Operation cancelled by user.",
        "log_missing": "No received file was found.", "error": "Error",
        "ask_cancel": "Cancel the transfer and exit?", "busy_title": "Transfer in progress",
        "window_error": "Could not open the window. A graphical desktop is required: ",
        "size": "Size", "unknown": "Unknown",
        "history": "Activity log", "history_open": "Open log",
        "history_empty": "No saved activity yet.",
        "history_saved": "Activity log saved: ",
        "log_app_start": "Application started.", "log_app_close": "Application closed.",
        "log_send_failed": "Sending failed.", "log_receive_failed": "Receiving failed.",
    },
}


def wormhole_path():
    exe = "wormhole.exe" if os.name == "nt" else "wormhole"
    candidates = []
    try:
        import sysconfig
        candidates.append(Path(sysconfig.get_path("scripts")) / exe)
    except Exception:
        pass
    try:
        candidates.append(Path(site.getuserbase()) / ("Scripts" if os.name == "nt" else "bin") / exe)
    except Exception:
        pass
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    found = shutil.which("wormhole")
    if found:
        return found
    raise RuntimeError(TEXT["tr"]["no_wormhole"])


def default_target():
    downloads = Path.home() / "Downloads"
    if not downloads.is_dir():
        downloads = Path.home()
    return downloads / "Gelen_Dosyalar"


def load_settings():
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return {"language": data.get("language", "tr") if data.get("language") in TEXT else "tr"}
    except (OSError, ValueError, TypeError):
        return {"language": "tr"}


def save_settings(settings):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")


def clean_path(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    return value


def human_size(path):
    try:
        p = Path(path)
        size = p.stat().st_size if p.is_file() else sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
    except (OSError, PermissionError):
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return "—"


def format_speed(value, unit):
    factors = {"B/s": 1, "KB/s": 1000, "MB/s": 1000**2, "GB/s": 1000**3,
               "KiB/s": 1024, "MiB/s": 1024**2, "GiB/s": 1024**3}
    try:
        number = float(value.replace(",", "."))
        bps = number * factors[unit]
        for label, factor in (("GB/s", 1000**3), ("MB/s", 1000**2), ("KB/s", 1000), ("B/s", 1)):
            if bps >= factor or label == "B/s":
                return f"{bps / factor:.1f} {label}"
    except (ValueError, KeyError):
        pass
    return ""


class FileTransferApp:
    BG = "#f3f6fb"
    CARD = "#ffffff"
    TEXT = "#17253c"
    MUTED = "#64748b"
    BLUE = "#2563eb"
    BORDER = "#dbe4f0"

    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.lang = self.settings["language"]
        self.events = queue.Queue()
        self.busy = False
        self.cancel_event = threading.Event()
        self.process = None
        self.operation = None
        self.receive_dir = None
        self.last_receive_dir = None
        self.started_at = None
        self.current_speed = ""
        self.source = tk.StringVar()
        self.code_send = tk.StringVar(value=self.t("code_not_ready"))
        self.code_receive = tk.StringVar()
        self.target = tk.StringVar(value=str(default_target()))
        self.status = tk.StringVar(value=self.t("ready"))
        self.percent = tk.StringVar()
        self.speed = tk.StringVar(value="—")
        self.elapsed = tk.StringVar(value="00:00")
        self.source_info = tk.StringVar(value=self.t("source_placeholder"))

        self.root.title(APP_NAME)
        self.root.geometry("850x760")
        self.root.minsize(720, 680)
        self.root.configure(bg=self.BG)
        self._styles()
        self._build()
        self.source.trace_add("write", self._source_changed)
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(80, self._poll_events)
        self.root.after(500, self._update_elapsed)
        self._record_history("info", "log_app_start")

    def t(self, key):
        return TEXT[self.lang].get(key, key)

    def _styles(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        font = "Segoe UI"
        style.configure("App.TFrame", background=self.BG)
        style.configure("Card.TFrame", background=self.CARD)
        style.configure("Heading.TLabel", background=self.BG, foreground=self.TEXT, font=(font, 21, "bold"))
        style.configure("Muted.TLabel", background=self.BG, foreground=self.MUTED, font=(font, 9))
        style.configure("CardTitle.TLabel", background=self.CARD, foreground=self.TEXT, font=(font, 11, "bold"))
        style.configure("Card.TLabel", background=self.CARD, foreground=self.TEXT, font=(font, 10))
        style.configure("MutedCard.TLabel", background=self.CARD, foreground=self.MUTED, font=(font, 9))
        style.configure("Accent.TLabel", background=self.CARD, foreground=self.BLUE, font=(font, 10, "bold"))
        style.configure("TButton", padding=(10, 8), font=(font, 10))
        style.configure("Primary.TButton", padding=(14, 10), font=(font, 10, "bold"),
                        foreground="white", background=self.BLUE, borderwidth=0)
        style.map("Primary.TButton", background=[("active", "#1d4ed8"), ("disabled", "#aab7ca")])
        style.configure("TEntry", padding=8, font=(font, 10), fieldbackground="white")
        style.configure("TNotebook", background=self.CARD, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(20, 11), font=(font, 10, "bold"))
        style.configure("Blue.Horizontal.TProgressbar", troughcolor="#e7edf5", background=self.BLUE,
                        bordercolor="#e7edf5", lightcolor=self.BLUE, darkcolor=self.BLUE, thickness=13)

    def _build(self):
        self.main = ttk.Frame(self.root, style="App.TFrame", padding=(22, 17))
        self.main.pack(fill="both", expand=True)
        self.header = ttk.Frame(self.main, style="App.TFrame")
        self.header.pack(fill="x")
        self.heading = ttk.Label(self.header, text=APP_NAME, style="Heading.TLabel")
        self.heading.pack(side="left", anchor="w")
        self.settings_button = ttk.Button(self.header, text="⚙  " + self.t("settings"), command=self._settings)
        self.settings_button.pack(side="right", anchor="e")
        self.subtitle = ttk.Label(self.main, text=self.t("subtitle"), style="Muted.TLabel")
        self.subtitle.pack(anchor="w", pady=(4, 13))

        tab_card = ttk.Frame(self.main, style="Card.TFrame", padding=10)
        tab_card.pack(fill="x")
        self.tabs = ttk.Notebook(tab_card)
        self.tabs.pack(fill="x")
        self.send_tab = ttk.Frame(self.tabs, style="Card.TFrame", padding=(16, 17))
        self.receive_tab = ttk.Frame(self.tabs, style="Card.TFrame", padding=(16, 17))
        self.tabs.add(self.send_tab, text=self.t("send_tab"))
        self.tabs.add(self.receive_tab, text=self.t("receive_tab"))
        self._build_send()
        self._build_receive()

        self.status_card = ttk.Frame(self.main, style="Card.TFrame", padding=(17, 14))
        self.status_card.pack(fill="both", expand=True, pady=(12, 0))
        row = ttk.Frame(self.status_card, style="Card.TFrame")
        row.pack(fill="x")
        self.status_heading = ttk.Label(row, text=self.t("status_title"), style="CardTitle.TLabel")
        self.status_heading.pack(side="left")
        self.percent_label = ttk.Label(row, textvariable=self.percent, style="Accent.TLabel")
        self.percent_label.pack(side="right")
        self.status_label = ttk.Label(self.status_card, textvariable=self.status, style="MutedCard.TLabel")
        self.status_label.pack(anchor="w", pady=(7, 8))
        self.progress = ttk.Progressbar(self.status_card, orient="horizontal", mode="determinate",
                                         maximum=100, style="Blue.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(0, 10))

        metrics = ttk.Frame(self.status_card, style="Card.TFrame")
        metrics.pack(fill="x", pady=(0, 9))
        self.speed_label = ttk.Label(metrics, text=self.t("speed") + ": ", style="MutedCard.TLabel")
        self.speed_label.pack(side="left")
        self.speed_value = ttk.Label(metrics, textvariable=self.speed, style="Accent.TLabel")
        self.speed_value.pack(side="left", padx=(2, 18))
        self.elapsed_label = ttk.Label(metrics, text=self.t("elapsed") + ": ", style="MutedCard.TLabel")
        self.elapsed_label.pack(side="left")
        self.elapsed_value = ttk.Label(metrics, textvariable=self.elapsed, style="Card.TLabel")
        self.elapsed_value.pack(side="left", padx=(2, 0))

        logrow = ttk.Frame(self.status_card, style="Card.TFrame")
        logrow.pack(fill="x", pady=(0, 5))
        self.details_label = ttk.Label(logrow, text=self.t("details"), style="MutedCard.TLabel")
        self.details_label.pack(side="left")
        self.clear_button = ttk.Button(logrow, text=self.t("clear"), command=self._clear_log)
        self.clear_button.pack(side="right")
        self.history_button = ttk.Button(logrow, text=self.t("history"), command=self._open_history)
        self.history_button.pack(side="right", padx=(0, 6))
        logframe = ttk.Frame(self.status_card, style="Card.TFrame")
        logframe.pack(fill="both", expand=True)
        self.log = tk.Text(logframe, height=5, wrap="word", font=("Segoe UI", 9), bg="#f8fafc",
                           fg=self.TEXT, relief="flat", bd=0, highlightthickness=1,
                           highlightbackground=self.BORDER, padx=10, pady=8, state="disabled")
        scrollbar = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scrollbar.set)
        self.log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        bottom = ttk.Frame(self.main, style="App.TFrame")
        bottom.pack(fill="x", pady=(10, 0))
        self.open_button = ttk.Button(bottom, text=self.t("open_folder"), command=self._open_folder, state="disabled")
        self.open_button.pack(side="left")
        self.cancel_button = ttk.Button(bottom, text=self.t("cancel"), command=self._cancel, state="disabled")
        self.cancel_button.pack(side="right")

    def _build_send(self):
        f = self.send_tab
        self.source_title = ttk.Label(f, text=self.t("source_title"), style="CardTitle.TLabel")
        self.source_title.pack(anchor="w")
        row = ttk.Frame(f, style="Card.TFrame")
        row.pack(fill="x", pady=(8, 5))
        self.source_entry = ttk.Entry(row, textvariable=self.source)
        self.source_entry.pack(side="left", fill="x", expand=True)
        self.file_button = ttk.Button(row, text=self.t("choose_file"), command=self._choose_file)
        self.file_button.pack(side="left", padx=(7, 0))
        self.folder_button = ttk.Button(row, text=self.t("choose_folder"), command=self._choose_folder)
        self.folder_button.pack(side="left", padx=(5, 0))
        self.source_info_label = ttk.Label(f, textvariable=self.source_info, style="MutedCard.TLabel")
        self.source_info_label.pack(anchor="w", pady=(0, 12))
        row2 = ttk.Frame(f, style="Card.TFrame")
        row2.pack(fill="x")
        self.code_title = ttk.Label(row2, text=self.t("code_title"), style="CardTitle.TLabel")
        self.code_title.pack(side="left")
        self.send_button = ttk.Button(row2, text=self.t("send"), style="Primary.TButton", command=self._start_send)
        self.send_button.pack(side="right")
        row3 = ttk.Frame(f, style="Card.TFrame")
        row3.pack(fill="x", pady=(8, 0))
        self.code_entry = ttk.Entry(row3, textvariable=self.code_send, state="readonly")
        self.code_entry.pack(side="left", fill="x", expand=True)
        self.copy_button = ttk.Button(row3, text=self.t("copy"), command=self._copy_code, state="disabled")
        self.copy_button.pack(side="left", padx=(7, 0))

    def _build_receive(self):
        f = self.receive_tab
        self.receive_code_label = ttk.Label(f, text=self.t("receive_code"), style="CardTitle.TLabel")
        self.receive_code_label.pack(anchor="w")
        self.receive_entry = ttk.Entry(f, textvariable=self.code_receive)
        self.receive_entry.pack(fill="x", pady=(8, 13))
        row = ttk.Frame(f, style="Card.TFrame")
        row.pack(fill="x")
        self.destination_label = ttk.Label(row, text=self.t("destination"), style="CardTitle.TLabel")
        self.destination_label.pack(side="left")
        self.receive_button = ttk.Button(row, text=self.t("receive"), style="Primary.TButton", command=self._start_receive)
        self.receive_button.pack(side="right")
        row2 = ttk.Frame(f, style="Card.TFrame")
        row2.pack(fill="x", pady=(8, 4))
        self.target_entry = ttk.Entry(row2, textvariable=self.target)
        self.target_entry.pack(side="left", fill="x", expand=True)
        self.browse_button = ttk.Button(row2, text=self.t("browse"), command=self._choose_target)
        self.browse_button.pack(side="left", padx=(7, 0))
        self.folder_note_label = ttk.Label(f, text=self.t("folder_note"), style="MutedCard.TLabel")
        self.folder_note_label.pack(anchor="w")

    def _all_controls(self):
        return [self.source_entry, self.file_button, self.folder_button, self.send_button,
                self.receive_entry, self.target_entry, self.browse_button, self.receive_button]

    def _source_changed(self, *_):
        value = self.source.get().strip()
        if not value:
            self.source_info.set(self.t("source_placeholder"))
        else:
            p = Path(clean_path(value)).expanduser()
            kind = "Folder" if self.lang == "en" else "Klasör"
            if p.is_file():
                self.source_info.set(f"{self.t('size')}: {human_size(p)}")
            elif p.is_dir():
                self.source_info.set(f"{kind} · {self.t('size').lower()}: {human_size(p)}")
            else:
                self.source_info.set(self.t("source_selected"))

    def _choose_file(self):
        value = filedialog.askopenfilename(title=self.t("choose_file"))
        if value:
            self.source.set(value)

    def _choose_folder(self):
        value = filedialog.askdirectory(title=self.t("choose_folder"))
        if value:
            self.source.set(value)

    def _choose_target(self):
        current = self.target.get()
        value = filedialog.askdirectory(title=self.t("destination"),
                                         initialdir=current if Path(current).is_dir() else str(Path.home()))
        if value:
            self.target.set(value)

    def _settings(self):
        win = tk.Toplevel(self.root)
        win.title(self.t("settings"))
        win.configure(bg=self.BG)
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()
        frame = ttk.Frame(win, style="App.TFrame", padding=22)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=self.t("language"), style="CardTitle.TLabel").pack(anchor="w")
        lang = tk.StringVar(value=self.lang)
        choice = ttk.Combobox(frame, state="readonly", textvariable=lang, values=("Türkçe", "English"), width=25)
        choice.current(0 if self.lang == "tr" else 1)
        choice.pack(fill="x", pady=(7, 4))
        ttk.Label(frame, text=self.t("language_hint"), style="Muted.TLabel").pack(anchor="w")
        ttk.Label(frame, text=self.t("performance"), style="CardTitle.TLabel").pack(anchor="w", pady=(18, 4))
        ttk.Label(frame, text=self.t("performance_hint"), style="Muted.TLabel", wraplength=360).pack(anchor="w")
        buttons = ttk.Frame(frame, style="App.TFrame")
        buttons.pack(fill="x", pady=(18, 0))

        def apply():
            selected = "tr" if choice.get() == "Türkçe" else "en"
            self.lang = selected
            self.settings["language"] = selected
            try:
                save_settings(self.settings)
            except OSError as exc:
                messagebox.showwarning(self.t("error"), str(exc), parent=win)
            win.destroy()
            self._rebuild_texts()

        ttk.Button(buttons, text=self.t("close"), command=win.destroy).pack(side="right")
        ttk.Button(buttons, text=self.t("save"), style="Primary.TButton", command=apply).pack(side="right", padx=(0, 8))
        win.update_idletasks()
        win.geometry(f"+{self.root.winfo_rootx()+100}+{self.root.winfo_rooty()+100}")

    def _rebuild_texts(self):
        self.root.title(APP_NAME)
        self.heading.configure(text=APP_NAME)
        self.settings_button.configure(text="⚙  " + self.t("settings"))
        self.subtitle.configure(text=self.t("subtitle"))
        self.tabs.tab(self.send_tab, text=self.t("send_tab"))
        self.tabs.tab(self.receive_tab, text=self.t("receive_tab"))
        for widget, key in [
            (self.source_title, "source_title"), (self.file_button, "choose_file"),
            (self.folder_button, "choose_folder"), (self.send_button, "send"),
            (self.code_title, "code_title"), (self.copy_button, "copy"),
            (self.receive_code_label, "receive_code"), (self.destination_label, "destination"),
            (self.browse_button, "browse"), (self.receive_button, "receive"),
            (self.folder_note_label, "folder_note"), (self.status_heading, "status_title"),
            (self.details_label, "details"), (self.clear_button, "clear"),
            (self.history_button, "history"),
            (self.open_button, "open_folder"), (self.cancel_button, "cancel"),
            (self.speed_label, "speed"), (self.elapsed_label, "elapsed"),
        ]:
            if key in ("speed", "elapsed"):
                widget.configure(text=self.t(key) + ": ")
            else:
                widget.configure(text=self.t(key))
        if self.status.get() in (TEXT["tr"]["ready"], TEXT["en"]["ready"]):
            self.status.set(self.t("ready"))
        if self.code_send.get() in (TEXT["tr"]["code_not_ready"], TEXT["en"]["code_not_ready"]):
            self.code_send.set(self.t("code_not_ready"))
        if not self.source.get().strip():
            self.source_info.set(self.t("source_placeholder"))
        self._source_changed()

    def _copy_code(self):
        code = self.code_send.get().strip()
        if VALID_CODE.fullmatch(code):
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.status.set(self.t("copy_done"))

    def _start_send(self):
        if self.busy:
            return
        source = Path(clean_path(self.source.get())).expanduser()
        if not (source.is_file() or source.is_dir()):
            messagebox.showwarning(self.t("error"), self.t("choose_source"))
            return
        try:
            exe = wormhole_path()
            source = source.resolve()
        except (OSError, RuntimeError) as exc:
            messagebox.showerror(self.t("error"), str(exc))
            return
        self.code_send.set(self.t("creating_code"))
        self.copy_button.configure(state="disabled")
        self._start_process("send", [exe, "send", "--code-length", "3", str(source)], None,
                            self.t("creating_code"))
        self._log(self.t("log_started_send") + str(source))
        self._record_history("info", self.t("log_started_send").strip(), path=str(source), size=human_size(source))

    def _start_receive(self):
        if self.busy:
            return
        code = self.code_receive.get().strip()
        if not VALID_CODE.fullmatch(code):
            messagebox.showwarning(self.t("error"), self.t("bad_code"))
            return
        try:
            exe = wormhole_path()
            target = Path(clean_path(self.target.get())).expanduser().resolve()
            target.mkdir(parents=True, exist_ok=True)
            folder_prefix = "Alinan_" + datetime.now().strftime("%Y%m%d_%H%M%S") + "_"
            self.receive_dir = Path(tempfile.mkdtemp(prefix=folder_prefix, dir=str(target)))
        except (OSError, RuntimeError) as exc:
            messagebox.showerror(self.t("error"), str(exc))
            return
        self._start_process("receive", [exe, "receive", "--accept-file", code], str(self.receive_dir),
                            self.t("connecting"))
        self._log(self.t("log_started_receive") + str(self.receive_dir))
        self._record_history("info", self.t("log_started_receive").strip(), destination=str(self.receive_dir), code=code)

    def _start_process(self, operation, command, cwd, status):
        self.busy = True
        self.operation = operation
        self.cancel_event.clear()
        self.started_at = time.monotonic()
        self.current_speed = ""
        self.speed.set("—")
        self.elapsed.set("00:00")
        self.status.set(status)
        self.percent.set("")
        self.progress.stop()
        self.progress.configure(mode="indeterminate", value=0)
        self.progress.start(12)
        self.cancel_button.configure(state="normal")
        self.open_button.configure(state="disabled")
        for control in self._all_controls():
            control.configure(state="disabled")
        self._clear_log()
        threading.Thread(target=self._worker, args=(command, cwd), daemon=True).start()

    def _worker(self, command, cwd):
        exit_code = 1
        error = None
        proc = None
        try:
            env = os.environ.copy()
            env["WORMHOLE_QR"] = "0"
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUNBUFFERED"] = "1"
            kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
            proc = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    encoding="utf-8", errors="replace", bufsize=0, **kwargs)
            self.process = proc
            if self.cancel_event.is_set():
                proc.terminate()
            # Read chunks rather than waiting for newline: tqdm often updates with carriage returns.
            buffer = ""
            assert proc.stdout is not None
            while True:
                chunk = proc.stdout.read(1)
                if not chunk:
                    break
                if chunk in ("\r", "\n"):
                    self._parse_output(buffer)
                    buffer = ""
                else:
                    buffer += chunk
                    if len(buffer) > 12000:
                        self._parse_output(buffer[-12000:])
                        buffer = ""
                if self.cancel_event.is_set() and proc.poll() is None:
                    try:
                        proc.terminate()
                    except OSError:
                        pass
            if buffer:
                self._parse_output(buffer)
            exit_code = proc.wait()
        except Exception as exc:
            error = str(exc)
        finally:
            self.process = None
            self.events.put(("done", exit_code, error))

    def _parse_output(self, raw):
        line = ANSI_RE.sub("", raw).strip()
        if not line:
            return
        code = None
        for pattern in CODE_PATTERNS:
            match = pattern.search(line)
            if match:
                candidate = match.group(1)
                if VALID_CODE.fullmatch(candidate):
                    code = candidate
                    break
        if code:
            self.events.put(("code", code))
        progress = PROGRESS_RE.search(line)
        if progress:
            self.events.put(("progress", int(progress.group(1))))
        speed = SPEED_RE.search(line)
        if speed:
            normalized = format_speed(speed.group(1), speed.group(2))
            if normalized:
                self.events.put(("speed", normalized))
        # Don't fill the log with repeated progress-bar redraws.
        if not progress and not speed and not code:
            self.events.put(("log", line[:1500]))

    def _poll_events(self):
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            kind = event[0]
            if kind == "log":
                self._log(event[1])
            elif kind == "code":
                self.code_send.set(event[1])
                self.copy_button.configure(state="normal")
                self.status.set(self.t("waiting"))
            elif kind == "progress":
                value = event[1]
                if self.progress.cget("mode") != "determinate":
                    self.progress.stop()
                    self.progress.configure(mode="determinate")
                self.progress["value"] = value
                self.percent.set(f"{value}%")
                self.status.set(self.t("verifying") if value >= 100 else self.t("transferring"))
            elif kind == "speed":
                self.speed.set(event[1])
            elif kind == "done":
                self._finish(event[1], event[2])
        self.root.after(80, self._poll_events)

    def _finish(self, exit_code, error):
        cancelled = self.cancel_event.is_set()
        self.busy = False
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.cancel_button.configure(state="disabled")
        for control in self._all_controls():
            control.configure(state="normal")
        if cancelled:
            self.status.set(self.t("cancelled"))
            self.percent.set("")
            self.progress["value"] = 0
            self._log(self.t("log_cancel"))
            self._record_history("warning", self.t("log_cancel"), operation=self.operation or "unknown")
        elif error or exit_code != 0:
            self.status.set(self.t("failed"))
            self.percent.set("")
            self.progress["value"] = 0
            self._log(self.t("error") + ": " + (error or f"Wormhole exit code {exit_code}"))
            self._record_history("error", self.t("failed"), operation=self.operation or "unknown", exit_code=exit_code, error=error or "")
        else:
            self.progress["value"] = 100
            self.percent.set("100%")
            self.status.set(self.t("success"))
            self._log(self.t("log_complete"))
            self._record_history("success", self.t("log_complete"), operation=self.operation or "unknown", elapsed_seconds=int(time.monotonic() - self.started_at) if self.started_at else None)
            if self.operation == "receive" and self.receive_dir:
                try:
                    if any(self.receive_dir.iterdir()):
                        self.last_receive_dir = self.receive_dir
                        self.open_button.configure(state="normal")
                    else:
                        self._log(self.t("log_missing"))
                except OSError:
                    pass
        if self.operation == "receive" and self.receive_dir:
            try:
                if not any(self.receive_dir.iterdir()):
                    self.receive_dir.rmdir()
            except OSError:
                pass
        self.receive_dir = None

    def _update_elapsed(self):
        if self.busy and self.started_at:
            seconds = int(time.monotonic() - self.started_at)
            self.elapsed.set(f"{seconds // 60:02d}:{seconds % 60:02d}")
        self.root.after(500, self._update_elapsed)
        self._record_history("info", "log_app_start")

    def _record_history(self, level, message, **details):
        """Append a structured, persistent event to the activity log."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            record = {
                "time": datetime.now().astimezone().isoformat(timespec="seconds"),
                "level": level,
                "message": message,
                "details": details,
            }
            with ACTIVITY_LOG_FILE.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\\n")
        except OSError as exc:
            # Keep logging failures from interrupting file transfers.
            self._log(f"{self.t('error')}: {exc}")

    def _open_history(self):
        """Show persisted history in a separate window."""
        win = tk.Toplevel(self.root)
        win.title(self.t("history"))
        win.geometry("760x420")
        win.minsize(560, 280)
        win.transient(self.root)
        frame = ttk.Frame(win, padding=12)
        frame.pack(fill="both", expand=True)
        viewer = tk.Text(frame, wrap="word", font=("Consolas", 9), state="disabled")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=viewer.yview)
        viewer.configure(yscrollcommand=scroll.set)
        viewer.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        try:
            records = []
            if ACTIVITY_LOG_FILE.is_file():
                with ACTIVITY_LOG_FILE.open("r", encoding="utf-8") as handle:
                    for raw in handle:
                        try:
                            records.append(json.loads(raw))
                        except json.JSONDecodeError:
                            continue
            lines = []
            for item in records[-1000:]:
                detail = item.get("details") or {}
                suffix = " | ".join(f"{key}: {value}" for key, value in detail.items())
                line = f"[{item.get('time', '?')}] [{item.get('level', 'info').upper()}] {item.get('message', '')}"
                if suffix:
                    line += " | " + suffix
                lines.append(line)
            content = "\\n".join(lines) if lines else self.t("history_empty")
        except OSError as exc:
            content = f"{self.t('error')}: {exc}"
        viewer.configure(state="normal")
        viewer.insert("1.0", content)
        viewer.configure(state="disabled")
        viewer.see("end")

    def _log(self, message):
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        # Bound the log size so long sessions don't slow down the UI.
        lines = int(self.log.index("end-1c").split(".")[0])
        if lines > 400:
            self.log.delete("1.0", f"{lines-300}.0")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _cancel(self):
        if not self.busy:
            return
        self.cancel_event.set()
        self.status.set(self.t("cancelled"))
        self.cancel_button.configure(state="disabled")
        proc = self.process
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass
            self.root.after(1800, lambda: self._kill_if_needed(proc))

    @staticmethod
    def _kill_if_needed(proc):
        if proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass

    def _open_folder(self):
        folder = self.last_receive_dir
        if not folder or not folder.is_dir():
            messagebox.showwarning(self.t("error"), self.t("no_folder"))
            return
        try:
            if os.name == "nt":
                os.startfile(str(folder))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except OSError as exc:
            messagebox.showerror(self.t("error"), str(exc))

    def _close(self):
        self._record_history("info", "log_app_close")
        if self.busy:
            if not messagebox.askyesno(self.t("busy_title"), self.t("ask_cancel")):
                return
            self._cancel()
            self.root.after(250, self._wait_close)
            return
        self.root.destroy()

    def _wait_close(self):
        if self.busy:
            self.root.after(250, self._wait_close)
        else:
            self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description="Tkinter arayüzlü Magic Wormhole dosya aktarımı")
    sub = parser.add_subparsers(dest="action")
    send_parser = sub.add_parser("gonder", help="Terminalden dosya/klasör gönder")
    send_parser.add_argument("path", help="Gönderilecek dosya veya klasör yolu")
    receive_parser = sub.add_parser("al", help="Terminalden dosya/klasör al")
    receive_parser.add_argument("--klasor", "-k", default="Gelen_Dosyalar", help="Kayıt klasörü")
    args = parser.parse_args()
    if args.action == "gonder":
        path = Path(clean_path(args.path)).expanduser().resolve()
        if not (path.is_file() or path.is_dir()):
            parser.error(f"Dosya/klasör bulunamadı: {path}")
        return subprocess.run([wormhole_path(), "send", "--code-length", "3", str(path)]).returncode
    if args.action == "al":
        target = Path(clean_path(args.klasor)).expanduser().resolve()
        target.mkdir(parents=True, exist_ok=True)
        return subprocess.run([wormhole_path(), "receive"], cwd=str(target)).returncode
    root = tk.Tk()
    FileTransferApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
