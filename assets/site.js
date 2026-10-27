(() => {
  const button = document.querySelector('#theme');
  let preference;
  try { preference = localStorage.getItem('blog-theme'); } catch {}
  if (preference) document.documentElement.dataset.theme = preference;
  button?.addEventListener('click', () => {
    const dark = document.documentElement.dataset.theme === 'dark' || (!document.documentElement.dataset.theme && matchMedia('(prefers-color-scheme: dark)').matches);
    const next = dark ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('blog-theme', next); } catch {}
  });
  const cards = [...document.querySelectorAll('.entry')];
  const search = document.querySelector('#search');
  const filters = [...document.querySelectorAll('[data-filter]')];
  let filter = 'all';
  const normalize = s => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const update = () => {
    const query = normalize(search?.value.trim() || '');
    let count = 0;
    cards.forEach(card => {
      const show = (filter === 'all' || card.dataset.category === filter) && normalize(card.dataset.search).includes(query);
      card.hidden = !show;
      if (show) count++;
    });
    const empty = document.querySelector('#no-results');
    if (empty) empty.hidden = count > 0 || !cards.length;
  };
  filters.forEach(button => button.addEventListener('click', () => {
    filter = button.dataset.filter;
    filters.forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    update();
  }));
  search?.addEventListener('input', update);
})();
