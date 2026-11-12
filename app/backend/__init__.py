"""BACKEND pengolahan citra (dipasang belakangan, terpisah dari frontend).

Cara menambah fitur: buat file .py APA SAJA di folder ini, lalu daftarkan fungsinya
dengan ID menu. File di folder ini otomatis dimuat saat aplikasi start.

    # app/backend/basic_ops.py
    from app.backend import register

    @register("basic_ops.negative")
    def negative(img):                 # img: numpy uint8 RGB, shape (H, W, 3)
        return 255 - img               # kembalikan numpy array

Kontrak:
  * Masukan  : img = numpy.ndarray uint8, RGB, (H, W, 3)  + parameter dari popup sebagai **kwargs
  * Keluaran : numpy.ndarray. uint8 / float (otomatis di-clip 0..255) / bool (True -> 255),
               boleh 2D (grayscale), 3 kanal, atau berubah ukuran (crop, zoom, dst).
  * Nama & tipe parameter ada di app/param_specs.py (ringkasannya: docs/BACKEND_CONTRACT.md).
  * Melempar exception = frontend menampilkan pesan error; gambar tidak berubah.

Menu yang backend-nya belum terdaftar menampilkan pesan "belum diimplementasi".
"""

from __future__ import annotations

# ============================================================================
# FILE    : app/backend/__init__.py
# PERAN   : "MESIN PENGOLAH CITRA" (BACKEND) + "JEMBATAN" ke frontend.
#           Di sinilah algoritma pengolahan gambar yang sebenarnya akan
#           ditulis (negatif, konvolusi, filter, deteksi tepi, dst).
#           Kode di sini TIDAK boleh menyentuh Tkinter (GUI). Ia hanya menerima
#           array angka, memprosesnya, lalu mengembalikan array angka.
#
# STATUS: TERHUBUNG & BERFUNGSI
#   * MainWindow.__init__ memanggil load_all() -> semua file di folder ini dimuat.
#   * handlers.dispatch() memanggil is_available(ID) lalu run(ID, gambar, parameter).
#
# FILE DI FOLDER INI
#   common.py          fungsi bantu bersama (konvolusi, filter, warna, FFT, ...)
#   basic_ops.py       menu Basic Ops
#   enhancement.py     menu Enhancement
#   noise.py           menu Noise
#   edge_detection.py  menu Edge Detection
#   segmentation.py    menu Segmentation
#   Setiap file otomatis dimuat (load_all). File baru yang kamu tambahkan di sini
#   juga otomatis dimuat; tidak ada daftar yang perlu diedit.
#
# ---------------------------------------------------------------------------
# DUA "REGISTER" YANG BERBEDA (JANGAN TERTUKAR!)
# ---------------------------------------------------------------------------
#   1. register di app/backend/__init__.py  -> menyimpan ALGORITMA (_REGISTRY)
#                                              Fungsinya menerima numpy array.
#   2. register di app/handlers.py          -> menyimpan AKSI MENU (HANDLERS)
#                                              Fungsinya menerima objek app (GUI).
#   Keduanya punya nama sama tapi kamus dan fungsinya berbeda.
#
# ---------------------------------------------------------------------------
# ALUR DATA SAAT OPERASI DIJALANKAN (alur nyata aplikasi)
# ---------------------------------------------------------------------------
#   [User klik menu] -> handlers.dispatch(app, id, label)
#        -> app.result (PIL.Image)
#        -> run(id, pil_image, params)        <- fungsi di file ini
#              a. PIL -> numpy   : np.array(image.convert("RGB"), dtype=uint8)
#              b. panggil fungsi algoritma yang terdaftar: _REGISTRY[id](arr, **params)
#              c. numpy -> PIL   : _to_pil(hasil)   (dirapikan & di-clip ke 0..255)
#        -> app.apply_result(hasil_pil, label)  <- tampil di panel RESULT
#
#   Mengapa dibagi dua? Algoritma cukup bekerja dengan numpy (cepat & mudah diuji),
#   sedangkan GUI bekerja dengan PIL. run() adalah penerjemahnya di tengah.
#
# ---------------------------------------------------------------------------
# PENJELASAN SETIAP BAGIAN
# ---------------------------------------------------------------------------
#   _REGISTRY        : kamus {ID : fungsi algoritma}. Diisi oleh @register.
#   LOAD_ERRORS      : daftar (nama_modul, pesan_error) untuk modul yang gagal dimuat.
#                      Dipakai agar satu file backend yang rusak TIDAK mematikan GUI.
#   register(id)     : decorator. Menyimpan fungsi ke _REGISTRY[id].
#   unregister(id)   : menghapus pendaftaran (berguna saat testing).
#   is_available(id) : True jika algoritma untuk ID tersebut sudah ada.
#                      Bisa dipakai handlers.py untuk memutuskan: jalankan backend
#                      atau tampilkan placeholder "belum diimplementasi".
#   available_ids()  : daftar semua ID yang sudah terdaftar (urut abjad).
#   load_all()       : mengimpor SEMUA file .py di folder app/backend/ secara otomatis
#                      (pkgutil.iter_modules). Saat file diimpor, decorator @register
#                      di dalamnya ikut terjalankan dan mengisi _REGISTRY.
#                      Jika satu file error -> dicatat di LOAD_ERRORS, program lanjut.
#   run(id, image, params) : jembatan PIL <-> numpy seperti dijelaskan di atas.
#                      Memanggil _REGISTRY[id] dengan params sebagai **kwargs.
#   _to_pil(x)       : mengubah hasil algoritma apa pun menjadi PIL.Image RGB:
#                        - bool     -> True jadi 255, False jadi 0
#                        - bukan uint8 -> dibulatkan, di-clip ke 0..255, lalu diubah ke uint8
#                        - 2D (H,W) atau (H,W,1) -> diduplikasi jadi 3 kanal (grayscale->RGB)
#                        - 4 kanal (RGBA) -> buang kanal alpha, sisakan 3
#                        - bentuk lain -> ValueError (pesan error ditampilkan ke user)
#
# ---------------------------------------------------------------------------
# KONSEP PYTHON YANG DIPAKAI
# ---------------------------------------------------------------------------
#   from __future__ import annotations : agar type hint modern tetap aman.
#   Callable                           : type hint untuk "sesuatu yang bisa dipanggil (fungsi)".
#   **params                           : menerima argumen bernama dalam bentuk dict
#                                        (mis. params={"beta": 40} -> fn(arr, beta=40)).
#   np.ndarray                         : array numpy, bentuk data gambar di backend.
#   np.clip(x, 0, 255)                 : membatasi nilai ke rentang 0..255.
#   np.stack([x, x, x], axis=-1)       : menumpuk tiga salinan menjadi 3 kanal.
#   np.ascontiguousarray(x)            : memastikan array tersusun rapat di memori
#                                        (dibutuhkan PIL.Image.fromarray).
#   importlib.import_module(nama)      : mengimpor modul dari nama teks.
# ============================================================================

