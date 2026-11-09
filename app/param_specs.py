"""Definisi POPUP tiap menu: ID perintah -> ParamSpec (daftar Field + validasi).

Menu yang TIDAK ada di sini (Negative, NOT, Grayscale, Otsu) tidak punya parameter,
jadi langsung dijalankan tanpa popup.

Mengubah isi popup (label, default, rentang, pilihan) cukup di file ini.
Nama `key` pada Field = nama argumen fungsi backend. Ringkasan kontrak:
    python -m app.param_specs            (atau lihat docs/BACKEND_CONTRACT.md)
"""
# ↑ Docstring (komentar multi-baris) yang menjelaskan fungsi file ini.
#   - Setiap menu punya "ID perintah" (misal "enhancement.brightness")
#   - ID tersebut dipetakan ke ParamSpec (daftar field + validator)
#   - Menu yang tidak ada di sini = tidak butuh popup, langsung jalan


from __future__ import annotations
from app.ui.dialogs import Field, ParamSpec

# Fungsi pembuat ParamSpec untuk tiap menu. Mempermudah penulisan & konsistensi.
def spec(*fields, check=None) -> ParamSpec:
    return ParamSpec(tuple(fields), check)

# Fungsi untuk memeriksa input user
def _odd(v):    
    return None if int(v) % 2 == 1 else "harus bilangan ganjil."

# Fungsi untuk memeriksa input kernel kustom (matriks angka)
def _kernel(text):
    rows = [r for r in text.replace("\n", ";").split(";") if r.strip()]
    
    try:
        data = [[float(x) for x in r.replace(",", " ").split()] for r in rows]
    except ValueError:
        return "hanya boleh berisi angka. Contoh: 0 -1 0; -1 5 -1; 0 -1 0"
    if not data or len({len(r) for r in data}) != 1:
        return "setiap baris harus sama panjang. Contoh: 0 -1 0; -1 5 -1; 0 -1 0"
    if len(data) % 2 == 0 or len(data[0]) % 2 == 0:
        return "harus berukuran ganjil (3x3, 5x5, ...)."
    
    return None

# Pilihan mode untuk operasi aritmetika/boolean:
_MODES = ("Konstanta", "Gambar kedua")

# Helper untuk membuat field operand aritmetika/boolean
def operand(label, default, vmin, vmax, kind="float"):
    return (
        # Field 1: Dropdown pilih mode (Konstanta / Gambar kedua)
        Field("mode", "Operand", "choice", _MODES[0], choices=_MODES),
        
        # Field 2: Input angka (Konstanta)
        Field("value", label, kind, default, vmin, vmax, enabled_when=("mode", _MODES[0])),
        
        # Field 3: Input file gambar (Gambar kedua)
        Field("file", "Gambar kedua", "file", "", enabled_when=("mode", _MODES[1])),
    )

# Helper untuk membuat dropdown "Tampilan" pada operasi warna
def channel_view(*channels):
    return Field("view", "Tampilan", "choice", "Komposit", choices=("Komposit",) + channels)

_D0 = Field("d0", "Cutoff D0 (piksel)", "float", 40, 1, 5000)
# Parameter cutoff frequency untuk filter frekuensi (lowpass/highpass).
# Nama key: "d0", tipe: float, default: 40, rentang: 1 - 5000

_ORDER = Field("order", "Orde n", "int", 2, 1, 10)
# Orde untuk filter Butterworth (orde 1, 2, 3, dst).
# Semakin tinggi orde, semakin tajam transisi filter.

_FREQ_MODES = ("Highpass murni", "Tambahkan ke citra asli (sharpen)")
# Pilihan mode untuk operasi sharpening frekuensi.

_FMODE = Field("mode", "Mode", "choice", _FREQ_MODES[1], choices=_FREQ_MODES)
# Field mode untuk sharpening frekuensi.

_DIR = Field("direction", "Arah", "choice", "Magnitude",
             choices=("Magnitude", "Horizontal (Gx)", "Vertical (Gy)"))
# Pilihan arah untuk deteksi tepi gradient (Sobel, Prewitt, Robert).
#   - Magnitude = gabung Gx dan Gy
#   - Horizontal = hanya Gx (tepian vertikal)
#   - Vertical = hanya Gy (tepian horizontal)

_THR = Field("threshold", "Threshold 0-255 (0 = tanpa)", "int", 0, 0, 255)
# Nilai threshold untuk deteksi tepi. 0 = tanpa threshold.

