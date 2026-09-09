// app.bundle.js — авто-сборка (на сервере пересоберите через build_lk.sh при возможности)
const { useState, useEffect, useRef } = React;
const { useState: useStateD, useEffect: useEffectD, useRef: useRefD } = React;
const { useState: useStateB } = React;

// ============================================================
// auth.jsx — регистрация / вход / восстановление / подтверждение
// ============================================================

function AuthAside() {
  return (
    <div className="auth__aside">
      <a className="logo" href="#"><img src="/static/lk/assets/seal-192.png" alt="" /><b>uqqi<span className="dot">.</span>ru</b></a>
      <div className="auth__pitch">
        <h2>Сайт вашего бизнеса <em>уже почти готов.</em></h2>
        <p>Войдите в кабинет — и через минуту у вашей кофейни, кафе или магазина появится аккуратный сайт на собственном адресе.</p>
        <ul className="auth__bullets">
          <li><i data-lucide="zap"></i>Собираем сайт из карточки Яндекс Карт</li>
          <li><i data-lucide="pencil"></i>Контент меняете сами, без программиста</li>
          <li><i data-lucide="globe"></i>Свой адрес вида название.uqqi.ru</li>
        </ul>
      </div>
      <p className="legal">Нажимая «Войти», вы соглашаетесь с условиями использования сервиса.</p>
    </div>
  );
}

function PasswordField({ label = 'Пароль', name, placeholder = '••••••••', value, onChange }) {
  const [show, setShow] = useState(false);
  return (
    <div className="field">
      <label className="field__label">{label}</label>
      <div style={{ position: 'relative' }}>
        <input className="input" type={show ? 'text' : 'password'} placeholder={placeholder}
          style={{ paddingRight: '2.6rem' }} value={value} onChange={onChange} />
        <button type="button" onClick={() => setShow(s => !s)}
          style={{ position: 'absolute', right: '.6rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--ink-muted)', display: 'flex' }}>
          <i data-lucide={show ? 'eye-off' : 'eye'} style={{ width: 17, height: 17 }}></i>
        </button>
      </div>
    </div>
  );
}

