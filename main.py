#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tkinter arayuzlu, port yonlendirmesiz dosya/klasor aktarimi.

Gereksinim (iki bilgisayarda da):
    python -m pip install --upgrade "magic-wormhole>=0.23.0"

Arayuz:
    python dosya_aktar.py

Onceki terminal komutlari da calisir:
    python dosya_aktar.py gonder "dosya.zip"
    python dosya_aktar.py gonder "Fotograflar"
    python dosya_aktar.py al
    python dosya_aktar.py al --klasor "Gelen_Dosyalar"
"""

import argparse
from datetime import datetime
import os
from pathlib import Path
import queue
import re
import shutil
import site
import subprocess
import sys
import sysconfig
import tempfile
import threading

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError:
    tk = None
    ttk = None
    filedialog = None
    messagebox = None


# Wormhole CLI ciktilari surumler arasinda degisebildiginden esnek eslestirme.
KOD_DESENI = re.compile(r"\b(?:wormhole\s+code(?:\s+is)?|allocated\s+code)\s*:\s*([0-9]+(?:-[a-zA-Z0-9]+){2,})", re.I)
KOD_GECERLI = re.compile(r"^[0-9]+(?:-[a-zA-Z0-9]+){2,}$")
ILERI_DESENI = re.compile(r"(?<!\d)(100|[1-9]?\d)%\s*\|")
ANSI_DESENI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def wormhole_bul() -> str:
    """Bu Python ortaminin kurulu Wormhole komutunu bul."""
    komut = "wormhole.exe" if os.name == "nt" else "wormhole"
    dizinler = [
        Path(sysconfig.get_path("scripts")),
        Path(site.getuserbase()) / ("Scripts" if os.name == "nt" else "bin"),
    ]
    for dizin in dizinler:
        aday = dizin / komut
        if aday.is_file():
            return str(aday)

    bulunan = shutil.which("wormhole")
    if bulunan:
        return bulunan

    raise RuntimeError(
        "Magic Wormhole kurulu degil. Iki bilgisayarda da terminalde su komutu calistirin:\n\n"
        'python -m pip install --upgrade "magic-wormhole>=0.23.0"'
    )


def yolu_temizle(metin: str) -> str:
    metin = metin.strip()
    if len(metin) >= 2 and metin[0] == metin[-1] and metin[0] in ('"', "'"):
        return metin[1:-1]
    return metin


def varsayilan_hedef() -> Path:
    indirilenler = Path.home() / "Downloads"
    if not indirilenler.is_dir():
        indirilenler = Path.home()
    return indirilenler / "Gelen_Dosyalar"


def cli_gonder(yol_metni: str) -> int:
    yol = Path(yolu_temizle(yol_metni)).expanduser()
    if not (yol.is_file() or yol.is_dir()):
        raise ValueError(f"Dosya/klasor bulunamadi: {yol}")
    print(f"\nGonderiliyor: {yol.resolve()}")
    print("Ekrandaki tek kullanimlik kodu aliciya iletin.\n")
    return subprocess.run(
        [wormhole_bul(), "send", "--code-length", "3", str(yol.resolve())],
        check=False,
    ).returncode


def cli_al(hedef_metni: str) -> int:
    hedef = Path(yolu_temizle(hedef_metni)).expanduser().resolve()
    hedef.mkdir(parents=True, exist_ok=True)
    if not hedef.is_dir():
        raise ValueError(f"Hedef klasor gecersiz: {hedef}")
    print(f"\nDosyalarin kaydedilecegi klasor: {hedef}")
    print("Gonderenin verdigi kodu girin, sorulursa onaylayin.\n")
    return subprocess.run([wormhole_bul(), "receive"], cwd=str(hedef), check=False).returncode


def terminal_menu() -> int:
    print("\n=== KOLAY DOSYA AKTARIMI ===")
    print("1) Dosya / klasor gonder")
    print("2) Dosya / klasor al")
    secim = input("Seciminiz (1/2): ").strip()
    if secim == "1":
        return cli_gonder(input("Gonderilecek yol: "))
    if secim == "2":
        return cli_al(input("Kayit klasoru [Gelen_Dosyalar]: ").strip() or "Gelen_Dosyalar")
    raise ValueError("Gecersiz secim. 1 veya 2 girin.")


class DosyaAktarimArayuzu:
    """Ana Tk arayuzu. Ag islemleri ayri is parcaciginda yurutulur."""

    BG = "#f4f7fb"
    KART = "#ffffff"
    METIN = "#17253c"
    SOLUK = "#64748b"
    MAVI = "#2563eb"
    KENAR = "#dce4ee"

    def __init__(self, root):
        self.root = root
        self.root.title("Kolay Dosya Aktarımı")
        self.root.geometry("780x710")
        self.root.minsize(680, 680)
        self.root.configure(bg=self.BG)

        self.olaylar = queue.Queue()
        self.aktif_islem = None
        self.aktif_surec = None
        self.iptal_sinyali = threading.Event()
        self.mesgul = False
        self.kapatiliyor = False
        self.kayit_klasoru = None
        self.son_kayit_klasoru = None

        self.kaynak = tk.StringVar()
        self.kaynak_bilgi = tk.StringVar(value="Bir dosya ya da klasör seçin.")
        self.kod_gonder = tk.StringVar(value="Kod henüz oluşturulmadı")
        self.kod_al = tk.StringVar()
        self.hedef = tk.StringVar(value=str(varsayilan_hedef()))
        self.durum = tk.StringVar(value="Hazır · Bir işlem seçerek başlayın")
        self.yuzde = tk.StringVar(value="")

        self._stil_ayarla()
        self._arayuz_kur()
        self.kaynak.trace_add("write", self._kaynak_degisince)
        self.root.protocol("WM_DELETE_WINDOW", self._kapat)
        self.root.after(90, self._olaylari_isle)

    def _stil_ayarla(self):
        self.stil = ttk.Style(self.root)
        if "clam" in self.stil.theme_names():
            self.stil.theme_use("clam")

        if sys.platform == "darwin":
            font = "Helvetica Neue"
        elif os.name == "nt":
            font = "Segoe UI"
        else:
            font = "DejaVu Sans"

        self.font = font
        self.stil.configure("App.TFrame", background=self.BG)
        self.stil.configure("Card.TFrame", background=self.KART)
        self.stil.configure("App.TLabel", background=self.BG, foreground=self.METIN, font=(font, 10))
        self.stil.configure("Muted.TLabel", background=self.BG, foreground=self.SOLUK, font=(font, 9))
        self.stil.configure("Card.TLabel", background=self.KART, foreground=self.METIN, font=(font, 10))
        self.stil.configure("CardMuted.TLabel", background=self.KART, foreground=self.SOLUK, font=(font, 9))
        self.stil.configure("Heading.TLabel", background=self.BG, foreground=self.METIN, font=(font, 19, "bold"))
        self.stil.configure("CardTitle.TLabel", background=self.KART, foreground=self.METIN, font=(font, 11, "bold"))
        self.stil.configure("Accent.TLabel", background=self.KART, foreground=self.MAVI, font=(font, 10, "bold"))
        self.stil.configure("TEntry", padding=7, font=(font, 10), fieldbackground="white")
        self.stil.configure("TButton", padding=(10, 8), font=(font, 10))
        self.stil.configure("Primary.TButton", padding=(17, 10), font=(font, 10, "bold"),
                            foreground="white", background=self.MAVI, borderwidth=0)
        self.stil.map("Primary.TButton",
                      background=[("disabled", "#aab7ca"), ("active", "#1d4ed8")],
                      foreground=[("disabled", "#ffffff")])
        self.stil.configure("Danger.TButton", padding=(11, 8), foreground="#b42336")
        self.stil.configure("TNotebook", background=self.KART, borderwidth=0)
        self.stil.configure("TNotebook.Tab", padding=(20, 10), font=(font, 10, "bold"))
        self.stil.configure("Blue.Horizontal.TProgressbar", troughcolor="#e7edf5", background=self.MAVI,
                            bordercolor="#e7edf5", lightcolor=self.MAVI, darkcolor=self.MAVI, thickness=13)

    def _arayuz_kur(self):
        ana = ttk.Frame(self.root, style="App.TFrame", padding=(20, 15))
        ana.pack(fill="both", expand=True)

        ttk.Label(ana, text="Kolay Dosya Aktarımı", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(
            ana,
            text="İki bilgisayar arasında güvenli aktarım · IP ve port yönlendirmesi gerekmez",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(3, 11))

        sekme_kart = ttk.Frame(ana, style="Card.TFrame", padding=10)
        sekme_kart.pack(fill="x")
        self.sekmeler = ttk.Notebook(sekme_kart)
        self.sekmeler.pack(fill="x")

        self.gonder_sekmesi = ttk.Frame(self.sekmeler, style="Card.TFrame", padding=(15, 17))
        self.al_sekmesi = ttk.Frame(self.sekmeler, style="Card.TFrame", padding=(15, 17))
        self.sekmeler.add(self.gonder_sekmesi, text="  Dosya gönder  ")
        self.sekmeler.add(self.al_sekmesi, text="  Dosya al  ")
        self._gonderme_sekmesini_kur()
        self._alma_sekmesini_kur()

        durum_kart = ttk.Frame(ana, style="Card.TFrame", padding=(17, 13))
        durum_kart.pack(fill="both", expand=True, pady=(10, 0))
        baslik_satiri = ttk.Frame(durum_kart, style="Card.TFrame")
        baslik_satiri.pack(fill="x")
        ttk.Label(baslik_satiri, text="Aktarım durumu", style="CardTitle.TLabel").pack(side="left")
        ttk.Label(baslik_satiri, textvariable=self.yuzde, style="Accent.TLabel").pack(side="right")
        ttk.Label(durum_kart, textvariable=self.durum, style="CardMuted.TLabel").pack(anchor="w", pady=(7, 8))
        self.ilerleme = ttk.Progressbar(
            durum_kart, orient="horizontal", mode="determinate", maximum=100,
            style="Blue.Horizontal.TProgressbar",
        )
        self.ilerleme.pack(fill="x", pady=(0, 11))

        log_baslik = ttk.Frame(durum_kart, style="Card.TFrame")
        log_baslik.pack(fill="x", pady=(0, 5))
        ttk.Label(log_baslik, text="İşlem ayrıntıları", style="CardMuted.TLabel").pack(side="left")
        ttk.Button(log_baslik, text="Temizle", command=self._log_temizle).pack(side="right")

        log_alani = ttk.Frame(durum_kart, style="Card.TFrame")
        log_alani.pack(fill="both", expand=True)
        self.log = tk.Text(log_alani, height=4, wrap="word", font=(self.font, 9),
                           bg="#f8fafc", fg=self.METIN, relief="flat", bd=0,
                           highlightthickness=1, highlightbackground=self.KENAR,
                           padx=10, pady=8, state="disabled")
        log_scroll = ttk.Scrollbar(log_alani, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=log_scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

        kontrol = ttk.Frame(ana, style="App.TFrame")
        kontrol.pack(fill="x", pady=(8, 0))
        self.klasor_ac = ttk.Button(kontrol, text="Alınan klasörü aç", command=self._klasor_ac)
        self.klasor_ac.pack(side="left")
        self.klasor_ac.configure(state="disabled")
        self.iptal_buton = ttk.Button(kontrol, text="Aktarımı iptal et", style="Danger.TButton",
                                      command=self._iptal)
        self.iptal_buton.pack(side="right")
        self.iptal_buton.configure(state="disabled")

    def _gonderme_sekmesini_kur(self):
        frame = self.gonder_sekmesi
        ttk.Label(frame, text="1  Göndereceğiniz dosyayı veya klasörü seçin", style="CardTitle.TLabel").pack(anchor="w")
        satir = ttk.Frame(frame, style="Card.TFrame")
        satir.pack(fill="x", pady=(8, 5))
        self.kaynak_girdi = ttk.Entry(satir, textvariable=self.kaynak)
        self.kaynak_girdi.pack(side="left", fill="x", expand=True)
        self.dosya_buton = ttk.Button(satir, text="Dosya seç", command=self._dosya_sec)
        self.dosya_buton.pack(side="left", padx=(7, 0))
        self.dizin_buton = ttk.Button(satir, text="Klasör seç", command=self._kaynak_klasor_sec)
        self.dizin_buton.pack(side="left", padx=(5, 0))
        ttk.Label(frame, textvariable=self.kaynak_bilgi, style="CardMuted.TLabel").pack(anchor="w", pady=(0, 11))

        baslik_satiri = ttk.Frame(frame, style="Card.TFrame")
        baslik_satiri.pack(fill="x")
        ttk.Label(baslik_satiri, text="2  Gönderme kodunu paylaşın", style="CardTitle.TLabel").pack(side="left")
        self.gonder_buton = ttk.Button(baslik_satiri, text="Göndermeyi başlat", style="Primary.TButton",
                                        command=self._gondermeyi_baslat)
        self.gonder_buton.pack(side="right")
        kod_satiri = ttk.Frame(frame, style="Card.TFrame")
        kod_satiri.pack(fill="x", pady=(7, 0))
        self.kod_girdi = ttk.Entry(kod_satiri, textvariable=self.kod_gonder, state="readonly")
        self.kod_girdi.pack(side="left", fill="x", expand=True)
        self.kopyala_buton = ttk.Button(kod_satiri, text="Kodu kopyala", command=self._kod_kopyala)
        self.kopyala_buton.pack(side="left", padx=(7, 0))
        self.kopyala_buton.configure(state="disabled")


    def _alma_sekmesini_kur(self):
        frame = self.al_sekmesi
        ttk.Label(frame, text="1  Gönderen bilgisayardaki kodu girin", style="CardTitle.TLabel").pack(anchor="w")
        self.alma_kod_girdi = ttk.Entry(frame, textvariable=self.kod_al)
        self.alma_kod_girdi.pack(fill="x", pady=(8, 13))
        baslik_satiri = ttk.Frame(frame, style="Card.TFrame")
        baslik_satiri.pack(fill="x")
        ttk.Label(baslik_satiri, text="2  Dosyanın kaydedileceği yeri seçin", style="CardTitle.TLabel").pack(side="left")
        self.al_buton = ttk.Button(baslik_satiri, text="Dosyayı al", style="Primary.TButton",
                                   command=self._almayi_baslat)
        self.al_buton.pack(side="right")
        satir = ttk.Frame(frame, style="Card.TFrame")
        satir.pack(fill="x", pady=(8, 4))
        self.hedef_girdi = ttk.Entry(satir, textvariable=self.hedef)
        self.hedef_girdi.pack(side="left", fill="x", expand=True)
        self.hedef_buton = ttk.Button(satir, text="Göz at", command=self._hedef_sec)
        self.hedef_buton.pack(side="left", padx=(7, 0))
        ttk.Label(frame, text="Mevcut dosyaları korumak için her alım yeni bir alt klasöre kaydedilir.",
                  style="CardMuted.TLabel").pack(anchor="w")

    def _kaynak_degisince(self, *_):
        if self.kaynak.get().strip():
            self.kaynak_bilgi.set("Yol girildi · Gönderme başlamadan önce kontrol edilir")
        else:
            self.kaynak_bilgi.set("Bir dosya ya da klasör seçin.")

    def _dosya_sec(self):
        yol = filedialog.askopenfilename(title="Gönderilecek dosyayı seç")
        if yol:
            self.kaynak.set(yol)
            self.kaynak_bilgi.set(self._boyut_bilgisi(Path(yol)))

    def _kaynak_klasor_sec(self):
        yol = filedialog.askdirectory(title="Gönderilecek klasörü seç")
        if yol:
            self.kaynak.set(yol)
            self.kaynak_bilgi.set("Klasör seçildi · Alt dosyalarıyla birlikte gönderilir")

    def _hedef_sec(self):
        baslangic = self.hedef.get()
        yol = filedialog.askdirectory(title="Kayıt klasörünü seç",
                                      initialdir=baslangic if Path(baslangic).is_dir() else str(Path.home()))
        if yol:
            self.hedef.set(yol)

    @staticmethod
    def _boyut_bilgisi(yol: Path) -> str:
        try:
            boyut = yol.stat().st_size
        except OSError:
            return "Dosya seçildi"
        for birim in ("B", "KB", "MB", "GB", "TB"):
            if boyut < 1024 or birim == "TB":
                return f"Dosya boyutu: {boyut:.1f} {birim}"
            boyut /= 1024
        return "Dosya seçildi"

    def _kod_kopyala(self):
        kod = self.kod_gonder.get()
        if KOD_GECERLI.fullmatch(kod):
            self.root.clipboard_clear()
            self.root.clipboard_append(kod)
            self.durum.set("Kod panoya kopyalandı · Diğer bilgisayara gönderin")

    def _gondermeyi_baslat(self):
        if self.mesgul:
            return
        yol = Path(yolu_temizle(self.kaynak.get())).expanduser()
        if not (yol.is_file() or yol.is_dir()):
            messagebox.showwarning("Dosya seçilmedi", "Lütfen göndereceğiniz dosya veya klasörü seçin.")
            return
        try:
            komut = wormhole_bul()
            yol = yol.resolve()
        except (OSError, RuntimeError) as hata:
            messagebox.showerror("Başlatılamadı", str(hata))
            return

        self.kod_gonder.set("Kod oluşturuluyor...")
        self.kopyala_buton.configure(state="disabled")
        self._baslat("gonder", [komut, "send", "--code-length", "3", str(yol)], None,
                     "Tek kullanımlık kod oluşturuluyor...")
        self._log_ekle(f"Gönderilecek: {yol}")

    def _almayi_baslat(self):
        if self.mesgul:
            return
        kod = self.kod_al.get().strip()
        if not KOD_GECERLI.fullmatch(kod):
            messagebox.showwarning("Kod hatalı", "Örneğin 7-purple-elephant-moon biçiminde bir kod girin.")
            return
        try:
            komut = wormhole_bul()
            hedef = Path(yolu_temizle(self.hedef.get())).expanduser().resolve()
            hedef.mkdir(parents=True, exist_ok=True)
            if not hedef.is_dir():
                raise ValueError("Kayıt konumu bir klasör değil.")
            # Her oturum icin bos bir klasor: --accept-file var olan dosyalari ezemez.
            onek = "Alinan_" + datetime.now().strftime("%Y%m%d_%H%M%S") + "_"
            alt_klasor = Path(tempfile.mkdtemp(prefix=onek, dir=str(hedef)))
        except (ValueError, OSError, RuntimeError) as hata:
            messagebox.showerror("Başlatılamadı", str(hata))
            return

        self.kayit_klasoru = alt_klasor
        self._baslat("al", [komut, "receive", "--accept-file", kod], alt_klasor,
                     "Gönderen bilgisayara bağlanılıyor...")
        self._log_ekle(f"Kayıt klasörü: {alt_klasor}")

    def _baslat(self, islem, komut, calisma_dizini, baslangic_mesaji):
        self.mesgul = True
        self.aktif_islem = islem
        self.iptal_sinyali.clear()
        self.durum.set(baslangic_mesaji)
        self.yuzde.set("")
        self.ilerleme.stop()
        self.ilerleme.configure(mode="indeterminate", value=0)
        self.ilerleme.start(14)
        self._log_temizle()
        self.klasor_ac.configure(state="disabled")
        self.iptal_buton.configure(state="normal")
        for widget in (self.kaynak_girdi, self.dosya_buton, self.dizin_buton, self.gonder_buton,
                       self.alma_kod_girdi, self.hedef_girdi, self.hedef_buton, self.al_buton):
            widget.configure(state="disabled")
        worker = threading.Thread(target=self._calistir, args=(komut, calisma_dizini), daemon=True)
        worker.start()

    def _calistir(self, komut, calisma_dizini):
        surec = None
        hata = None
        kod = 1
        try:
            env = os.environ.copy()
            env["WORMHOLE_QR"] = "0"  # Terminale QR resmi basmasin.
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUNBUFFERED"] = "1"
            secenek = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
            surec = subprocess.Popen(
                komut,
                cwd=str(calisma_dizini) if calisma_dizini else None,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                **secenek,
            )
            self.aktif_surec = surec
            if self.iptal_sinyali.is_set():
                surec.terminate()

            son_yuzde = -1
            assert surec.stdout is not None
            for cikti in surec.stdout:
                satir = ANSI_DESENI.sub("", cikti).strip()
                if not satir:
                    continue
                kod_eslesmesi = KOD_DESENI.search(satir)
                if kod_eslesmesi:
                    self.olaylar.put(("kod", kod_eslesmesi.group(1)))
                ilerleme = ILERI_DESENI.search(satir)
                if ilerleme:
                    sayi = int(ilerleme.group(1))
                    if sayi != son_yuzde:
                        self.olaylar.put(("ilerleme", sayi))
                        son_yuzde = sayi
                    # Tqdm'nin yuzlerce satirini kayit ekraninda gostermeyelim.
                    continue
                self.olaylar.put(("log", satir))
            kod = surec.wait()
        except Exception as exc:
            hata = str(exc)
        finally:
            self.aktif_surec = None
            self.olaylar.put(("bitti", kod, hata))

    def _olaylari_isle(self):
        while True:
            try:
                olay = self.olaylar.get_nowait()
            except queue.Empty:
                break
            tur = olay[0]
            if tur == "log":
                self._log_ekle(olay[1])
            elif tur == "kod":
                self.kod_gonder.set(olay[1])
                self.kopyala_buton.configure(state="normal")
                self.durum.set("Kod hazır · Alıcı bu kodu girene kadar bekleniyor")
            elif tur == "ilerleme":
                if str(self.ilerleme.cget("mode")) != "determinate":
                    self.ilerleme.stop()
                    self.ilerleme.configure(mode="determinate")
                self.ilerleme["value"] = olay[1]
                self.yuzde.set(f"%{olay[1]}")
                self.durum.set("Dosya aktarılıyor..." if olay[1] < 100 else "Aktarım doğrulanıyor...")
            elif tur == "bitti":
                self._islem_bitti(olay[1], olay[2])
        if not self.kapatiliyor or self.mesgul:
            self.root.after(90, self._olaylari_isle)

    def _islem_bitti(self, cikis_kodu, hata):
        iptal = self.iptal_sinyali.is_set()
        self.mesgul = False
        self.ilerleme.stop()
        self.ilerleme.configure(mode="determinate")
        self.iptal_buton.configure(state="disabled")
        for widget in (self.kaynak_girdi, self.dosya_buton, self.dizin_buton, self.gonder_buton,
                       self.alma_kod_girdi, self.hedef_girdi, self.hedef_buton, self.al_buton):
            widget.configure(state="normal")
        if iptal:
            self.durum.set("Aktarım iptal edildi")
            self.yuzde.set("")
            self.ilerleme["value"] = 0
            self._log_ekle("İşlem kullanıcı tarafından iptal edildi.")
        elif hata is not None or cikis_kodu != 0:
            self.durum.set("Aktarım tamamlanamadı · Ayrıntıları kontrol edin")
            self.yuzde.set("")
            self.ilerleme["value"] = 0
            self._log_ekle("Hata: " + (hata or f"Wormhole çıkış kodu {cikis_kodu}"))
        else:
            self.ilerleme["value"] = 100
            self.yuzde.set("%100")
            self.durum.set("Aktarım başarıyla tamamlandı")
            self._log_ekle("Aktarım tamamlandı.")
            if self.aktif_islem == "al" and self.kayit_klasoru:
                if any(self.kayit_klasoru.iterdir()):
                    self.son_kayit_klasoru = self.kayit_klasoru
                    self.klasor_ac.configure(state="normal")
                else:
                    self._log_ekle("Alınan bir dosya bulunamadı (metin aktarılmış olabilir).")

        # Basarisiz/iptal edilen, bos bir aktarim klasoru birakmayalim.
        if self.aktif_islem == "al" and self.kayit_klasoru:
            try:
                if not any(self.kayit_klasoru.iterdir()):
                    self.kayit_klasoru.rmdir()
            except OSError:
                pass
        self.kayit_klasoru = None
        if self.kapatiliyor:
            self.root.destroy()

    def _log_ekle(self, mesaj):
        self.log.configure(state="normal")
        self.log.insert("end", mesaj + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _log_temizle(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _iptal(self):
        if not self.mesgul:
            return
        self.iptal_sinyali.set()
        self.durum.set("Aktarım iptal ediliyor...")
        self.iptal_buton.configure(state="disabled")
        surec = self.aktif_surec
        if surec and surec.poll() is None:
            try:
                surec.terminate()
            except OSError:
                pass
            self.root.after(2000, lambda: self._gerekirse_durdur(surec))

    @staticmethod
    def _gerekirse_durdur(surec):
        if surec.poll() is None:
            try:
                surec.kill()
            except OSError:
                pass

    def _klasor_ac(self):
        klasor = self.son_kayit_klasoru
        if not klasor or not klasor.is_dir():
            messagebox.showwarning("Klasör bulunamadı", "Alınan dosya klasörü bulunamadı.")
            return
        try:
            if os.name == "nt":
                os.startfile(str(klasor))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(klasor)])
            else:
                subprocess.Popen(["xdg-open", str(klasor)])
        except OSError as hata:
            messagebox.showerror("Klasör açılamadı", str(hata))

    def _kapat(self):
        if self.mesgul:
            if not messagebox.askyesno("Aktarım devam ediyor", "Aktarımı iptal edip çıkmak istiyor musunuz?"):
                return
            self.kapatiliyor = True
            self._iptal()
            return
        self.root.destroy()


def arayuz_ac() -> int:
    if tk is None:
        raise RuntimeError("Tkinter bulunamadı. Linux için python3-tk paketini kurun.")
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise RuntimeError(f"Pencere açılamadı. Grafik masaüstü ortamı gerekli: {exc}") from exc
    DosyaAktarimArayuzu(root)
    root.mainloop()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Port forwarding gerektirmeyen, Tkinter arayüzlü dosya aktarımı."
    )
    alt = parser.add_subparsers(dest="islem")
    gp = alt.add_parser("gonder", help="Terminalden dosya/klasor gonder")
    gp.add_argument("yol", help="Gonderilecek dosyanin veya klasorun yolu")
    ap = alt.add_parser("al", help="Terminalden dosya/klasor al")
    ap.add_argument("--klasor", "-k", default="Gelen_Dosyalar", help="Kayit klasoru")
    alt.add_parser("terminal", help="Eski terminal menusunu ac")
    alt.add_parser("gui", help="Tkinter arayuzunu ac")
    args = parser.parse_args()
    try:
        if args.islem == "gonder":
            return cli_gonder(args.yol)
        if args.islem == "al":
            return cli_al(args.klasor)
        if args.islem == "terminal":
            return terminal_menu()
        return arayuz_ac()
    except (ValueError, RuntimeError, OSError) as hata:
        print(f"HATA: {hata}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
