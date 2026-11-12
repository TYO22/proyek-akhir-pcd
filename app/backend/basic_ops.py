"""BACKEND menu "Basic Ops": negatif, aritmetika, boolean, geometrik, threshold, konvolusi, Fourier, warna.
Menggunakan cv2 untuk konvolusi, geometrik, konversi warna, dan operasi aritmetika.
"""

from __future__ import annotations

# ============================================================================
# FILE    : app/backend/basic_ops.py
# LIBRARY : cv2 (OpenCV), numpy, PIL
# ============================================================================

import math
import numpy as np
import cv2
from PIL import Image
from app.backend import common as C
from app.backend import register


# =============================================================================
# 1. NEGATIF
# =============================================================================
@register("basic_ops.negative")
def negative(img):
    """Negatif citra via cv2.bitwise_not."""
    return cv2.bitwise_not(np.asarray(img))


# =============================================================================
# 2. ARITMETIKA
# =============================================================================
def _operand(img, mode, value, file):
    """Kembalikan operand: float (Konstanta) atau array gambar kedua float32."""
    if mode == "Gambar kedua":
        h, w = img.shape[:2]
        return C.load_second_image(file, (w, h)).astype(np.float32)
    return float(value)


@register("basic_ops.arithmetic.add")
def add(img, mode="Konstanta", value=50, file=""):
    """Penjumlahan via cv2.add (otomatis clip ke 0..255 untuk uint8)."""
    op = _operand(img, mode, value, file)
    if isinstance(op, np.ndarray):
        return cv2.add(img.astype(np.float32), op)
    return cv2.add(img.astype(np.float32), np.float32(op))


@register("basic_ops.arithmetic.substract")
def substract(img, mode="Konstanta", value=50, file=""):
    """Pengurangan via cv2.subtract (otomatis clip, tidak jadi negatif)."""
    op = _operand(img, mode, value, file)
    if isinstance(op, np.ndarray):
        return cv2.subtract(img.astype(np.float32), op)
    return cv2.subtract(img.astype(np.float32), np.float32(op))


@register("basic_ops.arithmetic.multiply")
def multiply(img, mode="Konstanta", value=1.5, file=""):
    """Perkalian via cv2.multiply (untuk gambar kedua: masking)."""
    f = img.astype(np.float32)
    op = _operand(img, mode, value, file)
    if mode == "Gambar kedua":
        return cv2.multiply(f, op / 255.0)
    return cv2.multiply(f, np.float32(op))


@register("basic_ops.arithmetic.divide")
def divide(img, mode="Konstanta", value=2, file=""):
    """Pembagian aman via numpy."""
    f = img.astype(np.float32)
    if mode == "Gambar kedua":
        g2 = _operand(img, mode, value, file)
        return f / np.maximum(g2 / 255.0, 1.0 / 255.0)
    return f / float(value)


# =============================================================================
# 3. BOOLEAN
# =============================================================================
def _bool_operand(img, mode, value, file):
    """Operand boolean: uint8 konstanta atau gambar kedua uint8."""
    if mode == "Gambar kedua":
        h, w = img.shape[:2]
        return C.load_second_image(file, (w, h))
    return np.uint8(int(value) & 0xFF)


@register("basic_ops.boolean.not")
def bool_not(img):
    """NOT via cv2.bitwise_not."""
    return cv2.bitwise_not(np.asarray(img))


@register("basic_ops.boolean.and")
def bool_and(img, mode="Konstanta", value=128, file=""):
    """AND via cv2.bitwise_and."""
    return cv2.bitwise_and(np.asarray(img), _bool_operand(img, mode, value, file))


@register("basic_ops.boolean.or")
def bool_or(img, mode="Konstanta", value=128, file=""):
    """OR via cv2.bitwise_or."""
    return cv2.bitwise_or(np.asarray(img), _bool_operand(img, mode, value, file))