import importlib
import pkgutil
import sys
import traceback
from typing import Callable

import numpy as np
from PIL import Image

_REGISTRY: dict[str, Callable] = {}
LOAD_ERRORS: list[tuple[str, str]] = []


def register(command_id: str):
    def deco(fn):
        _REGISTRY[command_id] = fn
        return fn
    return deco


def unregister(command_id: str) -> None:
    # pop(key, None) = hapus kalau ada, diam saja kalau tidak ada.
    _REGISTRY.pop(command_id, None)


def is_available(command_id: str) -> bool:
    return command_id in _REGISTRY


def available_ids() -> list[str]:
    # sorted() mengembalikan list ID yang sudah diurutkan.
    return sorted(_REGISTRY)


def load_all() -> None:
    """Impor semua modul di paket ini agar @register terpanggil."""
    LOAD_ERRORS.clear()
    # pkgutil.iter_modules(__path__) = daftar semua modul di folder paket ini.
    # __path__ = variabel otomatis Python berisi lokasi folder paket.
    for mod in pkgutil.iter_modules(__path__):
        try:
            # Nama lengkap modul, mis. "app.backend.basic_ops". Import = jalankan file-nya.
            importlib.import_module(f"{__name__}.{mod.name}")
        except Exception as exc:                       # backend rusak tidak boleh mematikan GUI
            LOAD_ERRORS.append((mod.name, f"{type(exc).__name__}: {exc}"))
            print(f"[backend] gagal memuat '{mod.name}':", file=sys.stderr)
            # traceback.print_exc() mencetak detail error (baris mana, kenapa) ke stderr.
            traceback.print_exc()


def run(command_id: str, image: Image.Image, params: dict) -> Image.Image:
    """Jembatan frontend -> backend: PIL -> numpy -> fungsi backend -> PIL."""
    # PIL -> numpy. convert("RGB") memastikan 3 kanal. dtype=uint8 = nilai 0..255.
    arr = np.array(image.convert("RGB"), dtype=np.uint8)
    # _REGISTRY[command_id] = fungsi algoritma. **params = kirim sebagai argumen bernama.
    out = _REGISTRY[command_id](arr, **params)
    # Hasil numpy -> PIL agar bisa ditampilkan oleh GUI.
    return _to_pil(out)


def _to_pil(x) -> Image.Image:
    # Ubah hasil algoritma apa pun menjadi array numpy yang aman untuk gambar.
    x = np.asarray(x)
    if x.dtype == bool:
        # Hasil boolean (True/False) -> 255/0 agar terlihat sebagai hitam-putih.
        x = x.astype(np.uint8) * 255
    elif x.dtype != np.uint8:
        # Float atau tipe lain -> batasi 0..255 lalu ubah ke uint8.
        x = np.clip(np.rint(np.nan_to_num(x)), 0, 255).astype(np.uint8)
    if x.ndim == 3 and x.shape[2] == 1:
        # Bentuk (H, W, 1) -> buang sumbu terakhir jadi (H, W).
        x = x[..., 0]
    if x.ndim == 2:
        # Grayscale (H, W) -> tumpuk 3 kali jadi (H, W, 3) agar bisa jadi RGB.
        x = np.stack([x, x, x], axis=-1)
    elif x.ndim == 3 and x.shape[2] == 4:
        # RGBA -> ambil 3 kanal pertama (RGB), buang alpha.
        x = x[..., :3]
    if x.ndim != 3 or x.shape[2] != 3:
        raise ValueError(f"Keluaran backend harus (H,W), (H,W,1), (H,W,3) atau (H,W,4); dapat {x.shape}")
    # ascontiguousarray = susun ulang array agar kompatibel dengan PIL.
    return Image.fromarray(np.ascontiguousarray(x))
