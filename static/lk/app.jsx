// ============================================================
// app.jsx — оболочка, роутер, состояние, навигация
// ============================================================
const { useState, useEffect, useRef } = React;

// group — заголовок раздела в боковом меню (показывается один раз перед первым пунктом группы)
const NAV = [
  { id: 'sites', label: 'Мои сайты', ic: 'layout-grid', group: 'Сайт' },
  { id: 'subscriptions', label: 'Подписки и платежи', ic: 'credit-card', group: 'Аккаунт' },
  { id: 'settings', label: 'Настройки', ic: 'settings', group: 'Аккаунт' },
  { id: 'support', label: 'Поддержка', ic: 'life-buoy', group: 'Помощь' },
];
const SECTION_OF = { sites: 'sites', 'add-site': 'sites', building: 'sites', payment: 'sites', admin: 'sites', design: 'sites', subscriptions: 'subscriptions', support: 'support', settings: 'settings' };
const TITLES = {
  sites: ['Мои сайты', null],
  'add-site': ['Новый сайт', null],
  building: ['Создаём сайт', null],
  payment: ['Оплата', null],
  admin: ['Редактор сайта', null],
  design: ['Дизайн сайта', null],
  subscriptions: ['Подписки и платежи', null],
  support: ['Поддержка', null],
  settings: ['Настройки', 'Аккаунт и безопасность'],
};

// Вторая строка титула — курсивной антиквой. Пишем в неё ТОЛЬКО состояние
// аккаунта: сколько сайтов, до какого числа Pro, когда был последний ответ.
// Пересказ заголовка («Статусы, продление и история») сюда не годится —
// он занимает место, но ничего не сообщает.
function plural(n, one, few, many) {
  const a = Math.abs(n) % 100, b = a % 10;
  if (a > 10 && a < 20) return many;
  if (b > 1 && b < 5) return few;
  if (b === 1) return one;
  return many;
}
function headState(screen, sites, tickets) {
  if (screen === 'sites') {
    if (!sites.length) return null;
    const building = sites.filter(s => s.build_status === 'queued' || s.build_status === 'building').length;
    const pro = sites.filter(s => s.proActive).length;
    const parts = [sites.length + ' ' + plural(sites.length, 'сайт', 'сайта', 'сайтов')];
    if (building) parts.push(building + ' ' + plural(building, 'собирается', 'собираются', 'собираются'));
    if (pro) parts.push(pro + ' на Pro');
    return parts.join(', ');
  }
  if (screen === 'subscriptions') {
    const proSite = sites.find(s => s.proActive && s.proUntil);
    if (proSite) return 'Pro до ' + proSite.proUntil;
    return sites.length ? 'все сайты на бесплатном тарифе' : null;
  }
  if (screen === 'support') {
    if (!tickets || !tickets.length) return 'обращений пока не было';
    return 'последнее обращение — ' + tickets[0].date;
  }
  return null;
}


const CABINET = new Set(['sites', 'add-site', 'building', 'payment', 'admin', 'design', 'subscriptions', 'support', 'settings', 'metrics']);

