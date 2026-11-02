"""Panel gambar (ORIGINAL / RESULT) dengan auto-fit. Menerima PIL.Image."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk


class ImagePanel(ttk.Frame):
    def __init__(self, master, title: str, placeholder: str):
        super().__init__(master)
        self.placeholder = placeholder
        self.scale = 1.0
        self.on_render = None            # callback setelah render (update status zoom)
        self._img = None
        self._photo = None
        ttk.Label(self, text=title, font=("Segoe UI", 10, "bold"), anchor="center").pack(fill="x", pady=(2, 0))
        self.canvas = tk.Canvas(self, bg="#2b2b2b", highlightthickness=1, highlightbackground="#888")
        self.canvas.pack(fill="both", expand=True, padx=6, pady=(2, 6))
        self.canvas.bind("<Configure>", lambda _e: self._render())

    def show(self, img) -> None:
        self._img = img
        self._render()

    def _render(self) -> None:
        c = self.canvas
        w, h = c.winfo_width(), c.winfo_height()
        if w < 10 or h < 10:             # belum ter-layout
            return
        c.delete("all")
        if self._img is None:
            self.scale = 1.0
            c.create_text(w // 2, h // 2, text=self.placeholder, fill="#bbbbbb",
                          font=("Segoe UI", 11), justify="center")
        else:
            iw, ih = self._img.size
            self.scale = min(1.0, (w - 4) / iw, (h - 4) / ih)
            im = self._img
            if self.scale < 1.0:
                im = im.resize((max(1, int(iw * self.scale)), max(1, int(ih * self.scale))), Image.LANCZOS)
            self._photo = ImageTk.PhotoImage(im)
            c.create_image(w // 2, h // 2, image=self._photo)
        if self.on_render:
            self.on_render()
