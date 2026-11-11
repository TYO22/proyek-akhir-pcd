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
# --- Spasial & Filter ---
# =============================================================================



# =============================================================================
# --- Frekuensi & Warna ---
# =============================================================================