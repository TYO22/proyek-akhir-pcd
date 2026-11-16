"""BACKEND menu "Edge Detection": Sobel, Prewitt, Roberts, Laplacian, LoG, Canny, Compass (Kirsch).
Menggunakan OpenCV (filter2D, Laplacian, Canny, GaussianBlur) + kernel manual untuk Kirsch."""

import math
import numpy as np
import cv2
from app.backend import register

# ---------------------------------------------------------------------------
# Kernel operator tepi (orde pertama)
# ---------------------------------------------------------------------------
_SOBEL_GX = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
_SOBEL_GY = _SOBEL_GX.T
_PREWITT_GX = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], dtype=np.float32)
_PREWITT_GY = _PREWITT_GX.T
_ROBERTS_GX = np.array([[0, 0, 0], [0, 1, 0], [0, 0, -1]], dtype=np.float32)
_ROBERTS_GY = np.array([[0, 0, 0], [0, 0, 1], [0, -1, 0]], dtype=np.float32)


def _finish(strength: np.ndarray, threshold):
    """Skala kekuatan tepi ke 0..255, lalu (jika threshold > 0) ubah jadi peta hitam-putih."""
    s = strength.astype(np.float32)
    mx = float(s.max())
    out = (s / mx * 255.0) if mx > 0 else np.zeros_like(s, dtype=np.float32)
    if float(threshold) > 0:
        return out > float(threshold)
    return out


def _gradient_edges(img, kx, ky, direction, threshold):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    gx = cv2.filter2D(gray, -1, kx)
    gy = cv2.filter2D(gray, -1, ky)
    if direction.startswith("Horizontal"):
        strength = np.abs(gx)
    elif direction.startswith("Vertical"):
        strength = np.abs(gy)
    else:
        strength = np.hypot(gx, gy)
    return _finish(strength, threshold)


@register("edge_detection.1_st_differential_gradient.sobel")
def sobel(img, direction="Magnitude", threshold=0):
    return _gradient_edges(img, _SOBEL_GX, _SOBEL_GY, direction, threshold)


@register("edge_detection.1_st_differential_gradient.prewit")
def prewit(img, direction="Magnitude", threshold=0):
    return _gradient_edges(img, _PREWITT_GX, _PREWITT_GY, direction, threshold)


@register("edge_detection.1_st_differential_gradient.robert")
def robert(img, direction="Magnitude", threshold=0):
    return _gradient_edges(img, _ROBERTS_GX, _ROBERTS_GY, direction, threshold)


# ---------------------------------------------------------------------------
# Orde kedua
# ---------------------------------------------------------------------------
@register("edge_detection.2_nd_differential_gradient.laplacian")
def laplacian(img, neighbors="8-tetangga", threshold=0):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    if neighbors.startswith("4"):
        k = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
        resp = cv2.filter2D(gray, -1, k)
    else:
        # ksize=1 -> kernel 3x3 (8-tetangga)
        resp = cv2.Laplacian(gray, cv2.CV_32F, ksize=1)
    return _finish(np.abs(resp), threshold)


def _log_kernel(sigma: float) -> np.ndarray:
    """Kernel LoG: (r^2 - 2s^2) / s^4 * exp(-r^2 / 2s^2), dinormalisasi agar jumlah = 0."""
    r = int(math.ceil(3.0 * sigma))
    ax = np.arange(-r, r + 1, dtype=np.float32)
    xx, yy = np.meshgrid(ax, ax)
    d2 = xx * xx + yy * yy
    k = (d2 - 2 * sigma ** 2) / (sigma ** 4) * np.exp(-d2 / (2 * sigma ** 2))
    return (k - k.mean()).astype(np.float32)


def _zero_crossings(resp: np.ndarray, thr: float) -> np.ndarray:
    """Tandai piksel di mana respons berganti tanda terhadap tetangganya DAN selisihnya > thr."""
    zc = np.zeros(resp.shape, dtype=bool)
    pairs = (
        (resp[:, :-1], resp[:, 1:], (slice(None), slice(0, -1))),
        (resp[:-1, :], resp[1:, :], (slice(0, -1), slice(None))),
        (resp[:-1, :-1], resp[1:, 1:], (slice(0, -1), slice(0, -1))),
        (resp[:-1, 1:], resp[1:, :-1], (slice(0, -1), slice(1, None))),
    )
    for a, b, where in pairs:
        zc[where] |= (a * b < 0) & (np.abs(a - b) > thr)
    return zc


@register("edge_detection.2_nd_differential_gradient.laplacian_of_gaussian_log")
def laplacian_of_gaussian_log(img, sigma=1.4, mode="Zero-crossing", threshold=5):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=float(sigma))
    resp = cv2.Laplacian(blurred, cv2.CV_32F, ksize=1)
    peak = float(np.max(np.abs(resp))) or 1.0
    resp = resp / peak * 255.0
    if mode == "Magnitude":
        mag = np.abs(resp)
        return mag > float(threshold) if float(threshold) > 0 else mag
    return _zero_crossings(resp, float(threshold))


# ---------------------------------------------------------------------------
# Canny (OpenCV — standar industri, sudah mencakup Gaussian blur + NMS + hysteresis)
# ---------------------------------------------------------------------------
@register("edge_detection.2_nd_differential_gradient.canny")
def canny(img, low=80, high=160, blur=1.0):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    if float(blur) > 0:
        gray = cv2.GaussianBlur(gray, (0, 0), sigmaX=float(blur))
    # Output cv2.Canny = uint8 (0/255); konversi ke bool agar kompatibel dengan UI lama
    return cv2.Canny(gray, float(low), float(high)) > 0


# ---------------------------------------------------------------------------
# Compass (Kirsch) — 8 kernel arah, ambil respons maksimum
# ---------------------------------------------------------------------------
def _kirsch_kernels():
    ring = [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (1, 0)]
    base = [5, 5, 5, -3, -3, -3, -3, -3]
    kernels = []
    for s in range(8):
        k = np.zeros((3, 3), dtype=np.float32)
        for idx, (r, c) in enumerate(ring):
            k[r, c] = base[(idx - s) % 8]
        kernels.append(k)
    return kernels


_KIRSCH = _kirsch_kernels()


@register("edge_detection.compass")
def compass(img, threshold=0):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    responses = [cv2.filter2D(gray, -1, k) for k in _KIRSCH]
    best = np.maximum.reduce(responses)
    return _finish(np.maximum(best, 0), threshold)