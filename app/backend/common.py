"""Fungsi bantu BERSAMA untuk semua file backend (konvolusi, filter, warna, FFT, dll).
SETELAH MODIFIKASI: Menggunakan OpenCV (cv2), scikit-image (skimage), dan Pillow
alih-alih implementasi numpy murni, agar lebih cepat dan robust.
"""

from __future__ import annotations

# ============================================================================
# FILE    : app/backend/common.py
# PERAN   : "KOTAK PERKAKAS" untuk algoritma pengolahan citra.
# LIBRARY : cv2 (OpenCV), skimage (scikit-image), PIL (Pillow), numpy
# ============================================================================

import math
import numpy as np
import cv2
from PIL import Image
from skimage import filters as ski_filters
from skimage import exposure as ski_exposure

# Batas jumlah piksel hasil (mencegah memori habis saat zoom/rotasi ekstrem).
MAX_OUTPUT_PIXELS = 60_000_000
# Jika kernel punya lebih dari sekian elemen, konvolusi dihitung lewat FFT (lebih cepat).
FFT_KERNEL_THRESHOLD = 121


# =============================================================================
# KONVERSI DASAR
# =============================================================================
def to_gray(img) -> np.ndarray:
    """RGB (H,W,3) -> abu-abu float32 (H,W). Jika sudah 2D, dikembalikan apa adanya."""
    a = np.asarray(img)
    if a.ndim == 2:
        return a.astype(np.float32)
    # OpenCV memakai BGR, jadi kita konversi RGB->GRAY secara manual dengan bobot ITU-R BT.601
    # atau pakai cv2.cvtColor setelah flip kanal. Untuk akurasi rumus asli, pakai numpy.
    a = a.astype(np.float32)
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def clip_u8(x) -> np.ndarray:
    """Bulatkan lalu batasi ke 0..255 dan ubah ke uint8."""
    return np.clip(np.rint(x), 0, 255).astype(np.uint8)


def scale_max_to_255(x: np.ndarray) -> np.ndarray:
    """Skala linear: nilai terbesar menjadi 255 (nilai 0 tetap 0)."""
    hi = float(np.max(x)) if x.size else 0.0
    if hi <= 1e-12:
        return np.zeros(x.shape, dtype=np.float32)
    return (x / hi * 255.0).astype(np.float32)


def normalize_to_255(x: np.ndarray) -> np.ndarray:
    """Regangkan kontras: min -> 0, max -> 255 (min-max normalization)."""
    lo, hi = float(np.min(x)), float(np.max(x))
    if hi - lo < 1e-12:
        return np.zeros(x.shape, dtype=np.float32)
    return ((x - lo) / (hi - lo) * 255.0).astype(np.float32)


# =============================================================================
# FILTER SPASIAL
# =============================================================================
def pad_reflect(a: np.ndarray, top: int, bottom: int, left: int, right: int) -> np.ndarray:
    """Tambah bingkai di tepi gambar dengan memantulkan piksel."""
    h, w = a.shape[:2]
    widths = [(top, bottom), (left, right)] + [(0, 0)] * (a.ndim - 2)
    mode = "reflect" if max(top, bottom) < h and max(left, right) < w else "edge"
    return np.pad(a, widths, mode=mode)


def correlate2d(a: np.ndarray, kernel) -> np.ndarray:
    """Korelasi 2D menggunakan cv2.filter2D (jauh lebih cepat dari loop numpy)."""
    a = np.asarray(a, dtype=np.float32)
    k = np.asarray(kernel, dtype=np.float32)
    kh, kw = k.shape
    if kh % 2 == 0 or kw % 2 == 0:
        raise ValueError("Ukuran kernel harus ganjil (3x3, 5x5, ...).")
    # anchor=(-1,-1) = pusat kernel otomatis
    # borderType=REFLECT agar tepi tidak hitam
    if a.ndim == 3:
        return cv2.filter2D(a, ddepth=-1, kernel=k,
                            anchor=(-1, -1), borderType=cv2.BORDER_REFLECT)
    return cv2.filter2D(a, ddepth=-1, kernel=k,
                        anchor=(-1, -1), borderType=cv2.BORDER_REFLECT)


def convolve2d(a: np.ndarray, kernel) -> np.ndarray:
    """Konvolusi 2D sejati = korelasi dengan kernel yang dibalik."""
    k = np.asarray(kernel, dtype=np.float32)
    return correlate2d(a, k[::-1, ::-1])


def correlate1d(a: np.ndarray, k, axis: int) -> np.ndarray:
    """Korelasi 1D sepanjang sumbu 0 (vertikal) atau 1 (horizontal)."""
    k = np.asarray(k, dtype=np.float32).ravel()
    a = np.asarray(a, dtype=np.float32)
    # Buat kernel 2D: jika axis=0 -> kolom (size,1); axis=1 -> baris (1,size)
    if axis == 0:
        kernel2d = k.reshape(-1, 1)
    else:
        kernel2d = k.reshape(1, -1)
    return cv2.filter2D(a, ddepth=-1, kernel=kernel2d,
                        anchor=(-1, -1), borderType=cv2.BORDER_REFLECT)


