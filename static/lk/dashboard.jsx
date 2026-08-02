// ============================================================
// dashboard.jsx — список сайтов, статусы, пусто, добавление, прогресс
// ============================================================
const { useState: useStateD, useEffect: useEffectD, useRef: useRefD } = React;

// ---- бейдж статуса ----
function StatusBadge({ site }) {
  const map = {
    building: { cls: 'badge--building', ic: 'loader', txt: 'Создаётся…' },
    error:    { cls: 'badge--error', ic: 'alert-triangle', txt: 'Ошибка сборки' },
    free:     { cls: 'badge--active', ic: null, txt: 'Бесплатный' },
    protrial: { cls: 'badge--trial', ic: null, txt: `Pro-триал — осталось ${site.proDays} дн.` },
    pro:      { cls: 'badge--active', ic: null, txt: `Pro до ${site.proUntil}` },
    claim:    { cls: 'badge--unpaid', ic: null, txt: 'Демо — оплатите, чтобы забрать' },
  };
  const m = map[site.status] || map.free;
  return (
    <span className={'badge ' + m.cls}>
      {m.ic ? <i data-lucide={m.ic} style={{ width: 13, height: 13 }} className={site.status === 'building' ? 'spin-ic' : ''}></i> : <span className="dot"></span>}
      {m.txt}
    </span>
  );
}

// ---- карточка сайта ----
function SiteCard({ site, nav, onPay, onStats, onDesign, onDelete }) {
  const isBuilding = site.status === 'building';
  const isError = site.status === 'error';
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
          <span>Pro: <b>от 990 ₽ / мес</b></span>
          <span>Создан: <b>{site.created}</b></span>
        </div>
      )}

      <div className="sitecard__actions">
        {!isBuilding && !isError && <button className="btn btn--ghost btn--sm" onClick={() => onStats(site)}><i data-lucide="bar-chart-2"></i> Статистика</button>}
        {!isBuilding && !isError && <button className="btn btn--ghost btn--sm" onClick={() => onDesign(site)}><i data-lucide="palette"></i> Дизайн</button>}
        {!isBuilding && !isError && (site.canDelete === false
          ? <span className="tip-wrap" data-tip="Дождитесь окончания trial-периода"><button className="btn btn--ghost btn--sm" disabled style={{ opacity: .45, cursor: 'not-allowed' }}><i data-lucide="trash-2"></i> Удалить</button></span>
          : <button className="btn btn--ghost btn--sm" style={{ color: 'var(--danger)' }} onClick={() => onDelete(site)}><i data-lucide="trash-2"></i> Удалить</button>)}
        {site.status === 'claim' && <button className="btn btn--primary btn--sm" onClick={() => onPay(site)}>Оплатить, чтобы забрать сайт</button>}
        {site.status === 'free' && <button className="btn btn--primary btn--sm" onClick={() => onPay(site)}>Оформить Pro</button>}
        {(site.status === 'protrial' || site.status === 'pro') && <button className="btn btn--ghost btn--sm" onClick={() => onPay(site)}>Продлить Pro</button>}
        {isError && <button className="btn btn--primary btn--sm" onClick={() => nav('add-site')}><i data-lucide="rotate-cw"></i> Попробовать снова</button>}
      </div>
    </div>
  );
}

// ---- экран «Мои сайты» ----
function ScreenSites({ nav, sites, onPay, onStats, onDesign, onDelete, canAdd }) {
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
      {sites.map(s => <SiteCard key={s.id} site={s} nav={nav} onPay={onPay} onStats={onStats} onDesign={onDesign} onDelete={onDelete} />)}
      <div style={{ marginTop: '.3rem' }}>
        {canAdd
          ? <button className="btn btn--outline" onClick={() => nav('add-site')}><i data-lucide="plus"></i> Добавить сайт</button>
          : <div className="card" style={{ padding: '1rem 1.1rem', display: 'flex', gap: '.7rem', alignItems: 'center', background: 'var(--warning-wash)', borderColor: 'color-mix(in srgb,var(--warning) 30%,var(--line))' }}>
              <i data-lucide="info" style={{ width: 18, height: 18, color: 'var(--warning)', flex: 'none' }}></i>
              <span style={{ fontSize: '.84rem', color: 'var(--ink-2)' }}>Дождитесь завершения сборки текущего сайта — потом можно добавить ещё.</span>
            </div>}
      </div>
    </div>
  );
}

