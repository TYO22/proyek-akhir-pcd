"""Jendela histogram (tk.Canvas + PIL, tanpa numpy/matplotlib)."""
# ============================================================================
# FILE    : app/ui/histogram_window.py
# PERAN   : Jendela yang menampilkan HISTOGRAM gambar: grafik seberapa banyak
#           piksel yang memiliki tiap tingkat kecerahan (0..255). Grafik ikut
#           ter-update otomatis setiap gambar berubah (pola OBSERVER).
#           Warna mengikuti tema (app/theme.py: hist_r, hist_g, hist_b, hist_gray).
#
# DIPANGGIL DARI: app/handlers.py -> histogram(app) -> open_histogram(app)
#
# APA ITU HISTOGRAM? Tiap piksel punya nilai 0 (hitam) .. 255 (putih). Histogram
# menghitung "berapa piksel bernilai 0? 1? ... 255?" lalu menggambarnya sebagai
# grafik garis. Sumbu X = nilai, sumbu Y = jumlah piksel. Berguna untuk melihat
# gambar gelap / terang / berkontras rendah (sebelum & sesudah Hist. Equalization).
#
# ALUR
#   open_histogram(app) : jika jendela sudah ada -> angkat ke depan & gambar ulang;
#                         jika belum -> buat HistogramWindow(app).
#   HistogramWindow.__init__ : pilihan sumber (Result/Original) + checkbox R,G,B,Gray,
#       canvas; mendaftarkan draw ke app.listeners (dipanggil tiap gambar berubah);
#       mencabut diri saat jendela ditutup (<Destroy>).
#   draw() : hapus canvas -> gambar sumbu -> img.convert("RGB").histogram() (768 angka:
#       0..255 = R, 256..511 = G, 512..767 = B) + img.convert("L").histogram() untuk Gray
#       -> skala tinggi dari PUNCAK tertinggi -> gambar polyline tiap kanal.
#
# RUMUS KOORDINAT
#   x = x0 + (x1 - x0) * i / 255          (posisi horizontal untuk nilai i)
#   y = y1 - (y1 - y0 - 4) * val / peak   (canvas menghitung y dari ATAS, jadi dikurangkan dari y1)
#   peak dibuat minimal 1 dengan "or 1" agar tidak membagi nol.
# ============================================================================

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app import theme

_instance = None                      # jendela histogram yang sedang terbuka (None = belum)
_KEYS = ("R", "G", "B", "Gray")
_THEME_KEY = {"R": "hist_r", "G": "hist_g", "B": "hist_b", "Gray": "hist_gray"}


class HistogramWindow(tk.Toplevel):
    W, H, PAD = 600, 350, 40          # ukuran canvas (piksel logis) & jarak kiri untuk label

    def __init__(self, app):
        super().__init__(app)
        theme.style_window(self)
        self.app = app
        self.title("Histogram")
        self.resizable(False, False)
        # (jangan namai atribut '_w' / '_h': nama itu dipakai internal Tkinter untuk path widget)
        self._cw, self._ch, self._pad = theme.px(self.W), theme.px(self.H), theme.px(self.PAD)

        top = ttk.Frame(self, padding=(theme.px(12), theme.px(10)))
        top.pack(fill="x")
        ttk.Label(top, text="Sumber:").pack(side="left")
        self.source = tk.StringVar(value="Result")
        cb = ttk.Combobox(top, values=("Result", "Original"), textvariable=self.source,
                          state="readonly", width=9)
        cb.pack(side="left", padx=(theme.px(6), theme.px(14)))
        cb.bind("<<ComboboxSelected>>", lambda _e: self.draw())
        self.show = {k: tk.BooleanVar(value=True) for k in _KEYS}
        for k in _KEYS:
            ttk.Checkbutton(top, text=k, variable=self.show[k], command=self.draw).pack(
                side="left", padx=theme.px(4))

        self.canvas = tk.Canvas(self, width=self._cw, height=self._ch, bg=theme.color("field"),
                                highlightthickness=1, highlightbackground=theme.color("border"))
        self.canvas.pack(padx=theme.px(12), pady=(0, theme.px(12)))
        app.listeners.append(self.draw)            # ikut update saat gambar berubah
        self.bind("<Destroy>", self._on_destroy)
        self.draw()

    def _on_destroy(self, event):
        # <Destroy> dikirim juga untuk widget anak; hanya tangani jendela ini sendiri.
        if event.widget is self and self.draw in self.app.listeners:
            self.app.listeners.remove(self.draw)

    def draw(self):
        c = self.canvas
        c.delete("all")
        dim, border = theme.color("fg_dim"), theme.color("border")
        img = self.app.result if self.source.get() == "Result" else self.app.original
        x0, y0, x1, y1 = self._pad, theme.px(16), self._cw - theme.px(16), self._ch - theme.px(32)
        c.create_rectangle(x0, y0, x1, y1, outline=border)
        for v in (0, 64, 128, 192, 255):
            x = x0 + (x1 - x0) * v / 255
            c.create_line(x, y1, x, y1 + theme.px(4), fill=dim)
            c.create_text(x, y1 + theme.px(16), text=str(v), fill=dim, font=theme.font(-2))
        if img is None:
            c.create_text(self._cw // 2, self._ch // 2, text="Belum ada gambar", fill=dim, font=theme.font())
            return
        rgb = img.convert("RGB").histogram()
        series = {"R": rgb[0:256], "G": rgb[256:512], "B": rgb[512:768], "Gray": img.convert("L").histogram()}
        series = {k: v for k, v in series.items() if self.show[k].get()}
        if not series:
            return
        peak = max(max(v) for v in series.values()) or 1
        for k, hist in series.items():
            pts = []
            for i, val in enumerate(hist):
                pts += [x0 + (x1 - x0) * i / 255, y1 - (y1 - y0 - 4) * val / peak]
            c.create_line(*pts, fill=theme.color(_THEME_KEY[k]), width=max(1.5, theme.px(1.5)))
        c.create_text(x0 + theme.px(6), y0 + theme.px(10), anchor="w", fill=dim, font=theme.font(-2),
                      text=f"{self.source.get()}  {img.width}x{img.height}  puncak={peak}")


def open_histogram(app):
    global _instance
    if _instance is not None and _instance.winfo_exists():
        _instance.lift()
        _instance.draw()
        return
    _instance = HistogramWindow(app)
