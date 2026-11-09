"""
FILE    : app/menu_builder.py
PERAN   : "TUKANG GAMBAR MENU". Mengubah data menu (MENUBAR di menu_structure.py)
          menjadi menu bar sungguhan di jendela Tkinter. File ini hanya menyusun
          menu dan mengikatkan klik ke app.run_command(). Ia TIDAK tahu isi aksinya.

DIPANGGIL DARI: 
    app/main_window.py -> _build_layout() -> build_menubar(self)

DUA MODE (config.USE_NATIVE_MENUBAR):
    - False (default) : Menu bar KUSTOM = Frame berisi tombol-tombol (tk.Menubutton),
                        warnanya mengikuti tema gelap di Windows/Linux. Menu dropdown
                        di-style lewat option_add di theme.apply_theme().
    - True            : Menu bar bawaan OS (app.config(menu=...)). Di Windows tetap terang.

ALUR PROSES:
    1. build_menubar(app) -> Untuk tiap judul di MENUBAR (File, Basic Ops, ...) buat menu
       dropdown -> _fill() mengisi item di dalamnya.
    2. _fill(app, menu, children, prefix) (REKURSIF):
       - SEP            -> Garis pemisah.
       - str            -> Item perintah.
       - (label, anak)  -> SUBMENU + _fill lagi.

KONSEP KEYWORD & IDENTIFIER:
    - prefix : Daftar nama menu dari atas, misal: ["basic_ops", "arithmetic"].
    - cid    : ID perintah = prefix + slug(label) -> "basic_ops.arithmetic.add".
               ID inilah yang dikirim ke app.run_command(cid, label).

TRIK "lambda c=cid, l=ch":
    Dalam perulangan, cid dan ch berubah tiap iterasi. Tanpa default argument, semua tombol
    akan memakai nilai TERAKHIR. Dengan "c=cid, l=ch", nilai akan disalin saat lambda dibuat.

PINTASAN KEYBOARD (misal Ctrl+O):
    Diikat dengan bind_all (dua versi: huruf kecil & kapital untuk mengantisipasi Caps Lock).
    Diabaikan jika ada dialog modal terbuka (app.modal_count > 0).
"""

from __future__ import annotations

import tkinter as tk
from app.menu_structure import ACCELERATORS, MENUBAR, SEP, slug

# Fungsi utama untuk membangun menu bar, memeriksa mode kustom atau native
def build_menubar(app) -> None: # fungsi untuk membangun menu bar standar Tkinter, menerima instance aplikasi 'app'
    bar = tk.Menu(app) # Membuat objek Menu utama yang akan dilampirkan ke jendela aplikasi (app)
    for title, children in MENUBAR: # Melakukan iterasi pada setiap item menu tingkat atas (title) dan anak-anaknya (children) dari struktur MENUBAR
        menu = tk.Menu(bar, tearoff=0) # Membuat objek Menu dropdown untuk setiap item tingkat atas, tearoff=0 menonaktifkan fitur pemisahan menu menjadi jendela baru
        bar.add_cascade(label=title, menu=menu) # Menambahkan menu dropdown ke menu bar utama dengan label sesuai 'title'
        _fill(app, menu, children, [slug(title)]) # Memanggil fungsi helper _fill untuk mengisi item-item di dalam menu dropdown secara rekursif
    app.config(menu=bar) # Mengonfigurasi jendela aplikasi agar menggunakan menu bar yang baru saja dibuat