@register("basic_ops.boolean.xor")
def bool_xor(img, mode="Konstanta", value=128, file=""):
    """XOR via cv2.bitwise_xor."""
    return cv2.bitwise_xor(np.asarray(img), _bool_operand(img, mode, value, file))



# =============================================================================
# 4. GEOMETRIK
# =============================================================================
@register("basic_ops.geometrics.translation")
def translation(img, dx=30, dy=30):
    """Translasi via cv2.warpAffine (lebih cepat, interpolasi otomatis)."""
    h, w = img.shape[:2]
    dx, dy = int(dx), int(dy)
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=0)


@register("basic_ops.geometrics.rotation")
def rotation(img, angle=30, scale=1.0, expand="Ya"):
    """Rotasi via cv2.getRotationMatrix2D + warpAffine (inverse mapping otomatis)."""
    h, w = img.shape[:2]
    angle_f, scale_f = float(angle), float(scale)
    cx_in, cy_in = (w - 1) / 2.0, (h - 1) / 2.0
    # cv2.getRotationMatrix2D: angle positif = berlawanan arah jarum jam (sesuai ekspektasi)
    if expand == "Ya":
        cos_t = abs(math.cos(math.radians(angle_f)))
        sin_t = abs(math.sin(math.radians(angle_f)))
        out_w = int(math.ceil((w * cos_t + h * sin_t) * scale_f))
        out_h = int(math.ceil((w * sin_t + h * cos_t) * scale_f))
        cx_out, cy_out = (out_w - 1) / 2.0, (out_h - 1) / 2.0
        # Matriks rotasi dengan pusat baru + translasi ke pusat output
        M = cv2.getRotationMatrix2D((cx_in, cy_in), angle_f, scale_f)
        M[0, 2] += (cx_out - cx_in)
        M[1, 2] += (cy_out - cy_in)
    else:
        out_w, out_h = w, h
        M = cv2.getRotationMatrix2D((cx_in, cy_in), angle_f, scale_f)
    C.check_output_size(out_w, out_h)
    return cv2.warpAffine(img, M, (out_w, out_h),
                          flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)


_RESAMPLE_CV2 = {
    "Nearest": cv2.INTER_NEAREST,
    "Bilinear": cv2.INTER_LINEAR,
    "Bicubic": cv2.INTER_CUBIC,
    "Lanczos": cv2.INTER_LANCZOS4,
}


@register("basic_ops.geometrics.zooming")
def zooming(img, factor=1.5, interpolation="Bilinear"):
    """Zoom via cv2.resize (jauh lebih cepat dari PIL untuk ukuran besar)."""
    h, w = img.shape[:2]
    nw, nh = max(1, int(round(w * float(factor)))), max(1, int(round(h * float(factor))))
    C.check_output_size(nw, nh)
    interp = _RESAMPLE_CV2.get(interpolation, cv2.INTER_LINEAR)
    return cv2.resize(img, (nw, nh), interpolation=interp)


@register("basic_ops.geometrics.flipping")
def flipping(img, mode="Horizontal"):
    """Flip via cv2.flip."""
    if mode == "Horizontal":
        return cv2.flip(img, 1)
    if mode == "Vertical":
        return cv2.flip(img, 0)
    return cv2.flip(img, -1)  # Horizontal + Vertical


@register("basic_ops.geometrics.cropping")
def cropping(img, left=10, top=10, right=90, bottom=90):
    """Crop: ambil persegi panjang dengan batas dalam PERSEN."""
    h, w = img.shape[:2]
    x0 = int(round(w * float(left) / 100.0))
    x1 = int(round(w * float(right) / 100.0))
    y0 = int(round(h * float(top) / 100.0))
    y1 = int(round(h * float(bottom) / 100.0))
    x1, y1 = max(x1, x0 + 1), max(y1, y0 + 1)
    return img[y0:y1, x0:x1].copy()