// ---- Статистика сайта (функциональная версия; визуал — по макету Claude Design) ----
function ScreenMetrics({ nav, metrics }) {
  const m = metrics;
  if (!m) {
    return <div className="wrap-md"><div className="card" style={{ padding: '1.6rem' }}><div className="spin"></div></div></div>;
  }
  const maxD = Math.max(1, ...m.daily.map(d => d.unique));
  const sub = m.subscription || {};
  return (
    <div className="wrap-md">
      <a className="linklike" style={{ fontSize: '.84rem', display: 'inline-flex', alignItems: 'center', gap: '.3rem', marginBottom: '1.2rem' }} onClick={() => nav('sites')}><i data-lucide="arrow-left" style={{ width: 15, height: 15 }}></i> Мои сайты</a>
      <div className="card" style={{ padding: '1.6rem' }}>
        <span className="eyebrow">Статистика</span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.3rem', color: 'var(--ink)', margin: '.4rem 0 1.1rem' }}>{m.title}</h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '.6rem' }}>
          {[['7 дней', 'd7'], ['30 дней', 'd30'], ['90 дней', 'd90']].map(([lbl, k]) => (
            <div key={k} style={{ padding: '.9rem', textAlign: 'center', background: 'var(--paper-2)', borderRadius: 'var(--r-lg)' }}>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--ink)' }}>{m.unique[k]}</div>
              <div className="muted" style={{ fontSize: '.72rem' }}>уник. / {lbl}</div>
            </div>
          ))}
        </div>
        <p className="muted" style={{ fontSize: '.82rem', marginTop: '.8rem' }}>Просмотров за 30 дней: <b style={{ color: 'var(--ink)' }}>{m.views.d30}</b></p>

        <p className="field__label" style={{ margin: '1.3rem 0 .5rem' }}>Посетители по дням (30 дней)</p>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '2px', height: '80px' }}>
          {m.daily.map((d, i) => (
            <div key={i} title={d.day + ': ' + d.unique} style={{ flex: 1, background: 'var(--terracotta)', opacity: d.unique ? .85 : .15, height: Math.max(3, d.unique / maxD * 80) + 'px', borderRadius: '2px' }}></div>
          ))}
        </div>

        <div style={{ marginTop: '1.3rem', padding: '.9rem 1rem', background: 'var(--paper-2)', borderRadius: 'var(--r-lg)', fontSize: '.86rem', color: 'var(--ink-2)' }}>
          {sub.status === 'pro' && <span>Pro активен до <b style={{ color: 'var(--ink)' }}>{sub.until}</b></span>}
          {sub.status === 'protrial' && <span>Pro-триал — осталось <b style={{ color: 'var(--ink)' }}>{sub.proDays} дн.</b></span>}
          {sub.status === 'free' && <span>Бесплатный сайт · <b style={{ color: 'var(--ink)' }}>Pro</b> откроет премиум-дизайн и чат</span>}
          {sub.status === 'claim' && <span style={{ color: 'var(--danger)' }}>Демо-сайт — оплатите, чтобы забрать</span>}
        </div>
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

// ---- галерея дизайнов (пикер при создании + смена оформления в ЛК) ----
// MP4-лупы владелец кладёт в static/designs/<key>.mp4 (+ <key>.jpg постер).
// Пока файла нет — карточка показывает плейсхолдер с названием (video.onError).
function DesignCard({ d, selected, onSelect }) {
  const [vidBad, setVidBad] = useStateD(false);
  const isPro = d.tier === 'pro';
  const showVideo = isPro && d.preview && !vidBad;
  return (
    <div onClick={() => onSelect(d.key)}
      style={{ cursor: 'pointer', borderRadius: 'var(--r-lg)', overflow: 'hidden',
        border: '2px solid ' + (selected ? 'var(--terracotta)' : 'var(--line)'),
        background: selected ? 'var(--terracotta-wash)' : 'var(--paper)' }}>
      <div style={{ position: 'relative', aspectRatio: '16 / 10', overflow: 'hidden',
        background: 'linear-gradient(135deg, var(--paper-2), color-mix(in srgb, var(--terracotta) 14%, var(--paper-2)))',
        display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {showVideo
          ? <video muted loop autoPlay playsInline preload="none" poster={d.poster || undefined}
              onError={() => setVidBad(true)}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}>
              <source src={d.preview} type="video/mp4" />
            </video>
          : <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.02rem', color: 'var(--ink-2)' }}>{d.name}</span>}
        {isPro && <span style={{ position: 'absolute', top: '.5rem', left: '.5rem', background: 'var(--gold-dim)', color: '#fff', fontSize: '.64rem', fontWeight: 700, letterSpacing: '.06em', textTransform: 'uppercase', padding: '.18rem .5rem', borderRadius: '999px' }}>Pro</span>}
        {selected && <span style={{ position: 'absolute', top: '.5rem', right: '.5rem', width: 22, height: 22, borderRadius: '50%', background: 'var(--terracotta)', color: '#fff', display: 'grid', placeItems: 'center' }}><i data-lucide="check" style={{ width: 14, height: 14 }}></i></span>}
      </div>
      <div style={{ padding: '.55rem .7rem .65rem' }}>
        <div style={{ fontWeight: 700, color: 'var(--ink)', fontSize: '.9rem' }}>{d.name}</div>
        {d.vibe && <div className="muted" style={{ fontSize: '.74rem', marginTop: '.15rem', lineHeight: 1.4 }}>{d.vibe}</div>}
        {d.fit && <div className="muted" style={{ fontSize: '.7rem', marginTop: '.2rem', opacity: .75 }}>Подходит: {d.fit}</div>}
      </div>
    </div>
  );
}

function DesignGallery({ designs, value, onSelect }) {
  if (!designs || !designs.length) return <div className="spin" style={{ margin: '1rem auto' }}></div>;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(178px, 1fr))', gap: '.7rem', marginTop: '.5rem' }}>
      {designs.map(d => <DesignCard key={d.key} d={d} selected={value === d.key} onSelect={onSelect} />)}
    </div>
  );
}