// Подтверждение пароля с подсказками: правила загораются по мере ввода,
// последняя строка — совпадение. Гейт на кнопке остаётся прежним (ok),
// подсказка только объясняет, чего не хватает.
function PasswordConfirm({ pw, value, onChange, label = 'Повтор пароля' }) {
  const [show, setShow] = useState(false);
  const rules = [
    { id: 'len',   ok: (value || '').length >= 8,                       text: 'Не короче 8 символов' },
    { id: 'mix',   ok: /[a-zA-Zа-яА-Я]/.test(value) && /\d/.test(value), text: 'Есть буквы и цифры' },
    { id: 'match', ok: !!value && value === pw,                          text: 'Совпадает с паролем' },
  ];
  const bad = value && rules.some(r => !r.ok);
  return (
    <div className="field">
      <label className="field__label">{label}</label>
      <div style={{ position: 'relative' }}>
        <input className={'input' + (bad ? ' is-error' : (value && !bad ? ' is-valid' : ''))}
          type={show ? 'text' : 'password'} placeholder="••••••••"
          style={{ paddingRight: '2.6rem' }} value={value} onChange={onChange} />
        <button type="button" onClick={() => setShow(s => !s)} aria-label={show ? 'Скрыть пароль' : 'Показать пароль'}
          style={{ position: 'absolute', right: '.6rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--ink-muted)', display: 'flex' }}>
          <i data-lucide={show ? 'eye-off' : 'eye'} style={{ width: 17, height: 17 }}></i>
        </button>
      </div>
      <ul className="pwrules" aria-live="polite">
        {rules.map(r => (
          <li key={r.id} className={'pwrule' + (r.ok ? ' is-ok' : '')}>
            <i data-lucide={r.ok ? 'check' : 'circle'}></i>{r.text}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ---------- Вход ----------
function ScreenLogin({ nav, ctx }) {
  const [email, setEmail] = useState(ctx.email || '');
  const [pw, setPw] = useState('');
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setErr(''); setBusy(true);
    try {
      await window.API.login(email, pw);
      ctx.setEmail(email);
      nav('sites');
    } catch (ex) {
      setErr(ex.message || 'Не удалось войти');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="screen fade-enter">
      <div className="auth">
        <AuthAside />
        <div className="auth__main">
          <div className="auth__box">
            <h1 className="auth__h">С возвращением</h1>
            <p className="auth__sub">Войдите, чтобы управлять своими сайтами.</p>
            <form className="auth__form" onSubmit={submit}>
              <div className="field">
                <label className="field__label">Email</label>
                <input className="input" type="email" placeholder="Введите ваш email" value={email} onChange={e => setEmail(e.target.value)} required />
              </div>
              <PasswordField value={pw} onChange={e => setPw(e.target.value)} />
              {err && <div className="field__err" style={{ marginTop: '-.3rem' }}>{err}</div>}
              <div className="between" style={{ marginTop: '-.3rem' }}>
                <label className="check"><input type="checkbox" defaultChecked /> Запомнить меня</label>
                <a className="linklike" style={{ fontSize: '.82rem' }} onClick={() => nav('forgot')}>Забыли пароль?</a>
              </div>
              <button className="btn btn--primary btn--block btn--lg" type="submit" disabled={busy}>{busy ? 'Входим…' : 'Войти'}</button>
            </form>
            <p className="auth__alt">Нет аккаунта? <a className="linklike" onClick={() => nav('register')}>Создать аккаунт</a></p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------- Регистрация ----------
function ScreenRegister({ nav, ctx }) {
  const [email, setEmail] = useState(ctx.email || '');
  const [pw, setPw] = useState('');
  const [pw2, setPw2] = useState('');
  const [agree, setAgree] = useState(false);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const mismatch = pw2.length > 0 && pw !== pw2;
  const ok = email && pw.length >= 6 && pw === pw2 && agree;

  async function submit(e) {
    e.preventDefault();
    if (!ok) return;
    setErr(''); setBusy(true);
    try {
      await window.API.register(email, pw, agree, ctx.pendingClaim || '');
      ctx.setEmail(email);
      nav('register-sent');
    } catch (ex) {
      setErr(ex.message || 'Не удалось зарегистрироваться');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="screen fade-enter">
      <div className="auth">
        <AuthAside />
        <div className="auth__main">
          <div className="auth__box">
            <h1 className="auth__h">Создать аккаунт</h1>
            <p className="auth__sub">Бесплатно. Базовый сайт остаётся бесплатным навсегда.</p>
            <form className="auth__form" onSubmit={submit}>
              <div className="field">
                <label className="field__label">Email</label>
                <input className="input" type="email" placeholder="Введите ваш email" value={email} onChange={e => setEmail(e.target.value)} required />
              </div>
              <PasswordField label="Пароль" value={pw} onChange={e => setPw(e.target.value)} />
              <PasswordConfirm pw={pw} value={pw2} onChange={e => setPw2(e.target.value)} />
              <label className="check">
                <input type="checkbox" checked={agree} onChange={e => setAgree(e.target.checked)} />
                <span>Я принимаю <a className="linklike" href="/oferta" target="_blank">оферту</a> и <a className="linklike" href="/privacy" target="_blank">политику конфиденциальности</a>.</span>
              </label>
              {err && <div className="field__err">{err}</div>}
              <button className="btn btn--primary btn--block btn--lg" type="submit" disabled={!ok || busy}>{busy ? 'Создаём…' : 'Зарегистрироваться'}</button>
            </form>
            <p className="auth__alt">Уже есть аккаунт? <a className="linklike" onClick={() => nav('login')}>Войти</a></p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------- Подтвердите email ----------
function ScreenRegisterSent({ nav, ctx }) {
  const [sent, setSent] = useState(false);
  async function resend(e) {
    e.preventDefault();
    try { await window.API.resendVerify(ctx.email); setSent(true); } catch (ex) {}
  }
  return (
    <div className="screen fade-enter">
      <div className="auth">
        <AuthAside />
        <div className="notice">
          <div className="notice__box">
            <div className="notice__ic"><i data-lucide="mail-check"></i></div>
            <h2>Подтвердите email</h2>
            <p>Мы отправили письмо на <b>{ctx.email || 'you@example.ru'}</b>. Перейдите по ссылке из письма, чтобы активировать аккаунт.</p>
            {ctx.pendingClaim && (
              <p style={{ background: 'var(--surface2, #f5f0e8)', borderRadius: '10px', padding: '.7rem .9rem', fontSize: '.86rem', marginTop: '.6rem' }}>
                После подтверждения ваш готовый сайт появится в кабинете — первые 7 дней бесплатно.
              </p>
            )}
            <div className="row" style={{ gap: '.7rem', marginTop: '.4rem' }}>
              <button className="btn btn--ghost btn--sm" onClick={() => nav('login')}>Я подтвердил — войти</button>
            </div>
            <p className="legal" style={{ marginTop: '.4rem' }}>
              Не пришло письмо? Проверьте папку «Спам» или {sent
                ? <span style={{ color: 'var(--success-soft)' }}>письмо отправлено повторно</span>
                : <a className="linklike" href="#" onClick={resend}>отправьте ещё раз</a>}.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------- Email подтверждён (verify по токену из URL) ----------
function ScreenConfirmEmail({ nav, ctx }) {
  const [err, setErr] = useState('');
  const [claimed, setClaimed] = useState(null);
  React.useEffect(() => {
    const token = new URLSearchParams(window.location.search).get('token');
    if (!token) { setErr('Ссылка недействительна'); return; }
    fetch('/lk/api/verify?token=' + encodeURIComponent(token), { credentials: 'same-origin' })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(data => {
        if (data && data.claimed) {
          setClaimed(data.claimed);
          setTimeout(() => { window.history.replaceState({}, '', '/'); nav('sites'); }, 2600);
        } else {
          setTimeout(() => { window.history.replaceState({}, '', '/'); nav('sites'); }, 1500);
        }
      })
      .catch(() => setErr('Ссылка недействительна или устарела'));
  }, []);
  return (
    <div className="screen fade-enter">
      <div className="notice">
        <div className="notice__box">
          {err ? (
            <>
              <div className="notice__ic" style={{ background: 'var(--danger-wash, #fde8e8)', color: 'var(--danger)' }}><i data-lucide="alert-triangle"></i></div>
              <h2>Не удалось подтвердить</h2>
              <p>{err}</p>
              <button className="btn btn--primary btn--sm" style={{ marginTop: '.4rem' }} onClick={() => nav('login')}>Ко входу</button>
            </>
          ) : claimed ? (
            <>
              <div className="notice__ic ok"><i data-lucide="check"></i></div>
              <h2>Готово! Сайт ваш</h2>
              <p>«{claimed.title}» добавлен в ваш кабинет.<br />Первые 7 дней — бесплатно.</p>
              <div className="spin" style={{ marginTop: '.4rem' }}></div>
            </>
          ) : (
            <>
              <div className="notice__ic ok"><i data-lucide="check"></i></div>
              <h2>Email подтверждён</h2>
              <p>Входим в кабинет<span className="dots"><span>.</span><span>.</span><span>.</span></span></p>
              <div className="spin" style={{ marginTop: '.4rem' }}></div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------- Забыли пароль ----------
function ScreenForgot({ nav, ctx }) {
  const [email, setEmail] = useState(ctx.email || '');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try { await window.API.forgot(email); ctx.setEmail(email); nav('forgot-sent'); }
    catch (ex) { ctx.setEmail(email); nav('forgot-sent'); }  // не раскрываем существование email
    finally { setBusy(false); }
  }

  return (
    <div className="screen fade-enter">
      <div className="auth">
        <AuthAside />
        <div className="auth__main">
          <div className="auth__box">
            <a className="linklike" style={{ fontSize: '.82rem', display: 'inline-flex', alignItems: 'center', gap: '.3rem', marginBottom: '1.2rem' }} onClick={() => nav('login')}><i data-lucide="arrow-left" style={{ width: 15, height: 15 }}></i> Назад ко входу</a>
            <h1 className="auth__h">Восстановление пароля</h1>
            <p className="auth__sub">Укажите email — пришлём ссылку для сброса пароля.</p>
            <form className="auth__form" onSubmit={submit}>
              <div className="field">
                <label className="field__label">Email</label>
                <input className="input" type="email" placeholder="Введите ваш email" value={email} onChange={e => setEmail(e.target.value)} required />
              </div>
              <button className="btn btn--primary btn--block btn--lg" type="submit" disabled={busy}>{busy ? 'Отправляем…' : 'Отправить ссылку для сброса'}</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

function ScreenForgotSent({ nav, ctx }) {
  return (
    <div className="screen fade-enter">
      <div className="auth">
        <AuthAside />
        <div className="notice">
          <div className="notice__box">
            <div className="notice__ic"><i data-lucide="send"></i></div>
            <h2>Письмо отправлено</h2>
            <p>Если аккаунт с адресом <b>{ctx.email || 'you@example.ru'}</b> существует, ссылка для сброса пароля придёт на почту. Откройте её, чтобы задать новый пароль.</p>
            <div className="row" style={{ gap: '.7rem', marginTop: '.4rem' }}>
              <button className="btn btn--ghost btn--sm" onClick={() => nav('login')}>Ко входу</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------- Новый пароль (reset по токену из URL) ----------
function ScreenReset({ nav, ctx }) {
  const [pw, setPw] = useState('');
  const [pw2, setPw2] = useState('');
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const mismatch = pw2.length > 0 && pw !== pw2;
  const ok = pw.length >= 6 && pw === pw2;
  const token = new URLSearchParams(window.location.search).get('token') || '';

  async function submit(e) {
    e.preventDefault();
    if (!ok) return;
    if (!token) { setErr('Ссылка недействительна'); return; }
    setErr(''); setBusy(true);
    try {
      await window.API.reset(token, pw);
      window.history.replaceState({}, '', '/');
      nav('login');
    } catch (ex) {
      setErr(ex.message || 'Ссылка недействительна или устарела');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="screen fade-enter">
      <div className="auth">
        <AuthAside />
        <div className="auth__main">
          <div className="auth__box">
            <h1 className="auth__h">Новый пароль</h1>
            <p className="auth__sub">Придумайте новый пароль для входа в кабинет.</p>
            <form className="auth__form" onSubmit={submit}>
              <PasswordField label="Новый пароль" value={pw} onChange={e => setPw(e.target.value)} />
              <PasswordConfirm pw={pw} value={pw2} onChange={e => setPw2(e.target.value)} />
              {err && <div className="field__err">{err}</div>}
              <button className="btn btn--primary btn--block btn--lg" type="submit" disabled={!ok || busy}>{busy ? 'Сохраняем…' : 'Сохранить пароль'}</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}


// ============================================================
// dashboard.jsx — список сайтов, статусы, пусто, добавление, прогресс
// ============================================================

// ---- бейдж статуса ----
function StatusBadge({ site }) {
  const map = {
    building: { cls: 'badge--building', ic: 'loader', txt: 'Создаётся…' },
    error:    { cls: 'badge--error', ic: 'alert-triangle', txt: 'Ошибка сборки' },
    free:     { cls: 'badge--free', ic: null, txt: 'Бесплатный' },
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
function SiteCard({ site, nav, onPay, onDesign, onDelete, onStats }) {
  const isBuilding = site.status === 'building';
  const isError = site.status === 'error';
  return (
    <div className="card sitecard">
      <div className="sitecard__top">
        <div className="row" style={{ alignItems: 'flex-start' }}>
          <div className="sitecard__thumb" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--terracotta-deep)', background: 'var(--sand)', borderColor: 'var(--sand-line)' }}>
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
          {site.status !== 'pro' && site.status !== 'protrial' && <span>Pro: <b>от 299 ₽ / мес</b></span>}
          <span>Создан: <b>{site.created}</b></span>
        </div>
      )}

      {/* Все действия — отдельными кнопками на карточке: за «шестерёнкой»
          их приходилось искать, а на телефоне это лишний экран. */}
      <div className="sitecard__actions">
        {!isBuilding && !isError && <button className="btn btn--ghost btn--sm" onClick={() => onStats(site)}><i data-lucide="bar-chart-2"></i> Статистика</button>}
        {!isBuilding && !isError && <button className="btn btn--ghost btn--sm" onClick={() => onDesign(site)}><i data-lucide="palette"></i> Дизайн</button>}
        {/* Редактирование содержимого — Pro-функция: бэкенд гейтит тем же
            pro_active (_can_edit_site), кнопка лишь не ведёт в тупик. */}
        {!isBuilding && !isError && (site.proActive
          ? <a className="btn btn--ghost btn--sm" href={`/site/${site.slug}/edit`}><i data-lucide="pencil"></i> Редактировать</a>
          : <span className="tip-wrap" data-tip="Редактирование содержимого входит в Pro">
              <button className="btn btn--ghost btn--sm" disabled style={{ opacity: .45, cursor: 'not-allowed' }}><i data-lucide="pencil"></i> Редактировать</button>
            </span>)}
        {site.status === 'claim' && <button className="btn btn--primary btn--sm" onClick={() => onPay(site)}>Оплатить, чтобы забрать сайт</button>}
        {site.status === 'free' && <button className="btn btn--primary btn--sm" onClick={() => onPay(site)}>Сделать PRO-сайтом</button>}
        {(site.status === 'protrial' || site.status === 'pro') && <button className="btn btn--ghost btn--sm" onClick={() => onPay(site)}>Продлить Pro</button>}
        {isError && <button className="btn btn--primary btn--sm" onClick={() => nav('add-site')}><i data-lucide="rotate-cw"></i> Попробовать снова</button>}
        {!isBuilding && (site.canDelete === false
          ? <span className="tip-wrap" data-tip="Дождитесь окончания пробного периода">
              <button className="btn btn--ghost btn--sm" disabled style={{ opacity: .45, cursor: 'not-allowed' }}><i data-lucide="trash-2"></i> Удалить</button>
            </span>
          : <button className="btn btn--ghost btn--sm sitecard__del" onClick={() => onDelete(site)}><i data-lucide="trash-2"></i> Удалить</button>)}
      </div>
    </div>
  );
}

// ---- окно «пробный Pro закончился» ----
// Показываем один раз за сессию (sessionStorage): «при входе в ЛК», а не на
// каждом переключении экрана. Ключ с id сайта — про каждый сайт напоминаем свой раз.
function TrialEndedModal({ site, onPay, onClose }) {
  if (!site) return null;
  return (
    <div className="scrim" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <h3>Пробный Pro закончился</h3>
        <p>На сайте <b>{site.name}</b> ({site.slug}.uqqi.ru) закончился пробный
          период{site.trialEndedAt ? ` ${site.trialEndedAt}` : ''}. Сайт продолжает работать
          бесплатно, но эти возможности сейчас отключены:</p>
        <ul className="trial-lost">
          <li><i data-lucide="palette"></i>Премиум-оформления витрины</li>
          <li><i data-lucide="calendar-check"></i>Онлайн-запись со слотами</li>
          <li><i data-lucide="message-circle"></i>Чат на сайте с сообщениями в Telegram</li>
          <li><i data-lucide="pencil"></i>Редактирование содержимого сайта</li>
        </ul>
        <div className="trial-price">
          {/* <s> — семантическое «уже не действует»: скринридер объявит его как
              зачёркнутое, одного line-through в CSS для этого мало. */}
          <s className="trial-price__old"><span className="sr-only">Старая цена </span>1990 ₽</s>
          <span className="trial-price__new">{fmtRub(PLANS_LK[0].amount)} ₽</span>
          <span className="trial-price__per">в месяц</span>
        </div>
        <div className="modal__actions">
          <button className="btn btn--ghost btn--block" onClick={onClose}>Позже</button>
          <button className="btn btn--primary btn--block" onClick={() => onPay(site)}>Вернуть Pro</button>
        </div>
      </div>
    </div>
  );
}

// ---- экран «Мои сайты» ----
function ScreenSites({ nav, sites, onPay, onDesign, onDelete, onStats, canAdd }) {
  if (sites.length === 0) {
    return (
      <div className="empty">
        <div className="empty__box">
          <div className="empty__ic"><i data-lucide="layout-template"></i></div>
          <h2>У вас пока нет сайтов</h2>
          <p>Вставьте ссылку на карточку вашей организации в Яндекс Картах — и мы соберём готовый сайт за минуту.</p>
          <button className="btn btn--primary btn--lg" onClick={() => nav('add-site')}>
            <i data-lucide="plus"></i> Создать первый сайт
            <span className="btn__pro">PRO 7 дней</span>
          </button>
        </div>
      </div>
    );
  }
  return (
    <div className="sites">
      {sites.map(s => <SiteCard key={s.id} site={s} nav={nav} onPay={onPay} onDesign={onDesign} onDelete={onDelete} onStats={onStats} />)}
      <div style={{ marginTop: '.3rem' }}>
        {canAdd
          ? (sites.length >= 4 && <button className="btn btn--outline" onClick={() => nav('add-site')}><i data-lucide="plus"></i> Добавить сайт</button>)
          : <div className="card" style={{ padding: '1rem 1.1rem', display: 'flex', gap: '.7rem', alignItems: 'center', background: 'var(--warning-wash)', borderColor: 'color-mix(in srgb,var(--warning) 30%,var(--line))' }}>
              <i data-lucide="info" style={{ width: 18, height: 18, color: 'var(--warning)', flex: 'none' }}></i>
              <span style={{ fontSize: '.84rem', color: 'var(--ink-2)' }}>Дождитесь завершения сборки текущего сайта — потом можно добавить ещё.</span>
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

// ---- галерея дизайнов (пикер при создании + смена оформления в ЛК) ----
// Превью ЖИВОЕ: витрина клиента рендерится по ?variant=<key>&preview=1 и
// ужимается в карточку, поэтому человек видит СВОИ фото, услуги и отзывы,
// а не абстрактную картинку. Пока сайта нет (экран «Добавить сайт»), slug
// неизвестен — тогда показываем текстовую карточку.
function designPreviewUrl(slug, key) {
  return 'https://' + slug + '.uqqi.ru/?variant=' + encodeURIComponent(key) + '&preview=1';
}

function DesignCard({ d, selected, onSelect, slug, onZoom, lead }) {
  const [near, setNear] = useStateD(false);   // ленивая подгрузка iframe
  const [scale, setScale] = useStateD(0.27);  // витрина 1280px, ужатая под карточку
  const boxRef = useRefD(null);
  const stageRef = useRefD(null);
  useEffectD(() => {
    if (!slug || near) return;
    const el = boxRef.current;
    if (!el || !window.IntersectionObserver) { setNear(true); return; }
    const io = new window.IntersectionObserver(function (es) {
      if (es[0].isIntersecting) { setNear(true); io.disconnect(); }
    }, { rootMargin: '300px' });
    io.observe(el);
    return function () { io.disconnect(); };
  }, [slug, near]);
  useEffectD(() => {
    const el = stageRef.current;
    if (!el) return;
    function fit() { const w = el.clientWidth; if (w) setScale(w / 1280); }
    fit();
    if (!window.ResizeObserver) return;
    const ro = new window.ResizeObserver(fit);
    ro.observe(el);
    return function () { ro.disconnect(); };
  }, []);

  const isPro = d.tier === 'pro';
  return (
    <div className={'dcard' + (selected ? ' on' : '') + (lead ? ' dcard--lead' : '')} ref={boxRef}>
      <div className="dcard__stage" ref={stageRef}>
        {slug && near
          ? <iframe className="dcard__frame" src={designPreviewUrl(slug, d.key)} loading="lazy"
              tabIndex="-1" aria-hidden="true" title={'Предпросмотр оформления ' + d.name}
              style={{ transform: 'scale(' + scale + ')' }}></iframe>
          : <div className="dcard__ph">{d.name}</div>}
      </div>
      <div className="dcard__body">
        <div className="dcard__name">{d.name}</div>
        {d.vibe && <div className="dcard__vibe">{d.vibe}</div>}
        {d.fit && <div className="dcard__fit">{d.fit}</div>}
      </div>
      <button type="button" className="dcard__pick" aria-pressed={selected ? 'true' : 'false'}
        onClick={() => onSelect(d.key)} title={'Выбрать оформление ' + d.name}>
        <span className="sr-only">{'Выбрать оформление ' + d.name}</span>
      </button>
      <div className="dcard__tags">
        {isPro && <span className="dtag dtag--pro">Pro</span>}
        {lead && <span className="dtag dtag--on">Сейчас на сайте</span>}
        {selected && !lead && <span className="dtag dtag--on">Выбран</span>}
      </div>
      {slug && onZoom && (
        <button type="button" className="dcard__zoom" onClick={() => onZoom(d)}
          title={'Открыть ' + d.name + ' на весь экран'}>
          <i data-lucide="maximize-2"></i> Крупнее
        </button>
      )}
    </div>
  );
}

function DesignGallery({ designs, value, onSelect, slug, onZoom, applied, demoSlugs }) {
  if (!designs || !designs.length) return <div className="spin" style={{ margin: '1rem auto' }}></div>;
  // Действующее оформление идёт первым и во всю ширину: это ответ на вопрос
  // «что у меня сейчас», который человек задаёт раньше всех остальных.
  const lead = applied ? designs.filter(d => d.key === applied) : [];
  const rest = applied ? designs.filter(d => d.key !== applied) : designs;
  const list = lead.concat(rest);
  // На экране «Новый сайт» своего сайта ещё нет: показываем наши витрины-образцы,
  // каждой карточке — свою, чтобы оформления сравнивались на разных заведениях.
  const demos = (demoSlugs && demoSlugs.length) ? demoSlugs : null;
  return (
    <div className="dgrid">
      {list.map((d, i) => (
        <DesignCard key={d.key} d={d} selected={value === d.key} onSelect={onSelect}
          slug={slug || (demos ? demos[i % demos.length] : '')}
          onZoom={onZoom} lead={applied ? d.key === applied : false} />
      ))}
    </div>
  );
}

// Полноэкранный предпросмотр одного дизайна на данных клиента
function DesignPreview({ d, slug, onClose, onApply, applying }) {
  const [device, setDevice] = useStateD('desktop');
  useEffectD(() => {
    function onKey(e) { if (e.key === 'Escape') onClose(); }
    window.addEventListener('keydown', onKey);
    return function () { window.removeEventListener('keydown', onKey); };
  }, [onClose]);
  const url = designPreviewUrl(slug, d.key);
  // Портал в body: экран дизайна лежит внутри прокручиваемой области кабинета,
  // и position:fixed там ограничивается контейнером — предпросмотр не накрывал бы меню.
  return ReactDOM.createPortal((
    <div className="dpv" role="dialog" aria-modal="true" aria-label={'Предпросмотр оформления ' + d.name}>
      <div className="dpv__bar">
        <div className="dpv__title">
          <b>{d.name}</b>
          {d.vibe && <span className="muted" style={{ fontSize: '.82rem' }}>{d.vibe}</span>}
        </div>
        <div className="dpv__actions">
          <div className="seg">
            <button type="button" className={device === 'desktop' ? 'on' : ''} onClick={() => setDevice('desktop')}>
              <i data-lucide="monitor"></i> Компьютер
            </button>
            <button type="button" className={device === 'mobile' ? 'on' : ''} onClick={() => setDevice('mobile')}>
              <i data-lucide="smartphone"></i> Телефон
            </button>
          </div>
          <a className="btn btn--ghost btn--sm" href={url} target="_blank" rel="noopener">
            <i data-lucide="external-link"></i> В новой вкладке
          </a>
          {onApply && (
            <button type="button" className="btn btn--primary btn--sm" disabled={applying}
              onClick={() => onApply(d.key)}>{applying ? 'Применяем…' : 'Выбрать это оформление'}</button>
          )}
          <button type="button" className="iconbtn" onClick={onClose} aria-label="Закрыть предпросмотр">
            <i data-lucide="x"></i>
          </button>
        </div>
      </div>
      <div className="dpv__stage">
        <iframe className="dpv__frame" data-device={device} src={url}
          title={'Предпросмотр оформления ' + d.name}></iframe>
      </div>
    </div>
  ), document.body);
}

// ---- экран «Дизайн сайта» (смена оформления + живой предпросмотр) ----
function ScreenDesign({ nav, site, designs, onApply, onPay }) {
  const [design, setDesign] = useStateD((site && site.design) || 'A');
  const [busy, setBusy] = useStateD(false);
  const [zoom, setZoom] = useStateD(null);
  if (!site) return null;
  const chosen = (designs || []).find(d => d.key === design);
  const isPro = !!(chosen && chosen.tier === 'pro');
  const proActive = !!site.proActive;
  const changed = design !== (site.design || 'A');
  const liveUrl = designPreviewUrl(site.slug, design);
  async function apply(key) {
    setBusy(true);
    try { await onApply(site.id, key || design); setZoom(null); } finally { setBusy(false); }
  }
  return (
    <div className="wrap-lg">
      <a className="linklike" style={{ fontSize: '.84rem', display: 'inline-flex', alignItems: 'center', gap: '.3rem', marginBottom: '1.2rem' }} onClick={() => nav('sites')}><i data-lucide="arrow-left" style={{ width: 15, height: 15 }}></i> Мои сайты</a>
      <div className="card card--lead" style={{ padding: '1.6rem' }}>
        <span className="eyebrow">Оформление сайта</span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '1.35rem', letterSpacing: '-.03em', color: 'var(--ink)', margin: '.5rem 0 .4rem' }}>{site.name}</h2>
        <p className="muted" style={{ fontSize: '.88rem', lineHeight: 1.6 }}>Каждая карточка показывает ваш сайт в этом оформлении: ваши фото, услуги и отзывы. Премиум-оформления работают, пока активен Pro; без Pro сайт показывается в базовом.</p>
        <DesignGallery designs={designs} value={design} onSelect={setDesign}
          slug={site.slug} onZoom={setZoom} applied={site.design || 'A'} />
        {isPro && !proActive && (
          <div className="card" style={{ padding: '.9rem 1rem', marginTop: '1rem', display: 'flex', gap: '.7rem', background: 'var(--warning-wash)', borderColor: 'rgba(138,90,6,.28)' }}>
            <i data-lucide="info" style={{ width: 18, height: 18, color: 'var(--warning)', flex: 'none' }}></i>
            <span style={{ fontSize: '.84rem', color: 'var(--ink-2)', lineHeight: 1.6 }}>Это премиум-оформление. Выбор сохранится, но посетители увидят базовое, пока не активен Pro.</span>
          </div>
        )}
        <div className="dactions">
          <span className="dactions__pick">
            {changed ? <>Выбрано: <b>{chosen ? chosen.name : design}</b></> : <>Сейчас на сайте: <b>{chosen ? chosen.name : design}</b></>}
          </span>
          <button className="btn btn--primary" disabled={!changed || busy} onClick={() => apply()}>{busy ? 'Применяем…' : 'Применить'}</button>
          <a className="btn btn--ghost" href={liveUrl} target="_blank" rel="noopener"><i data-lucide="external-link"></i> Открыть в новой вкладке</a>
          {isPro && !proActive && onPay && <button className="btn btn--outline" onClick={() => onPay(site)}>Сделать PRO-сайтом</button>}
        </div>
      </div>
      {zoom && <DesignPreview d={zoom} slug={site.slug} onClose={() => setZoom(null)}
        onApply={apply} applying={busy} />}
    </div>
  );
}

// ---- экран «Добавить сайт» ----
function ScreenAddSite({ nav, onStartBuild, designs, demoSlugs }) {
  const [url, setUrl] = useStateD('');
  const [design, setDesign] = useStateD('A');
  const [zoom, setZoom] = useStateD(null);
  const valid = validYandex(url);
  const isProSel = (designs || []).some(d => d.key === design && d.tier === 'pro');
  const demos = demoSlugs || [];
  // slug для полноэкранного просмотра — тот же образец, что и в карточке
  const zoomSlug = zoom && demos.length
    ? demos[(designs || []).findIndex(d => d.key === zoom.key) % demos.length] : '';
  return (
    <div className="wrap-md">
      <a className="linklike" style={{ fontSize: '.84rem', display: 'inline-flex', alignItems: 'center', gap: '.3rem', marginBottom: '1.2rem' }} onClick={() => nav('sites')}><i data-lucide="arrow-left" style={{ width: 15, height: 15 }}></i> Мои сайты</a>
      <div className="card" style={{ padding: '1.6rem' }}>
        <span className="eyebrow">Новый сайт</span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '1.4rem', letterSpacing: '-.02em', color: 'var(--ink)', margin: '.5rem 0 .4rem' }}>Ссылка на Яндекс Карты</h2>
        <p className="muted" style={{ fontSize: '.88rem', lineHeight: 1.6 }}>Вставьте ссылку на карточку вашей организации — мы возьмём оттуда название, адрес, фото, часы работы и отзывы.</p>
        <div className="field" style={{ marginTop: '1.3rem' }}>
          <label className="field__label">Ссылка на карточку организации</label>
          <input className={'input' + (valid === true ? ' is-valid' : valid === false ? ' is-error' : '')} placeholder="https://yandex.ru/maps/org/… или /maps/-/…" value={url} onChange={e => setUrl(e.target.value)} />
          {valid === false && <span className="field__err">Похоже, это не ссылка на карточку организации в Яндекс Картах. Проверьте формат.</span>}
          {valid === true && <span className="field__hint" style={{ color: 'var(--success-soft)' }}><i data-lucide="check" style={{ width: 14, height: 14, display: 'inline-block', verticalAlign: '-2px' }}></i> Ссылка распознана</span>}
        </div>
        <div className="tip" style={{ marginTop: '1rem' }}>
          <i data-lucide="lightbulb"></i>
          <span>Где взять ссылку: откройте карточку компании в Яндекс Картах, нажмите кнопку <b>«Поделиться»</b> и скопируйте ссылку. Можно вставить скопированное целиком — вместе с названием и адресом.</span>
        </div>
        <div className="field" style={{ marginTop: '1.3rem' }}>
          <label className="field__label">Дизайн сайта</label>
          <DesignGallery designs={designs} value={design} onSelect={setDesign}
            demoSlugs={demos} onZoom={demos.length ? setZoom : null} />
          {demos.length > 0 && (
            <span className="field__hint" style={{ marginTop: '.5rem', display: 'block' }}>
              В карточках — наши готовые сайты в этом оформлении. Ваш соберётся из вашей карточки Яндекс Карт.
            </span>
          )}
          {isProSel && <span className="field__hint" style={{ marginTop: '.6rem', display: 'block' }}>Премиум-дизайн активен, пока действует Pro (в т.ч. пробный период). Без Pro сайт покажется в базовом дизайне — оформить Pro можно в любой момент из кабинета.</span>}
        </div>
        <button className="btn btn--primary btn--lg btn--block" style={{ marginTop: '1.3rem' }} disabled={valid !== true} onClick={() => onStartBuild(url, design)}>Создать сайт</button>
      </div>
      {zoom && zoomSlug && (
        <DesignPreview d={zoom} slug={zoomSlug} onClose={() => setZoom(null)}
          onApply={(key) => { setDesign(key); setZoom(null); }} applying={false} />
      )}
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
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '1.3rem', color: 'var(--ink)' }}>Не удалось собрать сайт</h2>
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
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '1.3rem', letterSpacing: '-.02em', color: 'var(--ink)', marginTop: '.8rem' }}>Собираем ваш сайт</h2>
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


// ============================================================
// billing.jsx — оплата, ЮKassa, подписки, поддержка, настройки
// ============================================================

// Что даёт Pro — держать синхронно с карточкой тарифа на лендинге.
const INCLUDED = [
  'Десять премиум-оформлений витрины',
  'Онлайн-запись: клиент сам выбирает время, заявка приходит в Telegram',
  'Чат на сайте — сообщения приходят вам в Telegram',
  'Редактирование содержимого: фото, тексты, часы, цены',
  'Снятие пометки «демонстрация» и индексация в поиске',
  'Больше сайтов на аккаунте: с одним Pro — до пяти',
];

// ---- Сводка оплаты (внутри кабинета) ----
// Тарифы Pro — синхронно с PLANS в app/cabinet.py
const PLANS_LK = [
  { id: 'month',   label: 'Месяц',    amount: 990,  perMonth: 990, period: '30 дней',  save: '' },
  { id: 'quarter', label: '3 месяца', amount: 2490, perMonth: 830, period: '90 дней',  save: 'выгода 480 ₽' },
  { id: 'year',    label: 'Год',      amount: 8900, perMonth: 742, period: '365 дней', save: 'выгода 2 980 ₽' },
];
const fmtRub = n => n.toLocaleString('ru-RU');

function ScreenPayment({ nav, site, onProceed }) {
  const s = site || {};
  const [busy, setBusy] = useStateB(false);
  const [err, setErr] = useStateB('');
  const [plan, setPlan] = useStateB('quarter');
  const sel = PLANS_LK.find(p => p.id === plan) || PLANS_LK[1];

  async function pay() {
    setErr(''); setBusy(true);
    try {
      const res = await window.API.createPayment(s.id, plan);
      if (res.confirmation_url) {
        window.location.href = res.confirmation_url;  // редирект на ЮKassa
      } else {
        setErr('Не удалось создать платёж');
        setBusy(false);
      }
    } catch (ex) {
      setErr(ex.message || 'Ошибка оплаты');
      setBusy(false);
    }
  }

  return (
    <div className="wrap-md">
      <a className="linklike" style={{ fontSize: '.84rem', display: 'inline-flex', alignItems: 'center', gap: '.3rem', marginBottom: '1.2rem' }} onClick={() => nav('sites')}><i data-lucide="arrow-left" style={{ width: 15, height: 15 }}></i> Мои сайты</a>
      <div className="card" style={{ padding: '1.6rem' }}>
        <span className="eyebrow">Оформление Pro</span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '1.4rem', letterSpacing: '-.02em', color: 'var(--ink)', margin: '.5rem 0 1.2rem' }}>{s.name || 'Ваш сайт'}</h2>

        <div className="row" style={{ padding: '.9rem 1rem', background: 'var(--paper-2)', borderRadius: 'var(--r-lg)' }}>
          <div className="sitecard__thumb" style={{ width: 42, height: 42, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--terracotta)', background: 'var(--terracotta-wash)' }}><i data-lucide={s.icon || 'store'} style={{ width: 20, height: 20 }}></i></div>
          <div>
            <div style={{ fontWeight: 600, color: 'var(--ink)', fontSize: '.92rem' }}>{(s.slug || 'site') + '.uqqi.ru'}</div>
            <div className="muted" style={{ fontSize: '.8rem' }}>{s.city || ''}</div>
          </div>
        </div>

        <p className="field__label" style={{ margin: '1.3rem 0 .7rem' }}>Выберите тариф</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '.55rem' }}>
          {PLANS_LK.map(p => (
            <div key={p.id} onClick={() => setPlan(p.id)}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '.8rem 1rem',
                border: '2px solid ' + (plan === p.id ? 'var(--terracotta)' : 'var(--line)'),
                borderRadius: 'var(--r-lg)', cursor: 'pointer',
                background: plan === p.id ? 'var(--terracotta-wash)' : 'transparent' }}>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--ink)', fontSize: '.95rem' }}>
                  {p.label}
                  {p.save && <span style={{ fontSize: '.72rem', color: 'var(--terracotta)', fontWeight: 600, marginLeft: '.5rem' }}>{p.save}</span>}
                </div>
                <div className="muted" style={{ fontSize: '.78rem', marginTop: '.1rem' }}>{fmtRub(p.perMonth)} ₽ / мес · {p.period}</div>
              </div>
              <div style={{ fontWeight: 600, color: 'var(--ink)', whiteSpace: 'nowrap' }}>{fmtRub(p.amount)} ₽</div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: '1.1rem' }}>
          <div className="sum-total"><span className="k" style={{ color: 'var(--ink)', fontWeight: 600 }}>Итого сегодня</span><span className="amt">{fmtRub(sel.amount)} ₽</span></div>
        </div>

        <hr className="divider" style={{ margin: '1.3rem 0' }} />
        <p className="field__label" style={{ marginBottom: '.7rem' }}>Что входит</p>
        <ul className="feat-list">
          {INCLUDED.map((f, i) => <li key={i}><i data-lucide="check"></i>{f}</li>)}
        </ul>

        {err && <div className="field__err" style={{ marginTop: '1rem' }}>{err}</div>}
        <button className="btn btn--primary btn--lg btn--block" style={{ marginTop: '1.5rem' }} onClick={pay} disabled={busy}><i data-lucide="lock"></i> {busy ? 'Создаём платёж…' : 'Перейти к оплате — ' + fmtRub(sel.amount) + ' ₽'}</button>
        <p className="legal" style={{ textAlign: 'center', marginTop: '.8rem' }}>Оплата проходит через ЮKassa. Мы не храним данные вашей карты.</p>
      </div>
    </div>
  );
}

// ---- ЮKassa (полноэкранный «редирект») ----
function ScreenYukassa({ nav }) {
  return (
    <div className="screen fade-enter">
      <div className="yk">
        <div className="yk__card">
          <div className="yk__head">
            <div className="yk__brand">Ю<span>Kassa</span></div>
            <span style={{ fontSize: '.78rem', opacity: .7 }}>uqqi.ru</span>
          </div>
          <div className="yk__body">
            <div className="between" style={{ marginBottom: '.2rem' }}>
              <span style={{ color: '#666', fontSize: '.86rem' }}>К оплате</span>
              <span style={{ fontWeight: 600, fontSize: '1.2rem', color: '#1d1d1b' }}>990,00 ₽</span>
            </div>
            <div>
              <div className="yk__lbl">Номер карты</div>
              <div className="yk__inp">0000 0000 0000 0000</div>
            </div>
            <div className="row" style={{ gap: '.7rem' }}>
              <div style={{ flex: 1 }}><div className="yk__lbl">ММ / ГГ</div><div className="yk__inp">00 / 00</div></div>
              <div style={{ flex: 1 }}><div className="yk__lbl">CVC</div><div className="yk__inp">•••</div></div>
            </div>
            <div className="yk__pay" onClick={() => nav('payment-processing')}>Оплатить 990 ₽</div>
            <p style={{ fontSize: '.7rem', color: '#aaa', textAlign: 'center', marginTop: '.2rem' }}>Демонстрационный экран. Реальное списание не производится.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---- Оплата обрабатывается → успех ----
// Поллим список сайтов: webhook ЮKassa переведёт сайт в active.
function ScreenPaymentProcessing({ onConfirmed }) {
  React.useEffect(() => {
    let tries = 0;
    const iv = setInterval(async () => {
      tries++;
      try {
        const data = await window.API.sites();
        const anyPaid = (data.sites || []).some(s => s.status === 'pro');
        if (anyPaid) { clearInterval(iv); onConfirmed(); return; }
      } catch (e) {}
      if (tries > 15) { clearInterval(iv); onConfirmed(); }
    }, 2000);
    return () => clearInterval(iv);
  }, []);
  return (
    <div className="screen fade-enter">
      <div className="notice">
        <div className="notice__box">
          <div className="spin"></div>
          <h2>Оплата обрабатывается</h2>
          <p>Ждём подтверждение от платёжной системы<span className="dots"><span>.</span><span>.</span><span>.</span></span><br />Это занимает несколько секунд.</p>
        </div>
      </div>
    </div>
  );
}

function ScreenPaymentSuccess({ nav, site }) {
  return (
    <div className="screen fade-enter">
      <div className="notice">
        <div className="notice__box">
          <div className="notice__ic ok"><i data-lucide="check"></i></div>
          <h2>Оплачено</h2>
          <p>Сайт <b>{(site && site.slug) || 'site'}.uqqi.ru</b> активен до <b>{(site && site.until) || '22.07.2026'}</b>. Спасибо!</p>
          <button className="btn btn--primary btn--lg" style={{ marginTop: '.4rem' }} onClick={() => nav('sites')}>Вернуться в кабинет</button>
        </div>
      </div>
    </div>
  );
}

// ---- Подписки и платежи ----
function ScreenSubscriptions({ nav, sites, payments, onPay }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.6rem' }}>
      <div>
        <p className="field__label" style={{ marginBottom: '.7rem' }}>Подписки по сайтам</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '.8rem' }}>
          {sites.map(s => (
            <div key={s.id} className="card" style={{ padding: '1rem 1.2rem' }}>
              <div className="between">
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--ink)', fontSize: '.95rem' }}>{s.name}</div>
                  <div className="muted" style={{ fontSize: '.8rem', marginTop: '.2rem' }}>{s.slug}.uqqi.ru</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <StatusBadge site={s} />
                  {s.status === 'claim' && <button className="btn btn--primary btn--sm" onClick={() => onPay(s)}>Забрать сайт</button>}
                  {s.status === 'free' && <button className="btn btn--primary btn--sm" onClick={() => onPay(s)}>Сделать PRO-сайтом</button>}
                  {(s.status === 'protrial' || s.status === 'pro') && <button className="btn btn--ghost btn--sm" onClick={() => onPay(s)}>Продлить Pro</button>}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <p className="field__label" style={{ marginBottom: '.7rem' }}>История платежей</p>
        <div className="card" style={{ padding: '.4rem .6rem' }}>
          <table className="ptable">
            <thead><tr><th>Дата</th><th>Сайт</th><th>Сумма</th><th>Статус</th></tr></thead>
            <tbody>
              {payments.map((p, i) => (
                <tr key={i}>
                  <td data-l="Дата">{p.date}</td>
                  <td data-l="Сайт">{p.site}</td>
                  <td data-l="Сумма" className="amt">{p.amount}</td>
                  <td data-l="Статус"><span className={'badge ' + (p.ok ? 'badge--active' : 'badge--unpaid')} style={{ fontSize: '.7rem' }}><span className="dot"></span>{p.ok ? 'Оплачен' : 'Отклонён'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ---- Поддержка ----
function ScreenSupport({ email, tickets, onSubmit }) {
  const [subj, setSubj] = useStateB('');
  const [msg, setMsg] = useStateB('');
  const ok = subj.trim() && msg.trim();
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.6rem' }}>
      <div className="card" style={{ padding: '1.4rem 1.5rem' }}>
        <p className="field__label" style={{ marginBottom: '1rem' }}>Новое обращение</p>
        <form style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }} onSubmit={e => { e.preventDefault(); if (!ok) return; onSubmit(subj, msg); setSubj(''); setMsg(''); }}>
          <div className="field">
            <label className="field__label">Тема</label>
            <input className="input" placeholder="Например: не загрузились фото" value={subj} onChange={e => setSubj(e.target.value)} />
          </div>
          <div className="field">
            <label className="field__label">Сообщение</label>
            <textarea className="input" placeholder="Опишите, что случилось…" value={msg} onChange={e => setMsg(e.target.value)}></textarea>
          </div>
          <div className="between">
            <span className="muted" style={{ fontSize: '.8rem' }}><i data-lucide="mail" style={{ width: 14, height: 14, verticalAlign: '-2px', marginRight: 4 }}></i> Ответим на {email || 'you@example.ru'}</span>
            <button className="btn btn--primary" type="submit" disabled={!ok}>Отправить</button>
          </div>
        </form>
      </div>
      <div>
        <p className="field__label" style={{ marginBottom: '.7rem' }}>История обращений</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '.8rem' }}>
          {tickets.map((t, i) => (
            <div key={i} className="card ticket">
              <div className="ticket__head">
                <span className="ticket__subj">{t.subj}</span>
                <span className={'badge ' + (t.status === 'open' ? 'badge--trial' : t.status === 'answered' ? 'badge--active' : 'badge--building')} style={{ fontSize: '.7rem' }}>
                  <span className="dot"></span>{t.status === 'open' ? 'В работе' : t.status === 'answered' ? 'Отвечено' : 'Закрыто'}
                </span>
              </div>
              <div className="ticket__body">{t.body}</div>
              <div className="ticket__date">{t.date}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---- Подключение Telegram (чат с сайтов, Pro) ----
function TelegramCard() {
  const [st, setSt] = React.useState(null);
  const [busy, setBusy] = React.useState(false);
  async function load() {
    try { setSt(await window.API.telegramStatus()); }
    catch (e) { setSt({ connected: false, link: '', botConfigured: false }); }
  }
  React.useEffect(() => { load(); }, []);
  async function disconnect() {
    setBusy(true);
    try { await window.API.telegramDisconnect(); await load(); }
    finally { setBusy(false); }
  }
  return (
    <div className="card" style={{ padding: '1.4rem 1.5rem' }}>
      <p className="field__label" style={{ marginBottom: '.6rem' }}>Чат на сайте → Telegram <span style={{ fontSize: '.68rem', fontWeight: 600, color: 'var(--terracotta-deep)', border: '1px solid var(--terracotta-deep)', borderRadius: 6, padding: '1px 6px', marginLeft: 6 }}>PRO</span></p>
      <p className="muted" style={{ fontSize: '.84rem', lineHeight: 1.6 }}>Сообщения посетителей с ваших Pro-сайтов приходят вам в Telegram. Отвечайте прямо из Telegram (кнопка «Ответить») — ответ появится в чате на сайте.</p>
      {!st && <p className="muted" style={{ marginTop: '.8rem', fontSize: '.84rem' }}>Загрузка…</p>}
      {st && st.connected && (
        <div className="between" style={{ marginTop: '.9rem', gap: '1rem' }}>
          <span className="field__hint" style={{ color: 'var(--success-soft)' }}><i data-lucide="check" style={{ width: 14, height: 14, display: 'inline-block', verticalAlign: '-2px' }}></i> Telegram подключён</span>
          <button className="btn btn--ghost btn--sm" onClick={disconnect} disabled={busy}>Отключить</button>
        </div>
      )}
      {st && !st.connected && st.botConfigured && (
        <div style={{ marginTop: '.9rem', display: 'flex', gap: '.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <a className="btn btn--primary btn--sm" href={st.link} target="_blank" rel="noopener">Подключить Telegram</a>
          <button className="btn btn--ghost btn--sm" onClick={load}>Я нажал «Старт» — проверить</button>
        </div>
      )}
      {st && !st.connected && !st.botConfigured && (
        <p className="field__err" style={{ marginTop: '.9rem' }}>Бот пока не настроен. Напишите в поддержку.</p>
      )}
    </div>
  );
}

// ---- Настройки аккаунта ----
function ScreenSettings({ email, onDelete }) {
  const [pw, setPw] = useStateB('');
  const [pw2, setPw2] = useStateB('');
  const [np, setNp] = useStateB('');
  const [msg, setMsg] = useStateB(null);
  const [busy, setBusy] = useStateB(false);

  async function savePassword() {
    setMsg(null);
    if (np.length < 6) { setMsg({ t: 'err', m: 'Новый пароль минимум 6 символов' }); return; }
    if (np !== pw2) { setMsg({ t: 'err', m: 'Пароли не совпадают' }); return; }
    setBusy(true);
    try {
      await window.API.changePassword(pw, np);
      setMsg({ t: 'ok', m: 'Пароль изменён' });
      setPw(''); setNp(''); setPw2('');
    } catch (ex) {
      setMsg({ t: 'err', m: ex.message || 'Ошибка смены пароля' });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="wrap-md" style={{ display: 'flex', flexDirection: 'column', gap: '1.6rem' }}>
      <div className="card" style={{ padding: '1.4rem 1.5rem' }}>
        <p className="field__label" style={{ marginBottom: '1rem' }}>Email аккаунта</p>
        <div className="between">
          <div className="row"><div className="usercard"><div className="av" style={{ width: 38, height: 38 }}>{(email || 'U')[0].toUpperCase()}</div></div><span style={{ color: 'var(--ink)', fontWeight: 500 }}>{email || 'you@example.ru'}</span></div>
        </div>
      </div>

      <div className="card" style={{ padding: '1.4rem 1.5rem' }}>
        <p className="field__label" style={{ marginBottom: '1rem' }}>Смена пароля</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="field"><label className="field__label">Текущий пароль</label><input className="input" type="password" placeholder="••••••••" value={pw} onChange={e => setPw(e.target.value)} /></div>
          <div className="field"><label className="field__label">Новый пароль</label><input className="input" type="password" placeholder="••••••••" value={np} onChange={e => setNp(e.target.value)} /></div>
          <div className="field"><label className="field__label">Повтор нового пароля</label><input className="input" type="password" placeholder="••••••••" value={pw2} onChange={e => setPw2(e.target.value)} /></div>
          {msg && <div className={msg.t === 'ok' ? 'field__hint' : 'field__err'} style={msg.t === 'ok' ? { color: 'var(--success-soft)' } : {}}>{msg.m}</div>}
          <div><button className="btn btn--primary" onClick={savePassword} disabled={busy}>{busy ? 'Сохраняем…' : 'Сохранить пароль'}</button></div>
        </div>
      </div>

      <TelegramCard />

      <div className="card" style={{ padding: '1.4rem 1.5rem', borderColor: 'color-mix(in srgb,var(--danger) 25%,var(--line))' }}>
        <p className="field__label" style={{ marginBottom: '.5rem', color: 'var(--danger)' }}>Опасная зона</p>
        <div className="between" style={{ gap: '1rem' }}>
          <p className="muted" style={{ fontSize: '.84rem', lineHeight: 1.6, maxWidth: 360 }}>Удаление аккаунта необратимо. Все сайты будут отключены, а данные удалены без возможности восстановления.</p>
          <button className="btn btn--danger" style={{ flex: 'none' }} onClick={onDelete}><i data-lucide="trash-2"></i> Удалить аккаунт</button>
        </div>
      </div>
    </div>
  );
}


// ============================================================
// app.jsx — оболочка, роутер, состояние, навигация
// ============================================================

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
      <div className="card card--lead" style={{ padding: '1.6rem' }}>
        <span className="eyebrow">Статистика</span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '1.3rem', color: 'var(--ink)', margin: '.4rem 0 1.1rem' }}>{m.title}</h2>

        <div className="statgrid">
          {[['7 дней', 'd7'], ['30 дней', 'd30'], ['90 дней', 'd90']].map(([lbl, k]) => (
            <div key={k} className="stat">
              <div className="stat__n">{m.unique[k]}</div>
              <div className="stat__k">уник. / {lbl}</div>
            </div>
          ))}
        </div>
        <p className="muted" style={{ fontSize: '.82rem', marginTop: '.8rem' }}>Просмотров за 30 дней: <b style={{ color: 'var(--ink)' }}>{m.views.d30}</b></p>

        <p className="field__label" style={{ margin: '1.3rem 0 .5rem' }}>Посетители по дням (30 дней)</p>
        <div className="chart">
          {m.daily.map((d, i) => (
            <i key={i} title={d.day + ': ' + d.unique}
               style={{ opacity: d.unique ? .85 : .15, height: Math.max(3, d.unique / maxD * 80) + 'px' }}></i>
          ))}
        </div>

        <div className="subline">
          {sub.status === 'pro' && <span>Pro активен до <b style={{ color: 'var(--ink)' }}>{sub.until}</b></span>}
          {sub.status === 'protrial' && <span>Pro-триал — осталось <b style={{ color: 'var(--ink)' }}>{sub.proDays} дн.</b></span>}
          {sub.status === 'free' && <span>Бесплатный сайт · <b style={{ color: 'var(--ink)' }}>Pro</b> откроет премиум-дизайн и чат</span>}
          {sub.status === 'claim' && <span style={{ color: 'var(--danger)' }}>Демо-сайт — оплатите, чтобы забрать</span>}
        </div>
      </div>
    </div>
  );
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
  const [demoSlugs, setDemoSlugs] = useState([]);
  const [trialEnded, setTrialEnded] = useState(null);
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
      ensureDemoSites();
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

  // Почту берём на любом экране за логином, если её ещё нет: после
  // подтверждения email (/verify) и сброса пароля загрузка идёт мимо API.me(),
  // и до перезагрузки страницы в шапке висел запасной адрес.
  useEffect(() => {
    const authed = ['sites', 'add-site', 'building', 'design', 'metrics',
                    'subscriptions', 'settings', 'support', 'payment-processing'];
    if (!booted || email || !authed.includes(screen)) return;
    window.API.me().then(u => { if (u && u.email) setEmail(u.email); }).catch(() => {});
  }, [booted, email, screen]);

  // Первый сайт, у которого догорел пробный Pro и о котором ещё не напоминали
  // в этой сессии. sessionStorage: «при входе в ЛК» — один раз, а не на каждом
  // переключении экрана; в новой вкладке напомним снова.
  function pickTrialEnded(list) {
    try {
      const seen = JSON.parse(sessionStorage.getItem('uqqiTrialSeen') || '[]');
      const hit = (list || []).find(s => s.trialEnded && seen.indexOf(s.id) === -1);
      if (!hit) return null;
      sessionStorage.setItem('uqqiTrialSeen', JSON.stringify(seen.concat([hit.id])));
      return hit;
    } catch (e) { return null; }   // приватный режим — просто не показываем
  }

  async function loadSites() {
    try {
      const data = await window.API.sites();
      setSites(data.sites || []);
      setCanAdd(data.canAdd !== false);
      setCanAddReason(data.canAddReason || '');
      const hit = pickTrialEnded(data.sites);
      if (hit) setTrialEnded(hit);
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
  // Витрины-образцы для предпросмотра на экране «Новый сайт». Нет их — карточка
  // просто покажет название оформления, как было раньше.
  async function ensureDemoSites() {
    if (demoSlugs.length) return;
    try { const d = await window.API.demoSites(); setDemoSlugs(d.slugs || []); } catch (e) {}
  }
  function openDesign(site) {
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
  if (screen === 'sites') body = <ScreenSites nav={nav} sites={sites} onPay={openPay} onDesign={openDesign} onDelete={askDeleteSite} onStats={openMetrics} canAdd={canAdd} />;
  else if (screen === 'add-site') body = <ScreenAddSite nav={nav} onStartBuild={startBuild} designs={designs} demoSlugs={demoSlugs} />;
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
        <TrialEndedModal site={trialEnded}
          onPay={(s) => { setTrialEnded(null); openPay(s); }}
          onClose={() => setTrialEnded(null)} />

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