def opencv_sigma(size: int) -> float:
    """Sigma Gaussian otomatis dari ukuran kernel (rumus OpenCV)."""
    return 0.3 * ((size - 1) * 0.5 - 1) + 0.8


def gaussian_kernel_1d(size: int, sigma: float | None = None) -> np.ndarray:
    """Kernel Gaussian 1D yang dinormalisasi (jumlah = 1)."""
    if sigma is None or sigma <= 0:
        sigma = opencv_sigma(size)
    x = np.arange(size, dtype=np.float32) - size // 2
    k = np.exp(-(x * x) / (2.0 * sigma * sigma))
    return (k / k.sum()).astype(np.float32)


def gaussian_blur(a: np.ndarray, sigma: float, size: int | None = None) -> np.ndarray:
    """Blur Gaussian menggunakan cv2.GaussianBlur (sangat cepat, implementasi C++)."""
    a = np.asarray(a, dtype=np.float32)
    if size is None:
        size = max(3, 2 * int(math.ceil(3.0 * sigma)) + 1)
    if size % 2 == 0:
        size += 1
    # ksize harus tuple (width, height), sigma=0 -> dihitung otomatis dari ksize
    return cv2.GaussianBlur(a, (size, size), sigmaX=sigma, sigmaY=sigma,
                            borderType=cv2.BORDER_REFLECT)


def box_filter(a: np.ndarray, size: int) -> np.ndarray:
    """Rata-rata dalam jendela size x size memakai cv2.blur (integral image, sangat cepat)."""
    a = np.asarray(a, dtype=np.float32)
    return cv2.blur(a, (size, size), borderType=cv2.BORDER_REFLECT)


def median_filter(img: np.ndarray, size: int) -> np.ndarray:
    """Filter median menggunakan cv2.medianBlur (implementasi C, sangat cepat)."""
    if size <= 1:
        return img
    # cv2.medianBlur butuh uint8 untuk gambar berwarna
    orig_dtype = img.dtype
    if img.ndim == 3:
        img_u8 = np.clip(np.rint(img), 0, 255).astype(np.uint8)
        out = cv2.medianBlur(img_u8, int(size))
        return out.astype(np.float32) if orig_dtype == np.float32 else out
    else:
        img_u8 = np.clip(np.rint(img), 0, 255).astype(np.uint8)
        out = cv2.medianBlur(img_u8, int(size))
        return out.astype(np.float32) if orig_dtype == np.float32 else out


# =============================================================================
# GEOMETRIK
# =============================================================================
def remap_bilinear(img: np.ndarray, sx: np.ndarray, sy: np.ndarray) -> np.ndarray:
    """Bangun gambar baru dengan cv2.remap + interpolasi bilinear (jauh lebih cepat)."""
    img = np.asarray(img)
    sx = np.asarray(sx, dtype=np.float32)
    sy = np.asarray(sy, dtype=np.float32)
    # cv2.remap butuh map1 (x) dan map2 (y) dengan shape yang sama
    # Koordinat di luar gambar akan jadi hitam (default BORDER_CONSTANT=0)
    if img.ndim == 2:
        return cv2.remap(img, sx, sy, interpolation=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return cv2.remap(img, sx, sy, interpolation=cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))


# =============================================================================
# WARNA
# =============================================================================
def rgb_to_hsv(img) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """RGB (0..255) -> (H, S, V) masing-masing float 0..1, via cv2.cvtColor."""
    a = np.asarray(img)
    if a.dtype != np.uint8:
        a = np.clip(np.rint(a), 0, 255).astype(np.uint8)
    # OpenCV: BGR->HSV menghasilkan H:0-180, S:0-255, V:0-255
    hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV).astype(np.float32)
    h = hsv[..., 0] / 180.0   # normalisasi ke 0..1
    s = hsv[..., 1] / 255.0
    v = hsv[..., 2] / 255.0
    return h, s, v


def hsv_to_rgb(h, s, v) -> np.ndarray:
    """(H, S, V) float 0..1 -> RGB float 0..255 via cv2.cvtColor."""
    h = np.asarray(h, dtype=np.float32)
    s = np.asarray(s, dtype=np.float32)
    v = np.asarray(v, dtype=np.float32)
    # Skala ke range OpenCV: H:0-180, S:0-255, V:0-255
    hsv = np.stack([h * 180.0, s * 255.0, v * 255.0], axis=-1).astype(np.uint8)
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    return rgb.astype(np.float32)


