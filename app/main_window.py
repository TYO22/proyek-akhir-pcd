"""Jendela utama aplikasi + "otak state" (gambar asli, hasil, undo/redo)."""
# ============================================================================
# FILE    : app/main_window.py
# PERAN   : JENDELA UTAMA + PUSAT STATE aplikasi. Semua file lain (handlers,
#           histogram, dll) bekerja lewat objek MainWindow ini, yang biasa
#           dipanggil "app".
#
# DIPANGGIL DARI: main.py  ->  MainWindow().mainloop()
#
# ---------------------------------------------------------------------------
# 1. STATE (data yang disimpan selama aplikasi berjalan)
# ---------------------------------------------------------------------------
#   self.original  : gambar ASLI dari File > Open (PIL.Image RGB). TIDAK PERNAH diubah.
#   self.result    : gambar HASIL operasi terakhir (ditampilkan di panel RESULT).
#                    Operasi berikutnya memproses result -> operasi bisa BERANTAI
#                    (mis. Noise lalu Median Filter). Reset mengembalikan ke original.
#   self.path / self.save_path : lokasi file asli / lokasi simpan terakhir (untuk "Save").
#   self.last_op   : nama operasi terakhir (tampil di status bar).
#   self.listeners : fungsi yang dipanggil setiap gambar berubah (pola OBSERVER; dipakai histogram).
#   self._undo / self._redo : tumpukan riwayat (gambar, nama operasi). Maks config.MAX_UNDO.
#   self.busy      : True saat operasi sedang dihitung di thread latar (lihat handlers.py).
#   self.modal_count : jumlah dialog modal yang terbuka (pintasan keyboard diabaikan jika > 0).
#
# POLA UNTUK FITUR BARU:
#   hasil = proses(app.result);  app.apply_result(hasil, "Nama Operasi")
#
# ---------------------------------------------------------------------------
# 2. LAYOUT (RESPONSIF - mengikuti ukuran jendela & layar)
# ---------------------------------------------------------------------------
#   +----------------------------------------------+
#   | MENU BAR                                      |  <- menu_builder.py
#   +----------------------------------------------+
#   | [ ORIGINAL ]         |        [ RESULT ]      |  <- 2 ImagePanel, berdampingan
#   +----------------------------------------------+     (ditumpuk atas-bawah jika
#   | status bar: File | Resolusi | Mode | Zoom    |        jendela lebih tinggi daripada lebar)
#   +----------------------------------------------+
#   * Ukuran awal = config.WINDOW_SCREEN_FRACTION dari layar, di tengah layar;
#     ukuran minimum dari config.MIN_WINDOW_SIZE. Jendela boleh di-resize/maximize.
#   * Urutan pack: status bar (bawah) -> menu bar (atas) -> body (sisa ruang). Urutan ini
#     penting: widget yang di-pack lebih dulu mendapat jatah ruang lebih dulu.
#
# ---------------------------------------------------------------------------
# 3. METHOD PENTING (API untuk file lain)
# ---------------------------------------------------------------------------
#   load_image(img, path)   : File > Open berhasil. Set original & result, kosongkan riwayat.
#   apply_result(img,label) : set result (push ke undo, kosongkan redo), tampilkan.
#   undo() / redo()         : mundur / maju satu langkah.
#   set_message(text)       : pesan di status bar.
#   set_busy(flag, text)    : tandai sedang memproses (kursor jam pasir + pesan).
#   run_command(id,label)   : dari menu -> handlers.dispatch().
#   run_shortcut(id,label)  : sama, tapi diabaikan saat ada dialog modal.
#   quit_app()              : tutup aplikasi.
#   refresh()               : gambar ulang panel + status bar + panggil semua listener.
# ============================================================================

from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk

