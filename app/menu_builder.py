"""Membangun menu bar Tkinter dari app.menu_structure.MENUBAR."""
from __future__ import annotations

import tkinter as tk

from app.menu_structure import ACCELERATORS, MENUBAR, SEP, slug


def build_menubar(app) -> None:
    bar = tk.Menu(app)
    for title, children in MENUBAR:
        menu = tk.Menu(bar, tearoff=0)
        bar.add_cascade(label=title, menu=menu)
        _fill(app, menu, children, [slug(title)])
    app.config(menu=bar)


def _fill(app, menu: tk.Menu, children, prefix) -> None:
    for ch in children:
        if ch == SEP:
            menu.add_separator()
        elif isinstance(ch, str):
            cid = ".".join(prefix + [slug(ch)])
            accel = ACCELERATORS.get(cid)
            menu.add_command(label=ch, accelerator=accel,
                             command=lambda c=cid, l=ch: app.run_command(c, l))
            if accel:
                key = accel.split("+")[-1]
                for seq in (f"<Control-{key.lower()}>", f"<Control-{key.upper()}>"):
                    app.bind_all(seq, lambda _e, c=cid, l=ch: app.run_command(c, l))
        else:
            label, kids = ch
            sub = tk.Menu(menu, tearoff=0)
            menu.add_cascade(label=label, menu=sub)
            _fill(app, sub, kids, prefix + [slug(label)])
