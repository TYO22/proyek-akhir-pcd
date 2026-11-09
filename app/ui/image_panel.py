"""Panel gambar (ORIGINAL / RESULT): auto-fit, zoom dengan scroll mouse, geser dengan drag."""
# ============================================================================
# FILE    : app/ui/image_panel.py
# PERAN   : Satu KOTAK TAMPILAN GAMBAR. Dipakai dua kali di jendela utama:
#           panel kiri/atas (ORIGINAL) dan panel kanan/bawah (RESULT).
#           Menerima objek PIL.Image lalu menggambarnya di canvas.
#
# DIPAKAI OLEH: app/main_window.py -> ImagePanel(body, "ORIGINAL", ...)
#
# ---------------------------------------------------------------------------
# FITUR
# ---------------------------------------------------------------------------
#   * AUTO-FIT   : gambar otomatis disesuaikan dengan ukuran panel (dan ikut berubah
#                  saat jendela di-resize). Batas perbesaran diatur config.FIT_MAX_SCALE.
#   * ZOOM       : putar roda mouse di atas gambar. Zoom diarahkan ke posisi kursor.
#   * GESER (PAN): tahan klik kiri lalu seret (saat gambar diperbesar).
#   * RESET      : klik ganda = kembali ke mode auto-fit.
#   * SINKRON    : jika kedua panel berisi gambar berukuran sama, zoom/geser satu panel
#                  diikuti panel lain (memudahkan membandingkan ORIGINAL vs RESULT).
#   * KUALITAS   : memperkecil memakai LANCZOS (tajam); memperbesar <3x memakai BILINEAR,
#                  >=3x memakai NEAREST agar piksel terlihat jelas.
#
# ---------------------------------------------------------------------------
# KONSEP: "scale" dan "view"
# ---------------------------------------------------------------------------
#   scale   : piksel layar per piksel gambar (1.0 = 100%, 0.5 = 50%). Dibaca
#             MainWindow untuk teks "Zoom: xx%" di status bar.
#   _zoom   : None = mode FIT (scale dihitung otomatis). Angka = zoom manual.
#   _cx,_cy : titik di gambar (koordinat piksel gambar) yang berada di TENGAH panel.
#             Mengubah _cx/_cy = menggeser pandangan.
#
# ---------------------------------------------------------------------------
# ALUR _render()
# ---------------------------------------------------------------------------
#   1. Ukur canvas. Terlalu kecil (< 10 px) -> berhenti (belum tampil).
#   2. Hitung scale (fit atau zoom manual).
#   3. _origin(): tentukan area gambar yang terlihat (x0, y0, lebar, tinggi dalam
#      koordinat gambar) dan jepit agar tidak keluar tepi.
#   4. Potong area itu dari gambar dan ubah ukurannya ke ukuran layar dengan
#      Image.resize(..., box=...) (hanya bagian yang terlihat yang diproses -> cepat
#      walau gambar sangat besar).
#   5. Gambar di canvas, perbarui label ukuran, panggil on_render (status bar).
#   Event <Configure> (resize) memakai debounce 60 ms agar tidak berat saat di-drag.
#
# ⚠ self._photo WAJIB disimpan sebagai atribut; jika tidak, Python membuangnya
#   (garbage collection) dan gambar di canvas menghilang.
# ============================================================================

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from app import config, theme

_RS = Image.Resampling


