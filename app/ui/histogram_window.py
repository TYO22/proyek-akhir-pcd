"""Jendela histogram (tk.Canvas + PIL, tanpa numpy/matplotlib)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

_instance = None
_COLORS = {"R": "#d62728", "G": "#2ca02c", "B": "#1f77b4", "Gray": "#222222"}


class HistogramWindow(tk.Toplevel):
    W, H, PAD = 560, 330, 36

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Histogram")
        self.resizable(False, False)
        top = ttk.Frame(self, padding=(10, 8))
        top.pack(fill="x")
        ttk.Label(top, text="Sumber:").pack(side="left")
        self.source = tk.StringVar(value="Result")
        cb = ttk.Combobox(top, values=("Result", "Original"), textvariable=self.source, state="readonly", width=9)
        cb.pack(side="left", padx=(4, 12))
        cb.bind("<<ComboboxSelected>>", lambda _e: self.draw())
        self.show = {k: tk.BooleanVar(value=True) for k in _COLORS}
        for k in _COLORS:
            ttk.Checkbutton(top, text=k, variable=self.show[k], command=self.draw).pack(side="left", padx=3)
        self.canvas = tk.Canvas(self, width=self.W, height=self.H, bg="white", highlightthickness=0)
        self.canvas.pack(padx=10, pady=(0, 10))
        app.listeners.append(self.draw)        # ikut update saat gambar berubah
        self.bind("<Destroy>", self._on_destroy)
        self.draw()

    def _on_destroy(self, event):
        if event.widget is self and self.draw in self.app.listeners:
            self.app.listeners.remove(self.draw)

    def draw(self):
        c = self.canvas
        c.delete("all")
        img = self.app.result if self.source.get() == "Result" else self.app.original
        x0, y0, x1, y1 = self.PAD, 14, self.W - 14, self.H - 30
        c.create_rectangle(x0, y0, x1, y1, outline="#999")
        for v in (0, 64, 128, 192, 255):
            x = x0 + (x1 - x0) * v / 255
            c.create_line(x, y1, x, y1 + 4, fill="#666")
            c.create_text(x, y1 + 14, text=str(v), fill="#444", font=("Segoe UI", 8))
        if img is None:
            c.create_text(self.W // 2, self.H // 2, text="Belum ada gambar", fill="#888")
            return
        rgb = img.convert("RGB").histogram()
        series = {"R": rgb[0:256], "G": rgb[256:512], "B": rgb[512:768], "Gray": img.convert("L").histogram()}
        series = {k: v for k, v in series.items() if self.show[k].get()}
        if not series:
            return
        peak = max(max(v) for v in series.values()) or 1
        for k, h in series.items():
            pts = []
            for i, val in enumerate(h):
                pts += [x0 + (x1 - x0) * i / 255, y1 - (y1 - y0 - 4) * val / peak]
            c.create_line(*pts, fill=_COLORS[k], width=1.5)
        c.create_text(x0 + 4, y0 + 8, anchor="w", fill="#444", font=("Segoe UI", 8),
                      text=f"{self.source.get()}  {img.width}x{img.height}  puncak={peak}")


def open_histogram(app):
    global _instance
    if _instance is not None and _instance.winfo_exists():
        _instance.lift()
        _instance.draw()
        return
    _instance = HistogramWindow(app)