def rgb_to_ycbcr(img) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """RGB -> (Y, Cb, Cr) float, skala 0..255 via cv2.cvtColor (standar JPEG)."""
    a = np.asarray(img)
    if a.dtype != np.uint8:
        a = np.clip(np.rint(a), 0, 255).astype(np.uint8)
    ycrcb = cv2.cvtColor(a, cv2.COLOR_RGB2YCrCb).astype(np.float32)
    return ycrcb[..., 0], ycrcb[..., 1], ycrcb[..., 2]


def ycbcr_to_rgb(y, cb, cr) -> np.ndarray:
    """(Y, Cb, Cr) -> RGB float via cv2.cvtColor."""
    y = np.asarray(y, dtype=np.float32)
    cb = np.asarray(cb, dtype=np.float32)
    cr = np.asarray(cr, dtype=np.float32)
    ycrcb = np.stack([y, cb, cr], axis=-1)
    ycrcb = np.clip(np.rint(ycrcb), 0, 255).astype(np.uint8)
    rgb = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2RGB)
    return rgb.astype(np.float32)


# =============================================================================
# HISTOGRAM
# =============================================================================
def otsu_threshold(gray_u8: np.ndarray) -> int:
    """Metode Otsu via cv2.threshold (implementasi C, cepat & akurat)."""
    g = np.asarray(gray_u8)
    if g.dtype != np.uint8:
        g = np.clip(np.rint(g), 0, 255).astype(np.uint8)
    if g.ndim == 3:
        g = cv2.cvtColor(g, cv2.COLOR_RGB2GRAY)
    thresh, _ = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return int(thresh)


def equalize_u8(ch: np.ndarray) -> np.ndarray:
    """Ekualisasi histogram satu kanal uint8 via cv2.equalizeHist."""
    c = np.asarray(ch)
    if c.dtype != np.uint8:
        c = np.clip(np.rint(c), 0, 255).astype(np.uint8)
    return cv2.equalizeHist(c)


# =============================================================================
# DOMAIN FREKUENSI
# =============================================================================
def filter_in_frequency(img: np.ndarray, h_func, pad: bool = True) -> np.ndarray:
    """Terapkan filter domain frekuensi pada tiap kanal gambar.
    Menggunakan numpy FFT (karena skimage tidak menyediakan API filter frekuensi
    langsung yang cocok dengan kontrak h_func(D) -> H(u,v)).
    """
    a = np.asarray(img, dtype=np.float32)
    m, n = a.shape[:2]
    pp, qq = (2 * m, 2 * n) if (pad and m * n <= 1_500_000) else (m, n)
    u = np.arange(pp, dtype=np.float32) - pp // 2
    v = np.arange(qq, dtype=np.float32) - qq // 2
    dist = np.sqrt(u[:, None] ** 2 + v[None, :] ** 2)
    hf = np.fft.ifftshift(np.asarray(h_func(dist), dtype=np.float32))
    planes = [a] if a.ndim == 2 else [a[..., c] for c in range(a.shape[2])]
    outs = []
    for pl in planes:
        spec = np.fft.fft2(pl, s=(pp, qq))
        outs.append(np.fft.ifft2(spec * hf).real[:m, :n].astype(np.float32))
    return outs[0] if a.ndim == 2 else np.stack(outs, axis=-1)


# =============================================================================
# LAIN-LAIN
# =============================================================================
def load_second_image(path: str, size_wh: tuple[int, int]) -> np.ndarray:
    """Buka 'gambar kedua' dari path, ubah ke RGB, samakan ukuran dengan gambar utama."""
    if not path:
        raise ValueError("Pilih gambar kedua terlebih dahulu (kolom 'Gambar kedua').")
    with Image.open(path) as im:
        im = im.convert("RGB")
        if im.size != tuple(size_wh):
            im = im.resize(tuple(size_wh), Image.Resampling.BILINEAR)
        return np.asarray(im, dtype=np.uint8)


def check_output_size(w: int, h: int) -> None:
    """Lempar error jika ukuran hasil terlalu besar."""
    if w * h > MAX_OUTPUT_PIXELS:
        raise ValueError(f"Hasil terlalu besar ({w}x{h} px). Kurangi faktor zoom/skala.")


def parse_kernel(text: str) -> np.ndarray:
    """Ubah teks kernel 'a b c; d e f; g h i' menjadi matriks numpy float32."""
    rows = [r for r in text.replace("\n", ";").split(";") if r.strip()]
    data = [[float(x) for x in r.replace(",", "  ").split()] for r in rows]
    k = np.array(data, dtype=np.float32)
    if k.ndim != 2 or k.shape[0] % 2 == 0 or k.shape[1] % 2 == 0:
        raise ValueError("Kernel harus berukuran ganjil (3x3, 5x5, ...).")
    return k