(function () {
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];

  // Bookmark toggle (progressive: falls back to nothing if JS is off; buttons are JS-only)
  $$('[data-bookmark]').forEach((btn) => btn.addEventListener('click', async (e) => {
    e.preventDefault(); e.stopPropagation();
    const res = await fetch(`/resep/${btn.dataset.bookmark}/simpan`, { method: 'POST', headers: { 'x-csrf-token': window.csrf, accept: 'application/json' } });
    if (!res.ok) return window.toast('Gagal menyimpan resep');
    const { bookmarked } = await res.json();
    $$(`[data-bookmark="${btn.dataset.bookmark}"]`).forEach((b) => {
      b.setAttribute('aria-pressed', bookmarked);
      b.querySelector('svg').setAttribute('fill', bookmarked ? 'currentColor' : 'none');
    });
    window.toast(bookmarked ? 'Resep disimpan' : 'Dihapus dari tersimpan');
  }));

  // Tabs
  $$('[data-tabs]').forEach((root) => {
    const tabs = $$('[data-tab]', root);
    tabs.forEach((t) => t.addEventListener('click', () => {
      tabs.forEach((x) => { x.classList.toggle('is-active', x === t); x.setAttribute('aria-selected', x === t); });
      $$('[data-panel]', root).forEach((p) => { p.hidden = p.dataset.panel !== t.dataset.tab; });
    }));
  });

  // Adjust Portion
  const fmt = (q) => {
    const whole = Math.floor(q); const frac = q - whole;
    const map = [[0.25, '1/4'], [0.33, '1/3'], [0.5, '1/2'], [0.67, '2/3'], [0.75, '3/4']];
    if (frac < 0.04) return String(whole);
    const hit = map.find(([v]) => Math.abs(frac - v) < 0.04);
    if (hit) return whole ? `${whole} ${hit[1]}` : hit[1];
    return String(Math.round(q * 10) / 10);
  };
  const portion = $('[data-portion]');
  let servings = portion ? Number(portion.dataset.base) : 1;
  function renderAmounts() {
    const base = Number(portion.dataset.base);
    $('[data-portion-value]').textContent = servings;
    $$('[data-ing]').forEach((el) => {
      const q = el.dataset.qty;
      $('[data-amount]', el).textContent = q === '' ? (el.dataset.note || 'Secukupnya') : `${fmt((Number(q) * servings) / base)} ${el.dataset.unit}`.trim();
    });
  }
  $$('[data-portion-step]').forEach((b) => b.addEventListener('click', () => {
    servings = Math.min(50, Math.max(1, servings + Number(b.dataset.portionStep)));
    renderAmounts();
  }));

  // Copy Ingredient List
  $$('[data-copy-list]').forEach((b) => b.addEventListener('click', async () => {
    const lines = $$('[data-ing]').map((el) => `- ${el.dataset.name}: ${$('[data-amount]', el).textContent}`);
    const text = `${b.dataset.title} (${servings} porsi)\n${lines.join('\n')}`;
    try { await navigator.clipboard.writeText(text); window.toast('Daftar bahan disalin'); }
    catch { window.prompt('Salin daftar bahan:', text); }
  }));

  // Cook mode: tick off ingredients
  $$('.cook-ing').forEach((b) => b.addEventListener('click', () => {
    const done = b.classList.toggle('is-done');
    b.setAttribute('aria-pressed', done);
  }));

  // Cook mode: stepper
  const stepper = $('[data-stepper]');
  if (stepper) {
    const total = Number(stepper.dataset.total);
    let cur = 0;
    const show = () => {
      $$('[data-step]', stepper).forEach((s) => { s.hidden = Number(s.dataset.step) !== cur; });
      $$('[data-bar]', stepper).forEach((bar) => {
        const i = Number(bar.dataset.bar);
        bar.className = i < cur ? 'is-done' : i === cur ? 'is-current' : '';
      });
      $('[data-step-num]', stepper).textContent = cur + 1;
      $('[data-step-prev]', stepper).disabled = cur === 0;
      $('[data-next-label]', stepper).textContent = cur === total - 1 ? 'Selesai' : 'Berikut';
    };
    $('[data-step-prev]', stepper).addEventListener('click', () => { if (cur > 0) { cur -= 1; show(); } });
    $('[data-step-next]', stepper).addEventListener('click', () => {
      if (cur < total - 1) { cur += 1; show(); } else { window.toast('Selamat menikmati! Jangan lupa beri ulasan.'); setTimeout(() => { location.href = location.pathname.replace('/masak', '#ulasan'); }, 1200); }
    });
    document.addEventListener('keydown', (e) => {
      if (stepper.closest('[data-panel]').hidden) return;
      if (e.key === 'ArrowRight') $('[data-step-next]', stepper).click();
      if (e.key === 'ArrowLeft') $('[data-step-prev]', stepper).click();
    });
    $$('[data-expand]').forEach((b) => b.addEventListener('click', () => {
      const modal = $('#media-modal');
      $('[data-modal-slot]', modal).innerHTML = $(`[data-media-src="${b.dataset.expand}"]`).innerHTML;
      modal.classList.add('is-open');
    }));
    show();
  }
})();
