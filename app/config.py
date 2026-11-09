"""Konfigurasi global aplikasi (ubah di sini, tidak perlu menyentuh kode lain)."""
# ============================================================================
# FILE    : app/config.py
# PERAN   : Satu-satunya tempat untuk NILAI PENGATURAN aplikasi: nama, tim,
#           ukuran jendela, perilaku zoom, batas undo, dll.
#           Tampilan warna/font ada di file terpisah: app/theme.py
#
# SIAPA YANG MEMAKAI FILE INI:
#   - app/main_window.py   : judul jendela, ukuran awal, ukuran minimum,
#                            MAX_UNDO, START_MAXIMIZED
#   - app/ui/image_panel.py: FIT_MAX_SCALE (batas perbesaran otomatis)
#   - app/menu_builder.py  : USE_NATIVE_MENUBAR
#   - app/handlers.py      : MEMBERS, GITHUB_URL, YOUTUBE_URL, APP_NAME, dll
#
# PENJELASAN VARIABEL
#   APP_NAME / TEAM_NAME / YEAR : teks judul jendela & dialog "Info Tim".
#        >>> TEAM_NAME masih "Kelompok X": ganti dengan nama kelompokmu.
#   MEMBERS      : daftar anggota (nama + NIM) untuk About > Info Tim Developer.
#   GITHUB_URL / YOUTUBE_URL : tautan menu About > Tutorial.
#        >>> YOUTUBE_URL masih placeholder: ganti dengan link video tutorial.
#
#   --- Ukuran jendela (AUTO-FIT semua ukuran layar) ---
#   WINDOW_SCREEN_FRACTION : jendela awal = sekian persen dari ukuran layar
#        (0.85 = 85%). Layar kecil -> jendela kecil, layar besar -> jendela besar.
#   MIN_WINDOW_SIZE        : ukuran terkecil yang diizinkan (lebar, tinggi) dalam
#        piksel "logis" (nanti dikalikan skala DPI layar). Jika layar sendiri
#        lebih kecil dari ini, ukuran minimum otomatis mengikuti layar.
#   START_MAXIMIZED        : True = jendela langsung dimaksimalkan saat dibuka.
#   Jendela BISA di-resize/maximize oleh user; panel gambar ikut menyesuaikan.
#
#   --- Perilaku panel gambar ---
#   FIT_MAX_SCALE : batas perbesaran saat mode "fit" (auto muat ke panel).
#        1.0 = gambar kecil tidak diperbesar (tetap tajam, 100%).
#        Isi 2.0 / 4.0 jika ingin gambar kecil otomatis diperbesar mengisi panel.
#   ZOOM_MAX      : batas zoom maksimum saat scroll mouse (32 = 3200%).
#   ZOOM_STEP     : pengali zoom per satu "klik" scroll (1.25 = 25% per klik).
#
#   --- Lain-lain ---
#   MAX_UNDO            : jumlah langkah Undo yang disimpan. Tiap langkah menyimpan
#        satu salinan gambar di memori; turunkan jika gambarmu sangat besar.
#   USE_NATIVE_MENUBAR  : False = menu bar bergaya tema gelap buatan sendiri
#        (konsisten di Windows/Linux). True = menu bar bawaan sistem operasi
#        (di Windows warnanya tetap terang, tidak bisa diubah).
# ============================================================================

APP_NAME = "PCD Studio"
TEAM_NAME = "Kelompok X"
YEAR = 2026

MEMBERS = [                        # tampil di About > Info Tim Developer
    {"name": "Muhamad Radityo Pratama", "nim": "2407110908"},
    {"name": "Aulia Arief", "nim": "2407112796"},
    {"name": "Yosia Sitompul", "nim": "2407114019"},
]

GITHUB_URL = "https://github.com/TYO22/proyek-akhir-pcd"
YOUTUBE_URL = "https://www.youtube.com/"

# ---- ukuran jendela (auto-fit) ----
WINDOW_SCREEN_FRACTION = 0.85
MIN_WINDOW_SIZE = (860, 580)
START_MAXIMIZED = False

# ---- panel gambar ----
FIT_MAX_SCALE = 1.0
ZOOM_MAX = 32.0
ZOOM_STEP = 1.25

# ---- lain-lain ----
MAX_UNDO = 10
USE_NATIVE_MENUBAR = False


def window_title() -> str:
    # Dipanggil sekali di MainWindow.__init__ untuk memberi judul jendela.
    # Hasil contoh: "PCD Studio © Kelompok X - (2026)".
    # \u00a9 = kode Unicode untuk simbol © (aman di semua editor).
    return f"{APP_NAME} \u00a9 {TEAM_NAME} - ({YEAR})"


def initial_window_size(screen_w: int, screen_h: int, min_w: int, min_h: int) -> tuple[int, int]:
    """Hitung ukuran jendela awal agar PAS di layar apa pun.

    screen_w/screen_h : ukuran layar (piksel fisik).
    min_w/min_h       : ukuran minimum (sudah dikali skala DPI).
    Aturan: ambil WINDOW_SCREEN_FRACTION dari layar, tapi tidak lebih kecil dari
    minimum (kecuali layarnya sendiri lebih kecil) dan tidak pernah melebihi layar.
    """
    w = int(screen_w * WINDOW_SCREEN_FRACTION)
    h = int(screen_h * WINDOW_SCREEN_FRACTION)
    w = min(screen_w, max(w, min(min_w, screen_w)))
    h = min(screen_h, max(h, min(min_h, screen_h)))
    return w, h
