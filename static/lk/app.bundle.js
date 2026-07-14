import { jsxDEV as _jsxDEV, Fragment as _Fragment } from "react/jsx-dev-runtime";
// ============================================================
// app.bundle.js — собранный кабинет (auth + dashboard + billing + app)
// Все компоненты в одной области видимости (без window-экспортов).
// ============================================================
const {
  useState,
  useEffect,
  useRef
} = React;
const {
  useState: useStateD,
  useEffect: useEffectD,
  useRef: useRefD
} = React;
const {
  useState: useStateB
} = React;

// ============================================================
// auth.jsx — регистрация / вход / восстановление / подтверждение
// ============================================================

function AuthAside() {
  return /*#__PURE__*/_jsxDEV("div", {
    className: "auth__aside",
    children: [/*#__PURE__*/_jsxDEV("a", {
      className: "logo",
      href: "#",
      children: [/*#__PURE__*/_jsxDEV("img", {
        src: "/static/lk/assets/seal-192.png",
        alt: ""
      }, void 0, false), "uqqi", /*#__PURE__*/_jsxDEV("span", {
        className: "dot",
        children: ".ru"
      }, void 0, false)]
    }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
      className: "auth__pitch",
      children: [/*#__PURE__*/_jsxDEV("h2", {
        children: ["Сайт вашего бизнеса ", /*#__PURE__*/_jsxDEV("em", {
          children: "уже почти готов."
        }, void 0, false)]
      }, void 0, true), /*#__PURE__*/_jsxDEV("p", {
        children: "Войдите в кабинет — и через минуту у вашей кофейни, кафе или магазина появится аккуратный сайт на собственном адресе."
      }, void 0, false), /*#__PURE__*/_jsxDEV("ul", {
        className: "auth__bullets",
        children: [/*#__PURE__*/_jsxDEV("li", {
          children: [/*#__PURE__*/_jsxDEV("i", {
            "data-lucide": "zap"
          }, void 0, false), "Собираем сайт из карточки Яндекс Карт"]
        }, void 0, true), /*#__PURE__*/_jsxDEV("li", {
          children: [/*#__PURE__*/_jsxDEV("i", {
            "data-lucide": "pencil"
          }, void 0, false), "Контент меняете сами, без программиста"]
        }, void 0, true), /*#__PURE__*/_jsxDEV("li", {
          children: [/*#__PURE__*/_jsxDEV("i", {
            "data-lucide": "globe"
          }, void 0, false), "Свой адрес вида название.uqqi.ru"]
        }, void 0, true)]
      }, void 0, true)]
    }, void 0, true), /*#__PURE__*/_jsxDEV("p", {
      className: "legal",
      children: "Нажимая «Войти», вы соглашаетесь с условиями использования сервиса."
    }, void 0, false)]
  }, void 0, true);
}
function PasswordField({
  label = 'Пароль',
  name,
  placeholder = '••••••••',
  value,
  onChange
}) {
  const [show, setShow] = useState(false);
  return /*#__PURE__*/_jsxDEV("div", {
    className: "field",
    children: [/*#__PURE__*/_jsxDEV("label", {
      className: "field__label",
      children: label
    }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
      style: {
        position: 'relative'
      },
      children: [/*#__PURE__*/_jsxDEV("input", {
        className: "input",
        type: show ? 'text' : 'password',
        placeholder: placeholder,
        style: {
          paddingRight: '2.6rem'
        },
        value: value,
        onChange: onChange
      }, void 0, false), /*#__PURE__*/_jsxDEV("button", {
        type: "button",
        onClick: () => setShow(s => !s),
        style: {
          position: 'absolute',
          right: '.6rem',
          top: '50%',
          transform: 'translateY(-50%)',
          color: 'var(--ink-muted)',
          display: 'flex'
        },
        children: /*#__PURE__*/_jsxDEV("i", {
          "data-lucide": show ? 'eye-off' : 'eye',
          style: {
            width: 17,
            height: 17
          }
        }, void 0, false)
      }, void 0, false)]
    }, void 0, true)]
  }, void 0, true);
}

// ---------- Вход ----------
function ScreenLogin({
  nav,
  ctx
}) {
  const [email, setEmail] = useState(ctx.email || '');
  const [pw, setPw] = useState('');
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault();
    setErr('');
    setBusy(true);
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
  return /*#__PURE__*/_jsxDEV("div", {
    className: "screen fade-enter",
    children: /*#__PURE__*/_jsxDEV("div", {
      className: "auth",
      children: [/*#__PURE__*/_jsxDEV(AuthAside, {}, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        className: "auth__main",
        children: /*#__PURE__*/_jsxDEV("div", {
          className: "auth__box",
          children: [/*#__PURE__*/_jsxDEV("h1", {
            className: "auth__h",
            children: "С возвращением"
          }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
            className: "auth__sub",
            children: "Войдите, чтобы управлять своими сайтами."
          }, void 0, false), /*#__PURE__*/_jsxDEV("form", {
            className: "auth__form",
            onSubmit: submit,
            children: [/*#__PURE__*/_jsxDEV("div", {
              className: "field",
              children: [/*#__PURE__*/_jsxDEV("label", {
                className: "field__label",
                children: "Email"
              }, void 0, false), /*#__PURE__*/_jsxDEV("input", {
                className: "input",
                type: "email",
                placeholder: "you@example.ru",
                value: email,
                onChange: e => setEmail(e.target.value),
                required: true
              }, void 0, false)]
            }, void 0, true), /*#__PURE__*/_jsxDEV(PasswordField, {
              value: pw,
              onChange: e => setPw(e.target.value)
            }, void 0, false), err && /*#__PURE__*/_jsxDEV("div", {
              className: "field__err",
              style: {
                marginTop: '-.3rem'
              },
              children: err
            }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
              className: "between",
              style: {
                marginTop: '-.3rem'
              },
              children: [/*#__PURE__*/_jsxDEV("label", {
                className: "check",
                children: [/*#__PURE__*/_jsxDEV("input", {
                  type: "checkbox",
                  defaultChecked: true
                }, void 0, false), " Запомнить меня"]
              }, void 0, true), /*#__PURE__*/_jsxDEV("a", {
                className: "linklike",
                style: {
                  fontSize: '.82rem'
                },
                onClick: () => nav('forgot'),
                children: "Забыли пароль?"
              }, void 0, false)]
            }, void 0, true), /*#__PURE__*/_jsxDEV("button", {
              className: "btn btn--primary btn--block btn--lg",
              type: "submit",
              disabled: busy,
              children: busy ? 'Входим…' : 'Войти'
            }, void 0, false)]
          }, void 0, true), /*#__PURE__*/_jsxDEV("p", {
            className: "auth__alt",
            children: ["Нет аккаунта? ", /*#__PURE__*/_jsxDEV("a", {
              className: "linklike",
              onClick: () => nav('register'),
              children: "Создать аккаунт"
            }, void 0, false)]
          }, void 0, true)]
        }, void 0, true)
      }, void 0, false)]
    }, void 0, true)
  }, void 0, false);
}

// ---------- Регистрация ----------
function ScreenRegister({
  nav,
  ctx
}) {
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
    setErr('');
    setBusy(true);
    try {
      await window.API.register(email, pw, agree);
      ctx.setEmail(email);
      nav('register-sent');
    } catch (ex) {
      setErr(ex.message || 'Не удалось зарегистрироваться');
    } finally {
      setBusy(false);
    }
  }
  return /*#__PURE__*/_jsxDEV("div", {
    className: "screen fade-enter",
    children: /*#__PURE__*/_jsxDEV("div", {
      className: "auth",
      children: [/*#__PURE__*/_jsxDEV(AuthAside, {}, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        className: "auth__main",
        children: /*#__PURE__*/_jsxDEV("div", {
          className: "auth__box",
          children: [/*#__PURE__*/_jsxDEV("h1", {
            className: "auth__h",
            children: "Создать аккаунт"
          }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
            className: "auth__sub",
            children: "Бесплатно. Первый сайт — 7 дней пробного периода."
          }, void 0, false), /*#__PURE__*/_jsxDEV("form", {
            className: "auth__form",
            onSubmit: submit,
            children: [/*#__PURE__*/_jsxDEV("div", {
              className: "field",
              children: [/*#__PURE__*/_jsxDEV("label", {
                className: "field__label",
                children: "Email"
              }, void 0, false), /*#__PURE__*/_jsxDEV("input", {
                className: "input",
                type: "email",
                placeholder: "you@example.ru",
                value: email,
                onChange: e => setEmail(e.target.value),
                required: true
              }, void 0, false)]
            }, void 0, true), /*#__PURE__*/_jsxDEV(PasswordField, {
              label: "Пароль",
              value: pw,
              onChange: e => setPw(e.target.value)
            }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
              className: "field",
              children: [/*#__PURE__*/_jsxDEV("label", {
                className: "field__label",
                children: "Повтор пароля"
              }, void 0, false), /*#__PURE__*/_jsxDEV("input", {
                className: 'input' + (mismatch ? ' is-error' : pw2 && !mismatch ? ' is-valid' : ''),
                type: "password",
                placeholder: "••••••••",
                value: pw2,
                onChange: e => setPw2(e.target.value)
              }, void 0, false), mismatch && /*#__PURE__*/_jsxDEV("span", {
                className: "field__err",
                children: "Пароли не совпадают"
              }, void 0, false)]
            }, void 0, true), /*#__PURE__*/_jsxDEV("label", {
              className: "check",
              children: [/*#__PURE__*/_jsxDEV("input", {
                type: "checkbox",
                checked: agree,
                onChange: e => setAgree(e.target.checked)
              }, void 0, false), /*#__PURE__*/_jsxDEV("span", {
                children: ["Я принимаю ", /*#__PURE__*/_jsxDEV("a", {
                  className: "linklike",
                  href: "/oferta",
                  target: "_blank",
                  children: "оферту"
                }, void 0, false), " и ", /*#__PURE__*/_jsxDEV("a", {
                  className: "linklike",
                  href: "/privacy",
                  target: "_blank",
                  children: "политику конфиденциальности"
                }, void 0, false), "."]
              }, void 0, true)]
            }, void 0, true), err && /*#__PURE__*/_jsxDEV("div", {
              className: "field__err",
              children: err
            }, void 0, false), /*#__PURE__*/_jsxDEV("button", {
              className: "btn btn--primary btn--block btn--lg",
              type: "submit",
              disabled: !ok || busy,
              children: busy ? 'Создаём…' : 'Зарегистрироваться'
            }, void 0, false)]
          }, void 0, true), /*#__PURE__*/_jsxDEV("p", {
            className: "auth__alt",
            children: ["Уже есть аккаунт? ", /*#__PURE__*/_jsxDEV("a", {
              className: "linklike",
              onClick: () => nav('login'),
              children: "Войти"
            }, void 0, false)]
          }, void 0, true)]
        }, void 0, true)
      }, void 0, false)]
    }, void 0, true)
  }, void 0, false);
}

