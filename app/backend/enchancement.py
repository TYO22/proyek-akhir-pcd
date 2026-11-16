"""BACKEND menu "Enhancement": kecerahan, kontras, ekualisasi histogram,
smoothing, sharpening, koreksi geometrik.
Library: OpenCV (operasi inti), NumPy FFT (filter frekuensi)."""

import math
import numpy as np
import cv2
from app.backend import register


# ===========================================================================
# KECERAHAN, KONTRAS, HISTOGRAM
# ===========================================================================
@register("enhancement.brightness")
def brightness(img, beta=40):
    return img.astype(np.float32) + float(beta)


@register("enhancement.contrast")
def contrast(img, alpha=1.5):
    return float(alpha) * (img.astype(np.float32) - 128.0) + 128.0


@register("enhancement.hist_equalization")
def hist_equalization(img, mode="Luminance (YCrCb)"):
    if mode.startswith("Luminance"):
        # Hanya kanal Y (terang) yang diequalize -> warna tetap stabil
        ycrcb = cv2.cvtColor(img, cv2.COLOR_RGB2YCrCb)
        ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
        return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2RGB)
    if mode.startswith("Per kanal"):
        out = np.empty_like(img)
        for i in range(3):
            ch = np.clip(img[:, :, i], 0, 255).astype(np.uint8)
            out[:, :, i] = cv2.equalizeHist(ch)
        return out
    # Grayscale
    gray = np.clip(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), 0, 255).astype(np.uint8)
    return cv2.equalizeHist(gray)


# ===========================================================================
# SMOOTHING - DOMAIN SPASIAL
# ===========================================================================
def _odd(n: int) -> int:
    return n if n % 2 == 1 else n + 1


@register("enhancement.smoothing.spatial_domain.lowpass_filtering")
def lowpass_filtering(img, size=5, kind="Gaussian"):
    size = _odd(int(size))
    f = img.astype(np.float32)
    if kind == "Mean":
        return cv2.blur(f, (size, size))
    # sigma=0 -> OpenCV menghitung sigma otomatis dari size (setara common.opencv_sigma)
    return cv2.GaussianBlur(f, (size, size), 0)


@register("enhancement.smoothing.spatial_domain.median_filtering")
def median_filtering(img, size=3):
    size = _odd(int(size))
    # cv2.medianBlur: uint8 untuk size berapapun; float32 hanya untuk size 3/5
    u8 = np.clip(img, 0, 255).astype(np.uint8)
    return cv2.medianBlur(u8, size).astype(np.float32)


# ===========================================================================
# SMOOTHING - DOMAIN FREKUENSI (via NumPy FFT)
# ===========================================================================
def _distance_grid(shape):
    h, w = shape
    y, x = np.ogrid[:h, :w]
    cy, cx = h / 2.0, w / 2.0
    return np.sqrt((x - cx) ** 2 + (y - cy) ** 2)


def _ideal_lowpass(d0, shape):
    return (_distance_grid(shape) <= d0).astype(np.float32)


def _butterworth_lowpass(d0, n, shape):
    return 1.0 / (1.0 + (_distance_grid(shape) / d0) ** (2 * n))


def _apply_freq_filter(img, h_func):
    """Terapkan filter H(u,v) di domain frekuensi, per kanal."""
    f = img.astype(np.float32)
    out = np.empty_like(f)
    for c in range(3):
        ch = f[:, :, c]
        fshift = np.fft.fftshift(np.fft.fft2(ch))
        H = h_func(fshift.shape)
        gshift = fshift * H
        out[:, :, c] = np.real(np.fft.ifft2(np.fft.ifftshift(gshift)))
    return out


@register("enhancement.smoothing.frequency_domain.ilpf")
def ilpf(img, d0=40):
    return _apply_freq_filter(img, lambda s: _ideal_lowpass(float(d0), s))


@register("enhancement.smoothing.frequency_domain.blpf")
def blpf(img, d0=40, order=2):
    return _apply_freq_filter(img, lambda s: _butterworth_lowpass(float(d0), int(order), s))


# ===========================================================================
# SHARPENING - DOMAIN SPASIAL
# ===========================================================================
_HIGHPASS_KERNEL = np.array([[-1, -1, -1],
                             [-1,  8, -1],
                             [-1, -1, -1]], dtype=np.float32)
_PURE = "Highpass murni"


def _finish_sharpen(img, hp, mode):
    if mode.startswith(_PURE):
        return np.abs(hp)
    return img.astype(np.float32) + hp


@register("enhancement.sharpening.spatial_domain.highpass_filtering")
def highpass_filtering(img, mode="Tambahkan ke citra asli (sharpen)"):
    hp = cv2.filter2D(img.astype(np.float32), -1, _HIGHPASS_KERNEL)
    return _finish_sharpen(img, hp, mode)


@register("enhancement.sharpening.spatial_domain.highboost_filtering")
def highboost_filtering(img, A=1.8, size=5):
    size = _odd(int(size))
    f = img.astype(np.float32)
    blurred = cv2.GaussianBlur(f, (size, size), 0)
    return float(A) * f - blurred


# ===========================================================================
# SHARPENING - DOMAIN FREKUENSI
# ===========================================================================
def _freq_sharpen(img, h_func, mode):
    hp = _apply_freq_filter(img, h_func)
    return _finish_sharpen(img, hp, mode)


@register("enhancement.sharpening.frequency_domain.ihpf")
def ihpf(img, d0=40, mode="Tambahkan ke citra asli (sharpen)"):
    d0 = float(d0)
    return _freq_sharpen(img, lambda s: 1.0 - _ideal_lowpass(d0, s), mode)


@register("enhancement.sharpening.frequency_domain.bhpf")
def bhpf(img, d0=40, order=2, mode="Tambahkan ke citra asli (sharpen)"):
    lp = lambda s: _butterworth_lowpass(float(d0), int(order), s)
    return _freq_sharpen(img, lambda s: 1.0 - lp(s), mode)


# ===========================================================================
# KOREKSI GEOMETRIK (inverse mapping + bilinear interpolation via cv2.remap)
# ===========================================================================
_RADIAL_PREFIX = "Distorsi radial"


@register("enhancement.geometrics_correction")
def geometrics_correction(img, mode="Distorsi radial (barrel/pincushion)", k1=0.2, k2=0.0, shear=5):
    h, w = img.shape[:2]
    ys, xs = np.indices((h, w), dtype=np.float32)
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    if mode.startswith(_RADIAL_PREFIX):
        rad = math.hypot(cx, cy) or 1.0
        xn, yn = (xs - cx) / rad, (ys - cy) / rad
        r2 = xn * xn + yn * yn
        factor = 1.0 + float(k1) * r2 + float(k2) * r2 * r2
        sx, sy = cx + xn * factor * rad, cy + yn * factor * rad
    else:
        sx = xs + math.tan(math.radians(float(shear))) * (ys - cy)
        sy = ys
    return cv2.remap(img,
                     sx.astype(np.float32),
                     sy.astype(np.float32),
                     interpolation=cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT,
                     borderValue=(0, 0, 0))