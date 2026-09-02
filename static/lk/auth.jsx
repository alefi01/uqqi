// ============================================================
// auth.jsx — регистрация / вход / восстановление / подтверждение
// ============================================================
const { useState } = React;

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
                <input className="input" type="email" placeholder="you@example.ru" value={email} onChange={e => setEmail(e.target.value)} required />
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
            <p className="auth__sub">Бесплатно. Первый сайт — 7 дней пробного периода.</p>
            <form className="auth__form" onSubmit={submit}>
              <div className="field">
                <label className="field__label">Email</label>
                <input className="input" type="email" placeholder="you@example.ru" value={email} onChange={e => setEmail(e.target.value)} required />
              </div>
              <PasswordField label="Пароль" value={pw} onChange={e => setPw(e.target.value)} />
              <div className="field">
                <label className="field__label">Повтор пароля</label>
                <input className={'input' + (mismatch ? ' is-error' : (pw2 && !mismatch ? ' is-valid' : ''))} type="password" placeholder="••••••••" value={pw2} onChange={e => setPw2(e.target.value)} />
                {mismatch && <span className="field__err">Пароли не совпадают</span>}
              </div>
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
                🎁 После подтверждения ваш готовый сайт появится в кабинете — первые 7 дней бесплатно.
              </p>
            )}
            <div className="row" style={{ gap: '.7rem', marginTop: '.4rem' }}>
              <button className="btn btn--ghost btn--sm" onClick={() => nav('login')}>Я подтвердил — войти</button>
            </div>
            <p className="legal" style={{ marginTop: '.4rem' }}>
              Не пришло письмо? Проверьте папку «Спам» или {sent
                ? <span style={{ color: 'var(--success-soft)' }}>письмо отправлено повторно ✓</span>
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
              <h2>Готово! Сайт ваш 🎉</h2>
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
                <input className="input" type="email" placeholder="you@example.ru" value={email} onChange={e => setEmail(e.target.value)} required />
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
              <div className="field">
                <label className="field__label">Повтор пароля</label>
                <input className={'input' + (mismatch ? ' is-error' : (pw2 && !mismatch ? ' is-valid' : ''))} type="password" placeholder="••••••••" value={pw2} onChange={e => setPw2(e.target.value)} />
                {mismatch && <span className="field__err">Пароли не совпадают</span>}
              </div>
              {err && <div className="field__err">{err}</div>}
              <button className="btn btn--primary btn--block btn--lg" type="submit" disabled={!ok || busy}>{busy ? 'Сохраняем…' : 'Сохранить пароль'}</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, {
  ScreenLogin, ScreenRegister, ScreenRegisterSent, ScreenConfirmEmail,
  ScreenForgot, ScreenForgotSent, ScreenReset,
});
