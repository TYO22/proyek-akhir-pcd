"""Status bar sesuai wireframe:  File: ... | Resolusi: ... | Mode: ...      Zoom: ..%"""
from __future__ import annotations

from tkinter import ttk


class StatusBar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, relief="sunken", padding=(8, 3))
        self._info = ttk.Label(self, anchor="w")
        self._info.pack(side="left")
        self._zoom = ttk.Label(self, anchor="e")
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
