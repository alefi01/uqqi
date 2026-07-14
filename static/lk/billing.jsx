// ============================================================
// billing.jsx — оплата, ЮKassa, подписки, поддержка, настройки
// ============================================================
const { useState: useStateB } = React;

const INCLUDED = [
  'Сайт на адресе название.uqqi.ru',
  'Данные из Яндекс Карт: фото, отзывы, часы',
  'Редактирование контента без программиста',
  'Онлайн-запись и приём заявок',
  'Поддержка и обновления',
];

// ---- Сводка оплаты (внутри кабинета) ----
function ScreenPayment({ nav, site, onProceed }) {
  const s = site || {};
  const [busy, setBusy] = useStateB(false);
  const [err, setErr] = useStateB('');

  async function pay() {
    setErr(''); setBusy(true);
    try {
      const res = await window.API.createPayment(s.id);
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
        <span className="eyebrow">Оплата подписки</span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.4rem', letterSpacing: '-.02em', color: 'var(--ink)', margin: '.5rem 0 1.2rem' }}>{s.name || 'Ваш сайт'}</h2>

        <div className="row" style={{ padding: '.9rem 1rem', background: 'var(--paper-2)', borderRadius: 'var(--r-lg)' }}>
          <div className="sitecard__thumb" style={{ width: 42, height: 42, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--terracotta)', background: 'var(--terracotta-wash)' }}><i data-lucide={s.icon || 'store'} style={{ width: 20, height: 20 }}></i></div>
          <div>
            <div style={{ fontWeight: 600, color: 'var(--ink)', fontSize: '.92rem' }}>{(s.slug || 'site') + '.uqqi.ru'}</div>
            <div className="muted" style={{ fontSize: '.8rem' }}>{s.city || ''}</div>
          </div>
        </div>

        <div style={{ marginTop: '1.2rem' }}>
          <div className="sumrow"><span className="k">Тариф</span><span className="v">Стандарт — 990 ₽ / месяц</span></div>
          <div className="sumrow"><span className="k">Период</span><span className="v">30 дней</span></div>
          <div className="sum-total"><span className="k" style={{ color: 'var(--ink)', fontWeight: 600 }}>Итого сегодня</span><span className="amt">990 ₽</span></div>
        </div>

        <hr className="divider" style={{ margin: '1.3rem 0' }} />
        <p className="field__label" style={{ marginBottom: '.7rem' }}>Что входит</p>
        <ul className="feat-list">
          {INCLUDED.map((f, i) => <li key={i}><i data-lucide="check"></i>{f}</li>)}
        </ul>

        {err && <div className="field__err" style={{ marginTop: '1rem' }}>{err}</div>}
        <button className="btn btn--primary btn--lg btn--block" style={{ marginTop: '1.5rem' }} onClick={pay} disabled={busy}><i data-lucide="lock"></i> {busy ? 'Создаём платёж…' : 'Перейти к оплате'}</button>
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
              <span style={{ fontWeight: 800, fontSize: '1.2rem', color: '#1d1d1b' }}>990,00 ₽</span>
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
        const anyActive = (data.sites || []).some(s => s.status === 'active');
        if (anyActive) { clearInterval(iv); onConfirmed(); return; }
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
                  {(s.status === 'trial' || s.status === 'unpaid') && <button className="btn btn--primary btn--sm" onClick={() => onPay(s)}>Оплатить</button>}
                  {s.status === 'active' && <button className="btn btn--ghost btn--sm" onClick={() => onPay(s)}>Продлить</button>}
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
            <thead><tr><th>Дата</th><th>Сайт</th><th>Сумма</th><th>Статус</th><th></th></tr></thead>
            <tbody>
              {payments.map((p, i) => (
                <tr key={i}>
                  <td data-l="Дата">{p.date}</td>
                  <td data-l="Сайт">{p.site}</td>
                  <td data-l="Сумма" className="amt">{p.amount}</td>
                  <td data-l="Статус"><span className={'badge ' + (p.ok ? 'badge--active' : 'badge--unpaid')} style={{ fontSize: '.7rem' }}><span className="dot"></span>{p.ok ? 'Оплачен' : 'Отклонён'}</span></td>
                  <td data-l="Чек">{p.ok ? <a className="linklike" style={{ fontSize: '.8rem', display: 'inline-flex', alignItems: 'center', gap: '.25rem' }} href="#" onClick={e => e.preventDefault()}>чек <i data-lucide="arrow-up-right" style={{ width: 12, height: 12 }}></i></a> : <span className="muted">—</span>}</td>
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
          <div><button className="btn btn--dark" onClick={savePassword} disabled={busy}>{busy ? 'Сохраняем…' : 'Сохранить пароль'}</button></div>
        </div>
      </div>

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

Object.assign(window, {
  ScreenPayment, ScreenYukassa, ScreenPaymentProcessing, ScreenPaymentSuccess,
  ScreenSubscriptions, ScreenSupport, ScreenSettings,
});
