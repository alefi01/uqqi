// ============================================================
// api.js — клиент REST API кабинета (заменяет моки)
// ============================================================
const API = {
  async _req(method, path, body) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch('/lk/api' + path, opts);
    let data = {};
    try { data = await res.json(); } catch (e) {}
    if (!res.ok) {
      throw new Error(data.detail || data.error || `Ошибка ${res.status}`);
    }
    return data;
  },

  // ── Авторизация ──
  register(email, password, agree, claim_code)  { return this._req('POST', '/register', { email, password, agree, claim_code: claim_code || '' }); },
  login(email, password)            { return this._req('POST', '/login', { email, password }); },
  logout()                          { return this._req('POST', '/logout'); },
  me()                              { return this._req('GET', '/me'); },
  forgot(email)                     { return this._req('POST', '/forgot', { email }); },
  reset(token, password)            { return this._req('POST', '/reset', { token, password }); },
  resendVerify(email)               { return this._req('POST', '/resend-verify', { email }); },

  // ── Сайты ──
  sites()                           { return this._req('GET', '/sites'); },
  addSite(url)                      { return this._req('POST', '/sites/add', { url }); },
  claimSite(code)                   { return this._req('POST', '/claim/' + encodeURIComponent(code)); },
  claimInfo(code)                   { return this._req('GET', '/claim/' + encodeURIComponent(code) + '/info'); },
  siteStatus(id)                    { return this._req('GET', '/sites/' + id + '/status'); },
  deleteSite(id)                    { return this._req('DELETE', '/sites/' + id); },
  cancelSubscription(id)            { return this._req('POST', '/sites/' + id + '/cancel'); },

  // ── Оплата ──
  createPayment(siteId)             { return this._req('POST', '/payment/create', { site_id: siteId }); },
  paymentStatus(paymentId)          { return this._req('GET', '/payment/' + paymentId + '/status'); },
  payments()                        { return this._req('GET', '/payments'); },

  // ── Поддержка ──
  tickets()                         { return this._req('GET', '/tickets'); },
  submitTicket(subject, message)    { return this._req('POST', '/tickets', { subject, message }); },

  // ── Настройки ──
  changePassword(current, next)     { return this._req('POST', '/account/password', { current, next }); },
  deleteAccount()                   { return this._req('DELETE', '/account'); },
};

window.API = API;