function plusDays(n) {
  const d = new Date(); d.setDate(d.getDate() + n);
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function App() {
  const [screen, setScreen] = useState('login');
  const [email, setEmail] = useState('');
  const [toast, setToast] = useState(null);
  const [payTarget, setPayTarget] = useState(null);
  const [menuSite, setMenuSite] = useState(null);
  const [confirmDel, setConfirmDel] = useState(false);
  const [delPw, setDelPw] = useState('');
  const [delSite, setDelSite] = useState(null);
  const [delSiteText, setDelSiteText] = useState('');
  const [metrics, setMetrics] = useState(null);
  const buildingRef = React.useRef(false);
  const [booted, setBooted] = useState(false);
  const [pendingClaim, setPendingClaim] = useState(null);

  const [sites, setSites] = useState([]);
  const [payments, setPayments] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [designs, setDesigns] = useState([]);
  const [designSite, setDesignSite] = useState(null);

  const ctx = { email, setEmail, pendingClaim, setPendingClaim };
  const nav = (s) => {
    setScreen(s);
    if (s === 'support') {
      window.API.tickets().then(d => setTickets(d.tickets || [])).catch(() => {});
    } else if (s === 'subscriptions') {
      loadSites();
      window.API.payments().then(d => setPayments(d.payments || [])).catch(() => {});
    } else if (s === 'sites') {
      loadSites();
    } else if (s === 'add-site') {
      ensureDesigns();
    }
  };
  const ping = (m) => { setToast(m); setTimeout(() => setToast(null), 2600); };

  // На старте: маршрут по URL (verify/reset/claim/возврат с оплаты) или проверка сессии
  useEffect(() => {
    const path = window.location.pathname;
    const params = new URLSearchParams(window.location.search);
    if (path === '/verify') { setScreen('confirm-email'); setBooted(true); return; }
    if (path === '/reset')  { setScreen('reset'); setBooted(true); return; }

    // Claim: /claim/{code} — забрать готовый сайт
    const claimMatch = path.match(/^\/claim\/([A-Za-z0-9_-]+)\/?$/);
    const claimCode = claimMatch ? claimMatch[1] : null;
    if (claimCode) {
      setPendingClaim(claimCode);
      window.API.me()
        .then(u => {
          // Уже залогинен — сразу привязываем
          setEmail(u.email);
          return window.API.claimSite(claimCode)
            .then(res => {
              window.history.replaceState({}, '', '/');
              ping('Сайт добавлен! Триал 7 дней активен.');
              setPendingClaim(null);
              setScreen('sites');
              return loadSites();
            })
            .catch(err => {
              window.history.replaceState({}, '', '/');
              ping(err.message || 'Не удалось забрать сайт');
              setScreen('sites');
              return loadSites();
            });
        })
        .catch(() => {
          // Не залогинен — на регистрацию. Код передадим в форму,
          // он «доедет» до привязки через письмо подтверждения email.
          setScreen('register');
        })
        .finally(() => setBooted(true));
      return;
    }

    const paidId = params.get('paid');
    window.API.me()
      .then(u => {
        setEmail(u.email);
        if (paidId) {
          window.history.replaceState({}, '', '/');
          setScreen('payment-processing');
        } else {
          setScreen('sites');
        }
        return loadSites();
      })
      .catch(() => setScreen('login'))
      .finally(() => setBooted(true));
  }, []);

  async function loadSites() {
    try {
      const data = await window.API.sites();
      setSites(data.sites || []);
      setCanAdd(data.canAdd !== false);
      setCanAddReason(data.canAddReason || '');
      return data;
    } catch (e) { return { sites: [] }; }
  }

  // refresh lucide icons after every render
  useEffect(() => { if (window.lucide) window.lucide.createIcons(); });

  const [canAdd, setCanAdd] = useState(true);
  const [canAddReason, setCanAddReason] = useState('');
  const [buildId, setBuildId] = useState(null);

  async function startBuild(url, design) {
    if (buildingRef.current) return;   // защита от двойного клика (дубль сайта)
    buildingRef.current = true;
    try {
      const res = await window.API.addSite(url, design);
      setBuildId(res.id);
      nav('building');
    } catch (ex) {
      ping(ex.message || 'Не удалось создать сайт');
    } finally {
      buildingRef.current = false;
    }
  }
  async function finishBuild() {
    await loadSites();
    nav('sites');
    ping('Сайт готов!');
  }
  function openPay(site) { setPayTarget(site); nav('payment'); }
  function confirmPaid() {
    nav('payment-success');
    loadSites();
  }
  async function openMetrics(site) {
    setMenuSite(null);
    setMetrics(null);
    nav('metrics');
    try {
      setMetrics(await window.API.siteMetrics(site.id));
    } catch (ex) {
      ping(ex.message || 'Не удалось загрузить статистику');
      nav('sites');
    }
  }
  async function ensureDesigns() {
    if (designs.length) return;
    try { const d = await window.API.designs(); setDesigns(d.designs || []); } catch (e) {}
  }
  function openDesign(site) {
    setMenuSite(null);
    setDesignSite(site);
    ensureDesigns();
    nav('design');
  }
  async function applyDesign(id, key) {
    try {
      await window.API.setDesign(id, key);
      setSites(prev => prev.map(s => s.id === id ? { ...s, design: key } : s));
      setDesignSite(prev => (prev && prev.id === id) ? { ...prev, design: key } : prev);
      ping('Дизайн применён');
    } catch (ex) {
      ping(ex.message || 'Не удалось сменить дизайн');
    }
  }
  function askDeleteSite(site) {
    if (site.canDelete === false) {
      ping('Дождитесь окончания trial-периода');
      return;
    }
    setMenuSite(null);
    setDelSiteText('');
    setDelSite(site);
  }
  async function confirmDeleteSite() {
    if (!delSite) return;
    try {
      await window.API.deleteSite(delSite.id, { confirm: delSiteText });
      setSites(prev => prev.filter(s => s.id !== delSite.id));
      setDelSite(null); setDelSiteText('');
      ping('Сайт удалён');
    } catch (ex) {
      ping(ex.message || 'Не удалось удалить сайт');
    }
  }
  async function submitTicket(subj, body) {
    try {
      await window.API.submitTicket(subj, body);
      setTickets(prev => [{ subj, body, status: 'open', date: new Date().toLocaleDateString('ru-RU') }, ...prev]);
      ping('Обращение отправлено');
    } catch (ex) {
      ping(ex.message || 'Не удалось отправить');
    }
  }
  async function logout() {
    try { await window.API.logout(); } catch (e) {}
    setEmail(''); setSites([]); setScreen('login');
  }
  async function deleteAccount() {
    try {
      await window.API.deleteAccount(delPw);
    } catch (ex) {
      ping(ex.message || 'Не удалось удалить аккаунт');
      return;
    }
    setConfirmDel(false); setDelPw(''); setEmail(''); setScreen('login'); ping('Аккаунт удалён');
  }

  if (!booted) {
    return <div className="app"><div className="screen"><div className="notice"><div className="notice__box"><div className="spin"></div></div></div></div></div>;
  }

  // ---------- AUTH / standalone screens ----------
  if (!CABINET.has(screen)) {
    let inner = null;
    if (screen === 'login') inner = <ScreenLogin nav={nav} ctx={ctx} />;
    else if (screen === 'register') inner = <ScreenRegister nav={nav} ctx={ctx} />;
    else if (screen === 'register-sent') inner = <ScreenRegisterSent nav={nav} ctx={ctx} />;
    else if (screen === 'confirm-email') inner = <ScreenConfirmEmail nav={nav} ctx={ctx} />;
    else if (screen === 'forgot') inner = <ScreenForgot nav={nav} ctx={ctx} />;
    else if (screen === 'forgot-sent') inner = <ScreenForgotSent nav={nav} ctx={ctx} />;
    else if (screen === 'reset') inner = <ScreenReset nav={nav} ctx={ctx} />;
    else if (screen === 'yukassa') inner = <ScreenYukassa nav={nav} />;
    else if (screen === 'payment-processing') inner = <ScreenPaymentProcessing onConfirmed={confirmPaid} />;
    else if (screen === 'payment-success') inner = <ScreenPaymentSuccess nav={nav} site={payTarget} />;
    return <div className="app">{inner}{toast && <div className="toast"><i data-lucide="check-circle"></i>{toast}</div>}</div>;
  }

  // ---------- CABINET ----------
  const [title, sub] = TITLES[screen] || ['', null];
  const state = headState(screen, sites, tickets);
  const section = SECTION_OF[screen] || 'sites';
  let body = null;
  if (screen === 'sites') body = <ScreenSites nav={nav} sites={sites} onPay={openPay} onMenu={setMenuSite} onStats={openMetrics} canAdd={canAdd} />;
  else if (screen === 'add-site') body = <ScreenAddSite nav={nav} onStartBuild={startBuild} designs={designs} />;
  else if (screen === 'design') body = <ScreenDesign nav={nav} site={designSite} designs={designs} onApply={applyDesign} onPay={openPay} />;
  else if (screen === 'building') body = <ScreenBuilding onDone={finishBuild} buildId={buildId} />;
  else if (screen === 'payment') body = <ScreenPayment nav={nav} site={payTarget} />;
  else if (screen === 'admin') body = <AdminStub nav={nav} site={payTarget} />;
  else if (screen === 'subscriptions') body = <ScreenSubscriptions nav={nav} sites={sites} payments={payments} onPay={openPay} />;
  else if (screen === 'support') body = <ScreenSupport email={email} tickets={tickets} onSubmit={submitTicket} />;
  else if (screen === 'settings') body = <ScreenSettings email={email} onDelete={() => setConfirmDel(true)} />;
  else if (screen === 'metrics') body = <ScreenMetrics nav={nav} metrics={metrics} />;

  return (
    <div className="app">
      <div className="screen">
        <div className="shell">
          {/* sidebar (desktop) */}
          <aside className="side">
            <a className="logo side__brand" onClick={() => nav('sites')} style={{ cursor: 'pointer' }}><img src="/static/lk/assets/seal-192.png" alt="" /><b>uqqi<span className="dot">.</span>ru</b></a>
            {NAV.map((n, i) => (
              <React.Fragment key={n.id}>
                {(i === 0 || NAV[i - 1].group !== n.group) && <div className="side__group">{n.group}</div>}
                <a className={'nav-i' + (section === n.id ? ' on' : '')} onClick={() => nav(n.id)}>
                  <i data-lucide={n.ic}></i>{n.label}
                </a>
              </React.Fragment>
            ))}
            <div className="side__foot">
              {!sites.some(s => s.proActive) && (
                <div className="side__promo">
                  <b>Сейчас базовый тариф</b>
                  <span>Pro добавляет премиум-оформления и чат с клиентами в Telegram. От 299 ₽ в месяц.</span>
                  <button type="button" className="btn btn--primary btn--sm btn--block" onClick={() => nav('subscriptions')}>Посмотреть Pro</button>
                </div>
              )}
              <div className="usercard"><div className="av">{(email || 'U')[0].toUpperCase()}</div><div style={{ minWidth: 0 }}>{sites.some(s => s.proActive) && <div style={{ fontSize: '.62rem', fontWeight: 600, letterSpacing: '.06em', color: 'var(--terracotta-deep)' }}>PRO</div>}<div className="em">{email}</div></div></div>
              <a className="nav-i" onClick={logout} style={{ marginTop: '.2rem' }}><i data-lucide="log-out"></i>Выйти</a>
            </div>
          </aside>

          {/* main */}
          <section className="main">
            {/* mobile topbar */}
            <header className="topbar">
              <a className="logo" onClick={() => nav('sites')} style={{ cursor: 'pointer' }}><img src="/static/lk/assets/seal-192.png" alt="" /><b>uqqi<span className="dot">.</span>ru</b></a>
              <div className="topbar__r">
                <span className="tag" style={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{email}</span>
                <button className="iconbtn" onClick={logout} title="Выйти"><i data-lucide="log-out"></i></button>
              </div>
            </header>

            <div className="main__head">
              <div>
                <h1 className="h">{title}</h1>
                {state && <div className="state">{state}</div>}
                {sub && <div className="sub">{sub}</div>}
              </div>
              {screen === 'sites' && (
                canAdd
                  ? <button className="btn btn--primary btn--sm" onClick={() => nav('add-site')}><i data-lucide="plus"></i> Добавить сайт</button>
                  : <span className="tip-wrap" data-tip={canAddReason || 'Сначала оплатите предыдущий'}>
                      <button className="btn btn--primary btn--sm" disabled><i data-lucide="plus"></i> Добавить сайт</button>
                    </span>
              )}
            </div>

            <div className="main__body fade-enter" key={screen}>{body}</div>

            {/* mobile bottom nav */}
            <nav className="bottomnav">
              {NAV.map(n => (
                <a key={n.id} className={section === n.id ? 'on' : ''} onClick={() => nav(n.id)}>
                  <i data-lucide={n.ic}></i>{n.label.split(' ')[0]}
                </a>
              ))}
            </nav>
          </section>
        </div>

        {/* site menu modal */}
        {menuSite && (
          <div className="scrim" onClick={() => setMenuSite(null)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h3>{menuSite.name}</h3>
              <p>{menuSite.slug}.uqqi.ru</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '.6rem', marginTop: '1.3rem' }}>
                {/* «Статистика» вынесена отдельной кнопкой на карточку сайта. */}
                {/* Редактирование содержимого — Pro-функция: бэкенд гейтит тем же
                    pro_active (_can_edit_site), кнопка лишь не ведёт в тупик. */}
                {menuSite.proActive
                  ? <a className="btn btn--ghost btn--block" href={`/site/${menuSite.slug}/edit`}><i data-lucide="pencil"></i> Редактировать контент</a>
                  : <span className="tip-wrap" data-tip="Редактирование содержимого входит в Pro" style={{ display: 'block' }}>
                      <button className="btn btn--ghost btn--block" disabled style={{ opacity: .45, cursor: 'not-allowed', width: '100%' }}><i data-lucide="pencil"></i> Редактировать контент</button>
                    </span>
                }
                <button className="btn btn--ghost btn--block" onClick={() => openDesign(menuSite)}><i data-lucide="palette"></i> Дизайн</button>
                {menuSite.canDelete === false
                  ? <span className="tip-wrap" data-tip="Дождитесь окончания trial-периода" style={{ display: 'block' }}>
                      <button className="btn btn--ghost btn--block" disabled style={{ opacity: .45, cursor: 'not-allowed', width: '100%' }}><i data-lucide="trash-2"></i> Удалить сайт</button>
                    </span>
                  : <button className="btn btn--danger btn--block" onClick={() => askDeleteSite(menuSite)}><i data-lucide="trash-2"></i> Удалить сайт</button>
                }
              </div>
            </div>
          </div>
        )}

        {/* delete site modal */}
        {delSite && (
          <div className="scrim" onClick={() => { setDelSite(null); setDelSiteText(''); }}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h3>Удалить сайт?</h3>
              <p>Сайт <b>{delSite.name}</b> ({delSite.slug}.uqqi.ru) будет удалён безвозвратно.</p>
              <p className="muted" style={{ fontSize: '.84rem', marginTop: '.6rem' }}>Введите название сайта для подтверждения:</p>
              <input className="input" placeholder={delSite.name} value={delSiteText} onChange={e => setDelSiteText(e.target.value)} style={{ margin: '.5rem 0 .2rem' }} />
              <div className="modal__actions">
                <button className="btn btn--ghost btn--block" onClick={() => { setDelSite(null); setDelSiteText(''); }}>Отмена</button>
                <button className="btn btn--danger btn--block"
                        disabled={delSiteText.trim().toLowerCase() !== (delSite.name || '').trim().toLowerCase() && delSiteText.trim().toLowerCase() !== (delSite.slug || '').toLowerCase()}
                        onClick={confirmDeleteSite}>Удалить</button>
              </div>
            </div>
          </div>
        )}

        {/* delete account modal */}
        {confirmDel && (
          <div className="scrim" onClick={() => { setConfirmDel(false); setDelPw(''); }}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h3>Удалить аккаунт?</h3>
              <p>Это действие необратимо. Все сайты будут отключены, а данные удалены навсегда.</p>
              <input className="input" type="password" placeholder="Введите пароль для подтверждения" value={delPw} onChange={e => setDelPw(e.target.value)} style={{ margin: '.8rem 0 .2rem' }} />
              <div className="modal__actions">
                <button className="btn btn--ghost btn--block" onClick={() => { setConfirmDel(false); setDelPw(''); }}>Отмена</button>
                <button className="btn btn--danger btn--block" disabled={!delPw} onClick={deleteAccount}>Удалить</button>
              </div>
            </div>
          </div>
        )}
        {toast && <div className="toast"><i data-lucide="check-circle"></i>{toast}</div>}
      </div>
    </div>
  );
}

function AdminStub({ nav }) {
  return (
    <div className="wrap-md">
      <a className="linklike" style={{ fontSize: '.84rem', display: 'inline-flex', alignItems: 'center', gap: '.3rem', marginBottom: '1.2rem' }} onClick={() => nav('sites')}><i data-lucide="arrow-left" style={{ width: 15, height: 15 }}></i> Мои сайты</a>
      <div className="card" style={{ padding: '2.2rem 1.8rem', textAlign: 'center' }}>
        <div className="empty__ic" style={{ margin: '0 auto 1rem' }}><i data-lucide="pencil-ruler"></i></div>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '1.3rem', letterSpacing: '-.02em', color: 'var(--ink)' }}>Редактор контента сайта</h2>
        <p className="muted" style={{ fontSize: '.9rem', lineHeight: 1.65, marginTop: '.5rem', maxWidth: 380, marginInline: 'auto' }}>Здесь владелец меняет тексты, фото, часы работы и услуги — без программиста. Отдельная админка контента.</p>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
