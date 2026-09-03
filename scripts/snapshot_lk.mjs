/**
 * Снимок личного кабинета для дизайн-гейтов.
 *
 * Кабинет — React-SPA: гейты кита (measure_render, verify_states, axe…) читают
 * файл, а не URL, и до JS не дожидаются. Скрипт открывает стенд
 * scripts/lk_fixture.html (там подставлены ответы API), проходит по экранам и
 * сохраняет уже отрисованный DOM с инлайновым CSS — обычные статические
 * страницы, по которым гейты работают как по витринам.
 *
 *   python3 -m http.server 8899 &            # отдаёт репозиторий
 *   node scripts/snapshot_lk.mjs             # -> .design-gate/lk/<экран>.html
 *   node scripts/measure_render.mjs .design-gate/lk/sites.html
 *
 * Снимки складываются в .design-gate/ (в .gitignore). React, Babel и lucide
 * стенд тянет с unpkg; если сети нет, положите копии в .design-gate/vendor/
 * (react.production.min.js, react-dom.production.min.js, babel.min.js,
 * lucide.min.js) — скрипт подставит их сам.
 */
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync, readFileSync, existsSync } from 'fs';

const BASE = process.env.LK_BASE || 'http://localhost:8899';
const OUT  = '.design-gate/lk';
const CSS  = readFileSync('static/lk/styles.css', 'utf8');

const SCREENS = [
  ['sites',    '',          async () => {}],
  ['empty',    '?empty=1',  async () => {}],
  ['login',    '?anon=1',   async () => {}],
  ['billing',  '',          async (p) => { await p.locator('.nav-i').nth(1).click(); }],
  ['settings', '',          async (p) => { await p.locator('.nav-i').nth(2).click(); }],
  ['support',  '',          async (p) => { await p.locator('.nav-i').nth(3).click(); }],
  ['design',   '',          async (p) => { await p.locator('.sitecard .iconbtn').first().click();
                                           await p.waitForTimeout(400);
                                           await p.getByText('Дизайн', { exact: true }).click(); }],
];

const VENDOR = '.design-gate/vendor';
const browser = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch());
mkdirSync(OUT, { recursive: true });

for (const [name, query, act] of SCREENS) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  // офлайн-режим: те же библиотеки из локальной папки вместо unpkg
  await page.route('https://unpkg.com/**', (route) => {
    const local = `${VENDOR}/${route.request().url().split('/').pop()}`;
    if (existsSync(local)) return route.fulfill({ path: local, contentType: 'application/javascript' });
    return route.continue();
  });
  await page.goto(`${BASE}/scripts/lk_fixture.html${query}`, { waitUntil: 'load' });
  await page.waitForTimeout(2500);
  await act(page);
  await page.waitForTimeout(1200);
  const body = await page.evaluate(() => document.body.innerHTML);
  writeFileSync(`${OUT}/${name}.html`,
    `<!DOCTYPE html>\n<html lang="ru"><head><meta charset="utf-8">\n` +
    `<meta name="viewport" content="width=device-width, initial-scale=1.0">\n` +
    `<title>Кабинет — ${name}</title>\n<style>\n${CSS}\n</style></head>\n<body>${body}</body></html>\n`);
  console.log('OK  ', name);
  await page.close();
}
await browser.close();
