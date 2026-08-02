/* ─── uqqi.ru — поведение витрин A/B/C на реальных данных ─── */
(function(){
  const D = window.UQQI;
  const $ = s => document.querySelector(s);
  const $$ = s => [...document.querySelectorAll(s)];

  function icons(){ if(window.lucide) lucide.createIcons(); }

  const PH_GRADIENTS = [
    'linear-gradient(135deg,#E8B98F,#C8643C)',
    'linear-gradient(135deg,#B97FA6,#7E5374)',
    'linear-gradient(135deg,#7FA98F,#4E7A5E)',
    'linear-gradient(135deg,#C8A96E,#9A7B3E)',
    'linear-gradient(135deg,#8FA9C8,#3E5E7A)',
    'linear-gradient(135deg,#C89A9A,#7A4E4E)',
  ];
  function phGradient(i){ return PH_GRADIENTS[i % PH_GRADIENTS.length]; }
  function bgStyle(url, idx){
    if(url) return `background-image:url('${url}');background-size:cover;background-position:center`;
    return `background:${phGradient(idx||0)}`;
  }

  /* ── CATALOG ── */
  const PER = 8;
  let curCat = "all", page = 1;
  function cats(){ return ["all", ...new Set(D.services.map(s=>s.cat).filter(Boolean))]; }
  function visible(){ return D.services.filter(s=> curCat==="all" || s.cat===curCat); }

  function renderFilters(){
    const el = $("#catFilters"); if(!el) return;
    const list = cats();
    if(list.length <= 1){ el.innerHTML=''; return; }
    el.innerHTML = list.map(c=>
      `<button class="chip${c===curCat?' active':''}" data-cat="${c}">${c==="all"?"Все":c}</button>`).join("");
    $$("#catFilters .chip").forEach(b=>b.onclick=()=>{curCat=b.dataset.cat;page=1;renderCatalog();});
  }

  function renderCatalog(){
    const grid = $("#catalogGrid"); if(!grid) return;
    const layout = grid.dataset.layout || "cards";
    renderFilters();
    const items = visible();

    if(layout==="list"){
      const pagesL = Math.ceil(items.length/PER) || 1;
      page = Math.min(page, pagesL);
      const sliceL = items.slice((page-1)*PER, page*PER);
      grid.innerHTML = sliceL.map(s=>{
        const idx = D.services.indexOf(s);
        return `<div class="svc-row" data-i="${idx}">
          <div class="svc-row__main">
            <div class="svc-row__name">${s.name}</div>
            ${s.desc?`<div class="svc-row__desc">${s.desc}</div>`:''}
          </div>
          <div class="svc-row__dots"></div>
          <div class="svc-row__price">${s.price}</div>
        </div>`;
      }).join("");
      $$("#catalogGrid .svc-row").forEach(r=>r.onclick=()=>openPm(+r.dataset.i));
      renderPagination(pagesL);
      return;
    }

    const pages = Math.ceil(items.length/PER) || 1;
    page = Math.min(page, pages);
    const slice = items.slice((page-1)*PER, page*PER);
    grid.innerHTML = slice.map(s=>{
      const idx = D.services.indexOf(s);
      return `<div class="svc" data-i="${idx}">
        <div class="svc__img ph" style="${bgStyle(s.img, idx)}"></div>
        <div class="svc__body">
          <div class="svc__name">${s.name}</div>
          ${s.desc?`<div class="svc__desc">${s.desc}</div>`:''}
          <div class="svc__foot">
            <div class="svc__price">${s.price}</div>
            <span class="svc__pick">Выбрать <i data-lucide="arrow-right"></i></span>
          </div>
        </div></div>`;
    }).join("");
    $$("#catalogGrid .svc").forEach(c=>c.onclick=()=>openPm(+c.dataset.i));
    renderPagination(pages);
    icons();
  }

  function renderPagination(pages){
    const pg=$("#pagination"); if(!pg) return;
    if(pages<=1){pg.innerHTML="";return;}
    let h=`<button class="page-btn arrow" ${page===1?'disabled':''} data-p="${page-1}">‹</button>`;
    if(pages<=7){
      for(let i=1;i<=pages;i++) h+=`<button class="page-btn${i===page?' active':''}" data-p="${i}">${i}</button>`;
    } else {
      h+=`<button class="page-btn${1===page?' active':''}" data-p="1">1</button>`;
      if(page>3) h+=`<span class="page-ellipsis">…</span>`;
      for(let i=Math.max(2,page-1);i<=Math.min(pages-1,page+1);i++)
        h+=`<button class="page-btn${i===page?' active':''}" data-p="${i}">${i}</button>`;
      if(page<pages-2) h+=`<span class="page-ellipsis">…</span>`;
      h+=`<button class="page-btn${pages===page?' active':''}" data-p="${pages}">${pages}</button>`;
    }
    h+=`<button class="page-btn arrow" ${page===pages?'disabled':''} data-p="${page+1}">›</button>`;
    pg.innerHTML=h;
    $$("#pagination .page-btn").forEach(b=>{ if(!b.disabled) b.onclick=()=>{page=+b.dataset.p;renderCatalog();const c=$('#catalog');if(c)window.scrollTo({top:c.offsetTop-60,behavior:'smooth'});}; });
  }

  /* ── GALLERY ── */
  function renderGallery(){
    const g=$("#gallery"); if(!g) return;
    g.innerHTML = D.gallery.map((url,i)=>`<div class="g ph" style="${bgStyle(url,i)}" onclick="openLb(${i})"></div>`).join("");
  }

  /* ── REVIEWS ── */
  function reviewCard(r){
    const avatar = r.av && r.av.startsWith('http')
      ? `<div class="review__av" style="background-image:url('${r.av}');background-size:cover"></div>`
      : `<div class="review__av" style="background:${r.av||'#888'}">${r.name[0]||'?'}</div>`;
    return `<div class="review">
      <div class="review__hdr">
        ${avatar}
        <div>
          <div class="review__name">${r.name}</div>
          <div class="review__sub"><span class="review__stars">${"★".repeat(r.stars)}${"☆".repeat(5-r.stars)}</span><span class="review__date">${r.date}</span></div>
        </div>
      </div>
      <p class="review__text">${r.text}</p>
    </div>`;
  }
  // Перетаскивание горизонтального рельса мышью (тач скроллит нативно).
  function enableDragScroll(el){
    if(!el) return;
    let down=false, startX=0, startLeft=0, moved=false;
    el.style.cursor='grab';
    el.addEventListener('pointerdown', e=>{
      if(e.pointerType!=='mouse') return;
      down=true; moved=false; startX=e.clientX; startLeft=el.scrollLeft;
      el.style.cursor='grabbing'; el.style.scrollSnapType='none';
      try{ el.setPointerCapture(e.pointerId); }catch(_){}
    });
    el.addEventListener('pointermove', e=>{
      if(!down) return;
      const dx=e.clientX-startX;
      if(Math.abs(dx)>3) moved=true;
      el.scrollLeft=startLeft-dx;
    });
    function end(){ if(!down) return; down=false; el.style.cursor='grab'; el.style.scrollSnapType=''; }
    el.addEventListener('pointerup', end);
    el.addEventListener('pointercancel', end);
    // клик по карточке/ссылке не срабатывает, если это был драг
    el.addEventListener('click', e=>{ if(moved){ e.preventDefault(); e.stopPropagation(); } }, true);
  }
  function renderReviews(){
    const rail=$("#reviews-rail");
    if(rail){ rail.innerHTML=D.reviews.map(reviewCard).join(""); enableDragScroll(rail); }
    const grid=$("#reviews-grid");
    if(grid){
      grid.innerHTML=D.reviews.map((r,i)=>{
        const inner = reviewCard(r).replace(/^<div class="review">/,'').replace(/<\/div>\s*$/,'');
        return `<div class="review${i>=4?' rev-hidden':''}">${inner}</div>`;
      }).join("");
      const moreBtn = $("#revMoreBtn");
      if(moreBtn && D.reviews.length<=4) moreBtn.style.display='none';
    }
  }
  window.showMoreReviews=function(btn){
    $$("#reviews-grid .rev-hidden").slice(0,4).forEach(c=>c.classList.remove('rev-hidden'));
    const remaining = $$("#reviews-grid .rev-hidden").length;
    if(remaining===0 && btn){
      btn.style.display='none';
      const link=$("#allReviewsLink"); if(link) link.style.display='inline-flex';
    }
  };

  /* ── HOURS ── */
  const dayIdx = new Date().getDay();
  function markToday(){
    $$('[id^="hoursTable"] tr[data-d]').forEach(tr=>{ if(+tr.dataset.d===dayIdx) tr.classList.add('today'); });
    $$('.hours-table tr[data-d]').forEach(tr=>{ if(+tr.dataset.d===dayIdx) tr.classList.add('today'); });
  }
  window.toggleHours=function(){
    const t=$("#hoursToggle"), p=$("#hoursPanel");
    if(t) t.classList.toggle('open');
    if(p) p.classList.toggle('open');
  };

  /* ── PHONE ── */
  window.showPhone=function(btn){
    const span=btn.querySelector('span');
    if(span) span.textContent=btn.dataset.phone;
    btn.onclick=()=>location.href='tel:'+btn.dataset.tel;
  };

  /* ── НАПИСАТЬ ── */
  window.toggleWrite=function(e){
    if(e) e.stopPropagation();
    const m=$("#writeMenu"); if(m) m.classList.toggle('open');
  };
  document.addEventListener('click', e=>{
    const dd=$("#writeDropdown"), m=$("#writeMenu");
    if(m && dd && !dd.contains(e.target)) m.classList.remove('open');
  });

  /* ── LIGHTBOX ── */
  let lbI=0;
  window.openLb=function(i){
    const lb=$("#lb"); if(!lb || !D.gallery.length) return;
    lbI=i; updateLb(); lb.classList.add('open'); document.body.style.overflow='hidden';
  };
  window.closeLb=function(){ const lb=$("#lb"); if(lb){lb.classList.remove('open');document.body.style.overflow='';} };
  window.lbGo=function(d){ lbI=(lbI+d+D.gallery.length)%D.gallery.length; updateLb(); };
  function updateLb(){
    const img=$("#lbImg"); if(!img) return;
    const url=D.gallery[lbI];
    img.style.cssText = (url?`background-image:url('${url}')`:`background:${phGradient(lbI)}`) + ';background-size:contain;background-repeat:no-repeat;background-position:center';
    const c=$("#lbCnt"); if(c) c.textContent=`${lbI+1} / ${D.gallery.length}`;
  }

  /* ── PRODUCT MODAL ── */
  window.openPm=function(i){
    const s=D.services[i], pm=$("#pm"); if(!pm) return;
    const img=$("#pmImg");
    if(img) img.style.cssText = bgStyle(s.img, i);
    const setT=(id,v)=>{ const el=$(id); if(el) el.textContent=v; };
    setT("#pmCat", s.cat||'');
    setT("#pmName", s.name);
    setT("#pmPrice", s.price||'');
    setT("#pmDesc", s.desc||'');
    const descWrap=$("#pmDescWrap");
    if(descWrap) descWrap.style.display = s.desc ? '' : 'none';
    pm.classList.add('open'); document.body.style.overflow='hidden'; icons();
  };
  window.closePm=function(){ const pm=$("#pm"); if(pm){pm.classList.remove('open');document.body.style.overflow='';} };

  /* ── ACTIONS ── */
  window.book=function(){
    if(D.bookUrl) window.open(D.bookUrl,'_blank');
    else if(D.yandexUrl) window.open(D.yandexUrl,'_blank');
  };
  window.route=function(){
    if(D.routeUrl) window.open(D.routeUrl,'_blank');
    else if(D.yandexUrl) window.open(D.yandexUrl,'_blank');
  };
  window.goTo=function(sel){ const el=$(sel); if(el) window.scrollTo({top:el.getBoundingClientRect().top+window.scrollY-70,behavior:'smooth'}); };
  window.scrollRail=function(sel,dir){ const r=$(sel); if(!r) return; const card=r.querySelector('.review'); const step=card?card.offsetWidth+16:340; r.scrollBy({left:dir*step,behavior:'smooth'}); };

  /* ── NAV + REVEAL ── */
  function navScroll(){
    const nav=$("#nav");
    if(nav) window.addEventListener('scroll',()=>nav.classList.toggle('scrolled',window.scrollY>40),{passive:true});
    const links=$$('.nav__links a[href^="#"], .tabs a[href^="#"]');
    const io=new IntersectionObserver(es=>es.forEach(e=>{ if(e.isIntersecting) links.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+e.target.id)); }),{threshold:.25,rootMargin:"-60px 0px -50% 0px"});
    links.forEach(a=>{const s=$(a.getAttribute('href')); if(s) io.observe(s);});

    /* Кнопка "Записаться" в navbar появляется, когда основная ушла за верх экрана */
    const navBook=$("#navBook"), mainBook=$("#mainBook");
    if(navBook && mainBook){
      const bio=new IntersectionObserver(es=>es.forEach(e=>{
        navBook.style.display = e.isIntersecting ? 'none' : 'inline-flex';
      }),{rootMargin:"-60px 0px 0px 0px"});
      bio.observe(mainBook);
    }
  }
  function reveal(){
    const io=new IntersectionObserver(es=>es.forEach(e=>{ if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);} }),{threshold:.08});
    $$('.reveal').forEach(el=>io.observe(el));
  }

  /* ── KEYS ── */
  document.addEventListener('keydown',e=>{
    if($("#lb")?.classList.contains('open')){ if(e.key==='Escape')closeLb(); if(e.key==='ArrowRight')lbGo(1); if(e.key==='ArrowLeft')lbGo(-1); }
    if(e.key==='Escape')closePm();
  });

  /* ── INIT ── */
  document.addEventListener('DOMContentLoaded',()=>{
    renderCatalog(); renderGallery(); renderReviews();
    markToday(); navScroll(); reveal(); icons();
  });
})();