_RADIAL, _SHEAR = "Distorsi radial (barrel/pincushion)", "Kemiringan (shear)"
# Dua jenis koreksi geometrik:
#   - Radial = distorsi lensa (barrel/pincushion)
#   - Shear = kemiringan/miring

_PRESETS = ("Box Blur 3x3", "Gaussian 3x3", "Sharpen", "Emboss", "Laplacian", "Custom")
# Pilihan kernel preset untuk operasi konvolusi.

_CMAPS = ("Jet", "Hot", "Rainbow", "Ocean", "Cool", "Bone", "Turbo", "Viridis")
# Pilihan colormap untuk pseudo-coloring (pewarnaan palsu).



# DICTIONARY UTAMA: PARAM_SPECS
# Fungsi: memetakan ID perintah → ParamSpec (daftar field + validator).
# Key = ID perintah (string), Value = ParamSpec
PARAM_SPECS: dict[str, ParamSpec] = {
    # ↑ Type hint: dictionary dengan key string dan value ParamSpec
    
    # ============================================================
    # BASIC OPS: Operasi dasar (aritmetika, boolean, geometrik, dll)
    # ============================================================
    
    # --- Aritmetika ---
    "basic_ops.arithmetic.add": spec(*operand("Nilai konstanta", 50, -255, 255)),
    # ↑ Menu "Add": tampilkan popup operand dengan label "Nilai konstanta",
    #   default 50, rentang -255 sampai 255.
    #   *operand(...) = unpack tuple hasil operand() jadi 3 argumen terpisah.
    
    "basic_ops.arithmetic.substract": spec(*operand("Nilai konstanta", 50, -255, 255)),
    # ↑ Menu "Subtract": sama seperti add, tapi untuk pengurangan.
    
    "basic_ops.arithmetic.multiply": spec(*operand("Faktor konstanta", 1.5, 0, 10)),
    # ↑ Menu "Multiply": kalikan dengan konstanta (default 1.5, rentang 0-10).
    
    "basic_ops.arithmetic.divide": spec(*operand("Pembagi konstanta", 2, 0.1, 255)),
    # ↑ Menu "Divide": bagi dengan konstanta (default 2, rentang 0.1-255).
    #   Min 0.1 (bukan 0) untuk hindari pembagian dengan nol.
    
    # --- Boolean ---
    "basic_ops.boolean.and": spec(*operand("Nilai konstanta (0-255)", 128, 0, 255, "int")),
    # ↑ Operasi AND boolean. kind="int" karena nilai harus integer 0-255.
    
    "basic_ops.boolean.or": spec(*operand("Nilai konstanta (0-255)", 128, 0, 255, "int")),
    "basic_ops.boolean.xor": spec(*operand("Nilai konstanta (0-255)", 128, 0, 255, "int")),
    # ↑ OR dan XOR: sama seperti AND, hanya operasi logikanya berbeda.
    
    # --- Geometrik ---
    "basic_ops.geometrics.translation": spec(
        Field("dx", "Geser X (px)", "int", 30, -5000, 5000),
        Field("dy", "Geser Y (px)", "int", 30, -5000, 5000)),
    # ↑ Translasi (geser) gambar. dx = geser horizontal, dy = geser vertikal.
    #   Rentang besar (-5000 sampai 5000) untuk gambar beresolusi tinggi.
    
    "basic_ops.geometrics.rotation": spec(
        Field("angle", "Sudut (derajat, + = berlawanan jarum jam)", "float", 30, -360, 360),
        Field("scale", "Skala", "float", 1.0, 0.1, 5),
        Field("expand", "Perluas kanvas", "choice", "Ya", choices=("Ya", "Tidak"))),
    # ↑ Rotasi gambar:
    #   - angle: sudut rotasi (positif = berlawanan jarum jam)
    #   - scale: faktor skala (1.0 = ukuran asli)
    #   - expand: apakah kanvas diperluas agar gambar tidak terpotong
    
    "basic_ops.geometrics.zooming": spec(
        Field("factor", "Faktor zoom", "float", 1.5, 0.1, 5),
        Field("interpolation", "Interpolasi", "choice", "Bilinear",
              choices=("Nearest", "Bilinear", "Bicubic", "Lanczos"))),
    # ↑ Zoom gambar:
    #   - factor: faktor perbesar (1.5 = 150%)
    #   - interpolation: metode interpolasi (semakin kompleks = semakin halus)
    
    "basic_ops.geometrics.flipping": spec(
        Field("mode", "Arah", "choice", "Horizontal",
              choices=("Horizontal", "Vertical", "Horizontal + Vertical"))),
    # ↑ Flip/mirror gambar: horizontal, vertikal, atau keduanya.
    
    "basic_ops.geometrics.cropping": spec(
        Field("left", "Kiri (%)", "float", 10, 0, 99),
        Field("top", "Atas (%)", "float", 10, 0, 99),
        Field("right", "Kanan (%)", "float", 90, 1, 100),
        Field("bottom", "Bawah (%)", "float", 90, 1, 100),
        check=lambda p: ("Kanan harus lebih besar dari Kiri." if p["right"] <= p["left"]
                         else "Bawah harus lebih besar dari Atas." if p["bottom"] <= p["top"] else None)),
    # ↑ Crop/potong gambar berdasarkan persentase.
    #   check = validator lambda:
    #     - Jika right <= left → error "Kanan harus lebih besar dari Kiri"
    #     - Jika bottom <= top → error "Bawah harus lebih besar dari Atas"
    #     - Jika keduanya valid → return None (tidak ada error)
    
    "basic_ops.thresholding": spec(
        Field("threshold", "Nilai threshold", "int", 128, 0, 255),
        Field("kind", "Tipe", "choice", "Binary",
              choices=("Binary", "Binary Inverse", "Truncate", "To Zero"))),
    # ↑ Thresholding dasar: ubah gambar jadi biner berdasarkan nilai threshold.
    #   - Binary: pixel > threshold → 255, sisanya → 0
    #   - Binary Inverse: kebalikan Binary
    #   - Truncate: pixel > threshold → threshold, sisanya tetap
    #   - To Zero: pixel > threshold → tetap, sisanya → 0
    
    "basic_ops.convolution": spec(
        Field("preset", "Kernel", "choice", "Sharpen", choices=_PRESETS),
        Field("custom", "Kernel custom", "text", "0 -1 0; -1 5 -1; 0 -1 0",
              hint="baris dipisah ';'", enabled_when=("preset", "Custom"), validate=_kernel),
        Field("normalize", "Normalisasi (bagi jumlah kernel)", "choice", "Tidak", choices=("Tidak", "Ya"))),
    # ↑ Konvolusi dengan kernel:
    #   - preset: pilih kernel dari daftar preset
    #   - custom: input kernel manual (hanya aktif jika preset = "Custom")
    #     validate=_kernel → pakai validator _kernel() untuk cek format
    #   - normalize: apakah kernel dinormalisasi (dibagi jumlah total)
    
    "basic_ops.fourier_transform": spec(
        Field("view", "Tampilan spektrum", "choice", "Magnitude (log)", choices=("Magnitude (log)", "Phase"))),
    # ↑ Transformasi Fourier: tampilkan spektrum frekuensi.
    #   - Magnitude (log): magnitudo dalam skala log (lebih mudah dilihat)
    #   - Phase: fase dari spektrum
    
    # --- Colouring ---
    "basic_ops.colouring.binary": spec(
        Field("method", "Metode", "choice", "Manual", choices=("Manual", "Otsu (otomatis)")),
        Field("threshold", "Threshold", "int", 128, 0, 255, enabled_when=("method", "Manual"))),
    # ↑ Binerisasi dengan 2 metode:
    #   - Manual: user tentukan threshold sendiri
    #   - Otsu: threshold dihitung otomatis oleh algoritma Otsu
    #   Field threshold hanya aktif jika method = "Manual"
    
    "basic_ops.colouring.rgb": spec(
        Field("view", "Tampilan", "choice", "Asli", choices=("Asli", "Red", "Green", "Blue"))),
    # ↑ Tampilkan kanal RGB: asli (komposit), atau satu kanal saja (R/G/B).
    
    "basic_ops.colouring.hsv": spec(channel_view("Hue", "Saturation", "Value")),
    # ↑ Tampilkan kanal HSV: Hue (warna), Saturation (kejenuhan), Value (kecerahan).
    
    "basic_ops.colouring.cmy": spec(channel_view("Cyan", "Magenta", "Yellow")),
    "basic_ops.colouring.yuv": spec(channel_view("Y", "U", "V")),
    "basic_ops.colouring.yiq": spec(channel_view("Y", "I", "Q")),
    # ↑ Tampilkan kanal warna lain: CMY, YUV, YIQ (format warna berbeda).
    
    "basic_ops.colouring.pseudo": spec(Field("cmap", "Colormap", "choice", "Jet", choices=_CMAPS)),
    # ↑ Pseudo-coloring: ubah gambar grayscale jadi berwarna pakai colormap.
    #   Pilihan: Jet, Hot, Rainbow, dst.
    
    
    # ============================================================
    # ENHANCEMENT: Perbaikan kualitas gambar
    # ============================================================
    
    "enhancement.brightness": spec(Field("beta", "Perubahan kecerahan", "int", 40, -255, 255)),
    # ↑ Atur kecerahan: beta positif = lebih terang, negatif = lebih gelap.
    
    "enhancement.contrast": spec(Field("alpha", "Faktor kontras", "float", 1.5, 0.1, 5)),
    # ↑ Atur kontras: alpha > 1 = kontras naik, alpha < 1 = kontras turun.
    
    "enhancement.hist_equalization": spec(
        Field("mode", "Mode", "choice", "Luminance (YCrCb)",
              choices=("Luminance (YCrCb)", "Per kanal RGB", "Grayscale"))),
    # ↑ Histogram equalization (perbaikan kontras otomatis):
    #   - Luminance (YCrCb): hanya perbaiki kecerahan, warna tetap
    #   - Per kanal RGB: perbaiki tiap kanal terpisah (bisa ubah warna)
    #   - Grayscale: konversi ke grayscale dulu, baru equalize
    
    "enhancement.smoothing.spatial_domain.lowpass_filtering": spec(
        Field("size", "Ukuran kernel (ganjil)", "int", 5, 3, 51, validate=_odd),
        Field("kind", "Tipe", "choice", "Gaussian", choices=("Mean", "Gaussian"))),
    # ↑ Lowpass filter (blur) di domain spasial:
    #   - size: ukuran kernel (harus ganjil, divalidasi oleh _odd)
    #   - kind: Mean (rata-rata) atau Gaussian (lebih halus)
    
    "enhancement.smoothing.spatial_domain.median_filtering": spec(
        Field("size", "Ukuran kernel (ganjil)", "int", 3, 3, 51, validate=_odd)),
    # ↑ Median filter: bagus untuk menghilangkan noise impulse (salt & pepper).
    
    "enhancement.smoothing.frequency_domain.ilpf": spec(_D0),
    # ↑ Ideal Lowpass Filter: hanya butuh parameter cutoff D0.
    
    "enhancement.smoothing.frequency_domain.blpf": spec(_D0, _ORDER),
    # ↑ Butterworth Lowpass Filter: butuh D0 dan orde n.
    
    "enhancement.sharpening.spatial_domain.highpass_filtering": spec(
        Field("mode", "Mode", "choice", _FREQ_MODES[1], choices=_FREQ_MODES)),
    # ↑ Highpass filter (sharpen) di domain spasial.
    
    "enhancement.sharpening.spatial_domain.highboost_filtering": spec(
        Field("A", "Faktor boost A (>=1)", "float", 1.8, 1, 10),
        Field("size", "Ukuran kernel blur (ganjil)", "int", 5, 3, 51, validate=_odd)),
    # ↑ High-boost filtering: perkuat tepi dengan faktor A.
    #   A = 1 → highpass biasa, A > 1 → gambar asli + A * highpass
    
    "enhancement.sharpening.frequency_domain.ihpf": spec(_D0, _FMODE),
    # ↑ Ideal Highpass Filter di domain frekuensi.
    
    "enhancement.sharpening.frequency_domain.bhpf": spec(_D0, _ORDER, _FMODE),
    # ↑ Butterworth Highpass Filter di domain frekuensi.
    
    "enhancement.geometrics_correction": spec(
        Field("mode", "Jenis koreksi", "choice", _RADIAL, choices=(_RADIAL, _SHEAR)),
        Field("k1", "k1 (radial)", "float", 0.2, -1, 1, enabled_when=("mode", _RADIAL)),
        Field("k2", "k2 (radial)", "float", 0.0, -1, 1, enabled_when=("mode", _RADIAL)),
        Field("shear", "Sudut shear (derajat)", "float", 5, -45, 45, enabled_when=("mode", _SHEAR))),
    # ↑ Koreksi distorsi geometrik:
    #   - Radial: koreksi distorsi lensa (barrel/pincushion) dengan k1, k2
    #   - Shear: koreksi kemiringan dengan sudut shear
    #   Field k1, k2 hanya aktif jika mode = Radial
    #   Field shear hanya aktif jika mode = Shear
    
    
    # ============================================================
    # NOISE: Penambahan noise ke gambar
    # ============================================================
    
    "noise.gaussian_noise": spec(
        Field("mean", "Mean", "float", 0, -128, 128),
        Field("sigma", "Sigma (std dev)", "float", 25, 0, 128)),
    # ↑ Noise Gaussian: distribusi normal dengan mean dan sigma (standar deviasi).
    
    "noise.rayleigh_noise": spec(Field("scale", "Scale (b)", "float", 20, 0.1, 128)),
    # ↑ Noise Rayleigh: distribusi Rayleigh dengan parameter scale b.
    
    "noise.erlang_gamma_noise": spec(
        Field("k", "Shape k (bilangan bulat)", "int", 2, 1, 20),
        Field("scale", "Scale", "float", 10, 0.1, 100)),
    # ↑ Noise Erlang/Gamma: distribusi Gamma dengan shape k dan scale.
    
    "noise.exponential_noise": spec(Field("scale", "Scale", "float", 20, 0.1, 128)),
    # ↑ Noise Eksponensial: distribusi eksponensial dengan parameter scale.
    
    "noise.uniform_noise": spec(
        Field("low", "Batas bawah", "float", -30, -255, 255),
        Field("high", "Batas atas", "float", 30, -255, 255),
        check=lambda p: "Batas atas harus lebih besar dari batas bawah." if p["high"] <= p["low"] else None),
    # ↑ Noise Uniform: distribusi seragam antara low dan high.
    #   Validator: high harus > low.
    
    "noise.impulse_noise": spec(
        Field("p_salt", "Salt (%)", "float", 5, 0, 50),
        Field("p_pepper", "Pepper (%)", "float", 5, 0, 50),
        check=lambda p: "Salt + Pepper tidak boleh lebih dari 100%." if p["p_salt"] + p["p_pepper"] > 100 else None),
    # ↑ Noise Impulse (salt & pepper):
    #   - p_salt: persentase pixel putih (255)
    #   - p_pepper: persentase pixel hitam (0)
    #   Validator: total salt + pepper tidak boleh > 100%
    
    
    # ============================================================
    # EDGE DETECTION: Deteksi tepi
    # ============================================================
    
    "edge_detection.1_st_differential_gradient.sobel": spec(_DIR, _THR),
    "edge_detection.1_st_differential_gradient.prewit": spec(_DIR, _THR),
    "edge_detection.1_st_differential_gradient.robert": spec(_DIR, _THR),
    # ↑ Deteksi tepi orde pertama (gradient): Sobel, Prewitt, Robert.
    #   Semua pakai parameter direction (arah) dan threshold.
    
    "edge_detection.2_nd_differential_gradient.laplacian": spec(
        Field("neighbors", "Kernel", "choice", "8-tetangga", choices=("4-tetangga", "8-tetangga")), _THR),
    # ↑ Laplacian (orde kedua): pilih kernel 4-tetangga atau 8-tetangga.
    
    "edge_detection.2_nd_differential_gradient.laplacian_of_gaussian_log": spec(
        Field("sigma", "Sigma", "float", 1.4, 0.1, 10),
        Field("mode", "Keluaran", "choice", "Zero-crossing", choices=("Magnitude", "Zero-crossing")),
        Field("threshold", "Threshold 0-255", "int", 5, 0, 255)),
    # ↑ Laplacian of Gaussian (LoG):
    #   - sigma: standar deviasi Gaussian blur awal
    #   - mode: Magnitude (magnitudo LoG) atau Zero-crossing (titik nol)
    #   - threshold: untuk zero-crossing
    
    "edge_detection.2_nd_differential_gradient.canny": spec(
        Field("low", "Threshold bawah", "int", 80, 0, 255),
        Field("high", "Threshold atas", "int", 160, 0, 255),
        Field("blur", "Sigma blur awal (0 = tanpa)", "float", 1.0, 0, 10),
        check=lambda p: "Threshold atas tidak boleh lebih kecil dari threshold bawah." if p["high"] < p["low"] else None),
    # ↑ Canny Edge Detector (paling populer):
    #   - low, high: threshold untuk hysteresis
    #   - blur: Gaussian blur awal (sigma)
    #   Validator: high harus >= low
    
    "edge_detection.compass": spec(_THR),
    # ↑ Compass edge detection: deteksi tepi dengan kernel kompas (8 arah).
    
    
    # ============================================================
    # SEGMENTATION: Segmentasi gambar
    # ============================================================
    
    "segmentation.adaptive_thresholding": spec(
        Field("block", "Ukuran blok (ganjil)", "int", 11, 3, 199, validate=_odd),
        Field("c", "Konstanta C", "float", 2, -50, 50),
        Field("method", "Metode", "choice", "Gaussian", choices=("Mean", "Gaussian"))),
    # ↑ Adaptive thresholding: threshold berbeda untuk tiap blok gambar.
    #   - block: ukuran blok (harus ganjil)
    #   - c: konstanta yang dikurangi dari mean/weighted mean
    #   - method: Mean (rata-rata) atau Gaussian (weighted)
    
    "segmentation.k_means_clustering": spec(Field("k", "Jumlah klaster K", "int", 4, 2, 12)),
    # ↑ K-Means clustering: segmentasi berdasarkan warna.
    #   k = jumlah klaster/warna yang diinginkan.
}






