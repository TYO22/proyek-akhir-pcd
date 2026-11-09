"""Tema tampilan (warna, font, ukuran) untuk seluruh GUI. UBAH DI SINI untuk mengganti desain."""
# ============================================================================
# FILE    : app/theme.py
# PERAN   : PUSAT DESAIN GUI. Semua warna, font, dan gaya widget ada di file ini.
#           Karena semua file UI mengambil warna dari sini, kamu cukup mengubah
#           file ini untuk mengganti tampilan seluruh aplikasi.
#
# ---------------------------------------------------------------------------
# CARA MENGUBAH DESAIN (paling sering dipakai)
# ---------------------------------------------------------------------------
#   1. Ganti tema bawaan : ubah ACTIVE_THEME di bawah, mis. "Midnight" /
#                          "Graphite" / "Light". (Atau tanpa edit file:
#                          jalankan dengan  PCD_THEME=Midnight python main.py)
#   2. Ubah warna        : edit nilai hex di dalam THEMES (mis. "accent").
#   3. Buat tema sendiri : salin satu blok tema di THEMES, beri nama baru,
#                          ubah warnanya, lalu isi ACTIVE_THEME dengan nama itu.
#   4. Ganti font/ukuran : ubah FONT_CANDIDATES (urutan prioritas font) dan
#                          BASE_FONT_SIZE (ukuran dasar dalam poin).
#
# ---------------------------------------------------------------------------
# ARTI SETIAP KUNCI WARNA DI TEMA
# ---------------------------------------------------------------------------
#   bg          : latar jendela utama & dialog
#   surface     : latar menu, panel gambar, judul panel
#   surface_alt : latar status bar, tombol, elemen yang "naik" sedikit
#   field       : latar kotak input (Entry/Spinbox/Combobox)
#   canvas      : latar area gambar (tempat gambar ditampilkan)
#   border      : garis tepi / pemisah
#   fg          : warna teks utama
#   fg_dim      : teks sekunder / non-aktif
#   accent      : warna aksen (tombol utama, seleksi menu, fokus)
#   accent_fg   : warna teks di atas aksen
#   hover       : warna saat kursor di atas tombol/menu
#   select      : warna blok seleksi teks
#   hist_r / hist_g / hist_b / hist_gray : warna garis jendela histogram
#
# ---------------------------------------------------------------------------
# FUNGSI YANG DIPAKAI FILE LAIN
# ---------------------------------------------------------------------------
#   enable_hidpi()      : dipanggil di main.py SEBELUM jendela dibuat. Di Windows
#                         membuat aplikasi "sadar DPI" sehingga teks & gambar TAJAM
#                         di layar resolusi tinggi (tidak blur/di-upscale oleh Windows).
#   apply_theme(root)   : dipanggil di MainWindow. Menghitung skala DPI, mengatur
#                         font, gaya ttk, dan warna menu/dialog.
#   style_window(win)   : dipanggil untuk jendela tambahan (dialog, histogram).
#   color(name)         : ambil satu warna dari tema aktif, mis. color("accent").
#   colors()            : seluruh dict warna tema aktif.
#   font(delta, bold)   : tuple font siap pakai, mis. font(2, True) = lebih besar & tebal.
#   px(n)               : ubah ukuran "piksel logis" jadi piksel nyata sesuai DPI layar.
#                         Pakai px() untuk jarak/padding agar proporsional di layar besar.
# ============================================================================

from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# --------------------------------------------------------------------------- tema
# Nama tema yang dipakai. Bisa ditimpa lewat variabel lingkungan PCD_THEME.
ACTIVE_THEME = "Dark Slate"

