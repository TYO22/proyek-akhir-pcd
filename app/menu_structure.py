"""Struktur menu (dari PDF "Menu structure-Aplikasi-PCD").

Aturan penulisan:
    "Label"            -> item menu (perintah)
    ("Label", [ ... ]) -> submenu
    "-"                -> garis pemisah

ID perintah dibentuk otomatis dari jalur menu (huruf kecil, non-alfanumerik -> "_"):
    Basic Ops > Arithmetic > Add (+)   ->  "basic_ops.arithmetic.add"
    Enhancement > Smoothing > Spatial Domain > Median Filtering
                                       ->  "enhancement.smoothing.spatial_domain.median_filtering"
Daftar lengkap ID bisa dicetak dengan:  python -m app.menu_structure
"""
from __future__ import annotations

import re

SEP = "-"

MENUBAR = [
    ("File", [
        "Open...", "Save", "Save As",
        SEP,
        "Undo", "Redo", "Reset Result",      # tambahan (di luar PDF)
        SEP,
        "Histogram",                          # tambahan (di luar PDF)
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
    # PDF tidak merinci isi menu Segmentation -> tiga item ini adalah ASUMSI tim.
    ("Segmentation", ["Otsu Thresholding", "Adaptive Thresholding", "K-Means Clustering"]),
    ("About", [
        "Info Tim Developer",
        SEP,
        ("Tutorial", ["Link Github", "Link Youtube"]),
    ]),
]

# Pintasan keyboard: id perintah -> teks. Dipasang otomatis oleh menu_builder.
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
    """Hasilkan (command_id, label) untuk semua perintah (daun) di struktur menu."""
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


if __name__ == "__main__":
    for cid, label in iter_commands():
        print(f"{cid:<62} {label}")