// ---------- Подтвердите email ----------
function ScreenRegisterSent({
  nav,
  ctx
}) {
  const [sent, setSent] = useState(false);
  async function resend(e) {
    e.preventDefault();
    try {
      await window.API.resendVerify(ctx.email);
      setSent(true);
    } catch (ex) {}
  }
  return /*#__PURE__*/_jsxDEV("div", {
    className: "screen fade-enter",
    children: /*#__PURE__*/_jsxDEV("div", {
      className: "auth",
      children: [/*#__PURE__*/_jsxDEV(AuthAside, {}, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        className: "notice",
        children: /*#__PURE__*/_jsxDEV("div", {
          className: "notice__box",
          children: [/*#__PURE__*/_jsxDEV("div", {
            className: "notice__ic",
            children: /*#__PURE__*/_jsxDEV("i", {
              "data-lucide": "mail-check"
            }, void 0, false)
          }, void 0, false), /*#__PURE__*/_jsxDEV("h2", {
            children: "Подтвердите email"
          }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
            children: ["Мы отправили письмо на ", /*#__PURE__*/_jsxDEV("b", {
              children: ctx.email || 'you@example.ru'
            }, void 0, false), ". Перейдите по ссылке из письма, чтобы активировать аккаунт."]
          }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
            className: "row",
            style: {
              gap: '.7rem',
              marginTop: '.4rem'
            },
            children: /*#__PURE__*/_jsxDEV("button", {
              className: "btn btn--ghost btn--sm",
              onClick: () => nav('login'),
              children: "Я подтвердил — войти"
            }, void 0, false)
          }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
            className: "legal",
            style: {
              marginTop: '.4rem'
            },
            children: ["Не пришло письмо? Проверьте папку «Спам» или ", sent ? /*#__PURE__*/_jsxDEV("span", {
              style: {
                color: 'var(--success-soft)'
              },
              children: "письмо отправлено повторно ✓"
            }, void 0, false) : /*#__PURE__*/_jsxDEV("a", {
              className: "linklike",
              href: "#",
              onClick: resend,
              children: "отправьте ещё раз"
            }, void 0, false), "."]
          }, void 0, true)]
        }, void 0, true)
      }, void 0, false)]
    }, void 0, true)
  }, void 0, false);
}

// ---------- Email подтверждён (verify по токену из URL) ----------
function ScreenConfirmEmail({
  nav,
  ctx
}) {
  const [err, setErr] = useState('');
  React.useEffect(() => {
    const token = new URLSearchParams(window.location.search).get('token');
    if (!token) {
      setErr('Ссылка недействительна');
      return;
    }
    fetch('/lk/api/verify?token=' + encodeURIComponent(token), {
      credentials: 'same-origin'
    }).then(r => {
      if (!r.ok) throw new Error();
      return r.json();
    }).then(() => {
      setTimeout(() => {
        window.history.replaceState({}, '', '/');
        nav('sites');
      }, 1500);
    }).catch(() => setErr('Ссылка недействительна или устарела'));
  }, []);
  return /*#__PURE__*/_jsxDEV("div", {
    className: "screen fade-enter",
    children: /*#__PURE__*/_jsxDEV("div", {
      className: "notice",
      children: /*#__PURE__*/_jsxDEV("div", {
        className: "notice__box",
        children: err ? /*#__PURE__*/_jsxDEV(_Fragment, {
          children: [/*#__PURE__*/_jsxDEV("div", {
            className: "notice__ic",
            style: {
              background: 'var(--danger-wash, #fde8e8)',
              color: 'var(--danger)'
            },
            children: /*#__PURE__*/_jsxDEV("i", {
              "data-lucide": "alert-triangle"
            }, void 0, false)
          }, void 0, false), /*#__PURE__*/_jsxDEV("h2", {
            children: "Не удалось подтвердить"
          }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
            children: err
          }, void 0, false), /*#__PURE__*/_jsxDEV("button", {
            className: "btn btn--primary btn--sm",
            style: {
              marginTop: '.4rem'
            },
            onClick: () => nav('login'),
            children: "Ко входу"
          }, void 0, false)]
        }, void 0, true) : /*#__PURE__*/_jsxDEV(_Fragment, {
          children: [/*#__PURE__*/_jsxDEV("div", {
            className: "notice__ic ok",
            children: /*#__PURE__*/_jsxDEV("i", {
              "data-lucide": "check"
            }, void 0, false)
          }, void 0, false), /*#__PURE__*/_jsxDEV("h2", {
            children: "Email подтверждён"
          }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
            children: ["Входим в кабинет", /*#__PURE__*/_jsxDEV("span", {
              className: "dots",
              children: [/*#__PURE__*/_jsxDEV("span", {
                children: "."
              }, void 0, false), /*#__PURE__*/_jsxDEV("span", {
                children: "."
              }, void 0, false), /*#__PURE__*/_jsxDEV("span", {
                children: "."
              }, void 0, false)]
            }, void 0, true)]
          }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
            className: "spin",
            style: {
              marginTop: '.4rem'
            }
          }, void 0, false)]
        }, void 0, true)
      }, void 0, false)
    }, void 0, false)
  }, void 0, false);
}

// ---------- Забыли пароль ----------
function ScreenForgot({
  nav,
  ctx
}) {
  const [email, setEmail] = useState(ctx.email || '');
  const [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await window.API.forgot(email);
      ctx.setEmail(email);
      nav('forgot-sent');
    } catch (ex) {
      ctx.setEmail(email);
      nav('forgot-sent');
    } // не раскрываем существование email
    finally {
      setBusy(false);
    }
  }
  return /*#__PURE__*/_jsxDEV("div", {
    className: "screen fade-enter",
    children: /*#__PURE__*/_jsxDEV("div", {
      className: "auth",
      children: [/*#__PURE__*/_jsxDEV(AuthAside, {}, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        className: "auth__main",
        children: /*#__PURE__*/_jsxDEV("div", {
          className: "auth__box",
          children: [/*#__PURE__*/_jsxDEV("a", {
            className: "linklike",
            style: {
              fontSize: '.82rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '.3rem',
              marginBottom: '1.2rem'
            },
            onClick: () => nav('login'),
            children: [/*#__PURE__*/_jsxDEV("i", {
              "data-lucide": "arrow-left",
              style: {
                width: 15,
                height: 15
              }
            }, void 0, false), " Назад ко входу"]
          }, void 0, true), /*#__PURE__*/_jsxDEV("h1", {
            className: "auth__h",
            children: "Восстановление пароля"
          }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
            className: "auth__sub",
            children: "Укажите email — пришлём ссылку для сброса пароля."
          }, void 0, false), /*#__PURE__*/_jsxDEV("form", {
            className: "auth__form",
            onSubmit: submit,
            children: [/*#__PURE__*/_jsxDEV("div", {
              className: "field",
              children: [/*#__PURE__*/_jsxDEV("label", {
                className: "field__label",
                children: "Email"
              }, void 0, false), /*#__PURE__*/_jsxDEV("input", {
                className: "input",
                type: "email",
                placeholder: "you@example.ru",
                value: email,
                onChange: e => setEmail(e.target.value),
                required: true
              }, void 0, false)]
            }, void 0, true), /*#__PURE__*/_jsxDEV("button", {
              className: "btn btn--primary btn--block btn--lg",
              type: "submit",
              disabled: busy,
              children: busy ? 'Отправляем…' : 'Отправить ссылку для сброса'
            }, void 0, false)]
          }, void 0, true)]
        }, void 0, true)
      }, void 0, false)]
    }, void 0, true)
  }, void 0, false);
}
function ScreenForgotSent({
  nav,
  ctx
}) {
  return /*#__PURE__*/_jsxDEV("div", {
    className: "screen fade-enter",
    children: /*#__PURE__*/_jsxDEV("div", {
      className: "auth",
      children: [/*#__PURE__*/_jsxDEV(AuthAside, {}, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        className: "notice",
        children: /*#__PURE__*/_jsxDEV("div", {
          className: "notice__box",
          children: [/*#__PURE__*/_jsxDEV("div", {
            className: "notice__ic",
            children: /*#__PURE__*/_jsxDEV("i", {
              "data-lucide": "send"
            }, void 0, false)
          }, void 0, false), /*#__PURE__*/_jsxDEV("h2", {
            children: "Письмо отправлено"
          }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
            children: ["Если аккаунт с адресом ", /*#__PURE__*/_jsxDEV("b", {
              children: ctx.email || 'you@example.ru'
            }, void 0, false), " существует, ссылка для сброса пароля придёт на почту. Откройте её, чтобы задать новый пароль."]
          }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
            className: "row",
            style: {
              gap: '.7rem',
              marginTop: '.4rem'
            },
            children: /*#__PURE__*/_jsxDEV("button", {
              className: "btn btn--ghost btn--sm",
              onClick: () => nav('login'),
              children: "Ко входу"
            }, void 0, false)
          }, void 0, false)]
        }, void 0, true)
      }, void 0, false)]
    }, void 0, true)
  }, void 0, false);
}

// ---------- Новый пароль (reset по токену из URL) ----------
function ScreenReset({
  nav,
  ctx
}) {
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
    if (!token) {
      setErr('Ссылка недействительна');
      return;
    }
    setErr('');
    setBusy(true);
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
  return /*#__PURE__*/_jsxDEV("div", {
    className: "screen fade-enter",
    children: /*#__PURE__*/_jsxDEV("div", {
      className: "auth",
      children: [/*#__PURE__*/_jsxDEV(AuthAside, {}, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        className: "auth__main",
        children: /*#__PURE__*/_jsxDEV("div", {
          className: "auth__box",
          children: [/*#__PURE__*/_jsxDEV("h1", {
            className: "auth__h",
            children: "Новый пароль"
          }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
            className: "auth__sub",
            children: "Придумайте новый пароль для входа в кабинет."
          }, void 0, false), /*#__PURE__*/_jsxDEV("form", {
            className: "auth__form",
            onSubmit: submit,
            children: [/*#__PURE__*/_jsxDEV(PasswordField, {
              label: "Новый пароль",
              value: pw,
              onChange: e => setPw(e.target.value)
            }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
              className: "field",
              children: [/*#__PURE__*/_jsxDEV("label", {
                className: "field__label",
                children: "Повтор пароля"
              }, void 0, false), /*#__PURE__*/_jsxDEV("input", {
                className: 'input' + (mismatch ? ' is-error' : pw2 && !mismatch ? ' is-valid' : ''),
                type: "password",
                placeholder: "••••••••",
                value: pw2,
                onChange: e => setPw2(e.target.value)
              }, void 0, false), mismatch && /*#__PURE__*/_jsxDEV("span", {
                className: "field__err",
                children: "Пароли не совпадают"
              }, void 0, false)]
            }, void 0, true), err && /*#__PURE__*/_jsxDEV("div", {
              className: "field__err",
              children: err
            }, void 0, false), /*#__PURE__*/_jsxDEV("button", {
              className: "btn btn--primary btn--block btn--lg",
              type: "submit",
              disabled: !ok || busy,
              children: busy ? 'Сохраняем…' : 'Сохранить пароль'
            }, void 0, false)]
          }, void 0, true)]
        }, void 0, true)
      }, void 0, false)]
    }, void 0, true)
  }, void 0, false);
}

