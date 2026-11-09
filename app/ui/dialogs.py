"""
FILE    : app/ui/dialogs.py
PERAN   : "KOTAK POP-UP INPUT PARAMETER". Membuat jendela kecil yang menanyakan
          nilai kepada user (mis. "Nilai threshold?") sebelum sebuah operasi
          pengolahan citra dijalankan. Hasilnya dict {key_field: nilai}.

DIPAKAI OLEH
  - app/handlers.py    : ask_params(app, label, PARAM_SPECS[id]) setiap menu yang punya parameter
  - app/param_specs.py : mengimpor Field & ParamSpec untuk mendefinisikan isi popup tiap menu

KOMPONEN
  IMAGE_TYPES  : filter jenis file untuk dialog buka gambar.
  Field        : (dataclass) deskripsi SATU input di popup:
                    key         nama hasil = NAMA ARGUMEN fungsi backend (mis. "beta")
                    label       teks yang dilihat user
                    kind        "int" | "float" | "choice" | "text" | "file"
                    default     nilai awal
                    min, max    batas rentang (int/float)
                    choices     pilihan dropdown (kind="choice")
                    hint        keterangan kecil di kanan input
                    enabled_when (key_pemicu, nilai): field AKTIF hanya jika field
                                 key_pemicu bernilai 'nilai'. Contoh: input angka
                                 hanya aktif saat Operand = "Konstanta".
                    validate    fungsi cek nilai field: return None = valid, atau teks
                                pesan error (mis. harus ganjil).
  ParamSpec    : (dataclass) daftar Field untuk satu menu + 'check' opsional, yaitu fungsi
                 yang memeriksa HUBUNGAN antar field (mis. "kanan harus > kiri").
  ask_params   : fungsi praktis -> dict hasil, atau None jika dibatalkan.
  ParamDialog  : jendela modal (tk.Toplevel). Modal = jendela utama tidak bisa diklik
                 selama dialog terbuka.

ALUR KERJA ParamDialog
  1. __init__ membuat satu baris (label + input) untuk tiap Field, tombol OK/Batal.
  2. _refresh_enabled() mengaktif/nonaktifkan baris sesuai enabled_when. Dipanggil
     lagi setiap pilihan dropdown berubah (trace pada variabel).
  3. wait_window(): program BERHENTI di sini sampai dialog ditutup.
  4. OK -> _ok(): untuk tiap Field AKTIF: ubah teks ke tipe (int/float), cek rentang,
     jalankan validate. Lalu jalankan ParamSpec.check pada seluruh dict.
     Ada error -> messagebox, dialog tetap terbuka. Valid -> self.result = dict.
     Field NONAKTIF tetap dikirim dengan nilai DEFAULT-nya (kontrak backend).
  5. Batal/Escape -> result tetap None.

WIDGET PER JENIS: int/float -> Spinbox; choice -> Combobox readonly;
                  file -> Entry + tombol "..."; text -> Entry.

TENTANG modal_count: setiap dialog menaikkan app.modal_count agar pintasan keyboard
(Ctrl+O dll) diabaikan saat dialog terbuka (lihat menu_builder.py).
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable

from app import theme

IMAGE_TYPES = [("Gambar", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.gif *.webp"), ("Semua file", "*.*")]


@dataclass
class Field:
    # Satu input di popup (lihat penjelasan atribut di header file).
    key: str
    label: str
    kind: str = "float"
    default: Any = 0
    min: float | None = None
    max: float | None = None
    choices: tuple = ()
    hint: str = ""
    enabled_when: tuple | None = None            # (key_pemicu, nilai_pemicu)
    validate: Callable[[Any], str | None] | None = None


@dataclass
class ParamSpec:
    # Seluruh isi popup satu menu.
    fields: tuple
    check: Callable[[dict], str | None] | None = None


def ask_params(parent, title, spec):
    """Tampilkan popup. 'spec' boleh ParamSpec atau list/tuple Field. Return dict atau None (batal)."""
    return ParamDialog(parent, title, spec).result


def convert_value(f: Field, raw):
    """Ubah teks input ke tipe sesuai f.kind. Melempar ValueError jika bukan angka."""
    if f.kind == "int":
        return int(float(raw))
    if f.kind == "float":
        return float(raw)
    return raw


class ParamDialog(tk.Toplevel):
    def __init__(self, parent, title, spec):
        super().__init__(parent)
        theme.style_window(self)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)                   # selalu di atas jendela induk
        self._parent = parent
        if isinstance(spec, ParamSpec):
            self.fields, self.check = list(spec.fields), spec.check
        else:
            self.fields, self.check = list(spec), None
        self.vars: dict[str, tk.StringVar] = {}  # key -> StringVar (isi kotak input)
        self.rows: dict[str, tuple] = {}         # key -> (label_widget, input_widget)
        self.result = None                       # tetap None kecuali OK dengan input valid

        body = ttk.Frame(self, padding=theme.px(16))
        body.grid(row=0, column=0)
        for r, f in enumerate(self.fields):
            self._add_row(body, r, f)

        btns = ttk.Frame(self, padding=(theme.px(16), 0, theme.px(16), theme.px(14)))
        btns.grid(row=1, column=0, sticky="e")
        ttk.Button(btns, text="OK", style="Accent.TButton", command=self._ok).pack(side="right")
        ttk.Button(btns, text="Batal", command=self.destroy).pack(side="right", padx=theme.px(8))
        self.bind("<Return>", lambda _e: self._ok())
        self.bind("<Escape>", lambda _e: self.destroy())

        # Aktif/nonaktif awal + pantau perubahan field pemicu.
        for f in self.fields:
            self.vars[f.key].trace_add("write", lambda *_a: self._refresh_enabled())
        self._refresh_enabled()

        # Posisikan di tengah-atas jendela induk.
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_reqwidth()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

        self.modal_register(+1)
        try:
            self.wait_visibility()
            self.grab_set()                      # modal
        except tk.TclError:
            pass                                 # beberapa window manager menolak; dialog tetap jalan
        self.focus_set()
        self.wait_window(self)                   # BLOKIR sampai dialog ditutup
        self.modal_register(-1)

    def modal_register(self, delta: int) -> None:
        # Naik/turunkan penghitung dialog terbuka di jendela utama (bila ada).
        if hasattr(self._parent, "modal_count"):
            self._parent.modal_count = max(0, self._parent.modal_count + delta)

    # pembuatan baris
    def _add_row(self, body, row, f):
        var = tk.StringVar(value=str(f.default))
        self.vars[f.key] = var
        lab = ttk.Label(body, text=f.label)
        lab.grid(row=row, column=0, sticky="w", padx=(0, theme.px(14)), pady=theme.px(5))
        if f.kind in ("int", "float"):
            lo = -1e9 if f.min is None else f.min
            hi = 1e9 if f.max is None else f.max
            step = 1 if f.kind == "int" or (hi - lo) > 20 else 0.1   # langkah panah naik/turun
            w = ttk.Spinbox(body, from_=lo, to=hi, increment=step, textvariable=var, width=14)
        elif f.kind == "choice":
            w = ttk.Combobox(body, values=list(f.choices), textvariable=var, state="readonly", width=30)
        elif f.kind == "file":
            w = ttk.Frame(body)
            ttk.Entry(w, textvariable=var, width=26).pack(side="left")
            ttk.Button(w, text="...", width=3, command=lambda v=var: self._browse(v)).pack(
                side="left", padx=(theme.px(4), 0))
        else:
            w = ttk.Entry(body, textvariable=var, width=34)
        w.grid(row=row, column=1, sticky="w", pady=theme.px(5))
        if f.hint:
            ttk.Label(body, text=f.hint, style="Dim.TLabel").grid(
                row=row, column=2, sticky="w", padx=(theme.px(8), 0))
        self.rows[f.key] = (lab, w)

    def _browse(self, var):
        path = filedialog.askopenfilename(parent=self, filetypes=IMAGE_TYPES)
        if path:
            var.set(path)

    # enabled_when
    def _is_enabled(self, f: Field) -> bool:
        if f.enabled_when is None:
            return True
        trigger_key, trigger_value = f.enabled_when
        return self.vars[trigger_key].get() == trigger_value

    @staticmethod
    def _set_widget_state(w, enabled: bool) -> None:
        if isinstance(w, ttk.Combobox):
            w.configure(state="readonly" if enabled else "disabled")
        elif isinstance(w, (ttk.Entry, ttk.Spinbox)):
            w.configure(state="normal" if enabled else "disabled")
        elif isinstance(w, ttk.Button):
            w.configure(state="normal" if enabled else "disabled")
        elif isinstance(w, ttk.Frame):
            for child in w.winfo_children():
                ParamDialog._set_widget_state(child, enabled)

    def _refresh_enabled(self) -> None:
        for f in self.fields:
            on = self._is_enabled(f)
            lab, w = self.rows[f.key]
            self._set_widget_state(w, on)
            lab.configure(style="TLabel" if on else "Dim.TLabel")

    # OK
    def _ok(self):
        out = {}
        for f in self.fields:
            if not self._is_enabled(f):
                # Field nonaktif: kirim nilai DEFAULT (kontrak backend: semua key selalu ada).
                try:
                    out[f.key] = convert_value(f, f.default)
                except (ValueError, TypeError):
                    out[f.key] = f.default
                continue
            raw = self.vars[f.key].get().strip()
            try:
                v = convert_value(f, raw)
            except ValueError:
                messagebox.showerror("Input tidak valid", f"'{f.label}' harus berupa angka.", parent=self)
                return
            if f.kind in ("int", "float") and ((f.min is not None and v < f.min) or (f.max is not None and v > f.max)):
                messagebox.showerror("Di luar rentang", f"'{f.label}' harus di antara {f.min} dan {f.max}.", parent=self)
                return
            if f.validate is not None:
                msg = f.validate(v)
                if msg:
                    messagebox.showerror("Input tidak valid", f"'{f.label}' {msg}", parent=self)
                    return
            out[f.key] = v
        if self.check is not None:                # validasi hubungan antar field
            msg = self.check(out)
            if msg:
                messagebox.showerror("Input tidak valid", msg, parent=self)
                return
        self.result = out
        self.destroy()
