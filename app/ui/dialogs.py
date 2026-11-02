"""Dialog parameter generik (siap dipakai saat fitur diintegrasikan).

Contoh:
    params = ask_params(app, "Brightness", [Field("beta", "Perubahan", "int", 40, -255, 255)])
    if params is not None:   # None = dibatalkan
        print(params["beta"])
"""
from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk
from typing import Any

IMAGE_TYPES = [("Gambar", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.gif *.webp"), ("Semua file", "*.*")]


@dataclass
class Field:
    key: str
    label: str
    kind: str = "float"              # int | float | choice | text | file
    default: Any = 0
    min: float | None = None
    max: float | None = None
    choices: tuple = ()
    hint: str = ""


def ask_params(parent, title, fields):
    return ParamDialog(parent, title, fields).result


class ParamDialog(tk.Toplevel):
    def __init__(self, parent, title, fields):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.fields = list(fields)
        self.vars: dict[str, tk.StringVar] = {}
        self.result = None

        body = ttk.Frame(self, padding=14)
        body.grid(row=0, column=0)
        for r, f in enumerate(self.fields):
            self._add_row(body, r, f)

        btns = ttk.Frame(self, padding=(14, 0, 14, 12))
        btns.grid(row=1, column=0, sticky="e")
        ttk.Button(btns, text="OK", command=self._ok).pack(side="right")
        ttk.Button(btns, text="Batal", command=self.destroy).pack(side="right", padx=6)
        self.bind("<Return>", lambda _e: self._ok())
        self.bind("<Escape>", lambda _e: self.destroy())

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_reqwidth()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.wait_visibility()
        self.grab_set()
        self.focus_set()
        self.wait_window(self)

    def _add_row(self, body, row, f):
        var = tk.StringVar(value=str(f.default))
        self.vars[f.key] = var
        ttk.Label(body, text=f.label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=4)
        if f.kind in ("int", "float"):
            lo = -1e9 if f.min is None else f.min
            hi = 1e9 if f.max is None else f.max
            step = 1 if f.kind == "int" or (hi - lo) > 20 else 0.1
            w = ttk.Spinbox(body, from_=lo, to=hi, increment=step, textvariable=var, width=14)
        elif f.kind == "choice":
            w = ttk.Combobox(body, values=list(f.choices), textvariable=var, state="readonly", width=24)
        elif f.kind == "file":
            w = ttk.Frame(body)
            ttk.Entry(w, textvariable=var, width=24).pack(side="left")
            ttk.Button(w, text="...", width=3, command=lambda v=var: self._browse(v)).pack(side="left", padx=(4, 0))
        else:
            w = ttk.Entry(body, textvariable=var, width=28)
        w.grid(row=row, column=1, sticky="w", pady=4)
        if f.hint:
            ttk.Label(body, text=f.hint, foreground="#777").grid(row=row, column=2, sticky="w", padx=(8, 0))

    def _browse(self, var):
        path = filedialog.askopenfilename(parent=self, filetypes=IMAGE_TYPES)
        if path:
            var.set(path)

    def _ok(self):
        out = {}
        for f in self.fields:
            raw = self.vars[f.key].get().strip()
            try:
                v = int(float(raw)) if f.kind == "int" else float(raw) if f.kind == "float" else raw
            except ValueError:
                messagebox.showerror("Input tidak valid", f"'{f.label}' harus berupa angka.", parent=self)
                return
            if f.kind in ("int", "float") and ((f.min is not None and v < f.min) or (f.max is not None and v > f.max)):
                messagebox.showerror("Di luar rentang", f"'{f.label}' harus di antara {f.min} dan {f.max}.", parent=self)
                return
            out[f.key] = v
        self.result = out
        self.destroy()