# Generate dokumentasi otomatis dalam format Markdown
def contract_markdown() -> str:
    # ↑ Fungsi untuk generate dokumentasi otomatis dalam format Markdown.
    #   Digunakan untuk membuat file BACKEND_CONTRACT.md.
    
    from app.menu_structure import command_paths
    # ↑ Import fungsi untuk dapat daftar semua ID perintah dan path menu-nya.
    
    paths = command_paths()
    # ↑ paths = dictionary {command_id: "path menu di UI"}
    #   Contoh: {"basic_ops.arithmetic.add": "Basic Ops > Arithmetic > Add"}
    
    lines = [
        "# Kontrak Backend",
        "",
        "Setiap fungsi backend didaftarkan dengan `@register(\"<id>\")` di folder `app/backend/`.",
        "",
        "- **Masukan**: `img` = `numpy.ndarray` uint8 RGB `(H, W, 3)` + parameter di bawah sebagai `**kwargs`",
        "- **Keluaran**: `numpy.ndarray` (uint8 / float / bool; 2D atau 3 kanal; ukuran boleh berubah)",
        "- Parameter bernilai `file` berisi **path** gambar kedua (string); backend yang membukanya.",
        "- Parameter yang nonaktif di popup (mis. `value` saat Operand = Gambar kedua) tetap dikirim dengan nilai default.",
        "",
    ]
    # ↑ Header dokumentasi Markdown.
    
    for cid, path in paths.items():
        # ↑ Loop semua ID perintah dan path menu-nya.
        
        if cid.startswith(("file.", "about.")):
            continue
            # ↑ Skip perintah file (open, save) dan about (info aplikasi).
            #   Karena bukan operasi pengolahan gambar.
        
        lines.append(f"## {path}")
        # ↑ Tambahkan heading level 2 dengan nama path menu.
        
        lines.append(f"`@register(\"{cid}\")`")
        # ↑ Tampilkan decorator yang dipakai di backend.
        
        lines.append("")
        
        sp = PARAM_SPECS.get(cid)
        # ↑ Ambil ParamSpec untuk ID perintah ini (None jika tidak ada).
        
        if sp is None:
            lines += ["`def fn(img)`: tanpa parameter (langsung dijalankan).", ""]
            # ↑ Jika tidak ada ParamSpec → fungsi backend tidak butuh parameter.
            continue
        
        # Tambahkan tabel Markdown untuk parameter
        lines += ["| Parameter | Tipe | Default | Rentang / Pilihan |", "|---|---|---|---|"]
        # ↑ Header tabel: Parameter, Tipe, Default, Rentang/Pilihan
        
        for f in sp.fields:
            # ↑ Loop semua Field di ParamSpec.
            
            rng = ", ".join(f.choices) if f.kind == "choice" else (
                f"{f.min:g} .. {f.max:g}" if f.kind in ("int", "float") else "-")
            # ↑ Tentukan isi kolom "Rentang / Pilihan":
            #   - Jika kind = "choice" → tampilkan semua pilihan (dipisah koma)
            #   - Jika kind = "int" atau "float" → tampilkan rentang min..max
            #   - Lainnya → tampilkan "-"
            
            dflt = f.default if f.default != "" else "(kosong)"
            # ↑ Jika default kosong → tampilkan "(kosong)"
            
            lines.append(f"| `{f.key}` | {f.kind} | {dflt} | {rng} |")
            # ↑ Tambahkan baris tabel: key, tipe, default, rentang
        
        lines.append("")
        # ↑ Tambahkan baris kosong antar tabel.
    
    return "\n".join(lines)
    # ↑ Gabungkan semua baris jadi satu string dengan newline.


if __name__ == "__main__":
    print(contract_markdown())
    # ↑ Cetak dokumentasi Markdown ke console.