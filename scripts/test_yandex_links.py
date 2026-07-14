# ============================================================
# test_yandex_links.py — тесты разбора ссылок Яндекс.Карт (app/yandex_links.py).
# Запуск: venv/bin/python scripts/test_yandex_links.py
# Без pytest и без поднятия приложения — только stdlib.
# ============================================================

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.yandex_links import extract_yandex_url, extract_org_id, ERR_NO_LINK, ERR_NOT_ORG


def ok(raw, expected_url):
    url, err = extract_yandex_url(raw)
    assert err is None, f"ожидали успех, получили ошибку: {err!r}\n  вход: {raw!r}"
    assert url == expected_url, f"ожидали {expected_url!r}, получили {url!r}\n  вход: {raw!r}"


def fail(raw, expected_err):
    url, err = extract_yandex_url(raw)
    assert url is None, f"ожидали отказ, получили url: {url!r}\n  вход: {raw!r}"
    assert err == expected_err, f"ожидали ошибку {expected_err!r}, получили {err!r}"


# ── Короткий формат «Поделиться» ──────────────────────────────────────────────
ok("https://yandex.com/maps/-/CDe4bU8", "https://yandex.com/maps/-/CDe4bU8")
ok("https://yandex.ru/maps/-/CBu4ZDsldB", "https://yandex.ru/maps/-/CBu4ZDsldB")
ok("Смотри: https://yandex.ru/maps/-/CBu4ZDsldB.", "https://yandex.ru/maps/-/CBu4ZDsldB")

# ── Org-формат (пример из реального обращения клиента) ────────────────────────
ok("https://yandex.ru/maps/org/bork/1037407780?si=r9dgqe27c2jr7y6kphej5wv8c0",
   "https://yandex.ru/maps/org/bork/1037407780")
ok("https://yandex.ru/maps/org/bork/1037407780",
   "https://yandex.ru/maps/org/bork/1037407780")
ok("https://yandex.ru/maps/org/bork/1037407780/reviews/?ll=37.6%2C55.7&z=17",
   "https://yandex.ru/maps/org/bork/1037407780/reviews/")
ok("https://yandex.by/maps/org/kofeynya/123456789?si=abc",
   "https://yandex.by/maps/org/kofeynya/123456789")

# ── Блок «Поделиться» с телефона: название + адрес + ссылка ───────────────────
ok("Борк\nул. Ленина, 1, Москва\nhttps://yandex.ru/maps/org/bork/1037407780?si=r9dgqe27c2jr7y6kphej5wv8c0",
   "https://yandex.ru/maps/org/bork/1037407780")

# ── Mapframe/poi: org_id в query — канонизируем в прямой org-URL ─────────────
# (по mapframe-ссылке карточка открывается poi-оверлеем: вкладки каталога
#  не работают, лого не извлекается — парс идёт криво)
ok("https://yandex.ru/maps/213/moscow/?poi%5Buri%5D=ymapsbm1%3A%2F%2Forg%3Foid%3D1037407780&tab=overview",
   "https://yandex.ru/maps/org/1037407780/")
ok("https://yandex.ru/maps/2/saint-petersburg/?oid=987654&ol=biz",
   "https://yandex.ru/maps/org/987654/")
# Реальная ссылка из бага (товары не спарсились в poi-режиме)
ok("https://yandex.ru/maps/213/moscow/?from=mapframe&ll=37.593714%2C55.767255&mode=poi"
   "&poi%5Bpoint%5D=37.595650%2C55.766097&poi%5Buri%5D=ymapsbm1%3A%2F%2Forg%3Foid%3D20313286325"
   "&source=mapframe&utm_source=mapframe&z=17.17",
   "https://yandex.ru/maps/org/20313286325/")

# ── Отказы ────────────────────────────────────────────────────────────────────
fail("", ERR_NO_LINK)
fail("   ", ERR_NO_LINK)
fail("Кофейня Алекс, Саранск", ERR_NO_LINK)
fail("https://google.com/maps/place/bork", ERR_NO_LINK)
fail("https://yandex.ru/maps/213/moscow/", ERR_NOT_ORG)                    # просто город
fail("https://yandex.ru/maps/213/moscow/?rtext=55.7%2C37.6~55.8%2C37.7",   # маршрут
     ERR_NOT_ORG)

# ── extract_org_id ────────────────────────────────────────────────────────────
assert extract_org_id("https://yandex.ru/maps/org/bork/1037407780?si=abc") == "1037407780"
assert extract_org_id("https://yandex.ru/maps/org/1037407780") == "1037407780"
assert extract_org_id("https://yandex.ru/maps/213/moscow/?poi%5Buri%5D=ymapsbm1%3A%2F%2Forg%3Foid%3D555") == "555"
assert extract_org_id("https://yandex.ru/maps/2/spb/?oid=987654") == "987654"
assert extract_org_id("https://yandex.ru/maps/-/CDe4bU8") is None
assert extract_org_id("") is None

print("OK: все тесты yandex_links пройдены")
