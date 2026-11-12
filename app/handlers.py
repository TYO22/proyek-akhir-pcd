"""Penghubung menu -> aksi.

Menu yang diklik memanggil `dispatch(app, command_id, label)`:
 1. Ada fungsi di HANDLERS (Open, Save, Undo, Histogram, About, ...)  -> dijalankan.
 2. Tidak ada, tapi ada algoritma di app/backend/ untuk ID itu          -> popup parameter
    (jika ada di param_specs.py) -> algoritma dijalankan di thread latar -> hasil ke RESULT.
 3. Selain itu -> pesan "belum diimplementasi".

Menambah fitur pengolahan citra baru TIDAK perlu mengubah file ini: cukup tulis fungsi
di app/backend/ dengan @register("<id menu>") dan (jika perlu popup) isi param_specs.py.
"""
# ============================================================================
# FILE    : app/handlers.py
# PERAN   : "PUSAT PERINTAH" / DISPATCHER. Di sinilah KLIK MENU diterjemahkan
#           menjadi AKSI NYATA.
#
# ALUR SAAT MENU DIKLIK (inti seluruh aplikasi)
#   1. User klik "Enhancement > Brightness"
#   2. menu_builder.py (lambda) -> app.run_command("enhancement.brightness", "Brightness")
#   3. main_window.py run_command() -> handlers.dispatch(...)
#   4. dispatch() memeriksa berurutan:
#        a. sedang memproses operasi lain (app.busy)?        -> tolak dengan pesan
#        b. perlu gambar tapi belum ada gambar?              -> pesan "buka gambar dulu"
#        c. ID ada di HANDLERS?                              -> jalankan fungsi handler
#        d. backend.is_available(ID)?                        -> _run_backend_command()
#        e. lainnya                                          -> kotak "belum diimplementasi"
#
#   _run_backend_command(app, id, label):
#        1. PARAM_SPECS.get(id) ada? -> ask_params(...) menampilkan popup (ui/dialogs.py).
#           Dibatalkan (None) -> berhenti. Hasilnya dict {key: nilai}.
#        2. _run_in_background(): jalankan backend.run(id, app.result, params) di THREAD
#           terpisah agar jendela tidak "Not Responding" saat komputasi berat.
#           Thread TIDAK BOLEH menyentuh widget Tkinter, jadi hasilnya dititipkan lewat
#           queue.Queue, lalu app.after(30, poll) memeriksa antrean di thread utama GUI.
#        3. Sukses -> app.apply_result(gambar, label). Gagal -> messagebox error;
#           gambar TIDAK berubah.
#
# KAMUS HANDLERS : {"file.open": file_open, ...} diisi otomatis oleh decorator @register.
#   @register("x") di atas def = HANDLERS["x"] = nama_fungsi.
#   !! Ini BERBEDA dari @register milik app/backend/__init__.py (yang menyimpan ALGORITMA).
#
# NO_IMAGE_NEEDED : ID yang boleh dijalankan walau belum ada gambar (Open, Exit, About).
#
# HANDLER YANG ADA
#   file.open, file.save_as, file.save, file.undo, file.redo, file.reset_result,
#   file.histogram, file.exit, about.info_tim_developer, about.tutorial.link_github,
#   about.tutorial.link_youtube
#   Semua menu pengolahan citra (Basic Ops, Enhancement, Noise, Edge Detection,
#   Segmentation) ditangani lewat backend (langkah d).
#
# CATATAN
#   - Pillow (PIL) membuka/menyimpan gambar. Di app, gambar = objek PIL.Image (mode RGB).
#   - ImageOps.exif_transpose: memutar foto HP sesuai metadata orientasi agar tidak miring.
#   - parent=app pada dialog membuat dialog menempel di jendela utama.
# ============================================================================

from __future__ import annotations

import queue
import sys
import threading
import time
import traceback
import webbrowser
from tkinter import filedialog, messagebox
from typing import Callable

from PIL import Image, ImageOps

from app import backend, config, theme
from app.param_specs import PARAM_SPECS
from app.ui.dialogs import IMAGE_TYPES, ask_params
from app.ui.histogram_window import open_histogram

# Kamus global: ID perintah -> fungsi handler. Diisi oleh decorator @register.
HANDLERS: dict[str, Callable] = {}

# Perintah yang boleh dijalankan walau belum ada gambar.
NO_IMAGE_NEEDED = {"file.open", "file.exit", "about.info_tim_developer",
                   "about.tutorial.link_github", "about.tutorial.link_youtube"}

VIEW_HINT = "Scroll = zoom, seret = geser, klik ganda = fit"


def register(command_id: str):
    # Decorator dengan ARGUMEN: menyimpan fungsi ke HANDLERS lalu mengembalikannya apa adanya.
    def deco(fn):
        HANDLERS[command_id] = fn
        return fn
    return deco


