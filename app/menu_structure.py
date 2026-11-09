"""
FILE    : app/menu_structure.py
PERAN   : "PETA MENU" aplikasi. Menyimpan seluruh struktur menu bar (File, 
          Basic Ops, Enhancement, Noise, Edge Detection, Segmentation, About) 
          sebagai DATA. Pembuatan visual menu ditangani oleh app/menu_builder.py.

DIPAKAI OLEH:
    - app/menu_builder.py : Membaca MENUBAR, ACCELERATORS, SEP, dan slug.
    - app/param_specs.py  : Menggunakan ID perintah yang selaras.

KONSEP ID PERINTAH:
    Setiap item menu memiliki ID unik berbasis teks yang dibentuk dari jalur menu 
    (huruf kecil, non-alfanumerik diganti "_"). ID ini menjadi "jembatan" 
    penghubung antara MENU <-> HANDLERS <-> BACKEND <-> PARAM_SPECS.

    Contoh Pembentukan ID:
    - Basic Ops > Arithmetic > Add (+) 
      -> "basic_ops.arithmetic.add"
    - Enhancement > Smoothing > Spatial Domain > Median Filtering
      -> "enhancement.smoothing.spatial_domain.median_filtering"

STRUKTUR UTAMA FILE:
    - SEP          : Penanda garis pemisah menu ("-").
    - MENUBAR      : Data utama menu bar bertingkat (List of Tuple).
    - ACCELERATORS : Kamus {ID: "Teks Pintasan"} untuk tampilan visual menu (mis. "Ctrl+O").
                     Eksekusi pintasan diikat langsung oleh menu_builder.py.

FUNGSI DI FILE INI:
    - slug(text)       : Mengubah teks menu menjadi potongan ID (huruf kecil & underscore).
    - iter_commands()  : Generator rekursif penelusur MENUBAR yang menghasilkan 
                         pasangan (ID, label) untuk seluruh item yang bisa diklik.
    - command_paths()  : Memetakan {ID: "Menu > Submenu > Item"} untuk kebutuhan dokumentasi.

STATUS IMPLEMENTASI:
    Seluruh item menu terhubung ke modul terkait:
    - File / About    -> app/handlers.py (Open, Save, Undo, Redo, dll.)
    - Algoritma Citra -> app/backend/ (basic_ops, enhancement, noise, edge_detection, segmentation)

PENGATURAN & DOKUMENTASI:
    Jalankan `python -m app.menu_structure` untuk mencetak seluruh daftar ID perintah ke layar.
"""

from __future__ import annotations

import re

SEP = "-"

MENUBAR = [
    ("File", [
        "Open...", "Save", "Save As",
        SEP,
        "Undo", "Redo", "Reset Result",
        SEP,
        "Histogram",
        SEP,
        "Exit",
    ]),
    ("Basic Ops", [
        "Negative",
        ("Arithmetic", ["Add (+)", "Substract (-)", "Multiply (*)", "Divide (/)"]),
        ("Boolean", ["NOT", "AND", "OR", "XOR"]),
        ("Geometrics", ["Translation", "Rotation", "Zooming", "Flipping", "Cropping"]),
        "Thresholding",
        "Convolution",
        "Fourier Transform",
        ("Colouring", ["Binary", "Grayscale", "RGB", "HSV", "CMY", "YUV", "YIQ", "Pseudo"]),
    ]),
    ("Enhancement", [
        "Brightness",
        "Contrast",
        "Hist. Equalization",
        ("Smoothing", [
            ("Spatial Domain", ["Lowpass Filtering", "Median Filtering"]),
            ("Frequency Domain", ["ILPF", "BLPF"]),
        ]),
        ("Sharpening", [
            ("Spatial Domain", ["Highpass Filtering", "Highboost Filtering"]),
            ("Frequency Domain", ["IHPF", "BHPF"]),
        ]),
        "Geometrics Correction",
    ]),
    ("Noise", [
        "Gaussian Noise", "Rayleigh Noise", "Erlang (Gamma) Noise",
        "Exponential Noise", "Uniform Noise", "Impulse Noise",
    ]),
    ("Edge Detection", [
        ("1'st Differential Gradient", ["Sobel", "Prewit", "Robert"]),
        ("2'nd Differential Gradient", ["Laplacian", "Laplacian of Gaussian (LoG)", "Canny"]),
        "Compass",
    ]),

    ("Segmentation", ["Otsu Thresholding", "Adaptive Thresholding", "K-Means Clustering"]),

    ("About", [
        "Info Tim Developer",
        SEP,
        ("Tutorial", ["Link Github", "Link Youtube"]),
    ]),
]

ACCELERATORS = {
    "file.open": "Ctrl+O",
    "file.save": "Ctrl+S",
    "file.undo": "Ctrl+Z",
    "file.redo": "Ctrl+Y",
    "file.histogram": "Ctrl+H",
    "file.exit": "Ctrl+Q",
}

def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") 

def iter_commands(children=None, prefix=None):
    if children is None:
        for title, kids in MENUBAR:
            yield from iter_commands(kids, [slug(title)])
        return
    for ch in children:
        if ch == SEP:
            continue
        if isinstance(ch, str):
            yield ".".join(prefix + [slug(ch)]), ch
        else:
            yield from iter_commands(ch[1], prefix + [slug(ch[0])])

def command_paths() -> dict[str, str]:
    out: dict[str, str] = {}

    def walk(children, prefix, labels):
        for ch in children:
            if ch == SEP:
                continue
            if isinstance(ch, str):
                out[".".join(prefix + [slug(ch)])] = " > ".join(labels + [ch])
            else:
                walk(ch[1], prefix + [slug(ch[0])], labels + [ch[0]])

    for title, kids in MENUBAR:
        walk(kids, [slug(title)], [title])
    return out

# Untuk menampilkan daftar ID perintah dan labelnya
if __name__ == "__main__":
    for cid, label in iter_commands():
        print(f"{cid:<62} {label}")