// ============================================================
// dashboard.jsx — список сайтов, статусы, пусто, добавление, прогресс
// ============================================================

// ---- бейдж статуса ----
function StatusBadge({
  site
}) {
  const map = {
    building: {
      cls: 'badge--building',
      ic: 'loader',
      txt: 'Создаётся…'
    },
    error: {
      cls: 'badge--error',
      ic: 'alert-triangle',
      txt: 'Ошибка сборки'
    },
    trial: {
      cls: 'badge--trial',
      ic: null,
      txt: `Пробный период — осталось ${site.trialDays} дн.`
    },
    active: {
      cls: 'badge--active',
      ic: null,
      txt: `Активна до ${site.until}`
    },
    unpaid: {
      cls: 'badge--unpaid',
      ic: null,
      txt: 'Не оплачено'
    }
  };
  const m = map[site.status] || map.active;
  return /*#__PURE__*/_jsxDEV("span", {
    className: 'badge ' + m.cls,
    children: [m.ic ? /*#__PURE__*/_jsxDEV("i", {
      "data-lucide": m.ic,
      style: {
        width: 13,
        height: 13
      },
      className: site.status === 'building' ? 'spin-ic' : ''
    }, void 0, false) : /*#__PURE__*/_jsxDEV("span", {
      className: "dot"
    }, void 0, false), m.txt]
  }, void 0, true);
}

// ---- карточка сайта ----
function SiteCard({
  site,
  nav,
  onPay,
  onMenu
}) {
  const isBuilding = site.status === 'building';
  const isError = site.status === 'error';
  const needsPay = site.status === 'trial' || site.status === 'unpaid';
  return /*#__PURE__*/_jsxDEV("div", {
    className: "card sitecard",
    children: [/*#__PURE__*/_jsxDEV("div", {
      className: "sitecard__top",
      children: [/*#__PURE__*/_jsxDEV("div", {
        className: "row",
        style: {
          alignItems: 'flex-start'
        },
        children: [/*#__PURE__*/_jsxDEV("div", {
          className: "sitecard__thumb",
          style: {
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--terracotta)',
            background: 'var(--terracotta-wash)'
          },
          children: /*#__PURE__*/_jsxDEV("i", {
            "data-lucide": site.icon || 'store',
            style: {
              width: 24,
              height: 24
            }
          }, void 0, false)
        }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
          children: [/*#__PURE__*/_jsxDEV("div", {
            className: "sitecard__title",
            children: site.name
          }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
            className: "sitecard__url",
            children: [site.slug, ".uqqi.ru", !isBuilding && !isError && /*#__PURE__*/_jsxDEV("a", {
              href: 'https://' + site.slug + '.uqqi.ru',
              target: "_blank",
              rel: "noopener",
              children: ["открыть ", /*#__PURE__*/_jsxDEV("i", {
                "data-lucide": "arrow-up-right",
                style: {
                  width: 13,
                  height: 13
                }
              }, void 0, false)]
            }, void 0, true)]
          }, void 0, true)]
        }, void 0, true)]
      }, void 0, true), /*#__PURE__*/_jsxDEV(StatusBadge, {
        site: site
      }, void 0, false)]
    }, void 0, true), isBuilding && /*#__PURE__*/_jsxDEV("div", {
      children: [/*#__PURE__*/_jsxDEV("div", {
        className: "pbar",
        children: /*#__PURE__*/_jsxDEV("div", {
          className: "pbar__fill",
          style: {
            width: '62%'
          }
        }, void 0, false)
      }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
        className: "muted",
        style: {
          fontSize: '.8rem',
          marginTop: '.5rem'
        },
        children: "Собираем сайт из карточки Яндекс Карт — обычно занимает меньше минуты."
      }, void 0, false)]
    }, void 0, true), isError && /*#__PURE__*/_jsxDEV("p", {
      style: {
        fontSize: '.85rem',
        color: 'var(--danger)',
        lineHeight: 1.6
      },
      children: "Не получилось обработать ссылку. Проверьте её или напишите в поддержку."
    }, void 0, false), !isBuilding && !isError && /*#__PURE__*/_jsxDEV("div", {
      className: "sitecard__meta",
      children: [/*#__PURE__*/_jsxDEV("span", {
        children: /*#__PURE__*/_jsxDEV("b", {
          children: site.city
        }, void 0, false)
      }, void 0, false), /*#__PURE__*/_jsxDEV("span", {
        children: ["Тариф: ", /*#__PURE__*/_jsxDEV("b", {
          children: "990 ₽ / мес"
        }, void 0, false)]
      }, void 0, true), /*#__PURE__*/_jsxDEV("span", {
        children: ["Создан: ", /*#__PURE__*/_jsxDEV("b", {
          children: site.created
        }, void 0, false)]
      }, void 0, true)]
    }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
      className: "sitecard__actions",
      children: [needsPay && /*#__PURE__*/_jsxDEV("button", {
        className: "btn btn--primary btn--sm",
        onClick: () => onPay(site),
        children: site.status === 'unpaid' ? 'Оплатить, чтобы возобновить' : 'Оплатить 990 ₽'
      }, void 0, false), isError && /*#__PURE__*/_jsxDEV("button", {
        className: "btn btn--primary btn--sm",
        onClick: () => nav('add-site'),
        children: [/*#__PURE__*/_jsxDEV("i", {
          "data-lucide": "rotate-cw"
        }, void 0, false), " Попробовать снова"]
      }, void 0, true), !isBuilding && !isError && /*#__PURE__*/_jsxDEV("a", {
        className: "btn btn--ghost btn--sm",
        href: '/site/' + site.slug + '/edit',
        children: [/*#__PURE__*/_jsxDEV("i", {
          "data-lucide": "pencil"
        }, void 0, false), " Редактировать сайт"]
      }, void 0, true), !isBuilding && /*#__PURE__*/_jsxDEV("button", {
        className: "iconbtn",
        title: "Удалить",
        onClick: () => onMenu(site),
        children: /*#__PURE__*/_jsxDEV("i", {
          "data-lucide": "settings-2"
        }, void 0, false)
      }, void 0, false)]
    }, void 0, true)]
  }, void 0, true);
}

// ---- экран «Мои сайты» ----
function ScreenSites({
  nav,
  sites,
  onPay,
  onMenu,
  canAdd
}) {
  if (sites.length === 0) {
    return /*#__PURE__*/_jsxDEV("div", {
      className: "empty",
      children: /*#__PURE__*/_jsxDEV("div", {
        className: "empty__box",
        children: [/*#__PURE__*/_jsxDEV("div", {
          className: "empty__ic",
          children: /*#__PURE__*/_jsxDEV("i", {
            "data-lucide": "layout-template"
          }, void 0, false)
        }, void 0, false), /*#__PURE__*/_jsxDEV("h2", {
          children: "У вас пока нет сайтов"
        }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
          children: "Вставьте ссылку на карточку вашей организации в Яндекс Картах — и мы соберём готовый сайт за минуту."
        }, void 0, false), /*#__PURE__*/_jsxDEV("button", {
          className: "btn btn--primary btn--lg",
          onClick: () => nav('add-site'),
          children: [/*#__PURE__*/_jsxDEV("i", {
            "data-lucide": "plus"
          }, void 0, false), " Создать первый сайт"]
        }, void 0, true)]
      }, void 0, true)
    }, void 0, false);
  }
  return /*#__PURE__*/_jsxDEV("div", {
    className: "sites",
    children: [sites.map(s => /*#__PURE__*/_jsxDEV(SiteCard, {
      site: s,
      nav: nav,
      onPay: onPay,
      onMenu: onMenu
    }, s.id, false)), /*#__PURE__*/_jsxDEV("div", {
      style: {
        marginTop: '.3rem'
      },
      children: canAdd ? /*#__PURE__*/_jsxDEV("button", {
        className: "btn btn--outline",
        onClick: () => nav('add-site'),
        children: [/*#__PURE__*/_jsxDEV("i", {
          "data-lucide": "plus"
        }, void 0, false), " Добавить сайт"]
      }, void 0, true) : /*#__PURE__*/_jsxDEV("div", {
        className: "card",
        style: {
          padding: '1rem 1.1rem',
          display: 'flex',
          gap: '.7rem',
          alignItems: 'center',
          background: 'var(--warning-wash)',
          borderColor: 'color-mix(in srgb,var(--warning) 30%,var(--line))'
        },
        children: [/*#__PURE__*/_jsxDEV("i", {
          "data-lucide": "info",
          style: {
            width: 18,
            height: 18,
            color: 'var(--warning)',
            flex: 'none'
          }
        }, void 0, false), /*#__PURE__*/_jsxDEV("span", {
          style: {
            fontSize: '.84rem',
            color: 'var(--ink-2)'
          },
          children: "На пробном тарифе доступен один сайт. Чтобы добавить ещё — оплатите текущий."
        }, void 0, false)]
      }, void 0, true)
    }, void 0, false)]
  }, void 0, true);
}

// ---- валидация ссылки (короткая yandex.com/maps/-/...) ----
function validYandex(url) {
  if (!url.trim()) return null;
  return /^https:\/\/yandex\.(com|ru)\/maps\/-\/[A-Za-z0-9_~-]+\/?$/.test(url.trim());
}

