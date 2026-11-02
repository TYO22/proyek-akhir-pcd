"""Jendela utama 1024x768 sesuai wireframe "A1 & A2: Main Window Fix"."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app import config, handlers
from app.menu_builder import build_menubar
from app.ui.image_panel import ImagePanel
from app.ui.status_bar import StatusBar


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        w, h = config.WINDOW_SIZE
        self.title(config.window_title())
        self.geometry(f"{w}x{h}")
        self.resizable(False, False)

        self.original = None          # PIL.Image
        self.result = None            # PIL.Image
        self.path = None
        self.save_path = None
        self.last_op = ""
        self.listeners: list = []     # callback dipanggil tiap gambar berubah (mis. histogram)
        self._message = ""

        self._build_layout()
        build_menubar(self)
        self.protocol("WM_DELETE_WINDOW", self.quit_app)
        self.refresh()

    # ----------------------------------------------------------------- layout
    def _build_layout(self) -> None:
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side="bottom", fill="x")

        body = ttk.Frame(self, padding=6)
        body.pack(fill="both", expand=True)
        body.columnconfigure((0, 1), weight=1, uniform="col")
        body.rowconfigure(0, weight=1)
        self.panel_original = ImagePanel(body, "ORIGINAL", "[Gambar Asli]\n\nFile > Open... untuk membuka gambar")
        self.panel_result = ImagePanel(body, "RESULT", "[Hasil Operasi]")
        self.panel_original.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
        self.panel_result.grid(row=0, column=1, sticky="nsew", padx=(3, 0))
        self.panel_result.on_render = self._update_status

    # --------------------------------------------------------- API untuk fitur
    def load_image(self, img, path) -> None:
        """Muat gambar baru (PIL.Image RGB) ke ORIGINAL dan RESULT."""
        self.original, self.result = img, img.copy()
        self.path, self.save_path, self.last_op, self._message = path, None, "", ""
        self.refresh()

    def apply_result(self, img, label: str = "") -> None:
        """Tampilkan hasil operasi (PIL.Image) di panel RESULT."""
        self.result, self.last_op, self._message = img, label, ""
        self.refresh()

    def set_message(self, text: str) -> None:
        self._message = text
        self._update_status()

    def run_command(self, command_id: str, label: str) -> None:
        handlers.dispatch(self, command_id, label)

    def quit_app(self) -> None:
        self.destroy()

    # ---------------------------------------------------------------- tampilan
    def refresh(self) -> None:
        self.panel_original.show(self.original)
        self.panel_result.show(self.result)
        self._update_status()
        for cb in list(self.listeners):
            cb()

    def _update_status(self) -> None:
        if self.result is None:
            self.status_bar.update_status(message=self._message)
            return
        import os
        name = os.path.basename(self.path) if self.path else "-"
        if self.last_op:
            name_info = name
            msg = f"Operasi: {self.last_op}" + (f" - {self._message}" if self._message else "")
        else:
            name_info, msg = name, self._message
        self.status_bar.update_status(name_info, self.result.size, self.result.mode,
                                      round(self.panel_result.scale * 100), msg)