def _build_custom(app) -> None: # Mendefinisikan fungsi untuk membangun menu bar kustom menggunakan widget Frame dan Menubutton
    # Menu bar kustom: harus di-pack SEBELUM area gambar (lihat MainWindow._build_layout). # Komentar asli: peringatan urutan packing layout agar tidak tertimpa
    c = theme.colors() # Mengambil dictionary warna dari objek 'theme' (diasumsikan tersedia di scope global/impor lain) untuk styling
    bar = tk.Frame(app, bg=c["surface"]) # Membuat Frame sebagai wadah menu bar kustom dengan warna latar sesuai tema
    bar.pack(side="top", fill="x") # Meletakkan Frame di bagian atas jendela dan meregangkannya selebar jendela (fill="x")
    tk.Frame(app, height=1, bg=c["border"]).pack(side="top", fill="x")      # garis tipis di bawah menu bar # Membuat Frame setinggi 1 piksel sebagai garis pembatas (border) di bawah menu bar
    for title, children in MENUBAR: # Iterasi melalui setiap menu tingkat atas dan anak-anaknya
        mb = tk.Menubutton(bar, text=title, bg=c["surface"], fg=c["fg"], # Membuat tombol menu (Menubutton) dengan teks, warna latar, dan warna teks sesuai tema
                           activebackground=c["hover"], activeforeground=c["fg"], # Mengatur warna latar dan teks saat tombol di-hover/diklik
                           relief="flat", bd=0, highlightthickness=0, font=theme.font(), # Mengatur gaya visual: tanpa efek 3D (flat), tanpa border, tanpa highlight, dan menggunakan font dari tema
                           padx=theme.px(13), pady=theme.px(7)) # Mengatur padding horizontal dan vertikal menggunakan fungsi konversi piksel dari tema
        mb.pack(side="left") # Meletakkan Menubutton di sebelah kiri secara berurutan
        menu = tk.Menu(mb, tearoff=0)               # menu dropdown harus anak dari Menubutton-nya # Membuat objek Menu dropdown, parent-nya adalah Menubutton yang baru dibuat
        mb.config(menu=menu) # Mengaitkan objek Menu dropdown ke Menubutton agar muncul saat diklik
        _fill(app, menu, children, [slug(title)]) # Mengisi item-item di dalam menu dropdown secara rekursif

def _fill(app, menu: tk.Menu, children, prefix) -> None: # Mendefinisikan fungsi helper rekursif untuk mengisi konten menu, menerima prefix untuk pelacakan ID perintah
    for ch in children: # Iterasi melalui setiap elemen anak di dalam daftar children
        if ch == SEP: # Memeriksa apakah elemen saat ini adalah konstanta pemisah (separator)
            menu.add_separator() # Menambahkan garis pemisah visual di dalam menu
        elif isinstance(ch, str): # Memeriksa apakah elemen saat ini adalah string (yang merepresentasikan perintah/menu item)
            cid = ".".join(prefix + [slug(ch)]) # Membentuk ID perintah unik (cid) dengan menggabungkan prefix dan slug dari nama item, dipisah dengan titik
            accel = ACCELERATORS.get(cid) # Mencari definisi shortcut keyboard (accelerator) untuk ID perintah tersebut dari dictionary ACCELERATORS
            menu.add_command(label=ch, accelerator=accel, # Menambahkan item perintah ke menu dengan label teks dan teks shortcut (accelerator) untuk ditampilkan di UI
                             command=lambda c=cid, l=ch: app.run_command(c, l)) # Mengaitkan perintah dengan fungsi app.run_command, lambda c=cid menangkap nilai loop saat ini (mencegah late-binding bug)
            if accel: # Memeriksa apakah ada shortcut keyboard yang didefinisikan untuk item ini
                key = accel.split("+")[-1] # Mengekstrak tombol keyboard utama dari string shortcut (misal: "Ctrl+S" menjadi "S")
                for seq in (f"<Control-{key.lower()}>", f"<Control-{key.upper()}>"): # Membuat daftar event sequence Tkinter untuk huruf kecil dan besar (misal: <Control-s> dan <Control-S>)
                    app.bind_all(seq, lambda _e, c=cid, l=ch: app.run_command(c, l)) # Mengikat event keyboard secara global ke seluruh aplikasi agar memicu app.run_command saat ditekan
        else: # Jika elemen bukan separator dan bukan string, maka diasumsikan sebagai tuple/list untuk submenu (label, kids)
            label, kids = ch # Membongkar tuple/list menjadi label submenu dan daftar anak-anaknya (kids)
            sub = tk.Menu(menu, tearoff=0) # Membuat objek Menu baru untuk submenu
            menu.add_cascade(label=label, menu=sub) # Menambahkan submenu ke menu parent dengan label yang sesuai
            _fill(app, sub, kids, prefix + [slug(label)]) # Memanggil fungsi _fill secara rekursif untuk mengisi submenu dengan memperbarui prefix