// ---- экран «Добавить сайт» ----
function ScreenAddSite({
  nav,
  onStartBuild
}) {
  const [url, setUrl] = useStateD('');
  const valid = validYandex(url);
  return /*#__PURE__*/_jsxDEV("div", {
    className: "wrap-md",
    children: [/*#__PURE__*/_jsxDEV("a", {
      className: "linklike",
      style: {
        fontSize: '.84rem',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '.3rem',
        marginBottom: '1.2rem'
      },
      onClick: () => nav('sites'),
      children: [/*#__PURE__*/_jsxDEV("i", {
        "data-lucide": "arrow-left",
        style: {
          width: 15,
          height: 15
        }
      }, void 0, false), " Мои сайты"]
    }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
      className: "card",
      style: {
        padding: '1.6rem'
      },
      children: [/*#__PURE__*/_jsxDEV("span", {
        className: "eyebrow",
        children: "Новый сайт"
      }, void 0, false), /*#__PURE__*/_jsxDEV("h2", {
        style: {
          fontFamily: 'var(--font-display)',
          fontWeight: 700,
          fontSize: '1.4rem',
          letterSpacing: '-.02em',
          color: 'var(--ink)',
          margin: '.5rem 0 .4rem'
        },
        children: "Ссылка на Яндекс Карты"
      }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
        className: "muted",
        style: {
          fontSize: '.88rem',
          lineHeight: 1.6
        },
        children: "Вставьте ссылку на карточку вашей организации — мы возьмём оттуда название, адрес, фото, часы работы и отзывы."
      }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        className: "field",
        style: {
          marginTop: '1.3rem'
        },
        children: [/*#__PURE__*/_jsxDEV("label", {
          className: "field__label",
          children: "Ссылка на карточку организации"
        }, void 0, false), /*#__PURE__*/_jsxDEV("input", {
          className: 'input' + (valid === true ? ' is-valid' : valid === false ? ' is-error' : ''),
          placeholder: "https://yandex.com/maps/-/CDe…",
          value: url,
          onChange: e => setUrl(e.target.value)
        }, void 0, false), valid === false && /*#__PURE__*/_jsxDEV("span", {
          className: "field__err",
          children: "Похоже, это не ссылка на Яндекс Карты. Проверьте формат."
        }, void 0, false), valid === true && /*#__PURE__*/_jsxDEV("span", {
          className: "field__hint",
          style: {
            color: 'var(--success-soft)'
          },
          children: "Ссылка распознана ✓"
        }, void 0, false)]
      }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
        className: "card",
        style: {
          background: 'var(--paper-2)',
          border: 'none',
          boxShadow: 'none',
          padding: '.9rem 1rem',
          marginTop: '1rem',
          display: 'flex',
          gap: '.7rem'
        },
        children: [/*#__PURE__*/_jsxDEV("i", {
          "data-lucide": "lightbulb",
          style: {
            width: 18,
            height: 18,
            color: 'var(--gold-dim)',
            flex: 'none'
          }
        }, void 0, false), /*#__PURE__*/_jsxDEV("span", {
          style: {
            fontSize: '.82rem',
            color: 'var(--ink-2)',
            lineHeight: 1.6
          },
          children: ["Где взять ссылку: откройте карточку компании в Яндекс Картах, нажмите кнопку ", /*#__PURE__*/_jsxDEV("b", {
            children: "«Поделиться»"
          }, void 0, false), " и скопируйте ссылку."]
        }, void 0, true)]
      }, void 0, true), /*#__PURE__*/_jsxDEV("button", {
        className: "btn btn--primary btn--lg btn--block",
        style: {
          marginTop: '1.3rem'
        },
        disabled: valid !== true,
        onClick: () => onStartBuild(url),
        children: "Создать сайт"
      }, void 0, false)]
    }, void 0, true)]
  }, void 0, true);
}

// ---- экран прогресса сборки ----
const BUILD_STEPS = [{
  label: 'Ставим в очередь',
  ic: 'list'
}, {
  label: 'Анализируем карточку',
  ic: 'search'
}, {
  label: 'Загружаем фото',
  ic: 'image'
}, {
  label: 'Загружаем отзывы',
  ic: 'message-square'
}, {
  label: 'Публикуем на uqqi.ru',
  ic: 'rocket'
}];
function ScreenBuilding({
  onDone,
  buildId
}) {
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
          clearInterval(pollRef.current);
          clearInterval(stepRef.current);
          setStep(BUILD_STEPS.length);
          setTimeout(onDone, 800);
        } else if (st.build_status === 'error') {
          clearInterval(pollRef.current);
          clearInterval(stepRef.current);
          setFailed(true);
        }
      } catch (e) {}
    }, 2000);
    return () => {
      clearInterval(pollRef.current);
      clearInterval(stepRef.current);
    };
  }, [buildId]);
  if (failed) {
    return /*#__PURE__*/_jsxDEV("div", {
      className: "wrap-md",
      style: {
        paddingTop: '1rem'
      },
      children: /*#__PURE__*/_jsxDEV("div", {
        className: "card",
        style: {
          padding: '2rem 1.8rem',
          textAlign: 'center'
        },
        children: [/*#__PURE__*/_jsxDEV("div", {
          className: "empty__ic",
          style: {
            margin: '0 auto 1rem',
            color: 'var(--danger)'
          },
          children: /*#__PURE__*/_jsxDEV("i", {
            "data-lucide": "alert-triangle"
          }, void 0, false)
        }, void 0, false), /*#__PURE__*/_jsxDEV("h2", {
          style: {
            fontFamily: 'var(--font-display)',
            fontWeight: 700,
            fontSize: '1.3rem',
            color: 'var(--ink)'
          },
          children: "Не удалось собрать сайт"
        }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
          className: "muted",
          style: {
            fontSize: '.88rem',
            marginTop: '.5rem',
            lineHeight: 1.6
          },
          children: "Не получилось обработать ссылку. Проверьте, что это короткая ссылка на карточку организации в Яндекс Картах, или напишите в поддержку."
        }, void 0, false), /*#__PURE__*/_jsxDEV("button", {
          className: "btn btn--primary btn--lg",
          style: {
            marginTop: '1.2rem'
          },
          onClick: () => window.location.reload(),
          children: [/*#__PURE__*/_jsxDEV("i", {
            "data-lucide": "rotate-cw"
          }, void 0, false), " Попробовать снова"]
        }, void 0, true)]
      }, void 0, true)
    }, void 0, false);
  }
  const pct = Math.min(100, Math.round(step / BUILD_STEPS.length * 100));
  return /*#__PURE__*/_jsxDEV("div", {
    className: "wrap-md",
    style: {
      paddingTop: '1rem'
    },
    children: /*#__PURE__*/_jsxDEV("div", {
      className: "card",
      style: {
        padding: '2rem 1.8rem',
        textAlign: 'center'
      },
      children: [/*#__PURE__*/_jsxDEV("div", {
        className: "spin",
        style: {
          margin: '0 auto .4rem'
        }
      }, void 0, false), /*#__PURE__*/_jsxDEV("h2", {
        style: {
          fontFamily: 'var(--font-display)',
          fontWeight: 700,
          fontSize: '1.3rem',
          letterSpacing: '-.02em',
          color: 'var(--ink)',
          marginTop: '.8rem'
        },
        children: "Собираем ваш сайт"
      }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
        className: "muted",
        style: {
          fontSize: '.86rem',
          marginTop: '.4rem'
        },
        children: "Обычно это занимает меньше минуты. Можно не закрывать страницу — мы сохраним прогресс."
      }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        className: "pbar",
        style: {
          margin: '1.4rem 0 1.2rem'
        },
        children: /*#__PURE__*/_jsxDEV("div", {
          className: "pbar__fill",
          style: {
            width: pct + '%'
          }
        }, void 0, false)
      }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        style: {
          textAlign: 'left',
          maxWidth: 300,
          margin: '0 auto'
        },
        children: BUILD_STEPS.map((s, i) => /*#__PURE__*/_jsxDEV("div", {
          className: 'bstep ' + (i < step ? 'done' : i === step ? 'active' : ''),
          children: [/*#__PURE__*/_jsxDEV("span", {
            className: "bstep__ic",
            children: i < step ? /*#__PURE__*/_jsxDEV("i", {
              "data-lucide": "check"
            }, void 0, false) : i === step ? /*#__PURE__*/_jsxDEV("i", {
              "data-lucide": s.ic
            }, void 0, false) : /*#__PURE__*/_jsxDEV("span", {
              style: {
                width: 6,
                height: 6,
                borderRadius: 9,
                background: 'var(--line)'
              }
            }, void 0, false)
          }, void 0, false), s.label]
        }, i, true))
      }, void 0, false)]
    }, void 0, true)
  }, void 0, false);
}

// ============================================================
// billing.jsx — оплата, ЮKassa, подписки, поддержка, настройки
// ============================================================

const INCLUDED = ['Сайт на адресе название.uqqi.ru', 'Данные из Яндекс Карт: фото, отзывы, часы', 'Редактирование контента без программиста', 'Онлайн-запись и приём заявок', 'Поддержка и обновления'];

