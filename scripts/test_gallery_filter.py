# ============================================================
# test_gallery_filter.py — тесты фильтрации галереи (лого не должно
# попадать в фото/hero). Запуск: venv/bin/python scripts/test_gallery_filter.py
# ============================================================

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from yandex_maps_parser import _normalize_gallery_urls, photo_base

A = "https://avatars.mds.yandex.net/get-altay"

# ── photo_base: срез суффикса размера ────────────────────────────────────────
assert photo_base(f"{A}/123/photo1/XXXL") == f"{A}/123/photo1"
assert photo_base(f"{A}/123/photo1/M") == f"{A}/123/photo1"
assert photo_base(f"{A}/123/photo1/orig") == f"{A}/123/photo1"
assert photo_base(f"{A}/123/logo9/priority-headline-logo-square") == f"{A}/123/logo9"
assert photo_base(f"{A}/123/photo1/smart_crop_512x512") == f"{A}/123/photo1"
assert photo_base(f"{A}/123/photo1") == f"{A}/123/photo1"  # без суффикса — как есть
assert photo_base("") == ""

# ── _normalize_gallery_urls ──────────────────────────────────────────────────
T = "https://avatars.mds.yandex.net/get-tycoon"
raw = [
    f"{T}/13460727/23558409_pin_search_standard_2025-08-27T22_21_11/pin_x2",  # ПИН карты — отсев
    f"{T}/2/logo/priority-headline-logo-square",        # ЛОГО (реклама) — отсев
    f"{T}/3/hdr/priority-headline-background",          # БАННЕР-ШАПКА (реклама) — отсев
    f"{A}/1/aaa/XXXL",                                  # нормальное фото
    f"{A}/1/aaa/M",                                     # дубль того же фото
    f"{A}/4/ccc/XXL_height",                            # lazy-заготовка — отсев
    "https://avatars.mds.yandex.net/get-vh/5/video/XL_height",  # видео-заготовка — отсев
    f"{A}/6/ddd/L",                                     # нормальное фото
    "",                                                 # пустое — отсев
]
out = _normalize_gallery_urls(raw)
assert out == [f"{A}/1/aaa/XXXL", f"{A}/6/ddd/L"], out

# Реальные мусорные URL из бага bork не проходят
assert _normalize_gallery_urls([f"{T}/9/x/priority-headline-logo-square"]) == []
assert _normalize_gallery_urls([f"{T}/9/x/priority-headline-background"]) == []
assert _normalize_gallery_urls(
    [f"{T}/13460727/23558409_pin_search_standard_2025-08-27T22_21_11/pin_x2"]) == []

# Лимит соблюдается
many = [f"{A}/{i}/p{i}/M" for i in range(30)]
assert len(_normalize_gallery_urls(many, limit=15)) == 15

# ── сверка галереи с logo_url (страховка в parse_detail_page) ────────────────
logo_url = f"{A}/7/samelogo/M"
photos = [f"{A}/7/samelogo/XXXL", f"{A}/8/real/XXXL"]
logo_base = photo_base(logo_url)
filtered = [p for p in photos if photo_base(p) != logo_base]
assert filtered == [f"{A}/8/real/XXXL"], filtered

print("OK: все тесты gallery_filter пройдены")
