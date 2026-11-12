"""BACKEND menu "Basic Ops": negatif, aritmetika, boolean, geometrik, threshold, konvolusi, Fourier, warna.
Menggunakan cv2 untuk konvolusi, geometrik, konversi warna, dan operasi aritmetika.
"""
# ============================================================================
# FILE    : app/backend/basic_ops.py
# LIBRARY : cv2 (OpenCV), numpy, PIL
# ============================================================================
from __future__ import annotations
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
    """Negatif citra via cv2.bitwise_not (lebih cepat dari 255 - img)."""
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
    """Pembagian aman via numpy (cv2.divide tidak cocok untuk float arbitrary)."""
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
    """Konvolusi 2D via cv2.filter2D (sangat cepat, implementasi C++)."""
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
# --- Frekuensi & Warna ---
# =============================================================================