// ---- экран «Дизайн сайта» (смена оформления + живой предпросмотр ?variant=) ----
function ScreenDesign({ nav, site, designs, onApply, onPay }) {
  const [design, setDesign] = useStateD((site && site.design) || 'A');
  const [busy, setBusy] = useStateD(false);
  if (!site) return null;
  const chosen = (designs || []).find(d => d.key === design);
  const isPro = !!(chosen && chosen.tier === 'pro');
  const proActive = !!site.proActive;
  const changed = design !== (site.design || 'A');
  const liveUrl = 'https://' + site.slug + '.uqqi.ru/?variant=' + encodeURIComponent(design);
  async function apply() {
    setBusy(true);
    try { await onApply(site.id, design); } finally { setBusy(false); }
  }
  return (
    <div className="wrap-md">
      <a className="linklike" style={{ fontSize: '.84rem', display: 'inline-flex', alignItems: 'center', gap: '.3rem', marginBottom: '1.2rem' }} onClick={() => nav('sites')}><i data-lucide="arrow-left" style={{ width: 15, height: 15 }}></i> Мои сайты</a>
      <div className="card" style={{ padding: '1.6rem' }}>
        <span className="eyebrow">Дизайн сайта</span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.3rem', color: 'var(--ink)', margin: '.4rem 0 .4rem' }}>{site.name}</h2>
        <p className="muted" style={{ fontSize: '.86rem', lineHeight: 1.6 }}>Выберите оформление витрины. Премиум-дизайны показываются на сайте, пока активен Pro (в т.ч. пробный период); без Pro сайт остаётся на базовом.</p>
        <DesignGallery designs={designs} value={design} onSelect={setDesign} />
        {isPro && !proActive && (
          <div className="card" style={{ padding: '.9rem 1rem', marginTop: '1rem', display: 'flex', gap: '.7rem', background: 'var(--warning-wash)', borderColor: 'color-mix(in srgb, var(--warning) 30%, var(--line))' }}>
            <i data-lucide="info" style={{ width: 18, height: 18, color: 'var(--warning)', flex: 'none' }}></i>
            <span style={{ fontSize: '.82rem', color: 'var(--ink-2)', lineHeight: 1.6 }}>Это премиум-дизайн. Он сохранится за сайтом, но на витрине покажется базовый, пока не активен Pro.</span>
          </div>
        )}
        <div style={{ display: 'flex', gap: '.6rem', marginTop: '1.3rem', flexWrap: 'wrap' }}>
          <a className="btn btn--outline" href={liveUrl} target="_blank" rel="noopener"><i data-lucide="external-link"></i> Посмотреть на сайте</a>
          <button className="btn btn--primary" disabled={!changed || busy} onClick={apply}>{busy ? 'Применяем…' : 'Применить'}</button>
          {isPro && !proActive && onPay && <button className="btn btn--ghost" onClick={() => onPay(site)}>Оформить Pro</button>}
        </div>
      </div>
    </div>
  );
}

// ---- экран «Добавить сайт» ----
function ScreenAddSite({ nav, onStartBuild, designs }) {
  const [url, setUrl] = useStateD('');
  const [design, setDesign] = useStateD('A');
  const valid = validYandex(url);
  const isProSel = (designs || []).some(d => d.key === design && d.tier === 'pro');
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
        <div className="field" style={{ marginTop: '1.3rem' }}>
          <label className="field__label">Дизайн сайта</label>
          <DesignGallery designs={designs} value={design} onSelect={setDesign} />
          {isProSel && <span className="field__hint" style={{ marginTop: '.6rem', display: 'block' }}>Премиум-дизайн активен, пока действует Pro (в т.ч. пробный период). Без Pro сайт покажется в базовом дизайне — оформить Pro можно в любой момент из кабинета.</span>}
        </div>
        <button className="btn btn--primary btn--lg btn--block" style={{ marginTop: '1.3rem' }} disabled={valid !== true} onClick={() => onStartBuild(url, design)}>Создать сайт</button>
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