# =============================================================================
# 5. THRESHOLDING
# =============================================================================
@register("basic_ops.thresholding")
def thresholding(img, threshold=128, kind="Binary"):
    """Thresholding via cv2.threshold (untuk Binary/Binary Inverse)."""
    t = float(threshold)
    if kind == "Binary":
        gray = C.to_gray(img)
        _, out = cv2.threshold(gray.astype(np.float32), t, 255, cv2.THRESH_BINARY)
        return out
    if kind == "Binary Inverse":
        gray = C.to_gray(img)
        _, out = cv2.threshold(gray.astype(np.float32), t, 255, cv2.THRESH_BINARY_INV)
        return out
    if kind == "Truncate":
        return np.minimum(img, np.uint8(int(t)))
    # To Zero
    return np.where(img > t, img, 0)


# =============================================================================
# 6. KONVOLUSI
# =============================================================================
_PRESET_KERNELS = {
    "Box Blur 3x3": np.ones((3, 3), np.float32) / 9.0,
    "Gaussian 3x3": np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], np.float32) / 16.0,
    "Sharpen": np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], np.float32),
    "Emboss": np.array([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]], np.float32),
    "Laplacian": np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], np.float32),
}


@register("basic_ops.convolution")
def convolution(img, preset="Sharpen", custom="0 -1 0; -1 5 -1; 0 -1 0", normalize="Tidak"):
    """Konvolusi 2D via cv2.filter2D."""
    k = C.parse_kernel(custom) if preset == "Custom" else _PRESET_KERNELS[preset].copy()
    if normalize == "Ya":
        s = float(k.sum())
        if abs(s) > 1e-9:
            k = k / s
    # cv2.filter2D melakukan korelasi; untuk konvolusi sejati kernel harus dibalik
    out = cv2.filter2D(img.astype(np.float32), ddepth=-1, kernel=k[::-1, ::-1],
                       borderType=cv2.BORDER_REFLECT)
    if abs(float(k.sum())) < 1e-6:
        out = np.abs(out)
    return out



# =============================================================================
# 7. TRANSFORMASI FOURIER
# =============================================================================
@register("basic_ops.fourier_transform")
def fourier_transform(img, view="Magnitude (log)"):
    """FFT 2D via numpy."""
    spectrum = np.fft.fftshift(np.fft.fft2(C.to_gray(img)))
    if view.startswith("Magnitude"):
        return C.normalize_to_255(np.log1p(np.abs(spectrum)))
    return (np.angle(spectrum) + math.pi) / (2 * math.pi) * 255.0


# =============================================================================
# 8. COLOURING
# =============================================================================
@register("basic_ops.colouring.binary")
def colouring_binary(img, method="Manual", threshold=128):
    """Binerisasi via cv2.threshold (Otsu otomatis atau manual)."""
    gray = C.clip_u8(C.to_gray(img))
    if method.startswith("Otsu"):
        _, out = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        _, out = cv2.threshold(gray, int(threshold), 255, cv2.THRESH_BINARY)
    return out > 0


@register("basic_ops.colouring.grayscale")
def colouring_grayscale(img):
    """Abu-abu via cv2.cvtColor (lebih cepat)."""
    a = np.asarray(img)
    if a.dtype != np.uint8:
        a = np.clip(np.rint(a), 0, 255).astype(np.uint8)
    return cv2.cvtColor(a, cv2.COLOR_RGB2GRAY).astype(np.float32)


def _pick(planes, names, view):
    """Pilih tampilan: Komposit = RGB, selain itu satu kanal."""
    if view == "Komposit":
        return np.stack(planes, axis=-1)
    return planes[names.index(view)]


@register("basic_ops.colouring.rgb")
def colouring_rgb(img, view="Asli"):
    if view == "Asli":
        return img
    return img[..., ("Red", "Green", "Blue").index(view)]


