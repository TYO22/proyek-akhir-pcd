"""Status bar sesuai wireframe:  File: ... | Resolusi: ... | Mode: ...      Zoom: ..%"""
# ============================================================================
# FILE    : app/ui/status_bar.py
# PERAN   : BARIS INFORMASI di bagian bawah jendela. Menampilkan:
#             kiri  : File | Resolusi | Mode | [pesan operasi]
#             kanan : Zoom: xx%
#           Sesuai wireframe pada dokumen PDF. Warna & font diambil dari app/theme.py.
#
# DIPAKAI OLEH: app/main_window.py
#   - _build_layout()   : membuat StatusBar(self)
#   - _update_status()  : memanggil update_status(...) dengan data gambar
#
# CATATAN: widget ini TIDAK menyimpan data gambar. Ia hanya menerima teks/angka dari
# MainWindow lalu menampilkannya. Sumber data = state MainWindow.
#
# ALUR update_status(filename, size, mode, zoom, message):
#   -> susun "File: foto.png | Resolusi: 800x600 px | Mode: RGB"
#   -> jika ada message, tambahkan "   [pesan]" di belakang
#   -> teks info ke label kiri, teks zoom ke label kanan
# ============================================================================

from __future__ import annotations

from tkinter import ttk

from app import theme


class StatusBar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style="Status.TFrame", padding=(theme.px(12), theme.px(5)))
        self._info = ttk.Label(self, anchor="w", style="Status.TLabel")
        self._info.pack(side="left", fill="x", expand=True)
        self._zoom = ttk.Label(self, anchor="e", style="Status.TLabel")
        self._zoom.pack(side="right")

    def update_status(self, filename=None, size=None, mode=None, zoom=None, message="") -> None:
        if filename:
            w, h = size
            info = f"File: {filename} | Resolusi: {w}x{h} px | Mode: {mode}"
        else:
            info = "File: - | Resolusi: - | Mode: -"
        if message:
            info += f"   [{message}]"
        self._info.config(text=info)
        self._zoom.config(text=f"Zoom: {zoom}%" if zoom is not None else "Zoom: -")