// ---- Сводка оплаты (внутри кабинета) ----
function ScreenPayment({
  nav,
  site,
  onProceed
}) {
  const s = site || {};
  const [busy, setBusy] = useStateB(false);
  const [err, setErr] = useStateB('');
  async function pay() {
    setErr('');
    setBusy(true);
    try {
      const res = await window.API.createPayment(s.id);
      if (res.confirmation_url) {
        window.location.href = res.confirmation_url; // редирект на ЮKassa
      } else {
        setErr('Не удалось создать платёж');
        setBusy(false);
      }
    } catch (ex) {
      setErr(ex.message || 'Ошибка оплаты');
      setBusy(false);
    }
  }
  return /*#__PURE__*/_jsxDEV("div", {
    className: "wrap-md",
    children: [/*#__PURE__*/_jsxDEV("a", {
      className: "linklike",
      style: {
        fontSize: '.84rem',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '.3rem',
        marginBottom: '1.2rem'
      },
      onClick: () => nav('sites'),
      children: [/*#__PURE__*/_jsxDEV("i", {
        "data-lucide": "arrow-left",
        style: {
          width: 15,
          height: 15
        }
      }, void 0, false), " Мои сайты"]
    }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
      className: "card",
      style: {
        padding: '1.6rem'
      },
      children: [/*#__PURE__*/_jsxDEV("span", {
        className: "eyebrow",
        children: "Оплата подписки"
      }, void 0, false), /*#__PURE__*/_jsxDEV("h2", {
        style: {
          fontFamily: 'var(--font-display)',
          fontWeight: 700,
          fontSize: '1.4rem',
          letterSpacing: '-.02em',
          color: 'var(--ink)',
          margin: '.5rem 0 1.2rem'
        },
        children: s.name || 'Ваш сайт'
      }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        className: "row",
        style: {
          padding: '.9rem 1rem',
          background: 'var(--paper-2)',
          borderRadius: 'var(--r-lg)'
        },
        children: [/*#__PURE__*/_jsxDEV("div", {
          className: "sitecard__thumb",
          style: {
            width: 42,
            height: 42,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--terracotta)',
            background: 'var(--terracotta-wash)'
          },
          children: /*#__PURE__*/_jsxDEV("i", {
            "data-lucide": s.icon || 'store',
            style: {
              width: 20,
              height: 20
            }
          }, void 0, false)
        }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
          children: [/*#__PURE__*/_jsxDEV("div", {
            style: {
              fontWeight: 600,
              color: 'var(--ink)',
              fontSize: '.92rem'
            },
            children: (s.slug || 'site') + '.uqqi.ru'
          }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
            className: "muted",
            style: {
              fontSize: '.8rem'
            },
            children: s.city || ''
          }, void 0, false)]
        }, void 0, true)]
      }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
        style: {
          marginTop: '1.2rem'
        },
        children: [/*#__PURE__*/_jsxDEV("div", {
          className: "sumrow",
          children: [/*#__PURE__*/_jsxDEV("span", {
            className: "k",
            children: "Тариф"
          }, void 0, false), /*#__PURE__*/_jsxDEV("span", {
            className: "v",
            children: "Стандарт — 990 ₽ / месяц"
          }, void 0, false)]
        }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
          className: "sumrow",
          children: [/*#__PURE__*/_jsxDEV("span", {
            className: "k",
            children: "Период"
          }, void 0, false), /*#__PURE__*/_jsxDEV("span", {
            className: "v",
            children: "30 дней"
          }, void 0, false)]
        }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
          className: "sum-total",
          children: [/*#__PURE__*/_jsxDEV("span", {
            className: "k",
            style: {
              color: 'var(--ink)',
              fontWeight: 600
            },
            children: "Итого сегодня"
          }, void 0, false), /*#__PURE__*/_jsxDEV("span", {
            className: "amt",
            children: "990 ₽"
          }, void 0, false)]
        }, void 0, true)]
      }, void 0, true), /*#__PURE__*/_jsxDEV("hr", {
        className: "divider",
        style: {
          margin: '1.3rem 0'
        }
      }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
        className: "field__label",
        style: {
          marginBottom: '.7rem'
        },
        children: "Что входит"
      }, void 0, false), /*#__PURE__*/_jsxDEV("ul", {
        className: "feat-list",
        children: INCLUDED.map((f, i) => /*#__PURE__*/_jsxDEV("li", {
          children: [/*#__PURE__*/_jsxDEV("i", {
            "data-lucide": "check"
          }, void 0, false), f]
        }, i, true))
      }, void 0, false), err && /*#__PURE__*/_jsxDEV("div", {
        className: "field__err",
        style: {
          marginTop: '1rem'
        },
        children: err
      }, void 0, false), /*#__PURE__*/_jsxDEV("button", {
        className: "btn btn--primary btn--lg btn--block",
        style: {
          marginTop: '1.5rem'
        },
        onClick: pay,
        disabled: busy,
        children: [/*#__PURE__*/_jsxDEV("i", {
          "data-lucide": "lock"
        }, void 0, false), " ", busy ? 'Создаём платёж…' : 'Перейти к оплате']
      }, void 0, true), /*#__PURE__*/_jsxDEV("p", {
        className: "legal",
        style: {
          textAlign: 'center',
          marginTop: '.8rem'
        },
        children: "Оплата проходит через ЮKassa. Мы не храним данные вашей карты."
      }, void 0, false)]
    }, void 0, true)]
  }, void 0, true);
}

// ---- ЮKassa (полноэкранный «редирект») ----
function ScreenYukassa({
  nav
}) {
  return /*#__PURE__*/_jsxDEV("div", {
    className: "screen fade-enter",
    children: /*#__PURE__*/_jsxDEV("div", {
      className: "yk",
      children: /*#__PURE__*/_jsxDEV("div", {
        className: "yk__card",
        children: [/*#__PURE__*/_jsxDEV("div", {
          className: "yk__head",
          children: [/*#__PURE__*/_jsxDEV("div", {
            className: "yk__brand",
            children: ["Ю", /*#__PURE__*/_jsxDEV("span", {
              children: "Kassa"
            }, void 0, false)]
          }, void 0, true), /*#__PURE__*/_jsxDEV("span", {
            style: {
              fontSize: '.78rem',
              opacity: .7
            },
            children: "uqqi.ru"
          }, void 0, false)]
        }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
          className: "yk__body",
          children: [/*#__PURE__*/_jsxDEV("div", {
            className: "between",
            style: {
              marginBottom: '.2rem'
            },
            children: [/*#__PURE__*/_jsxDEV("span", {
              style: {
                color: '#666',
                fontSize: '.86rem'
              },
              children: "К оплате"
            }, void 0, false), /*#__PURE__*/_jsxDEV("span", {
              style: {
                fontWeight: 800,
                fontSize: '1.2rem',
                color: '#1d1d1b'
              },
              children: "990,00 ₽"
            }, void 0, false)]
          }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
            children: [/*#__PURE__*/_jsxDEV("div", {
              className: "yk__lbl",
              children: "Номер карты"
            }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
              className: "yk__inp",
              children: "0000 0000 0000 0000"
            }, void 0, false)]
          }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
            className: "row",
            style: {
              gap: '.7rem'
            },
            children: [/*#__PURE__*/_jsxDEV("div", {
              style: {
                flex: 1
              },
              children: [/*#__PURE__*/_jsxDEV("div", {
                className: "yk__lbl",
                children: "ММ / ГГ"
              }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
                className: "yk__inp",
                children: "00 / 00"
              }, void 0, false)]
            }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
              style: {
                flex: 1
              },
              children: [/*#__PURE__*/_jsxDEV("div", {
                className: "yk__lbl",
                children: "CVC"
              }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
                className: "yk__inp",
                children: "•••"
              }, void 0, false)]
            }, void 0, true)]
          }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
            className: "yk__pay",
            onClick: () => nav('payment-processing'),
            children: "Оплатить 990 ₽"
          }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
            style: {
              fontSize: '.7rem',
              color: '#aaa',
              textAlign: 'center',
              marginTop: '.2rem'
            },
            children: "Демонстрационный экран. Реальное списание не производится."
          }, void 0, false)]
        }, void 0, true)]
      }, void 0, true)
    }, void 0, false)
  }, void 0, false);
}

// ---- Оплата обрабатывается → успех ----
// Поллим список сайтов: webhook ЮKassa переведёт сайт в active.
function ScreenPaymentProcessing({
  onConfirmed
}) {
  React.useEffect(() => {
    let tries = 0;
    const iv = setInterval(async () => {
      tries++;
      try {
        const data = await window.API.sites();
        const anyActive = (data.sites || []).some(s => s.status === 'active');
        if (anyActive) {
          clearInterval(iv);
          onConfirmed();
          return;
        }
      } catch (e) {}
      if (tries > 15) {
        clearInterval(iv);
        onConfirmed();
      }
    }, 2000);
    return () => clearInterval(iv);
  }, []);
  return /*#__PURE__*/_jsxDEV("div", {
    className: "screen fade-enter",
    children: /*#__PURE__*/_jsxDEV("div", {
      className: "notice",
      children: /*#__PURE__*/_jsxDEV("div", {
        className: "notice__box",
        children: [/*#__PURE__*/_jsxDEV("div", {
          className: "spin"
        }, void 0, false), /*#__PURE__*/_jsxDEV("h2", {
          children: "Оплата обрабатывается"
        }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
          children: ["Ждём подтверждение от платёжной системы", /*#__PURE__*/_jsxDEV("span", {
            className: "dots",
            children: [/*#__PURE__*/_jsxDEV("span", {
              children: "."
            }, void 0, false), /*#__PURE__*/_jsxDEV("span", {
              children: "."
            }, void 0, false), /*#__PURE__*/_jsxDEV("span", {
              children: "."
            }, void 0, false)]
          }, void 0, true), /*#__PURE__*/_jsxDEV("br", {}, void 0, false), "Это занимает несколько секунд."]
        }, void 0, true)]
      }, void 0, true)
    }, void 0, false)
  }, void 0, false);
}
function ScreenPaymentSuccess({
  nav,
  site
}) {
  return /*#__PURE__*/_jsxDEV("div", {
    className: "screen fade-enter",
    children: /*#__PURE__*/_jsxDEV("div", {
      className: "notice",
      children: /*#__PURE__*/_jsxDEV("div", {
        className: "notice__box",
        children: [/*#__PURE__*/_jsxDEV("div", {
          className: "notice__ic ok",
          children: /*#__PURE__*/_jsxDEV("i", {
            "data-lucide": "check"
          }, void 0, false)
        }, void 0, false), /*#__PURE__*/_jsxDEV("h2", {
          children: "Оплачено"
        }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
          children: ["Сайт ", /*#__PURE__*/_jsxDEV("b", {
            children: [site && site.slug || 'site', ".uqqi.ru"]
          }, void 0, true), " активен до ", /*#__PURE__*/_jsxDEV("b", {
            children: site && site.until || '22.07.2026'
          }, void 0, false), ". Спасибо!"]
        }, void 0, true), /*#__PURE__*/_jsxDEV("button", {
          className: "btn btn--primary btn--lg",
          style: {
            marginTop: '.4rem'
          },
          onClick: () => nav('sites'),
          children: "Вернуться в кабинет"
        }, void 0, false)]
      }, void 0, true)
    }, void 0, false)
  }, void 0, false);
}

