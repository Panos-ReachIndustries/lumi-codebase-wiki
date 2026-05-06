// Shared client-side search across graph nodes + wiki pages.
// Uses Fuse.js (loaded as global by the host page).
(() => {
  const input = document.getElementById('search');
  const results = document.getElementById('search-results');
  if (!input || !results) return;

  let fuse = null;
  let items = [];

  Promise.all([
    fetch('data/graph.json').then(r => r.ok ? r.json() : { nodes: [] }).catch(() => ({ nodes: [] })),
    fetch('data/wiki-index.json').then(r => r.ok ? r.json() : { pages: [] }).catch(() => ({ pages: [] })),
  ]).then(([graph, wiki]) => {
    items = [
      ...graph.nodes.map(n => ({
        kind: 'node',
        title: n.label,
        subtitle: `${n.type} · ${n.repo}`,
        wiki: n.wiki,
        href: n.wiki ? `wiki.html?p=${encodeURIComponent(n.wiki)}` : `graph.html#${encodeURIComponent(n.id)}`,
        searchText: `${n.label} ${n.id} ${n.type} ${n.summary || ''}`,
      })),
      ...wiki.pages.map(p => ({
        kind: 'page',
        title: p.name,
        subtitle: `${p.type} · ${p.path.replace(/^wiki\//, '')}`,
        href: `wiki.html?p=${encodeURIComponent(p.path)}`,
        searchText: `${p.name} ${p.description} ${(p.tags || []).join(' ')}`,
      })),
    ];
    fuse = new Fuse(items, {
      keys: ['title', 'searchText'],
      threshold: 0.35,
      ignoreLocation: true,
      minMatchCharLength: 2,
    });
  });

  function render(matches) {
    if (!matches.length) {
      results.innerHTML = `<a><span style="color: var(--fg-muted)">No results.</span></a>`;
    } else {
      results.innerHTML = matches.slice(0, 10).map(m => {
        const it = m.item;
        const icon = it.kind === 'node' ? '◆' : '📄';
        return `<a href="${it.href}">${icon} ${escapeHtml(it.title)}<div class="meta">${escapeHtml(it.subtitle)}</div></a>`;
      }).join('');
    }
    results.classList.add('open');
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  input.addEventListener('input', () => {
    const q = input.value.trim();
    if (!q || !fuse) {
      results.classList.remove('open');
      return;
    }
    render(fuse.search(q));
  });

  input.addEventListener('focus', () => {
    if (input.value.trim() && fuse) render(fuse.search(input.value.trim()));
  });

  document.addEventListener('click', (e) => {
    if (!results.contains(e.target) && e.target !== input) {
      results.classList.remove('open');
    }
  });

  window.addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      input.focus();
      input.select();
    }
    if (e.key === 'Escape') results.classList.remove('open');
  });
})();
