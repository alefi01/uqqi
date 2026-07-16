// ============================================================
// dashboard.jsx — список сайтов, статусы, пусто, добавление, прогресс
// ============================================================
const { useState: useStateD, useEffect: useEffectD, useRef: useRefD } = React;

// ---- бейдж статуса ----
function StatusBadge({ site }) {
  const map = {
    building: { cls: 'badge--building', ic: 'loader', txt: 'Создаётся…' },
    error:    { cls: 'badge--error', ic: 'alert-triangle', txt: 'Ошибка сборки' },
    trial:    { cls: 'badge--trial', ic: null, txt: `Пробный период — осталось ${site.trialDays} дн.` },
    active:   { cls: 'badge--active', ic: null, txt: `Активна до ${site.until}` },
    unpaid:   { cls: 'badge--unpaid', ic: null, txt: 'Не оплачено' },
  };
  const m = map[site.status] || map.active;
  return (
    <span className={'badge ' + m.cls}>
      {m.ic ? <i data-lucide={m.ic} style={{ width: 13, height: 13 }} className={site.status === 'building' ? 'spin-ic' : ''}></i> : <span className="dot"></span>}
      {m.txt}
    </span>
  );
}

// ---- карточка сайта ----
function SiteCard({ site, nav, onPay, onMenu }) {
  const isBuilding = site.status === 'building';
  const isError = site.status === 'error';
  const needsPay = site.status === 'trial' || site.status === 'unpaid';
  return (
    <div className="card sitecard">
      <div className="sitecard__top">
        <div className="row" style={{ alignItems: 'flex-start' }}>
          <div className="sitecard__thumb" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--terracotta)', background: 'var(--terracotta-wash)' }}>
            <i data-lucide={site.icon || 'store'} style={{ width: 24, height: 24 }}></i>
          </div>
          <div>
            <div className="sitecard__title">{site.name}</div>
            <div className="sitecard__url">
              {site.slug}.uqqi.ru
              {!isBuilding && !isError && <a href={'https://' + site.slug + '.uqqi.ru'} target="_blank" rel="noopener">открыть <i data-lucide="arrow-up-right" style={{ width: 13, height: 13 }}></i></a>}
            </div>
          </div>
        </div>
        <StatusBadge site={site} />
      </div>

      {isBuilding && (
        <div>
          <div className="pbar"><div className="pbar__fill" style={{ width: '62%' }}></div></div>
          <p className="muted" style={{ fontSize: '.8rem', marginTop: '.5rem' }}>Собираем сайт из карточки Яндекс Карт — обычно занимает меньше минуты.</p>
        </div>
      )}

      {isError && (
        <p style={{ fontSize: '.85rem', color: 'var(--danger)', lineHeight: 1.6 }}>
          Не получилось обработать ссылку. Проверьте её или напишите в поддержку.
        </p>
      )}

      {!isBuilding && !isError && (
        <div className="sitecard__meta">
          <span><b>{site.city}</b></span>
          <span>Тариф: <b>от 1990 ₽ / мес</b></span>
          <span>Создан: <b>{site.created}</b></span>
        </div>
      )}

      <div className="sitecard__actions">
        {needsPay && <button className="btn btn--primary btn--sm" onClick={() => onPay(site)}>{site.status === 'unpaid' ? 'Оплатить, чтобы возобновить' : 'Оплатить'}</button>}
        {isError && <button className="btn btn--primary btn--sm" onClick={() => nav('add-site')}><i data-lucide="rotate-cw"></i> Попробовать снова</button>}
        {!isBuilding && <button className="iconbtn" title="Настройки" onClick={() => onMenu(site)}><i data-lucide="settings-2"></i></button>}
      </div>
    </div>
  );
}