// ---- Подписки и платежи ----
function ScreenSubscriptions({
  nav,
  sites,
  payments,
  onPay
}) {
  return /*#__PURE__*/_jsxDEV("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: '1.6rem'
    },
    children: [/*#__PURE__*/_jsxDEV("div", {
      children: [/*#__PURE__*/_jsxDEV("p", {
        className: "field__label",
        style: {
          marginBottom: '.7rem'
        },
        children: "Подписки по сайтам"
      }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        style: {
          display: 'flex',
          flexDirection: 'column',
          gap: '.8rem'
        },
        children: sites.map(s => /*#__PURE__*/_jsxDEV("div", {
          className: "card",
          style: {
            padding: '1rem 1.2rem'
          },
          children: /*#__PURE__*/_jsxDEV("div", {
            className: "between",
            children: [/*#__PURE__*/_jsxDEV("div", {
              children: [/*#__PURE__*/_jsxDEV("div", {
                style: {
                  fontWeight: 600,
                  color: 'var(--ink)',
                  fontSize: '.95rem'
                },
                children: s.name
              }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
                className: "muted",
                style: {
                  fontSize: '.8rem',
                  marginTop: '.2rem'
                },
                children: [s.slug, ".uqqi.ru"]
              }, void 0, true)]
            }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
              style: {
                display: 'flex',
                alignItems: 'center',
                gap: '1rem'
              },
              children: [/*#__PURE__*/_jsxDEV(StatusBadge, {
                site: s
              }, void 0, false), (s.status === 'trial' || s.status === 'unpaid') && /*#__PURE__*/_jsxDEV("button", {
                className: "btn btn--primary btn--sm",
                onClick: () => onPay(s),
                children: "Оплатить"
              }, void 0, false), s.status === 'active' && /*#__PURE__*/_jsxDEV("button", {
                className: "btn btn--ghost btn--sm",
                onClick: () => onPay(s),
                children: "Продлить"
              }, void 0, false)]
            }, void 0, true)]
          }, void 0, true)
        }, s.id, false))
      }, void 0, false)]
    }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
      children: [/*#__PURE__*/_jsxDEV("p", {
        className: "field__label",
        style: {
          marginBottom: '.7rem'
        },
        children: "История платежей"
      }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        className: "card",
        style: {
          padding: '.4rem .6rem'
        },
        children: /*#__PURE__*/_jsxDEV("table", {
          className: "ptable",
          children: [/*#__PURE__*/_jsxDEV("thead", {
            children: /*#__PURE__*/_jsxDEV("tr", {
              children: [/*#__PURE__*/_jsxDEV("th", {
                children: "Дата"
              }, void 0, false), /*#__PURE__*/_jsxDEV("th", {
                children: "Сайт"
              }, void 0, false), /*#__PURE__*/_jsxDEV("th", {
                children: "Сумма"
              }, void 0, false), /*#__PURE__*/_jsxDEV("th", {
                children: "Статус"
              }, void 0, false), /*#__PURE__*/_jsxDEV("th", {}, void 0, false)]
            }, void 0, true)
          }, void 0, false), /*#__PURE__*/_jsxDEV("tbody", {
            children: payments.map((p, i) => /*#__PURE__*/_jsxDEV("tr", {
              children: [/*#__PURE__*/_jsxDEV("td", {
                "data-l": "Дата",
                children: p.date
              }, void 0, false), /*#__PURE__*/_jsxDEV("td", {
                "data-l": "Сайт",
                children: p.site
              }, void 0, false), /*#__PURE__*/_jsxDEV("td", {
                "data-l": "Сумма",
                className: "amt",
                children: p.amount
              }, void 0, false), /*#__PURE__*/_jsxDEV("td", {
                "data-l": "Статус",
                children: /*#__PURE__*/_jsxDEV("span", {
                  className: 'badge ' + (p.ok ? 'badge--active' : 'badge--unpaid'),
                  style: {
                    fontSize: '.7rem'
                  },
                  children: [/*#__PURE__*/_jsxDEV("span", {
                    className: "dot"
                  }, void 0, false), p.ok ? 'Оплачен' : 'Отклонён']
                }, void 0, true)
              }, void 0, false), /*#__PURE__*/_jsxDEV("td", {
                "data-l": "Чек",
                children: p.ok ? /*#__PURE__*/_jsxDEV("a", {
                  className: "linklike",
                  style: {
                    fontSize: '.8rem',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '.25rem'
                  },
                  href: "#",
                  onClick: e => e.preventDefault(),
                  children: ["чек ", /*#__PURE__*/_jsxDEV("i", {
                    "data-lucide": "arrow-up-right",
                    style: {
                      width: 12,
                      height: 12
                    }
                  }, void 0, false)]
                }, void 0, true) : /*#__PURE__*/_jsxDEV("span", {
                  className: "muted",
                  children: "—"
                }, void 0, false)
              }, void 0, false)]
            }, i, true))
          }, void 0, false)]
        }, void 0, true)
      }, void 0, false)]
    }, void 0, true)]
  }, void 0, true);
}

// ---- Поддержка ----
function ScreenSupport({
  email,
  tickets,
  onSubmit
}) {
  const [subj, setSubj] = useStateB('');
  const [msg, setMsg] = useStateB('');
  const ok = subj.trim() && msg.trim();
  return /*#__PURE__*/_jsxDEV("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: '1.6rem'
    },
    children: [/*#__PURE__*/_jsxDEV("div", {
      className: "card",
      style: {
        padding: '1.4rem 1.5rem'
      },
      children: [/*#__PURE__*/_jsxDEV("p", {
        className: "field__label",
        style: {
          marginBottom: '1rem'
        },
        children: "Новое обращение"
      }, void 0, false), /*#__PURE__*/_jsxDEV("form", {
        style: {
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem'
        },
        onSubmit: e => {
          e.preventDefault();
          if (!ok) return;
          onSubmit(subj, msg);
          setSubj('');
          setMsg('');
        },
        children: [/*#__PURE__*/_jsxDEV("div", {
          className: "field",
          children: [/*#__PURE__*/_jsxDEV("label", {
            className: "field__label",
            children: "Тема"
          }, void 0, false), /*#__PURE__*/_jsxDEV("input", {
            className: "input",
            placeholder: "Например: не загрузились фото",
            value: subj,
            onChange: e => setSubj(e.target.value)
          }, void 0, false)]
        }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
          className: "field",
          children: [/*#__PURE__*/_jsxDEV("label", {
            className: "field__label",
            children: "Сообщение"
          }, void 0, false), /*#__PURE__*/_jsxDEV("textarea", {
            className: "input",
            placeholder: "Опишите, что случилось…",
            value: msg,
            onChange: e => setMsg(e.target.value)
          }, void 0, false)]
        }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
          className: "between",
          children: [/*#__PURE__*/_jsxDEV("span", {
            className: "muted",
            style: {
              fontSize: '.8rem'
            },
            children: [/*#__PURE__*/_jsxDEV("i", {
              "data-lucide": "mail",
              style: {
                width: 14,
                height: 14,
                verticalAlign: '-2px',
                marginRight: 4
              }
            }, void 0, false), " Ответим на ", email || 'you@example.ru']
          }, void 0, true), /*#__PURE__*/_jsxDEV("button", {
            className: "btn btn--primary",
            type: "submit",
            disabled: !ok,
            children: "Отправить"
          }, void 0, false)]
        }, void 0, true)]
      }, void 0, true)]
    }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
      children: [/*#__PURE__*/_jsxDEV("p", {
        className: "field__label",
        style: {
          marginBottom: '.7rem'
        },
        children: "История обращений"
      }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        style: {
          display: 'flex',
          flexDirection: 'column',
          gap: '.8rem'
        },
        children: tickets.map((t, i) => /*#__PURE__*/_jsxDEV("div", {
          className: "card ticket",
          children: [/*#__PURE__*/_jsxDEV("div", {
            className: "ticket__head",
            children: [/*#__PURE__*/_jsxDEV("span", {
              className: "ticket__subj",
              children: t.subj
            }, void 0, false), /*#__PURE__*/_jsxDEV("span", {
              className: 'badge ' + (t.status === 'open' ? 'badge--trial' : t.status === 'answered' ? 'badge--active' : 'badge--building'),
              style: {
                fontSize: '.7rem'
              },
              children: [/*#__PURE__*/_jsxDEV("span", {
                className: "dot"
              }, void 0, false), t.status === 'open' ? 'В работе' : t.status === 'answered' ? 'Отвечено' : 'Закрыто']
            }, void 0, true)]
          }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
            className: "ticket__body",
            children: t.body
          }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
            className: "ticket__date",
            children: t.date
          }, void 0, false)]
        }, i, true))
      }, void 0, false)]
    }, void 0, true)]
  }, void 0, true);
}

// ---- Настройки аккаунта ----
function ScreenSettings({
  email,
  onDelete
}) {
  const [pw, setPw] = useStateB('');
  const [pw2, setPw2] = useStateB('');
  const [np, setNp] = useStateB('');
  const [msg, setMsg] = useStateB(null);
  const [busy, setBusy] = useStateB(false);
  async function savePassword() {
    setMsg(null);
    if (np.length < 6) {
      setMsg({
        t: 'err',
        m: 'Новый пароль минимум 6 символов'
      });
      return;
    }
    if (np !== pw2) {
      setMsg({
        t: 'err',
        m: 'Пароли не совпадают'
      });
      return;
    }
    setBusy(true);
    try {
      await window.API.changePassword(pw, np);
      setMsg({
        t: 'ok',
        m: 'Пароль изменён'
      });
      setPw('');
      setNp('');
      setPw2('');
    } catch (ex) {
      setMsg({
        t: 'err',
        m: ex.message || 'Ошибка смены пароля'
      });
    } finally {
      setBusy(false);
    }
  }
  return /*#__PURE__*/_jsxDEV("div", {
    className: "wrap-md",
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: '1.6rem'
    },
    children: [/*#__PURE__*/_jsxDEV("div", {
      className: "card",
      style: {
        padding: '1.4rem 1.5rem'
      },
      children: [/*#__PURE__*/_jsxDEV("p", {
        className: "field__label",
        style: {
          marginBottom: '1rem'
        },
        children: "Email аккаунта"
      }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        className: "between",
        children: /*#__PURE__*/_jsxDEV("div", {
          className: "row",
          children: [/*#__PURE__*/_jsxDEV("div", {
            className: "usercard",
            children: /*#__PURE__*/_jsxDEV("div", {
              className: "av",
              style: {
                width: 38,
                height: 38
              },
              children: (email || 'U')[0].toUpperCase()
            }, void 0, false)
          }, void 0, false), /*#__PURE__*/_jsxDEV("span", {
            style: {
              color: 'var(--ink)',
              fontWeight: 500
            },
            children: email || 'you@example.ru'
          }, void 0, false)]
        }, void 0, true)
      }, void 0, false)]
    }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
      className: "card",
      style: {
        padding: '1.4rem 1.5rem'
      },
      children: [/*#__PURE__*/_jsxDEV("p", {
        className: "field__label",
        style: {
          marginBottom: '1rem'
        },
        children: "Смена пароля"
      }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        style: {
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem'
        },
        children: [/*#__PURE__*/_jsxDEV("div", {
          className: "field",
          children: [/*#__PURE__*/_jsxDEV("label", {
            className: "field__label",
            children: "Текущий пароль"
          }, void 0, false), /*#__PURE__*/_jsxDEV("input", {
            className: "input",
            type: "password",
            placeholder: "••••••••",
            value: pw,
            onChange: e => setPw(e.target.value)
          }, void 0, false)]
        }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
          className: "field",
          children: [/*#__PURE__*/_jsxDEV("label", {
            className: "field__label",
            children: "Новый пароль"
          }, void 0, false), /*#__PURE__*/_jsxDEV("input", {
            className: "input",
            type: "password",
            placeholder: "••••••••",
            value: np,
            onChange: e => setNp(e.target.value)
          }, void 0, false)]
        }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
          className: "field",
          children: [/*#__PURE__*/_jsxDEV("label", {
            className: "field__label",
            children: "Повтор нового пароля"
          }, void 0, false), /*#__PURE__*/_jsxDEV("input", {
            className: "input",
            type: "password",
            placeholder: "••••••••",
            value: pw2,
            onChange: e => setPw2(e.target.value)
          }, void 0, false)]
        }, void 0, true), msg && /*#__PURE__*/_jsxDEV("div", {
          className: msg.t === 'ok' ? 'field__hint' : 'field__err',
          style: msg.t === 'ok' ? {
            color: 'var(--success-soft)'
          } : {},
          children: msg.m
        }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
          children: /*#__PURE__*/_jsxDEV("button", {
            className: "btn btn--dark",
            onClick: savePassword,
            disabled: busy,
            children: busy ? 'Сохраняем…' : 'Сохранить пароль'
          }, void 0, false)
        }, void 0, false)]
      }, void 0, true)]
    }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
      className: "card",
      style: {
        padding: '1.4rem 1.5rem',
        borderColor: 'color-mix(in srgb,var(--danger) 25%,var(--line))'
      },
      children: [/*#__PURE__*/_jsxDEV("p", {
        className: "field__label",
        style: {
          marginBottom: '.5rem',
          color: 'var(--danger)'
        },
        children: "Опасная зона"
      }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
        className: "between",
        style: {
          gap: '1rem'
        },
        children: [/*#__PURE__*/_jsxDEV("p", {
          className: "muted",
          style: {
            fontSize: '.84rem',
            lineHeight: 1.6,
            maxWidth: 360
          },
          children: "Удаление аккаунта необратимо. Все сайты будут отключены, а данные удалены без возможности восстановления."
        }, void 0, false), /*#__PURE__*/_jsxDEV("button", {
          className: "btn btn--danger",
          style: {
            flex: 'none'
          },
          onClick: onDelete,
          children: [/*#__PURE__*/_jsxDEV("i", {
            "data-lucide": "trash-2"
          }, void 0, false), " Удалить аккаунт"]
        }, void 0, true)]
      }, void 0, true)]
    }, void 0, true)]
  }, void 0, true);
}

