"""Entry point GUI aplikasi PCD.  Jalankan:  python main.py"""
# ============================================================================
# FILE    : main.py
# PERAN   : TITIK MASUK (ENTRY POINT) APLIKASI. File PERTAMA yang dijalankan:
#               python main.py
#
# PERSIAPAN:  pip install -r requirements.txt     (pillow + numpy)
#
# ALUR SAAT PROGRAM DIJALANKAN
#   1. theme.enable_hidpi() : (Windows) aktifkan mode sadar-DPI SEBELUM jendela dibuat,
#      supaya teks & gambar tajam di layar resolusi tinggi. Harus paling awal.
#   2. Impor MainWindow -> Python memuat app/main_window.py beserta modul yang
#      dibutuhkan (config, theme, handlers, menu_builder, ui/*, backend). Saat
#      handlers.py dimuat, decorator @register mengisi kamus HANDLERS.
#   3. MainWindow() membuat jendela:
#        - theme.apply_theme()   -> warna/font/gaya
#        - backend.load_all()    -> memuat semua file algoritma di app/backend/
#        - layout, menu, status bar
#   4. .mainloop() = loop Tkinter: program menunggu klik/keyboard sampai jendela ditutup.
#
# "if __name__ == '__main__'" -> blok ini hanya berjalan jika file dijalankan LANGSUNG
# (bukan saat di-import dari file lain).
#
# ALUR BESAR PENGOLAHAN GAMBAR (ringkas; detail di PANDUAN.md & komentar tiap file)
#   klik menu -> menu_builder -> MainWindow.run_command -> handlers.dispatch
#     -> (popup parameter: param_specs.py + ui/dialogs.py)
#     -> backend.run -> app/backend/<kelompok>.py (ALGORITMA)
#     -> MainWindow.apply_result -> panel RESULT
# ============================================================================

from app import theme

theme.enable_hidpi()                     # harus SEBELUM jendela Tk dibuat

from app.main_window import MainWindow   # noqa: E402  (sengaja diimpor setelah enable_hidpi)


if __name__ == "__main__":
    MainWindow().mainloop()