THEMES: dict[str, dict[str, str]] = {
    # Biru-abu gelap yang tenang. Gelap tapi tidak hitam pekat (nyaman di mata).
    "Dark Slate": {
        "bg": "#232831", "surface": "#2b313c", "surface_alt": "#343b49", "field": "#1c2029",
        "canvas": "#171a20", "border": "#444c5c",
        "fg": "#e6e9ef", "fg_dim": "#9ba5b6",
        "accent": "#6cb2eb", "accent_fg": "#0f1823", "hover": "#3c4455", "select": "#3d6a94",
        "hist_r": "#ff7b7b", "hist_g": "#6fd99a", "hist_b": "#6aaeff", "hist_gray": "#d9dde5",
    },
    # Lebih biru-ungu dan lebih gelap.
    "Midnight": {
        "bg": "#1a1d2b", "surface": "#222639", "surface_alt": "#2d324b", "field": "#141623",
        "canvas": "#0f1120", "border": "#3b4163",
        "fg": "#e3e6f5", "fg_dim": "#8f97bf",
        "accent": "#8b9bff", "accent_fg": "#10132a", "hover": "#343a5a", "select": "#4a56a6",
        "hist_r": "#ff7b8a", "hist_g": "#79e0a6", "hist_b": "#7fb0ff", "hist_gray": "#dfe3f5",
    },
    # Abu-abu netral dengan aksen kuning-amber.
    "Graphite": {
        "bg": "#262626", "surface": "#2f2f2f", "surface_alt": "#393939", "field": "#1e1e1e",
        "canvas": "#181818", "border": "#4a4a4a",
        "fg": "#e8e8e8", "fg_dim": "#a1a1a1",
        "accent": "#e0a458", "accent_fg": "#1c1408", "hover": "#414141", "select": "#85683a",
        "hist_r": "#ff8080", "hist_g": "#7edb9c", "hist_b": "#7ab4ff", "hist_gray": "#e0e0e0",
    },
    # Contoh tema terang (bukti bahwa semua warna bisa diganti lewat file ini).
    "Light": {
        "bg": "#f1f2f5", "surface": "#ffffff", "surface_alt": "#e5e8ed", "field": "#ffffff",
        "canvas": "#d8dce2", "border": "#c2c7d0",
        "fg": "#1f2430", "fg_dim": "#6a7282",
        "accent": "#2f6fb2", "accent_fg": "#ffffff", "hover": "#dce1e9", "select": "#b8d2ee",
        "hist_r": "#d62728", "hist_g": "#2ca02c", "hist_b": "#1f77b4", "hist_gray": "#333333",
    },
}

# Font dicoba dari atas ke bawah; yang pertama tersedia di komputer dipakai.
FONT_CANDIDATES = ("Segoe UI", "SF Pro Text", "Inter", "Helvetica Neue", "Noto Sans",
                   "DejaVu Sans", "Arial")
BASE_FONT_SIZE = 10          # ukuran dasar (poin). Naikkan jika teks terasa kecil.

# State internal modul (skala DPI & nama font terpilih). Diisi oleh apply_theme().
_state = {"scale": 1.0, "family": "TkDefaultFont"}


def active_name() -> str:
    """Nama tema aktif: PCD_THEME (jika ada & valid) atau ACTIVE_THEME."""
    name = os.environ.get("PCD_THEME", ACTIVE_THEME)
    return name if name in THEMES else ACTIVE_THEME


def colors() -> dict[str, str]:
    """Seluruh warna tema aktif (dict)."""
    return THEMES[active_name()]


def color(name: str) -> str:
    """Satu warna dari tema aktif. Contoh: color('accent')."""
    return colors()[name]


def px(n: float) -> int:
    """Ubah piksel logis -> piksel nyata sesuai skala DPI layar (minimal 1)."""
    return max(1, int(round(n * _state["scale"])))


def font(delta: int = 0, bold: bool = False, italic: bool = False) -> tuple:
    """Tuple font untuk parameter font= widget. delta = tambahan ukuran dari BASE_FONT_SIZE."""
    style = " ".join(s for s, on in (("bold", bold), ("italic", italic)) if on)
    base = (_state["family"], BASE_FONT_SIZE + delta)
    return base + (style,) if style else base


def enable_hidpi() -> None:
    """Aktifkan mode sadar-DPI di Windows (panggil SEBELUM membuat jendela Tk)."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)   # per-monitor DPI
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()        # cadangan untuk Windows lama
    except Exception:
        pass                                                 # gagal -> tampil seperti biasa


def _is_dark(hex_color: str) -> bool:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return (0.299 * r + 0.587 * g + 0.114 * b) < 128


def set_dark_titlebar(win) -> None:
    """Windows 10/11: buat title bar jendela ikut gelap/terang sesuai tema (aman jika gagal)."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        value = ctypes.c_int(1 if _is_dark(color("bg")) else 0)
        for attr in (20, 19):                                # 20 = Win11/10 baru, 19 = Win10 lama
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)) == 0:
                break
    except Exception:
        pass


def style_window(win) -> None:
    """Terapkan warna latar tema + title bar gelap ke jendela tambahan (Toplevel)."""
    win.configure(bg=color("bg"))
    set_dark_titlebar(win)