def dispatch(app, command_id: str, label: str) -> None:
    # a. Operasi lain sedang berjalan (kecuali Exit yang selalu boleh).
    if app.busy and command_id != "file.exit":
        app.set_message("Masih memproses, tunggu sebentar...")
        return
    # b. Perlu gambar tetapi belum ada.
    if command_id not in NO_IMAGE_NEEDED and app.result is None:
        messagebox.showinfo("Belum ada gambar", "Buka gambar terlebih dahulu (File > Open...).", parent=app)
        return
    # c. Handler GUI (Open, Save, ...).
    fn = HANDLERS.get(command_id)
    if fn is not None:
        fn(app)
        return
    # d. Algoritma backend.
    if backend.is_available(command_id):
        _run_backend_command(app, command_id, label)
        return
    # e. Belum ada sama sekali.
    app.set_message(f"{label}: belum diimplementasi")
    messagebox.showinfo(
        label,
        f"Fitur '{label}' belum diimplementasi.\n\nID perintah:\n{command_id}\n\n"
        f"Tambahkan fungsi di app/backend/ dengan:\n@register(\"{command_id}\")",
        parent=app)


# ------------------------------------------------------------ backend + popup
def _run_backend_command(app, command_id: str, label: str) -> None:
    spec = PARAM_SPECS.get(command_id)
    params: dict = {}
    if spec is not None:
        params = ask_params(app, label, spec)      # popup modal; None = user menekan Batal
        if params is None:
            return
    _run_in_background(app, command_id, label, params)


def _run_in_background(app, command_id: str, label: str, params: dict) -> None:
    app.set_busy(True, f"Memproses {label}...")
    box: queue.Queue = queue.Queue()
    source = app.result                            # gambar masukan (tidak berubah selama busy)

    def work():                                    # berjalan di THREAD LATAR (tanpa menyentuh GUI)
        t0 = time.perf_counter()
        try:
            out = backend.run(command_id, source, params)
            box.put(("ok", out, time.perf_counter() - t0))
        except Exception as exc:                   # noqa: BLE001
            box.put(("err", exc, traceback.format_exc()))

    threading.Thread(target=work, daemon=True).start()

    def poll():                                    # berjalan di thread GUI: cek hasil tiap 30 ms
        try:
            item = box.get_nowait()
        except queue.Empty:
            app.after(30, poll)
            return
        app.set_busy(False)
        if item[0] == "ok":
            out, secs = item[1], item[2]
            app.apply_result(out, label)
            app.set_message(f"{out.width}x{out.height} px, {secs:.2f} dtk")
        else:
            exc = item[1]
            print(item[2], file=sys.stderr)        # detail error lengkap di terminal
            app.set_message(f"{label}: gagal")
            messagebox.showerror(f"Gagal: {label}", f"{type(exc).__name__}: {exc}", parent=app)

    app.after(30, poll)


# ------------------------------------------------------------------- File
@register("file.open")
def file_open(app):
    path = filedialog.askopenfilename(parent=app, title="Open", filetypes=IMAGE_TYPES)
    if not path:
        return
    try:
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im)       # luruskan orientasi foto HP
            app.load_image(im.convert("RGB"), path)
        app.set_message(VIEW_HINT)
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
        app.result.save(path)                      # format ditentukan dari ekstensi
        app.save_path = path
        app.set_message(f"Tersimpan: {path}")
    except Exception as exc:
        messagebox.showerror("Gagal menyimpan", str(exc), parent=app)


@register("file.save")
def file_save(app):
    if app.save_path:
        try:
            app.result.save(app.save_path)
            app.set_message(f"Tersimpan: {app.save_path}")
        except Exception as exc:
            messagebox.showerror("Gagal menyimpan", str(exc), parent=app)
    else:
        file_save_as(app)                          # belum pernah disimpan -> tanya lokasi


@register("file.undo")
def undo(app):
    app.undo()


@register("file.redo")
def redo(app):
    app.redo()


@register("file.reset_result")
def reset_result(app):
    # Kembalikan hasil ke gambar asli. Reset sendiri bisa di-Undo.
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
    theme.style_window(win)
    win.title("Info Tim Developer")
    win.resizable(False, False)
    win.transient(app)
    frm = ttk.Frame(win, padding=theme.px(22))
    frm.pack()
    ttk.Label(frm, text=config.APP_NAME, style="Heading.TLabel").grid(row=0, column=0, columnspan=2)
    ttk.Label(frm, text=f"\u00a9 {config.TEAM_NAME} ({config.YEAR})", style="Dim.TLabel").grid(
        row=1, column=0, columnspan=2, pady=(0, theme.px(12)))
    for c, head in enumerate(("Nama", "NIM")):
        ttk.Label(frm, text=head, font=theme.font(0, True)).grid(row=2, column=c, sticky="w", padx=theme.px(10))
    r = 2
    for r, m in enumerate(config.MEMBERS, start=3):
        ttk.Label(frm, text=m["name"]).grid(row=r, column=0, sticky="w", padx=theme.px(10), pady=theme.px(3))
        ttk.Label(frm, text=m["nim"]).grid(row=r, column=1, sticky="w", padx=theme.px(10), pady=theme.px(3))
    ttk.Button(frm, text="Tutup", style="Accent.TButton", command=win.destroy).grid(
        row=r + 1, column=0, columnspan=2, pady=(theme.px(16), 0))


@register("about.tutorial.link_github")
def link_github(app):
    webbrowser.open(config.GITHUB_URL)


@register("about.tutorial.link_youtube")
def link_youtube(app):
    webbrowser.open(config.YOUTUBE_URL)
