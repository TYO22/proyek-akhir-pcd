"""Penghubung menu -> aksi.

Menu yang diklik memanggil `dispatch(app, command_id, label)`.
 - Jika ID terdaftar di HANDLERS -> fungsinya dijalankan.
 - Jika belum -> tampil pesan "belum diimplementasi" (placeholder GUI).

Saat fitur pengolahan citra sudah siap, cukup daftarkan, contoh:

    @register("basic_ops.negative")
    def negative(app):
        app.apply_result(my_negative_function(app.result))   # PIL.Image -> PIL.Image

Daftar semua ID:  python -m app.menu_structure
"""
from __future__ import annotations

import webbrowser
from tkinter import filedialog, messagebox
from typing import Callable

from PIL import Image

from app import config
from app.ui.dialogs import IMAGE_TYPES
from app.ui.histogram_window import open_histogram

HANDLERS: dict[str, Callable] = {}

# Perintah yang boleh dijalankan walau belum ada gambar.
NO_IMAGE_NEEDED = {"file.open", "file.exit", "about.info_tim_developer",
                   "about.tutorial.link_github", "about.tutorial.link_youtube"}


def register(command_id: str):
    def deco(fn):
        HANDLERS[command_id] = fn
        return fn
    return deco


def dispatch(app, command_id: str, label: str) -> None:
    if command_id not in NO_IMAGE_NEEDED and app.result is None:
        messagebox.showinfo("Belum ada gambar", "Buka gambar terlebih dahulu (File > Open...).", parent=app)
        return
    fn = HANDLERS.get(command_id)
    if fn is None:
        app.set_message(f"{label}: belum diimplementasi")
        messagebox.showinfo(
            label,
            f"Fitur '{label}' belum diimplementasi.\n\n"
            f"ID perintah:\n{command_id}\n\n"
            f"Daftarkan di app/handlers.py dengan:\n@register(\"{command_id}\")",
            parent=app)
        return
    fn(app)


# ------------------------------------------------------------------- File
@register("file.open")
def file_open(app):
    path = filedialog.askopenfilename(parent=app, title="Open", filetypes=IMAGE_TYPES)
    if not path:
        return
    try:
        with Image.open(path) as im:
            app.load_image(im.convert("RGB"), path)
    except Exception as exc:
        messagebox.showerror("Gagal membuka gambar", str(exc), parent=app)


@register("file.save_as")
def file_save_as(app):
    path = filedialog.asksaveasfilename(
        parent=app, title="Save As", defaultextension=".png",
        filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp"), ("TIFF", "*.tif")])
    if not path:
        return
    try:
        app.result.save(path)
        app.save_path = path
        app.set_message(f"Tersimpan: {path}")
    except Exception as exc:
        messagebox.showerror("Gagal menyimpan", str(exc), parent=app)


@register("file.save")
def file_save(app):
    if app.save_path:
        app.result.save(app.save_path)
        app.set_message(f"Tersimpan: {app.save_path}")
    else:
        file_save_as(app)


@register("file.reset_result")
def reset_result(app):
    app.apply_result(app.original.copy(), "Reset")


@register("file.histogram")
def histogram(app):
    open_histogram(app)


@register("file.exit")
def exit_app(app):
    app.quit_app()


# ------------------------------------------------------------------ About
@register("about.info_tim_developer")
def info_team(app):
    import tkinter as tk
    from tkinter import ttk
    win = tk.Toplevel(app)
    win.title("Info Tim Developer")
    win.resizable(False, False)
    win.transient(app)
    frm = ttk.Frame(win, padding=18)
    frm.pack()
    ttk.Label(frm, text=config.APP_NAME, font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=2)
    ttk.Label(frm, text=f"\u00a9 {config.TEAM_NAME} ({config.YEAR})").grid(row=1, column=0, columnspan=2, pady=(0, 10))
    for c, head in enumerate(("Nama", "NIM")):
        ttk.Label(frm, text=head, font=("Segoe UI", 9, "bold")).grid(row=2, column=c, sticky="w", padx=8)
    r = 2
    for r, m in enumerate(config.MEMBERS, start=3):
        ttk.Label(frm, text=m["name"]).grid(row=r, column=0, sticky="w", padx=8, pady=2)
        ttk.Label(frm, text=m["nim"]).grid(row=r, column=1, sticky="w", padx=8, pady=2)
    ttk.Button(frm, text="Tutup", command=win.destroy).grid(row=r + 1, column=0, columnspan=2, pady=(14, 0))


@register("about.tutorial.link_github")
def link_github(app):
    webbrowser.open(config.GITHUB_URL)


@register("about.tutorial.link_youtube")
def link_youtube(app):
    webbrowser.open(config.YOUTUBE_URL)
