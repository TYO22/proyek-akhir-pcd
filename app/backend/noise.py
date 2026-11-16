"""BACKEND menu "Noise": menambahkan noise acak ke gambar.
Menggunakan numpy.random untuk distribusi khusus (Rayleigh, Erlang, dll.)
dan skimage.util.random_noise untuk impulse (salt & pepper)."""

import numpy as np
import skimage.util
from app.backend import register


def _rng() -> np.random.Generator:
    """Pembangkit acak baru setiap panggilan -> hasil berbeda tiap kali dijalankan."""
    return np.random.default_rng()


def _add(img, noise):
    """Tambahkan noise; clipping 0..255 dilakukan oleh backend.__init__ (sesuai perilaku lama)."""
    return img.astype(np.float32) + noise.astype(np.float32)


@register("noise.gaussian_noise")
def gaussian_noise(img, mean=0, sigma=25):
    return _add(img, _rng().normal(float(mean), float(sigma), img.shape))


@register("noise.rayleigh_noise")
def rayleigh_noise(img, scale=20):
    return _add(img, _rng().rayleigh(float(scale), img.shape))


@register("noise.erlang_gamma_noise")
def erlang_gamma_noise(img, k=2, scale=10):
    return _add(img, _rng().gamma(int(k), float(scale), img.shape))


@register("noise.exponential_noise")
def exponential_noise(img, scale=20):
    return _add(img, _rng().exponential(float(scale), img.shape))


@register("noise.uniform_noise")
def uniform_noise(img, low=-30, high=30):
    return _add(img, _rng().uniform(float(low), float(high), img.shape))


@register("noise.impulse_noise")
def impulse_noise(img, p_salt=5, p_pepper=5):
    """Salt & pepper via skimage.util.random_noise (lebih ringkas & teruji)."""
    total = (p_salt + p_pepper) / 100.0
    if total <= 0:
        return img.copy()
    ratio = p_salt / (p_salt + p_pepper)
    img_f = img.astype(np.float32) / 255.0
    noisy = skimage.util.random_noise(
        img_f, mode='s&p', amount=total, salt_vs_pepper=ratio
    )
    # Kembalikan ke uint8 agar kompatibel dengan output asli (img.copy())
    return (np.clip(noisy, 0.0, 1.0) * 255.0).astype(np.uint8)