from app import backend, config, handlers, theme
from app.menu_builder import build_menubar
from app.ui.image_panel import ImagePanel
from app.ui.status_bar import StatusBar


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        theme.apply_theme(self)              # skala DPI, font, warna (HARUS sebelum membuat widget)
        backend.load_all()                   # muat semua file algoritma di app/backend/
        self.title(config.window_title())
        self._init_geometry()

        # --- state aplikasi ---
        self.original = None
        self.result = None
        self.path = None
        self.save_path = None
        self.last_op = ""
        self.listeners: list = []
        self._message = ""
        self._undo: list = []
        self._redo: list = []
        self.busy = False
        self.modal_count = 0

        self._vertical = None                # orientasi panel saat ini (None = belum ditentukan)
        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self.quit_app)
        self.refresh()
        if backend.LOAD_ERRORS:              # satu file backend rusak tidak mematikan GUI
            names = ", ".join(n for n, _ in backend.LOAD_ERRORS)
            self.set_message(f"Backend gagal dimuat: {names} (lihat terminal)")

    # ------------------------------------------------------------ ukuran jendela
    def _init_geometry(self) -> None:
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        min_w, min_h = min(sw, theme.px(config.MIN_WINDOW_SIZE[0])), min(sh, theme.px(config.MIN_WINDOW_SIZE[1]))
        w, h = config.initial_window_size(sw, sh, min_w, min_h)
        x, y = (sw - w) // 2, max(0, (sh - h) // 2 - theme.px(20))
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(min_w, min_h)
        self.resizable(True, True)
        if config.START_MAXIMIZED:
            try:
                self.state("zoomed")             # Windows / macOS
            except tk.TclError:
                try:
                    self.attributes("-zoomed", True)   # Linux
                except tk.TclError:
                    pass

    # ----------------------------------------------------------------- layout
    def _build_layout(self) -> None:
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side="bottom", fill="x")
        build_menubar(self)                  # menu bar kustom di-pack di atas (sebelum body)

        self.body = ttk.Frame(self, padding=theme.px(8))
        self.body.pack(fill="both", expand=True)
        self.panel_original = ImagePanel(self.body, "ORIGINAL", "[Gambar Asli]\n\nFile > Open... untuk membuka gambar")
        self.panel_result = ImagePanel(self.body, "RESULT", "[Hasil Operasi]")
        self.panel_result.on_render = self._update_status
        # Zoom/geser satu panel diikuti panel lain (jika ukuran gambarnya sama).
        self.panel_original.on_view_change = self._sync_views
        self.panel_result.on_view_change = self._sync_views
        self.body.bind("<Configure>", self._on_body_resize)
        self._apply_orientation(False)

    def _on_body_resize(self, e) -> None:
        # Jendela potret (lebih tinggi daripada lebar) -> panel ditumpuk atas-bawah,
        # supaya tiap panel tetap berbentuk lebar (cocok untuk foto landscape).
        vertical = e.width < e.height
        if vertical != self._vertical:
            self._apply_orientation(vertical)

    def _apply_orientation(self, vertical: bool) -> None:
        self._vertical = vertical
        b, gap = self.body, theme.px(4)
        for i in (0, 1):
            b.columnconfigure(i, weight=0, uniform="")
            b.rowconfigure(i, weight=0, uniform="")
        if vertical:
            b.columnconfigure(0, weight=1)
            b.rowconfigure((0, 1), weight=1, uniform="row")
            self.panel_original.grid(row=0, column=0, sticky="nsew", pady=(0, gap))
            self.panel_result.grid(row=1, column=0, sticky="nsew", pady=(gap, 0))
        else:
            b.columnconfigure((0, 1), weight=1, uniform="col")
            b.rowconfigure(0, weight=1)
            self.panel_original.grid(row=0, column=0, sticky="nsew", padx=(0, gap), pady=0)
            self.panel_result.grid(row=0, column=1, sticky="nsew", padx=(gap, 0), pady=0)

    def _sync_views(self, src) -> None:
        other = self.panel_result if src is self.panel_original else self.panel_original
        if src._img is not None and other._img is not None and src._img.size == other._img.size:
            other.apply_view(src.view_state())

    # --------------------------------------------------------- API untuk fitur
    def load_image(self, img, path) -> None:
        """Muat gambar baru (PIL.Image RGB) ke ORIGINAL dan RESULT; riwayat dikosongkan."""
        self.original, self.result = img, img.copy()
        self.path, self.save_path, self.last_op, self._message = path, None, "", ""
        self._undo.clear()
        self._redo.clear()
        self.panel_original.reset_view()
        self.panel_result.reset_view()
        self.refresh()

    def apply_result(self, img, label: str = "") -> None:
        """Tampilkan hasil operasi (PIL.Image) di RESULT. Hasil sebelumnya disimpan untuk Undo."""
        if self.result is not None:
            self._undo.append((self.result, self.last_op))
            del self._undo[:-config.MAX_UNDO]            # buang riwayat tertua jika kelebihan
        self._redo.clear()
        self.result, self.last_op, self._message = img, label, ""
        self.refresh()

    def undo(self) -> None:
        if not self._undo:
            self.set_message("Tidak ada langkah untuk di-undo")
            return
        self._redo.append((self.result, self.last_op))
        self.result, self.last_op = self._undo.pop()
        self._message = ""
        self.refresh()

    def redo(self) -> None:
        if not self._redo:
            self.set_message("Tidak ada langkah untuk di-redo")
            return
        self._undo.append((self.result, self.last_op))
        self.result, self.last_op = self._redo.pop()
        self._message = ""
        self.refresh()

    def set_message(self, text: str) -> None:
        self._message = text
        self._update_status()

    def set_busy(self, flag: bool, text: str = "") -> None:
        self.busy = flag
        self.config(cursor="watch" if flag else "")
        self.set_message(text)
        self.update_idletasks()

    def run_command(self, command_id: str, label: str) -> None:
        # Jembatan GUI (menu) -> logika (handlers.dispatch).
        handlers.dispatch(self, command_id, label)

    def run_shortcut(self, command_id: str, label: str) -> None:
        # Pintasan keyboard: abaikan jika dialog modal sedang terbuka.
        if self.modal_count == 0:
            self.run_command(command_id, label)

    def quit_app(self) -> None:
        self.destroy()

    # ---------------------------------------------------------------- tampilan
    def refresh(self) -> None:
        self.panel_original.show(self.original)
        self.panel_result.show(self.result)
        self._update_status()
        for cb in list(self.listeners):                  # salinan: aman jika listener mengubah daftar
            cb()

    def _update_status(self) -> None:
        if self.result is None:
            self.status_bar.update_status(message=self._message)
            return
        name = os.path.basename(self.path) if self.path else "-"
        if self.last_op:
            msg = f"Operasi: {self.last_op}" + (f" - {self._message}" if self._message else "")
        else:
            msg = self._message
        self.status_bar.update_status(name, self.result.size, self.result.mode,
                                      round(self.panel_result.scale * 100), msg)
