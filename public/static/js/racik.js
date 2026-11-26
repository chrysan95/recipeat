// Racik: ingredient picker + Keranjang drawer. The basket lives in localStorage so it survives navigation
(function () {
  const KEY = 'recipeat.basket';
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch { return {}; } };
  const save = (b) => { try { localStorage.setItem(KEY, JSON.stringify(b)); } catch { /* private mode */ } };
  let basket = load();
  const drawer = $('#basket');
  const isResults = drawer?.dataset.mode === 'results';

  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const initials = (n) => n.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join('');
  const media = (i) => (i.img
    ? `<img class="media-img ph--round" src="${esc(i.img)}" alt="${esc(i.name)}" data-short="${esc(initials(i.name))}" referrerpolicy="no-referrer" onerror="phFallback(this)">`
    : `<div class="ph ph--round" role="img" aria-label="${esc(i.name)}"><span>${esc(initials(i.name))}</span></div>`);
  const closeIcon = '<svg class="icon" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>';

  function render() {
    const ids = Object.keys(basket);
    const label = ids.length ? `Keranjang (${ids.length})` : 'Keranjang';
    $$('[data-basket-label]').forEach((el) => { el.textContent = label; });
    $('[data-basket-empty]').hidden = ids.length > 0;
    $$('[data-pick]').forEach((b) => { const on = !!basket[b.dataset.pick]; b.classList.toggle('is-selected', on); b.setAttribute('aria-pressed', on); });
    if (isResults) return; // results-page basket is server-rendered from the URL
    $('[data-basket-grid]').innerHTML = ids.map((id) => `<div class="basket__item">${media(basket[id])}
      <button class="basket__rm" type="button" data-basket-remove="${esc(id)}" aria-label="Hapus ${esc(basket[id].name)}">${closeIcon}</button><span>${esc(basket[id].name)}</span></div>`).join('');
  }
  const bump = () => { $$('.basket-btn').forEach((b) => { b.classList.remove('is-bumped'); void b.offsetWidth; b.classList.add('is-bumped'); }); };

  // Results page: the URL is the source of truth (shareable link) → copy it into storage
  if (isResults) {
    basket = {};
    $$('[data-basket-grid] .basket__item').forEach((el) => { basket[el.dataset.id] = { name: el.dataset.name, img: el.dataset.img }; });
    save(basket);
  }

  // ?tambah=<id> from the home page quick-pick
  const add = new URLSearchParams(location.search).get('tambah');
  if (add) {
    const b = $(`[data-pick="${CSS.escape(add)}"]`);
    if (b) { basket[add] = { name: b.dataset.name, img: b.dataset.img }; save(basket); window.toast?.(`${b.dataset.name} masuk keranjang`); }
    const qs = new URLSearchParams(location.search); qs.delete('tambah');
    history.replaceState(null, '', location.pathname + (qs.toString() ? `?${qs}` : '') + location.hash);
  }

  // ---- Drawer ----
  const scrim = $('.drawer-scrim');
  let opener = null;
  function setDrawer(open) {
    if (!drawer) return;
    drawer.classList.toggle('is-open', open);
    scrim?.classList.toggle('is-open', open);
    document.body.classList.toggle('has-drawer', open);
    $$('[data-drawer-open]').forEach((b) => b.setAttribute('aria-expanded', open));
    if (open) { opener = document.activeElement; requestAnimationFrame(() => requestAnimationFrame(() => $('.drawer__close', drawer)?.focus())); } else { opener?.focus?.(); }
  }
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (drawer?.classList.contains('is-open')) setDrawer(false);
    closeMenu();
  });

  // ---- Category popover ----
  const menu = $('#cat-menu');
  const toggle = $('[data-cat-toggle]');
  function closeMenu() { menu?.classList.remove('is-open'); toggle?.setAttribute('aria-expanded', 'false'); }

  document.addEventListener('click', (e) => {
    if (e.target.closest('[data-drawer-open]')) { setDrawer(true); return; }
    if (e.target.closest('[data-drawer-close]')) { setDrawer(false); return; }

    const pick = e.target.closest('[data-pick]');
    if (pick) {
      const id = pick.dataset.pick;
      if (basket[id]) delete basket[id]; else { basket[id] = { name: pick.dataset.name, img: pick.dataset.img }; bump(); }
      save(basket); render(); return;
    }
    const rm = e.target.closest('[data-basket-remove]');
    if (rm) {
      delete basket[rm.dataset.basketRemove]; save(basket);
      if (isResults) { const ids = Object.keys(basket); location.href = ids.length ? `/racik/hasil?bahan=${ids.join(',')}` : '/racik'; return; }
      render(); return;
    }
    if (e.target.closest('[data-basket-clear]')) {
      basket = {}; save(basket);
      if (isResults) { location.href = '/racik'; return; }
      render(); return;
    }
    if (e.target.closest('[data-basket-search]')) {
      const ids = Object.keys(basket);
      if (!ids.length) { window.toast?.('Pilih minimal satu bahan dulu'); return; }
      location.href = `/racik/hasil?bahan=${ids.join(',')}`; return;
    }
    if (menu) {
      if (e.target.closest('[data-cat-toggle]')) { const open = menu.classList.toggle('is-open'); toggle.setAttribute('aria-expanded', open); }
      else if (!e.target.closest('#cat-menu')) closeMenu();
    }
  });

  // Keep the active category tab in view inside the horizontal slider
  $('.cat-tabs .is-active')?.scrollIntoView({ block: 'nearest', inline: 'center' });

  // Filter ingredient buttons by name (hides empty sections too)
  $('[data-ing-filter]')?.addEventListener('input', (e) => {
    const q = e.target.value.trim().toLowerCase();
    $$('[data-pick]').forEach((b) => { b.hidden = q && !b.dataset.name.toLowerCase().includes(q); });
    $$('.racik-section').forEach((s) => { s.hidden = q && !$$('[data-pick]', s).some((b) => !b.hidden); });
  });

  render();
})();
