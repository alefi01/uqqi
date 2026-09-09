/**
 * Снимок мини-приложения владельца (Telegram) для дизайн-гейтов.
 *
 * Приложение живёт за подписью Telegram и ходит в /tg/api — гейтам его не
 * достать. Скрипт открывает templates/tg_app.html напрямую, подставляет
 * ответы API и сохраняет отрисованный DOM с инлайновым CSS: по нему гейты
 * работают как по обычной странице.
 *
 *   node scripts/snapshot_tg.mjs           # -> .design-gate/tg/<экран>.html + .png
 *   node scripts/measure_render.mjs .design-gate/tg/day.html
 *
 * Экраны: day (записи на день), empty (день без записей), nopro (нет Pro),
 * sheet (лист добавления записи).
 *
 * verify_overflow гоняем по day/empty/nopro. На снимке `sheet` он всегда
 * ругается: лист снизу по построению накрывает страницу, а гейт сравнивает
 * геометрию и про модальные окна не знает (inert и aria-hidden он не читает).
 */
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync, readFileSync } from 'fs';

const OUT = '.design-gate/tg';
const PAGE = 'file://' + process.cwd() + '/templates/tg_app.html';

const iso = (shift) => {
  const d = new Date();
  d.setDate(d.getDate() + shift);
  return d.toISOString().slice(0, 10);
};

const SITES = [
  { id: 1, title: 'Барбершоп «Ножницы»', slug: 'nozhnitsy', tz: 3, duration: 60,
    multi: true, masters: ['Иван', 'Пётр'], services: ['Стрижка', 'Борода'], slotsOn: true },
  { id: 2, title: 'Шиномонтаж «Колесо»', slug: 'koleso', tz: 3, duration: 60,
    multi: false, masters: [], services: [], slotsOn: true },
];

const BOOKINGS = [
  { id: 11, date: iso(0), time: '10:00', start: iso(0) + 'T10:00', duration: 60,
    name: 'Алексей Петров', phone: '+7 900 123-45-67', email: 'a@example.ru',
    service: 'Стрижка', master: 'Иван', comment: '', status: 'confirmed', byOwner: false },
  { id: 12, date: iso(0), time: '11:00', start: iso(0) + 'T11:00', duration: 60,
    name: 'Мария', phone: '+7 900 765-43-21', email: '',
    service: 'Борода', master: 'Пётр', comment: 'Просила не опаздывать', status: 'new', byOwner: false },
  { id: 13, date: iso(0), time: '13:00', start: iso(0) + 'T13:00', duration: 60,
    name: 'Запись с улицы', phone: '', email: '', service: '', master: 'Иван',
    comment: '', status: 'canceled', byOwner: true },
];

const SLOTS = ['14:00', '15:00', '16:00'].map((t) => ({
  time: t, start: iso(0) + 'T' + t, masters: ['Иван', 'Пётр'],
}));

const SCREENS = [
  ['day',   { sites: SITES, bookings: BOOKINGS }, async () => {}],
  ['empty', { sites: SITES, bookings: [] },       async () => {}],
  ['nopro', { sites: [],    bookings: [] },       async () => {}],
  ['sheet', { sites: SITES, bookings: BOOKINGS }, async (p) => {
    await p.click('#addBtn');
    await p.waitForTimeout(400);
  }],
];

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch());

for (const [name, data, act] of SCREENS) {
  const page = await browser.newPage({ viewport: { width: 414, height: 900 } });
  page.on('pageerror', (e) => console.log(`  JS ERROR (${name}):`, e.message));

  // telegram-web-app.js тянется из сети, которой у контейнерного Chromium нет.
  await page.route('https://telegram.org/**', (r) => r.fulfill({ body: '', contentType: 'application/javascript' }));

  await page.addInitScript((fixture) => {
    const real = window.fetch;
    window.fetch = function (url, opts) {
      const path = String(url);
      let body = { ok: true };
      if (path.endsWith('/bootstrap')) body = { ok: true, sites: fixture.sites };
      else if (path.endsWith('/bookings')) body = { ok: true, bookings: fixture.bookings };
      else if (path.endsWith('/slots')) body = { ok: true, slots: fixture.slots };
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(body) });
    };
  }, { ...data, slots: SLOTS });

  await page.goto(PAGE, { waitUntil: 'load' });
  await page.waitForTimeout(600);
  await act(page);
  await page.waitForTimeout(300);

  await page.screenshot({ path: `${OUT}/${name}.png` });

  const html = await page.evaluate(() => {
    const clone = document.documentElement.cloneNode(true);
    clone.querySelectorAll('script').forEach((el) => el.remove());
    return clone.outerHTML;
  });
  writeFileSync(`${OUT}/${name}.html`, '<!DOCTYPE html>\n' + html);
  console.log('OK  ', name);
  await page.close();
}
await browser.close();
