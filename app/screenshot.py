"""
screenshot.py — снимок hero-области сайта для материалов клиенту (claim-продажи).
Снимается ПО КНОПКЕ из owner-панели, по реальному публичному адресу сайта.
Дизайн B — дефолт, заглушки у claim-сайтов нет, поэтому спец-параметры не нужны.
"""
import os
import asyncio

SCREENSHOTS_DIR = "static/screenshots"
VIEWPORT = {"width": 1280, "height": 800}


async def capture_hero(slug: str, base_domain: str = "uqqi.ru") -> str:
    """
    Скриншот первого экрана сайта (десктоп) по реальному адресу https://slug.domain/.
    Возвращает относительный путь к файлу или "" при ошибке.
    """
    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        print(f"[SCREENSHOT] playwright недоступен: {e}", flush=True)
        return ""

    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    out_path = f"{SCREENSHOTS_DIR}/{slug}.png"
    url = f"https://{slug}.{base_domain}/"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(args=["--no-sandbox"])
            context = await browser.new_context(
                viewport=VIEWPORT,
                device_scale_factor=2,  # retina — резче для писем
            )
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Ждём дорисовку (шрифты, lucide-иконки, изображения)
            await page.wait_for_timeout(3000)
            await page.screenshot(
                path=out_path,
                clip={"x": 0, "y": 0, "width": VIEWPORT["width"], "height": VIEWPORT["height"]},
            )
            await browser.close()
        print(f"[SCREENSHOT] сохранён: {out_path}", flush=True)
        return f"/{out_path}"
    except Exception as e:
        print(f"[SCREENSHOT] ошибка для {slug}: {e}", flush=True)
        return ""
