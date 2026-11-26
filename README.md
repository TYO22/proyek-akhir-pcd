# PCD Studio – Aplikasi Pengolahan Citra Digital

![Mata Kuliah](https://img.shields.io/badge/mata%20kuliah-Pengolahan%20Citra%20Digital-blue)
![Python](https://img.shields.io/badge/python-3.x-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

Proyek Akhir mata kuliah **Pengolahan Citra Digital (PCD)**: aplikasi desktop berbasis Tkinter untuk membuka citra, menerapkan berbagai operasi pengolahan citra, dan membandingkan hasilnya dengan citra asli secara langsung.

## Daftar Isi

- [Tentang Proyek](#tentang-proyek)
- [Fitur](#fitur)
- [Tampilan Aplikasi](#tampilan-aplikasi)
- [Teknologi](#teknologi)
- [Instalasi](#instalasi)
- [Cara Menjalankan](#cara-menjalankan)
- [Cara Penggunaan](#cara-penggunaan)
- [Struktur Folder](#struktur-folder)
- [Menambah Algoritma Baru](#menambah-algoritma-baru)
- [Anggota Kelompok](#anggota-kelompok)
- [Lisensi](#lisensi)

## Tentang Proyek

PCD Studio dikembangkan sebagai Proyek Akhir mata kuliah Pengolahan Citra Digital. Setiap algoritma diimplementasikan di folder `app/backend/` dan dihubungkan ke menu GUI melalui sistem ID perintah, sehingga menu, parameter, dan algoritma dapat dikelola secara terpisah.

## Fitur

- **File**: buka citra (`Open...`), simpan (`Save`, `Save As`), `Undo`, `Redo`, `Reset Result`, `Histogram`, dan `Exit`.
- **Basic Ops**
  - Negative
  - Aritmetika: Add, Subtract, Multiply, Divide
  - Boolean: NOT, AND, OR, XOR
  - Geometrik: Translation, Rotation, Zooming, Flipping, Cropping
  - Thresholding, Convolution, Fourier Transform
  - Colouring: Binary, Grayscale, RGB, HSV, CMY, YUV, YIQ, Pseudo
- **Enhancement**
  - Brightness, Contrast, Hist. Equalization
  - Smoothing: Lowpass dan Median Filtering (spatial domain), ILPF dan BLPF (frequency domain)
  - Sharpening: Highpass dan Highboost Filtering (spatial domain), IHPF dan BHPF (frequency domain)
  - Geometrics Correction
- **Noise**: Gaussian, Rayleigh, Erlang (Gamma), Exponential, Uniform, dan Impulse.
- **Edge Detection**
  - 1st Differential Gradient: Sobel, Prewitt, Roberts, Compass
  - 2nd Differential Gradient: Laplacian, Laplacian of Gaussian (LoG), Canny
- **Segmentation**: Otsu Thresholding, Adaptive Thresholding, K-Means Clustering.
- **About**: Info Tim Developer, serta tautan tutorial GitHub dan YouTube.

## Tampilan Aplikasi

Jendela utama terdiri dari dua panel, yaitu **ORIGINAL** untuk citra asli dan **RESULT** untuk hasil operasi. Ukuran jendela awal menyesuaikan resolusi layar (85% dari layar), dan panel gambar mendukung zoom menggunakan scroll mouse.

> Tambahkan screenshot di sini, misalnya `![Tampilan](docs/screenshot.png)`.

## Teknologi

- Python 3
- [NumPy](https://numpy.org/): operasi array dan algoritma manual
- [Pillow](https://python-pillow.org/): pemuatan dan penyimpanan citra
- [OpenCV (opencv-python)](https://pypi.org/project/opencv-python/): filter, transformasi, dan deteksi tepi
- [scikit-image](https://scikit-image.org/): dukungan untuk beberapa algoritma
- Tkinter: antarmuka grafis (bawaan Python)

## Instalasi

1. Clone repositori:
   ```bash
   git clone https://github.com/TYO22/proyek-akhir-pcd.git
   cd proyek-akhir-pcd
   ```

2. (Opsional) Buat virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux/macOS
   venv\Scripts\activate         # Windows
   ```

3. Pasang dependensi:
   ```bash
   pip install numpy pillow opencv-python scikit-image
   ```

> Pada Linux, Tkinter mungkin perlu dipasang terpisah, misalnya `sudo apt install python3-tk`.

## Cara Menjalankan

```bash
python main.py
```

## Cara Penggunaan

1. Jalankan aplikasi, lalu pilih **File → Open...** untuk memuat citra.
2. Pilih operasi dari menu **Basic Ops**, **Enhancement**, **Noise**, **Edge Detection**, atau **Segmentation**.
3. Atur parameter pada dialog yang muncul, lalu jalankan.
4. Hasil ditampilkan di panel **RESULT**. Gunakan **Undo** / **Redo** untuk kembali atau maju, atau **Reset Result** untuk membatalkan hasil.
5. Pilih **File → Save** atau **Save As** untuk menyimpan hasil.

## Struktur Folder

```
proyek-akhir-pcd/
├── main.py                  # Entry point aplikasi
├── LICENSE
└── app/
    ├── config.py            # Pengaturan global: nama aplikasi, anggota, URL, ukuran jendela
    ├── theme.py             # Warna, font, dan DPI awareness
    ├── menu_structure.py    # Peta menu (data struktur menu dan ID perintah)
    ├── menu_builder.py      # Membangun menu bar dari menu_structure.py
    ├── handlers.py          # Penangan aksi menu (Open, Save, Undo, About, dll.)
    ├── param_specs.py       # Spesifikasi parameter tiap operasi untuk dialog
    ├── main_window.py       # Jendela utama dan alur eksekusi operasi
    ├── ui/
    │   ├── image_panel.py       # Panel gambar dengan zoom dan fit
    │   ├── dialogs.py           # Dialog parameter dan Info Tim
    │   ├── histogram_window.py  # Jendela histogram
    │   └── status_bar.py        # Status bar (nama file, resolusi, mode, zoom)
    └── backend/
        ├── __init__.py          # Registry algoritma (@register) dan fungsi run()
        ├── common.py            # Fungsi bantu bersama (konvolusi, konversi warna, dll.)
        ├── basic_ops.py         # Basic Ops
        ├── enchancement.py      # Enhancement
        ├── noise.py             # Noise
        ├── edge_detection.py    # Edge Detection
        └── segmentation.py      # Segmentation
```

## Menambah Algoritma Baru

1. Tulis fungsi di file backend yang sesuai, lalu beri dekorator `@register("<id_perintah>")`.
2. Tambahkan item menu dengan ID yang sama di `app/menu_structure.py`.
3. Tambahkan spesifikasi parameter di `app/param_specs.py` jika algoritma memerlukan input.

ID perintah dibentuk dari jalur menu dalam huruf kecil, misalnya `Enhancement > Smoothing > Spatial Domain > Median Filtering` menjadi `enhancement.smoothing.spatial_domain.median_filtering`. Untuk melihat seluruh ID, jalankan:

```bash
python -m app.menu_structure
```

## Anggota Kelompok

| No | Nama | NIM |
|----|------|-----|
| 1 | Muhamad Radityo Pratama | 2407110908 |
| 2 | Aulia Arief | 2407112796 |
| 3 | Yosia Sitompul | 2407114019 |

## Lisensi

Didistribusikan di bawah lisensi MIT. Lihat berkas [LICENSE](LICENSE) untuk detail.

Copyright © 2026 Muhamad Radityo Pratama.