@register("basic_ops.colouring.hsv")
def colouring_hsv(img, view="Komposit"):
    """HSV via cv2.cvtColor."""
    h, s, v = C.rgb_to_hsv(img)
    return _pick([h * 255.0, s * 255.0, v * 255.0], ["Hue", "Saturation", "Value"], view)


@register("basic_ops.colouring.cmy")
def colouring_cmy(img, view="Komposit"):
    a = img.astype(np.float32)
    return _pick([255.0 - a[..., 0], 255.0 - a[..., 1], 255.0 - a[..., 2]],
                 ["Cyan", "Magenta", "Yellow"], view)


@register("basic_ops.colouring.yuv")
def colouring_yuv(img, view="Komposit"):
    a = img.astype(np.float32)
    y = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    u = 0.492 * (a[..., 2] - y)
    v = 0.877 * (a[..., 0] - y)
    return _pick([y, (u + 111.2) / 222.4 * 255.0, (v + 156.8) / 313.6 * 255.0],
                 ["Y", "U", "V"], view)


@register("basic_ops.colouring.yiq")
def colouring_yiq(img, view="Komposit"):
    a = img.astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    y = 0.299 * r + 0.587 * g + 0.114 * b
    i = 0.595716 * r - 0.274453 * g - 0.321263 * b
    q = 0.211456 * r - 0.522591 * g + 0.311135 * b
    return _pick([y, (i + 151.9) / 303.8 * 255.0, (q + 133.3) / 266.6 * 255.0],
                 ["Y", "I", "Q"], view)


# --- Pseudo-colour (colormap) ---
_CMAP_STOPS = {
    "Jet": [(0.0, 0, 0, 128), (0.125, 0, 0, 255), (0.375, 0, 255, 255),
            (0.625, 255, 255, 0), (0.875, 255, 0, 0), (1.0, 128, 0, 0)],
    "Hot": [(0.0, 0, 0, 0), (0.365, 255, 0, 0), (0.746, 255, 255, 0), (1.0, 255, 255, 255)],
    "Ocean": [(0.0, 0, 128, 0), (0.35, 0, 70, 150), (0.7, 90, 170, 215), (1.0, 255, 255, 255)],
    "Cool": [(0.0, 0, 255, 255), (1.0, 255, 0, 255)],
    "Bone": [(0.0, 0, 0, 0), (0.37, 80, 80, 113), (0.75, 166, 198, 198), (1.0, 255, 255, 255)],
    "Turbo": [(0.0, 48, 18, 59), (0.125, 68, 111, 222), (0.25, 35, 191, 222), (0.375, 70, 248, 132),
              (0.5, 162, 252, 60), (0.625, 225, 221, 55), (0.75, 254, 146, 42),
              (0.875, 217, 56, 6), (1.0, 122, 4, 3)],
    "Viridis": [(0.0, 68, 1, 84), (0.111, 72, 40, 120), (0.222, 62, 73, 137), (0.333, 49, 104, 142),
                (0.444, 38, 130, 142), (0.556, 31, 158, 137), (0.667, 53, 183, 121),
                (0.778, 110, 206, 88), (0.889, 181, 222, 43), (1.0, 253, 231, 37)],
}


def _build_lut(name: str) -> np.ndarray:
    """Bangun tabel 256 warna (256,3) untuk colormap."""
    t = np.linspace(0.0, 1.0, 256, dtype=np.float32)
    if name == "Rainbow":
        return C.hsv_to_rgb((1.0 - t) * 0.75, np.ones(256, np.float32), np.ones(256, np.float32))
    stops = np.array(_CMAP_STOPS[name], dtype=np.float32)
    return np.stack([np.interp(t, stops[:, 0], stops[:, c]) for c in (1, 2, 3)], axis=-1)


@register("basic_ops.colouring.pseudo")
def colouring_pseudo(img, cmap="Jet"):
    """Pseudo-color via LUT."""
    gray = C.clip_u8(C.to_gray(img))
    return _build_lut(cmap)[gray]