def apply_theme(root: tk.Tk) -> None:
    """Terapkan tema ke seluruh aplikasi. Panggil sekali, tepat setelah tk.Tk() dibuat."""
    c = colors()

    # 1) Skala DPI: 96 dpi = 1.0, 144 dpi = 1.5, 192 dpi = 2.0, dst.
    _state["scale"] = max(1.0, root.winfo_fpixels("1i") / 96.0)

    # 2) Pilih font pertama yang ada, lalu terapkan ke semua "font bernama" Tk.
    families = set(tkfont.families(root))
    _state["family"] = next((f for f in FONT_CANDIDATES if f in families), "TkDefaultFont")
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont",
                 "TkCaptionFont", "TkSmallCaptionFont", "TkTooltipFont"):
        try:
            tkfont.nametofont(name).configure(family=_state["family"], size=BASE_FONT_SIZE)
        except tk.TclError:
            pass

    root.configure(bg=c["bg"])

    # 3) Gaya widget ttk. Tema "clam" dipilih karena paling mudah diwarnai.
    st = ttk.Style(root)
    st.theme_use("clam")
    st.configure(".", background=c["bg"], foreground=c["fg"], fieldbackground=c["field"],
                 bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"],
                 troughcolor=c["field"], focuscolor=c["accent"], insertcolor=c["fg"],
                 selectbackground=c["select"], selectforeground=c["fg"], font=font())

    st.configure("TFrame", background=c["bg"])
    st.configure("Panel.TFrame", background=c["surface"])
    st.configure("Status.TFrame", background=c["surface_alt"], relief="flat")
    st.configure("TLabel", background=c["bg"], foreground=c["fg"])
    st.configure("Dim.TLabel", foreground=c["fg_dim"])
    st.configure("Heading.TLabel", font=font(3, True))
    st.configure("Panel.TLabel", background=c["surface"], foreground=c["fg"])
    st.configure("PanelTitle.TLabel", background=c["surface"], foreground=c["fg"], font=font(0, True))
    st.configure("PanelInfo.TLabel", background=c["surface"], foreground=c["fg_dim"], font=font(-1))
    st.configure("Status.TLabel", background=c["surface_alt"], foreground=c["fg"], font=font(-1))

    st.configure("TButton", background=c["surface_alt"], foreground=c["fg"], borderwidth=1,
                 focusthickness=1, padding=(px(16), px(6)), relief="flat")
    st.map("TButton", background=[("pressed", c["accent"]), ("active", c["hover"])],
           foreground=[("pressed", c["accent_fg"]), ("disabled", c["fg_dim"])])
    st.configure("Accent.TButton", background=c["accent"], foreground=c["accent_fg"])
    st.map("Accent.TButton", background=[("pressed", c["fg"]), ("active", c["accent"])],
           foreground=[("pressed", c["bg"]), ("disabled", c["fg_dim"])])

    for cls in ("TEntry", "TSpinbox", "TCombobox"):
        st.configure(cls, fieldbackground=c["field"], foreground=c["fg"], background=c["surface_alt"],
                     arrowcolor=c["fg"], bordercolor=c["border"], insertcolor=c["fg"],
                     selectbackground=c["select"], selectforeground=c["fg"], padding=px(4))
        st.map(cls, fieldbackground=[("disabled", c["surface"]), ("readonly", c["field"])],
               foreground=[("disabled", c["fg_dim"])],
               selectbackground=[("readonly", c["field"])], selectforeground=[("readonly", c["fg"])],
               bordercolor=[("focus", c["accent"])], arrowcolor=[("disabled", c["fg_dim"])])

    st.configure("TCheckbutton", background=c["bg"], foreground=c["fg"], indicatorcolor=c["field"])
    st.map("TCheckbutton", background=[("active", c["bg"])],
           indicatorcolor=[("selected", c["accent"]), ("pressed", c["hover"])],
           foreground=[("disabled", c["fg_dim"])])
    st.configure("TSeparator", background=c["border"])
    st.configure("TScrollbar", background=c["surface_alt"], troughcolor=c["field"], arrowcolor=c["fg"])

    # 4) Widget Tk klasik (bukan ttk): menu, daftar dropdown, dialog.
    opt = root.option_add
    opt("*Menu.background", c["surface"])
    opt("*Menu.foreground", c["fg"])
    opt("*Menu.activeBackground", c["accent"])
    opt("*Menu.activeForeground", c["accent_fg"])
    opt("*Menu.disabledForeground", c["fg_dim"])
    opt("*Menu.relief", "flat")
    opt("*Menu.borderWidth", 1)
    opt("*Menu.activeBorderWidth", 0)
    opt("*Menu.selectColor", c["accent"])
    opt("*Menu.font", font())
    opt("*TCombobox*Listbox.background", c["field"])
    opt("*TCombobox*Listbox.foreground", c["fg"])
    opt("*TCombobox*Listbox.selectBackground", c["accent"])
    opt("*TCombobox*Listbox.selectForeground", c["accent_fg"])
    opt("*TCombobox*Listbox.font", font())
    opt("*Toplevel.background", c["bg"])

    set_dark_titlebar(root)