// ---- экран «Мои сайты» ----
function ScreenSites({ nav, sites, onPay, onMenu, canAdd }) {
  if (sites.length === 0) {
    return (
      <div className="empty">
        <div className="empty__box">
          <div className="empty__ic"><i data-lucide="layout-template"></i></div>
          <h2>У вас пока нет сайтов</h2>
          <p>Вставьте ссылку на карточку вашей организации в Яндекс Картах — и мы соберём готовый сайт за минуту.</p>
          <button className="btn btn--primary btn--lg" onClick={() => nav('add-site')}><i data-lucide="plus"></i> Создать первый сайт</button>
        </div>
      </div>
    );
  }
  return (
    <div className="sites">
      {sites.map(s => <SiteCard key={s.id} site={s} nav={nav} onPay={onPay} onMenu={onMenu} />)}
      <div style={{ marginTop: '.3rem' }}>
        {canAdd
          ? <button className="btn btn--outline" onClick={() => nav('add-site')}><i data-lucide="plus"></i> Добавить сайт</button>
          : <div className="card" style={{ padding: '1rem 1.1rem', display: 'flex', gap: '.7rem', alignItems: 'center', background: 'var(--warning-wash)', borderColor: 'color-mix(in srgb,var(--warning) 30%,var(--line))' }}>
              <i data-lucide="info" style={{ width: 18, height: 18, color: 'var(--warning)', flex: 'none' }}></i>
              <span style={{ fontSize: '.84rem', color: 'var(--ink-2)' }}>На пробном тарифе доступен один сайт. Чтобы добавить ещё — оплатите текущий.</span>
            </div>}
      </div>
    </div>
  );
}

// ---- валидация ссылки: короткая /maps/-/CODE, org /maps/org/…/{id}, mapframe (oid=) ----
// Принимает и текст «Поделиться» с телефона (название + адрес + ссылка).
// ВАЖНО: та же логика на бэке — app/yandex_links.py. Менять синхронно.
function validYandex(text) {
  if (!text.trim()) return null;
  const m = text.match(/https?:\/\/(?:maps\.)?yandex\.(?:ru|com|by|kz|uz)\/maps\/[^\s]+/);
  if (!m) return false;
  const url = m[0];
  if (/\/maps\/-\/[A-Za-z0-9_~-]+/.test(url)) return true;    // короткая
  if (/\/maps\/org\/(?:[^\/]+\/)?\d+/.test(url)) return true; // карточка организации
  if (/(?:[?&]oid=|oid%3D)\d+/i.test(url)) return true;       // mapframe: oid в query
  return false;
}

// ---- экран «Добавить сайт» ----
function ScreenAddSite({ nav, onStartBuild }) {
  const [url, setUrl] = useStateD('');
  const valid = validYandex(url);
  return (
    <div className="wrap-md">
      <a className="linklike" style={{ fontSize: '.84rem', display: 'inline-flex', alignItems: 'center', gap: '.3rem', marginBottom: '1.2rem' }} onClick={() => nav('sites')}><i data-lucide="arrow-left" style={{ width: 15, height: 15 }}></i> Мои сайты</a>
      <div className="card" style={{ padding: '1.6rem' }}>
        <span className="eyebrow">Новый сайт</span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.4rem', letterSpacing: '-.02em', color: 'var(--ink)', margin: '.5rem 0 .4rem' }}>Ссылка на Яндекс Карты</h2>
        <p className="muted" style={{ fontSize: '.88rem', lineHeight: 1.6 }}>Вставьте ссылку на карточку вашей организации — мы возьмём оттуда название, адрес, фото, часы работы и отзывы.</p>
        <div className="field" style={{ marginTop: '1.3rem' }}>
          <label className="field__label">Ссылка на карточку организации</label>
          <input className={'input' + (valid === true ? ' is-valid' : valid === false ? ' is-error' : '')} placeholder="https://yandex.ru/maps/org/… или /maps/-/…" value={url} onChange={e => setUrl(e.target.value)} />
          {valid === false && <span className="field__err">Похоже, это не ссылка на карточку организации в Яндекс Картах. Проверьте формат.</span>}
          {valid === true && <span className="field__hint" style={{ color: 'var(--success-soft)' }}>Ссылка распознана ✓</span>}
        </div>
        <div className="card" style={{ background: 'var(--paper-2)', border: 'none', boxShadow: 'none', padding: '.9rem 1rem', marginTop: '1rem', display: 'flex', gap: '.7rem' }}>
          <i data-lucide="lightbulb" style={{ width: 18, height: 18, color: 'var(--gold-dim)', flex: 'none' }}></i>
          <span style={{ fontSize: '.82rem', color: 'var(--ink-2)', lineHeight: 1.6 }}>Где взять ссылку: откройте карточку компании в Яндекс Картах, нажмите кнопку <b>«Поделиться»</b> и скопируйте ссылку. Можно вставить скопированное целиком — вместе с названием и адресом.</span>
        </div>
        <button className="btn btn--primary btn--lg btn--block" style={{ marginTop: '1.3rem' }} disabled={valid !== true} onClick={() => onStartBuild(url)}>Создать сайт</button>
      </div>
    </div>
  );
}