// ============================================================
// app.jsx — оболочка, роутер, состояние, навигация
// ============================================================

const NAV = [{
  id: 'sites',
  label: 'Мои сайты',
  ic: 'layout-grid'
}, {
  id: 'subscriptions',
  label: 'Подписки и платежи',
  ic: 'credit-card'
}, {
  id: 'support',
  label: 'Поддержка',
  ic: 'life-buoy'
}, {
  id: 'settings',
  label: 'Настройки',
  ic: 'settings'
}];
const SECTION_OF = {
  sites: 'sites',
  'add-site': 'sites',
  building: 'sites',
  payment: 'sites',
  admin: 'sites',
  subscriptions: 'subscriptions',
  support: 'support',
  settings: 'settings'
};
const TITLES = {
  sites: ['Мои сайты', 'Сайты вашего бизнеса на uqqi.ru'],
  'add-site': ['Новый сайт', null],
  building: ['Создаём сайт', null],
  payment: ['Оплата', null],
  admin: ['Редактор сайта', null],
  subscriptions: ['Подписки и платежи', 'Статусы, продление и история'],
  support: ['Поддержка', 'Мы на связи и поможем'],
  settings: ['Настройки', 'Аккаунт и безопасность']
};
const CABINET = new Set(['sites', 'add-site', 'building', 'payment', 'admin', 'subscriptions', 'support', 'settings']);
function plusDays(n) {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
}
function App() {
  const [screen, setScreen] = useState('login');
  const [email, setEmail] = useState('');
  const [toast, setToast] = useState(null);
  const [payTarget, setPayTarget] = useState(null);
  const [menuSite, setMenuSite] = useState(null);
  const [confirmDel, setConfirmDel] = useState(false);
  const [booted, setBooted] = useState(false);
  const [sites, setSites] = useState([]);
  const [payments, setPayments] = useState([]);
  const [tickets, setTickets] = useState([]);
  const ctx = {
    email,
    setEmail
  };
  const nav = s => {
    setScreen(s);
    if (s === 'support') {
      window.API.tickets().then(d => setTickets(d.tickets || [])).catch(() => {});
    } else if (s === 'subscriptions') {
      loadSites();
      window.API.payments().then(d => setPayments(d.payments || [])).catch(() => {});
    } else if (s === 'sites') {
      loadSites();
    }
  };
  const ping = m => {
    setToast(m);
    setTimeout(() => setToast(null), 2600);
  };

  // На старте: маршрут по URL (verify/reset/возврат с оплаты) или проверка сессии
  useEffect(() => {
    const path = window.location.pathname;
    const params = new URLSearchParams(window.location.search);
    if (path === '/verify') {
      setScreen('confirm-email');
      setBooted(true);
      return;
    }
    if (path === '/reset') {
      setScreen('reset');
      setBooted(true);
      return;
    }
    const paidId = params.get('paid');
    window.API.me().then(u => {
      setEmail(u.email);
      if (paidId) {
        // Вернулись с ЮKassa — показываем «обрабатывается», чистим URL
        window.history.replaceState({}, '', '/');
        setScreen('payment-processing');
      } else {
        setScreen('sites');
      }
      return loadSites();
    }).catch(() => setScreen('login')).finally(() => setBooted(true));
  }, []);
  async function loadSites() {
    try {
      const data = await window.API.sites();
      setSites(data.sites || []);
      return data;
    } catch (e) {
      return {
        sites: []
      };
    }
  }

  // refresh lucide icons after every render
  useEffect(() => {
    if (window.lucide) window.lucide.createIcons();
  });
  const [canAdd, setCanAdd] = useState(true);
  const [buildId, setBuildId] = useState(null);

  // Обновляем canAdd при изменении списка
  useEffect(() => {
    setCanAdd(!sites.some(s => s.status === 'trial' || s.status === 'building'));
  }, [sites]);
  async function startBuild(url) {
    try {
      const res = await window.API.addSite(url);
      setBuildId(res.id);
      nav('building');
    } catch (ex) {
      ping(ex.message || 'Не удалось создать сайт');
    }
  }
  async function finishBuild() {
    await loadSites();
    nav('sites');
    ping('Сайт готов! Пробный период 7 дней');
  }
  function openPay(site) {
    setPayTarget(site);
    nav('payment');
  }
  function confirmPaid() {
    nav('payment-success');
    loadSites();
  }
  async function deleteSite(site) {
    try {
      await window.API.deleteSite(site.id);
    } catch (e) {}
    setSites(prev => prev.filter(s => s.id !== site.id));
    setMenuSite(null);
    ping('Сайт удалён');
  }
  async function submitTicket(subj, body) {
    try {
      await window.API.submitTicket(subj, body);
      setTickets(prev => [{
        subj,
        body,
        status: 'open',
        date: new Date().toLocaleDateString('ru-RU')
      }, ...prev]);
      ping('Обращение отправлено');
    } catch (ex) {
      ping(ex.message || 'Не удалось отправить');
    }
  }
  async function logout() {
    try {
      await window.API.logout();
    } catch (e) {}
    setEmail('');
    setSites([]);
    setScreen('login');
  }
  async function deleteAccount() {
    try {
      await window.API.deleteAccount();
    } catch (e) {}
    setConfirmDel(false);
    setEmail('');
    setScreen('login');
    ping('Аккаунт удалён');
  }
  if (!booted) {
    return /*#__PURE__*/_jsxDEV("div", {
      className: "app",
      children: /*#__PURE__*/_jsxDEV("div", {
        className: "screen",
        children: /*#__PURE__*/_jsxDEV("div", {
          className: "notice",
          children: /*#__PURE__*/_jsxDEV("div", {
            className: "notice__box",
            children: /*#__PURE__*/_jsxDEV("div", {
              className: "spin"
            }, void 0, false)
          }, void 0, false)
        }, void 0, false)
      }, void 0, false)
    }, void 0, false);
  }

  // ---------- AUTH / standalone screens ----------
  if (!CABINET.has(screen)) {
    let inner = null;
    if (screen === 'login') inner = /*#__PURE__*/_jsxDEV(ScreenLogin, {
      nav: nav,
      ctx: ctx
    }, void 0, false);else if (screen === 'register') inner = /*#__PURE__*/_jsxDEV(ScreenRegister, {
      nav: nav,
      ctx: ctx
    }, void 0, false);else if (screen === 'register-sent') inner = /*#__PURE__*/_jsxDEV(ScreenRegisterSent, {
      nav: nav,
      ctx: ctx
    }, void 0, false);else if (screen === 'confirm-email') inner = /*#__PURE__*/_jsxDEV(ScreenConfirmEmail, {
      nav: nav,
      ctx: ctx
    }, void 0, false);else if (screen === 'forgot') inner = /*#__PURE__*/_jsxDEV(ScreenForgot, {
      nav: nav,
      ctx: ctx
    }, void 0, false);else if (screen === 'forgot-sent') inner = /*#__PURE__*/_jsxDEV(ScreenForgotSent, {
      nav: nav,
      ctx: ctx
    }, void 0, false);else if (screen === 'reset') inner = /*#__PURE__*/_jsxDEV(ScreenReset, {
      nav: nav,
      ctx: ctx
    }, void 0, false);else if (screen === 'yukassa') inner = /*#__PURE__*/_jsxDEV(ScreenYukassa, {
      nav: nav
    }, void 0, false);else if (screen === 'payment-processing') inner = /*#__PURE__*/_jsxDEV(ScreenPaymentProcessing, {
      onConfirmed: confirmPaid
    }, void 0, false);else if (screen === 'payment-success') inner = /*#__PURE__*/_jsxDEV(ScreenPaymentSuccess, {
      nav: nav,
      site: payTarget
    }, void 0, false);
    return /*#__PURE__*/_jsxDEV("div", {
      className: "app",
      children: [inner, toast && /*#__PURE__*/_jsxDEV("div", {
        className: "toast",
        children: [/*#__PURE__*/_jsxDEV("i", {
          "data-lucide": "check-circle"
        }, void 0, false), toast]
      }, void 0, true)]
    }, void 0, true);
  }

  // ---------- CABINET ----------
  const [title, sub] = TITLES[screen] || ['', null];
  const section = SECTION_OF[screen] || 'sites';
  let body = null;
  if (screen === 'sites') body = /*#__PURE__*/_jsxDEV(ScreenSites, {
    nav: nav,
    sites: sites,
    onPay: openPay,
    onMenu: setMenuSite,
    canAdd: canAdd
  }, void 0, false);else if (screen === 'add-site') body = /*#__PURE__*/_jsxDEV(ScreenAddSite, {
    nav: nav,
    onStartBuild: startBuild
  }, void 0, false);else if (screen === 'building') body = /*#__PURE__*/_jsxDEV(ScreenBuilding, {
    onDone: finishBuild,
    buildId: buildId
  }, void 0, false);else if (screen === 'payment') body = /*#__PURE__*/_jsxDEV(ScreenPayment, {
    nav: nav,
    site: payTarget
  }, void 0, false);else if (screen === 'admin') body = /*#__PURE__*/_jsxDEV(AdminStub, {
    nav: nav,
    site: payTarget
  }, void 0, false);else if (screen === 'subscriptions') body = /*#__PURE__*/_jsxDEV(ScreenSubscriptions, {
    nav: nav,
    sites: sites,
    payments: payments,
    onPay: openPay
  }, void 0, false);else if (screen === 'support') body = /*#__PURE__*/_jsxDEV(ScreenSupport, {
    email: email,
    tickets: tickets,
    onSubmit: submitTicket
  }, void 0, false);else if (screen === 'settings') body = /*#__PURE__*/_jsxDEV(ScreenSettings, {
    email: email,
    onDelete: () => setConfirmDel(true)
  }, void 0, false);
  return /*#__PURE__*/_jsxDEV("div", {
    className: "app",
    children: /*#__PURE__*/_jsxDEV("div", {
      className: "screen",
      children: [/*#__PURE__*/_jsxDEV("div", {
        className: "shell",
        children: [/*#__PURE__*/_jsxDEV("aside", {
          className: "side",
          children: [/*#__PURE__*/_jsxDEV("a", {
            className: "logo side__brand",
            onClick: () => nav('sites'),
            style: {
              cursor: 'pointer'
            },
            children: [/*#__PURE__*/_jsxDEV("img", {
              src: "/static/lk/assets/seal-192.png",
              alt: ""
            }, void 0, false), "uqqi", /*#__PURE__*/_jsxDEV("span", {
              className: "dot",
              children: ".ru"
            }, void 0, false)]
          }, void 0, true), NAV.map(n => /*#__PURE__*/_jsxDEV("a", {
            className: 'nav-i' + (section === n.id ? ' on' : ''),
            onClick: () => nav(n.id),
            children: [/*#__PURE__*/_jsxDEV("i", {
              "data-lucide": n.ic
            }, void 0, false), n.label]
          }, n.id, true)), /*#__PURE__*/_jsxDEV("div", {
            className: "side__foot",
            children: [/*#__PURE__*/_jsxDEV("div", {
              className: "usercard",
              children: [/*#__PURE__*/_jsxDEV("div", {
                className: "av",
                children: email[0].toUpperCase()
              }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
                style: {
                  minWidth: 0
                },
                children: /*#__PURE__*/_jsxDEV("div", {
                  className: "em",
                  children: email
                }, void 0, false)
              }, void 0, false)]
            }, void 0, true), /*#__PURE__*/_jsxDEV("a", {
              className: "nav-i",
              onClick: logout,
              style: {
                marginTop: '.2rem'
              },
              children: [/*#__PURE__*/_jsxDEV("i", {
                "data-lucide": "log-out"
              }, void 0, false), "Выйти"]
            }, void 0, true)]
          }, void 0, true)]
        }, void 0, true), /*#__PURE__*/_jsxDEV("section", {
          className: "main",
          children: [/*#__PURE__*/_jsxDEV("header", {
            className: "topbar",
            children: [/*#__PURE__*/_jsxDEV("a", {
              className: "logo",
              onClick: () => nav('sites'),
              style: {
                cursor: 'pointer'
              },
              children: [/*#__PURE__*/_jsxDEV("img", {
                src: "/static/lk/assets/seal-192.png",
                alt: ""
              }, void 0, false), "uqqi", /*#__PURE__*/_jsxDEV("span", {
                className: "dot",
                children: ".ru"
              }, void 0, false)]
            }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
              className: "topbar__r",
              children: [/*#__PURE__*/_jsxDEV("span", {
                className: "tag",
                style: {
                  maxWidth: 150,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                },
                children: email
              }, void 0, false), /*#__PURE__*/_jsxDEV("button", {
                className: "iconbtn",
                onClick: logout,
                title: "Выйти",
                children: /*#__PURE__*/_jsxDEV("i", {
                  "data-lucide": "log-out"
                }, void 0, false)
              }, void 0, false)]
            }, void 0, true)]
          }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
            className: "main__head",
            children: [/*#__PURE__*/_jsxDEV("div", {
              children: [/*#__PURE__*/_jsxDEV("div", {
                className: "h",
                children: title
              }, void 0, false), sub && /*#__PURE__*/_jsxDEV("div", {
                className: "sub",
                children: sub
              }, void 0, false)]
            }, void 0, true), screen === 'sites' && canAdd && /*#__PURE__*/_jsxDEV("button", {
              className: "btn btn--primary btn--sm",
              onClick: () => nav('add-site'),
              children: [/*#__PURE__*/_jsxDEV("i", {
                "data-lucide": "plus"
              }, void 0, false), " Добавить сайт"]
            }, void 0, true)]
          }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
            className: "main__body fade-enter",
            children: body
          }, screen, false), /*#__PURE__*/_jsxDEV("nav", {
            className: "bottomnav",
            children: NAV.map(n => /*#__PURE__*/_jsxDEV("a", {
              className: section === n.id ? 'on' : '',
              onClick: () => nav(n.id),
              children: [/*#__PURE__*/_jsxDEV("i", {
                "data-lucide": n.ic
              }, void 0, false), n.label.split(' ')[0]]
            }, n.id, true))
          }, void 0, false)]
        }, void 0, true)]
      }, void 0, true), menuSite && /*#__PURE__*/_jsxDEV("div", {
        className: "scrim",
        onClick: () => setMenuSite(null),
        children: /*#__PURE__*/_jsxDEV("div", {
          className: "modal",
          onClick: e => e.stopPropagation(),
          children: [/*#__PURE__*/_jsxDEV("h3", {
            children: menuSite.name
          }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
            children: [menuSite.slug, ".uqqi.ru"]
          }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
            style: {
              display: 'flex',
              flexDirection: 'column',
              gap: '.6rem',
              marginTop: '1.3rem'
            },
            children: [/*#__PURE__*/_jsxDEV("a", {
              className: "btn btn--ghost btn--block",
              href: '/site/' + menuSite.slug + '/edit',
              children: [/*#__PURE__*/_jsxDEV("i", {
                "data-lucide": "pencil"
              }, void 0, false), " Редактировать контент"]
            }, void 0, true), /*#__PURE__*/_jsxDEV("button", {
              className: "btn btn--danger btn--block",
              onClick: () => deleteSite(menuSite),
              children: [/*#__PURE__*/_jsxDEV("i", {
                "data-lucide": "trash-2"
              }, void 0, false), " Удалить сайт"]
            }, void 0, true)]
          }, void 0, true)]
        }, void 0, true)
      }, void 0, false), confirmDel && /*#__PURE__*/_jsxDEV("div", {
        className: "scrim",
        onClick: () => setConfirmDel(false),
        children: /*#__PURE__*/_jsxDEV("div", {
          className: "modal",
          onClick: e => e.stopPropagation(),
          children: [/*#__PURE__*/_jsxDEV("h3", {
            children: "Удалить аккаунт?"
          }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
            children: "Это действие необратимо. Все сайты будут отключены, а данные удалены навсегда."
          }, void 0, false), /*#__PURE__*/_jsxDEV("div", {
            className: "modal__actions",
            children: [/*#__PURE__*/_jsxDEV("button", {
              className: "btn btn--ghost btn--block",
              onClick: () => setConfirmDel(false),
              children: "Отмена"
            }, void 0, false), /*#__PURE__*/_jsxDEV("button", {
              className: "btn btn--danger btn--block",
              onClick: deleteAccount,
              children: "Удалить"
            }, void 0, false)]
          }, void 0, true)]
        }, void 0, true)
      }, void 0, false), toast && /*#__PURE__*/_jsxDEV("div", {
        className: "toast",
        children: [/*#__PURE__*/_jsxDEV("i", {
          "data-lucide": "check-circle"
        }, void 0, false), toast]
      }, void 0, true)]
    }, void 0, true)
  }, void 0, false);
}
function AdminStub({
  nav
}) {
  return /*#__PURE__*/_jsxDEV("div", {
    className: "wrap-md",
    children: [/*#__PURE__*/_jsxDEV("a", {
      className: "linklike",
      style: {
        fontSize: '.84rem',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '.3rem',
        marginBottom: '1.2rem'
      },
      onClick: () => nav('sites'),
      children: [/*#__PURE__*/_jsxDEV("i", {
        "data-lucide": "arrow-left",
        style: {
          width: 15,
          height: 15
        }
      }, void 0, false), " Мои сайты"]
    }, void 0, true), /*#__PURE__*/_jsxDEV("div", {
      className: "card",
      style: {
        padding: '2.2rem 1.8rem',
        textAlign: 'center'
      },
      children: [/*#__PURE__*/_jsxDEV("div", {
        className: "empty__ic",
        style: {
          margin: '0 auto 1rem'
        },
        children: /*#__PURE__*/_jsxDEV("i", {
          "data-lucide": "pencil-ruler"
        }, void 0, false)
      }, void 0, false), /*#__PURE__*/_jsxDEV("h2", {
        style: {
          fontFamily: 'var(--font-display)',
          fontWeight: 700,
          fontSize: '1.3rem',
          letterSpacing: '-.02em',
          color: 'var(--ink)'
        },
        children: "Редактор контента сайта"
      }, void 0, false), /*#__PURE__*/_jsxDEV("p", {
        className: "muted",
        style: {
          fontSize: '.9rem',
          lineHeight: 1.65,
          marginTop: '.5rem',
          maxWidth: 380,
          marginInline: 'auto'
        },
        children: "Здесь владелец меняет тексты, фото, часы работы и услуги — без программиста. Отдельная админка контента."
      }, void 0, false)]
    }, void 0, true)]
  }, void 0, true);
}
ReactDOM.createRoot(document.getElementById('root')).render(/*#__PURE__*/_jsxDEV(App, {}, void 0, false));
