"""Konfigurasi global"""

APP_NAME = "PCD Studio"
TEAM_NAME = "Kelompok X"
YEAR = 2026
WINDOW_SIZE = (1024, 768)          # sesuai wireframe (fixed)

MEMBERS = [                        # tampil di About > Info Tim Developer
    {"name": "Muhamad Radityo Pratama", "nim": "2407110908"},
    {"name": "Aulia Arief", "nim": "2407112796"},
    {"name": "Yosia Sitompul", "nim": "2407114019"},
]

GITHUB_URL = "https://github.com/TYO22/proyek-akhir-pcd"
YOUTUBE_URL = "https://www.youtube.com/"


def window_title() -> str:
    return f"{APP_NAME} \u00a9 {TEAM_NAME} - ({YEAR})"