// ---- экран прогресса сборки ----
const BUILD_STEPS = [
  { label: 'Ставим в очередь', ic: 'list' },
  { label: 'Анализируем карточку', ic: 'search' },
  { label: 'Загружаем фото', ic: 'image' },
  { label: 'Загружаем отзывы', ic: 'message-square' },
  { label: 'Публикуем на uqqi.ru', ic: 'rocket' },
];
function ScreenBuilding({ onDone, buildId }) {
  const [step, setStep] = useStateD(0);
  const [failed, setFailed] = useStateD(false);
  const pollRef = useRefD(null);
  const stepRef = useRefD(null);

  useEffectD(() => {
    if (!buildId) return;
    // Плавная анимация шагов (визуальная, пока идёт реальный парсинг)
    stepRef.current = setInterval(() => {
      setStep(s => Math.min(s + 1, BUILD_STEPS.length - 1));
    }, 2500);
    // Поллинг реального статуса
    pollRef.current = setInterval(async () => {
      try {
        const st = await window.API.siteStatus(buildId);
        if (st.build_status === 'ready') {
          clearInterval(pollRef.current); clearInterval(stepRef.current);
          setStep(BUILD_STEPS.length);
          setTimeout(onDone, 800);
        } else if (st.build_status === 'error') {
          clearInterval(pollRef.current); clearInterval(stepRef.current);
          setFailed(true);
        }
      } catch (e) {}
    }, 2000);
    return () => { clearInterval(pollRef.current); clearInterval(stepRef.current); };
  }, [buildId]);

  // Перерисовываем lucide-иконки при каждой смене шага (check/rocket)
  useEffectD(() => {
    if (window.lucide) window.lucide.createIcons();
  }, [step, failed]);

  if (failed) {
    return (
      <div className="wrap-md" style={{ paddingTop: '1rem' }}>
        <div className="card" style={{ padding: '2rem 1.8rem', textAlign: 'center' }}>
          <div className="empty__ic" style={{ margin: '0 auto 1rem', color: 'var(--danger)' }}><i data-lucide="alert-triangle"></i></div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.3rem', color: 'var(--ink)' }}>Не удалось собрать сайт</h2>
          <p className="muted" style={{ fontSize: '.88rem', marginTop: '.5rem', lineHeight: 1.6 }}>
            Не получилось обработать ссылку. Проверьте, что это короткая ссылка на карточку организации в Яндекс Картах, или напишите в поддержку.
          </p>
          <button className="btn btn--primary btn--lg" style={{ marginTop: '1.2rem' }} onClick={() => window.location.reload()}>
            <i data-lucide="rotate-cw"></i> Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  const pct = Math.min(100, Math.round((step / BUILD_STEPS.length) * 100));
  return (
    <div className="wrap-md" style={{ paddingTop: '1rem' }}>
      <div className="card" style={{ padding: '2rem 1.8rem', textAlign: 'center' }}>
        <div className="spin" style={{ margin: '0 auto .4rem' }}></div>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.3rem', letterSpacing: '-.02em', color: 'var(--ink)', marginTop: '.8rem' }}>Собираем ваш сайт</h2>
        <p className="muted" style={{ fontSize: '.86rem', marginTop: '.4rem' }}>Обычно это занимает меньше минуты. Можно не закрывать страницу — мы сохраним прогресс.</p>
        <div className="pbar" style={{ margin: '1.4rem 0 1.2rem' }}><div className="pbar__fill" style={{ width: pct + '%' }}></div></div>
        <div style={{ textAlign: 'left', maxWidth: 300, margin: '0 auto' }}>
          {BUILD_STEPS.map((s, i) => (
            <div key={i} className={'bstep ' + (i < step ? 'done' : i === step ? 'active' : '')}>
              <span className="bstep__ic">
                {i < step ? <i data-lucide="check"></i> : i === step ? <i data-lucide={s.ic}></i> : <span style={{ width: 6, height: 6, borderRadius: 9, background: 'var(--line)' }}></span>}
              </span>
              {s.label}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { ScreenSites, ScreenAddSite, ScreenBuilding, SiteCard, StatusBadge });
