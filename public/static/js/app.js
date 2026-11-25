// Shared client helpers
(function () {
  const toastEl = document.getElementById('toast');
  window.toast = function (msg) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add('is-on');
    clearTimeout(window.__toastT);
    window.__toastT = setTimeout(() => toastEl.classList.remove('is-on'), 2200);
  };
  window.csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';

  // Password visibility: hidden by default with an open eye; click → text shown + closed eye
  document.querySelectorAll('[data-toggle-password]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const input = document.getElementById(btn.dataset.togglePassword);
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.setAttribute('aria-pressed', show);
      const label = show ? 'Sembunyikan kata sandi' : 'Tampilkan kata sandi';
      btn.setAttribute('aria-label', label); btn.title = label;
    });
  });

  // Custom file buttons: show the chosen file name + a preview
  document.querySelectorAll('[data-file]').forEach((input) => input.addEventListener('change', () => {
    const box = input.closest('.upload');
    const file = input.files[0];
    box.querySelector('[data-file-name]').textContent = file ? file.name : 'Belum ada file dipilih';
    const prev = box.querySelector('[data-file-preview]');
    if (file && prev && file.type.startsWith('image/')) {
      const img = document.createElement('img');
      img.className = 'media-img ph--round'; img.alt = 'Pratinjau foto'; img.dataset.filePreview = '';
      img.src = URL.createObjectURL(file);
      prev.replaceWith(img);
    }
  }));

  // Floating "current page" label under the navbar steps aside once the page scrolls (still shows on hover)
  const nav = document.querySelector('.nav');
  if (nav) {
    const onScroll = () => nav.classList.toggle('is-scrolled', window.scrollY > 8);
    window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
  }

  // Generic modal open/close
  document.querySelectorAll('[data-open]').forEach((b) => b.addEventListener('click', () => document.getElementById(b.dataset.open)?.classList.add('is-open')));
  document.querySelectorAll('[data-close]').forEach((b) => b.addEventListener('click', () => b.closest('.modal')?.classList.remove('is-open')));
  document.querySelectorAll('.modal').forEach((m) => m.addEventListener('click', (e) => { if (e.target === m) m.classList.remove('is-open'); }));
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') document.querySelectorAll('.modal.is-open').forEach((m) => m.classList.remove('is-open')); });
})();