class ImagePanel(ttk.Frame):
    def __init__(self, master, title: str, placeholder: str):
        super().__init__(master, style="Panel.TFrame")
        self.placeholder = placeholder
        self.scale = 1.0                 # skala tampilan saat ini (dibaca status bar)
        self.on_render = None            # callback setelah render (MainWindow: update status)
        self.on_view_change = None       # callback(panel) setelah user zoom/geser (sinkronisasi)
        self._img = None                 # PIL.Image yang ditampilkan
        self._photo = None               # ImageTk.PhotoImage (harus disimpan!)
        self._zoom = None                # None = fit; angka = zoom manual
        self._cx = self._cy = None       # pusat pandangan (koordinat gambar); None = tengah
        self._drag = None                # (x, y) terakhir saat drag
        self._after = None               # id jadwal render (debounce)

        # Baris judul: nama panel (kiri) + ukuran gambar (kanan).
        head = ttk.Frame(self, style="Panel.TFrame")
        head.pack(fill="x", padx=theme.px(10), pady=(theme.px(7), theme.px(5)))
        ttk.Label(head, text=title, style="PanelTitle.TLabel").pack(side="left")
        self._info = ttk.Label(head, text="", style="PanelInfo.TLabel")
        self._info.pack(side="right")

        # Canvas dibungkus Frame berwarna border (garis tepi 1 px tanpa ambiguitas koordinat canvas).
        frame = tk.Frame(self, bg=theme.color("border"))
        frame.pack(fill="both", expand=True, padx=theme.px(10), pady=(0, theme.px(10)))
        self.canvas = tk.Canvas(frame, bg=theme.color("canvas"), highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True, padx=1, pady=1)

        c = self.canvas
        c.bind("<Configure>", lambda _e: self._schedule_render())
        c.bind("<Enter>", lambda _e: c.focus_set())
        c.bind("<MouseWheel>", self._on_wheel)                       # Windows & macOS
        c.bind("<Button-4>", lambda e: self._on_wheel(e, +1))        # Linux: scroll atas
        c.bind("<Button-5>", lambda e: self._on_wheel(e, -1))        # Linux: scroll bawah
        c.bind("<ButtonPress-1>", self._on_press)
        c.bind("<B1-Motion>", self._on_drag)
        c.bind("<ButtonRelease-1>", self._on_release)
        c.bind("<Double-Button-1>", lambda _e: self.reset_view(notify=True))

    # ------------------------------------------------------------------ API
    def show(self, img) -> None:
        """Tampilkan gambar baru. Jika ukurannya berubah, tampilan kembali ke mode fit."""
        if img is None or self._img is None or img.size != self._img.size:
            self._zoom, self._cx, self._cy = None, None, None
        self._img = img
        self._render()

    def reset_view(self, notify: bool = False) -> None:
        self._zoom, self._cx, self._cy = None, None, None
        self._render()
        if notify:
            self._notify()

    def view_state(self):
        return self._zoom, self._cx, self._cy

    def apply_view(self, state) -> None:
        """Dipakai MainWindow untuk menyamakan zoom/geser dengan panel lain."""
        self._zoom, self._cx, self._cy = state
        self._render()

    # ------------------------------------------------------------------ geometri
    def _canvas_size(self):
        return self.canvas.winfo_width(), self.canvas.winfo_height()

    def _fit_scale(self, w, h) -> float:
        iw, ih = self._img.size
        return min(config.FIT_MAX_SCALE, (w - 4) / iw, (h - 4) / ih)

    def _scale_for(self, w, h) -> float:
        return self._fit_scale(w, h) if self._zoom is None else self._zoom

    @staticmethod
    def _clamp_origin(origin: float, visible: float, total: float) -> float:
        # Jika seluruh gambar muat, pusatkan; jika tidak, jepit agar tidak melewati tepi gambar.
        if visible >= total:
            return -(visible - total) / 2.0
        return min(max(origin, 0.0), total - visible)

    def _origin(self, w, h, s):
        """Area gambar yang terlihat: (x0, y0, lebar_terlihat, tinggi_terlihat) dalam koordinat gambar."""
        iw, ih = self._img.size
        vw, vh = w / s, h / s
        cx = iw / 2.0 if self._cx is None else self._cx
        cy = ih / 2.0 if self._cy is None else self._cy
        return (self._clamp_origin(cx - vw / 2.0, vw, iw),
                self._clamp_origin(cy - vh / 2.0, vh, ih), vw, vh)

    # ------------------------------------------------------------------ render
    def _schedule_render(self) -> None:
        # Debounce: gabungkan banyak event resize beruntun menjadi satu render.
        if self._after is not None:
            self.after_cancel(self._after)
        self._after = self.after(60, self._render)

    def _render(self) -> None:
        if self._after is not None:
            try:
                self.after_cancel(self._after)
            except tk.TclError:
                pass
            self._after = None
        c = self.canvas
        w, h = self._canvas_size()
        if w < 10 or h < 10:                       # belum ter-layout
            return
        c.delete("all")
        if self._img is None:
            self.scale, self._photo = 1.0, None
            self._info.config(text="")
            c.create_text(w // 2, h // 2, text=self.placeholder, fill=theme.color("fg_dim"),
                          font=theme.font(1), justify="center", width=max(50, w - 40))
        else:
            iw, ih = self._img.size
            s = self._scale_for(w, h)
            self.scale = s
            x0, y0, vw, vh = self._origin(w, h, s)
            if self._zoom is not None:             # simpan pusat yang sudah dijepit
                self._cx, self._cy = x0 + vw / 2.0, y0 + vh / 2.0
            bx0, by0 = max(x0, 0.0), max(y0, 0.0)
            bx1, by1 = min(x0 + vw, iw), min(y0 + vh, ih)
            dw, dh = max(1, round((bx1 - bx0) * s)), max(1, round((by1 - by0) * s))
            px_, py_ = round((bx0 - x0) * s), round((by0 - y0) * s)
            if s < 1.0:
                resample, extra = _RS.LANCZOS, ({"reducing_gap": 2.0} if s < 0.5 else {})
            else:
                resample, extra = (_RS.NEAREST if s >= 3.0 else _RS.BILINEAR), {}
            im = self._img.resize((dw, dh), resample, box=(bx0, by0, bx1, by1), **extra)
            self._photo = ImageTk.PhotoImage(im)   # simpan! (lihat catatan di header)
            c.create_image(px_, py_, image=self._photo, anchor="nw")
            self._info.config(text=f"{iw} \u00d7 {ih} px")
        if self.on_render:
            self.on_render()

    # ------------------------------------------------------------------ interaksi
    def _notify(self) -> None:
        if self.on_view_change:
            self.on_view_change(self)

    def _on_wheel(self, e, direction=None) -> None:
        if self._img is None:
            return
        d = direction if direction is not None else (1 if e.delta > 0 else -1)
        w, h = self._canvas_size()
        fit = self._fit_scale(w, h)
        s_old = self._scale_for(w, h)
        s_new = s_old * (config.ZOOM_STEP if d > 0 else 1.0 / config.ZOOM_STEP)
        s_new = min(s_new, config.ZOOM_MAX)
        if s_new <= fit + 1e-9:                    # sudah sekecil fit -> kembali ke mode fit
            self.reset_view(notify=True)
            return
        # Titik gambar di bawah kursor harus tetap di bawah kursor setelah zoom.
        x0, y0, _vw, _vh = self._origin(w, h, s_old)
        ix, iy = x0 + e.x / s_old, y0 + e.y / s_old
        nx0, ny0 = ix - e.x / s_new, iy - e.y / s_new
        self._zoom = s_new
        self._cx, self._cy = nx0 + (w / s_new) / 2.0, ny0 + (h / s_new) / 2.0
        self._render()
        self._notify()

    def _on_press(self, e) -> None:
        self._drag = (e.x, e.y)
        if self._zoom is not None:
            self.canvas.config(cursor="fleur")

    def _on_drag(self, e) -> None:
        if self._img is None or self._zoom is None or self._drag is None:
            return                                  # mode fit: seluruh gambar sudah terlihat
        dx, dy = e.x - self._drag[0], e.y - self._drag[1]
        self._drag = (e.x, e.y)
        self._cx -= dx / self._zoom
        self._cy -= dy / self._zoom
        self._render()
        self._notify()

    def _on_release(self, _e) -> None:
        self._drag = None
        self.canvas.config(cursor="")
