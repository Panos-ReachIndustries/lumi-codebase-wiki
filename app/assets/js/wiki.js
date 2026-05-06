// Markdown reader for the Lumi Codebase Wiki.
// Reads ?p=wiki/some/path.md, fetches it, renders via marked, and renders
// a sidebar TOC built from app/data/wiki-index.json.
(() => {
  const tocEl = document.getElementById('toc');
  const contentEl = document.getElementById('content');

  const params = new URLSearchParams(location.search);
  let activePath = params.get('p') || 'wiki/overview.md';

  // Strip a leading ../ if someone passed a path relative to /app
  activePath = activePath.replace(/^\.\.\//, '');

  // Configure marked
  marked.setOptions({ breaks: false, gfm: true });

  // Custom renderer to rewrite links between wiki pages so they go through ?p=
  const renderer = new marked.Renderer();
  const baseRenderer = new marked.Renderer();
  renderer.link = function(token) {
    const href = token.href;
    const text = token.text || token.raw;
    if (!href) return text;
    if (href.startsWith('http://') || href.startsWith('https://')) {
      return `<a href="${href}" target="_blank" rel="noopener">${text}</a>`;
    }
    // resolve relative .md links against current page directory
    if (href.endsWith('.md') || href.includes('.md#')) {
      const [hPath, frag] = href.split('#');
      const resolved = resolvePath(activePath, hPath);
      const fragSuffix = frag ? `#${frag}` : '';
      return `<a href="?p=${encodeURIComponent(resolved)}${fragSuffix}">${text}</a>`;
    }
    if (href.startsWith('../') || href.startsWith('./')) {
      // non-md relative link (image, source code reference) — leave as-is, browser will fail gracefully
      return `<a href="${href}">${text}</a>`;
    }
    return `<a href="${href}">${text}</a>`;
  };
  // wikilinks: [[slug]]
  function transformWikilinks(md) {
    return md.replace(/\[\[([^\]]+)\]\]/g, (_, raw) => {
      const [slug, label] = raw.split('|');
      // best-effort: search index for a page whose path ends with /slug.md
      const target = (window.__wikiIndex || []).find(p =>
        p.path.endsWith(`/${slug}.md`) || p.path.endsWith(`${slug}.md`));
      const href = target ? `?p=${encodeURIComponent(target.path)}` : '#';
      return `[${label || slug}](${href})`;
    });
  }

  function resolvePath(from, rel) {
    if (rel.startsWith('/')) return rel.replace(/^\//, '');
    const base = from.split('/').slice(0, -1);
    rel.split('/').forEach(part => {
      if (part === '..') base.pop();
      else if (part !== '.') base.push(part);
    });
    return base.join('/');
  }

  function load(path) {
    activePath = path;
    history.replaceState(null, '', `?p=${encodeURIComponent(path)}`);
    contentEl.innerHTML = '<div class="empty-state"><span class="spinner"></span></div>';
    fetch('../' + path)
      .then(r => r.ok ? r.text() : Promise.reject(`${r.status}`))
      .then(text => {
        const fmMatch = text.match(/^---\n([\s\S]*?)\n---\n/);
        let body = text;
        let isStub = false;
        if (fmMatch) {
          body = text.slice(fmMatch[0].length);
          isStub = /tags:\s*\[[^\]]*\bstub\b/.test(fmMatch[1]);
        }
        const md = transformWikilinks(body);
        const html = marked.parse(md, { renderer });
        const stubBanner = isStub
          ? `<div class="stub-banner">This page is a stub. Open a Claude Code session in this folder and ask "fill in <code>${path}</code>" — the page will get fleshed out.</div>`
          : '';
        const graphLink = currentGraphNode(path);
        const graphBtn = graphLink
          ? `<p><a href="graph.html#${encodeURIComponent(graphLink)}">↗ Open in graph</a></p>`
          : '';
        contentEl.innerHTML = stubBanner + html + graphBtn;
        document.title = (extractTitle(html) || 'Wiki') + ' — Lumi Codebase Wiki';
        markActive(path);
      })
      .catch(err => {
        contentEl.innerHTML = `
          <div class="empty-state">
            <p>Could not load <code>${escapeHtml(path)}</code>: ${escapeHtml(err)}</p>
            <p><a href="wiki.html?p=wiki/overview.md">Back to overview</a></p>
          </div>`;
      });
  }

  function currentGraphNode(path) {
    const map = window.__pathToGraphNode || {};
    return map[path];
  }

  function extractTitle(html) {
    const m = html.match(/<h1[^>]*>(.*?)<\/h1>/i);
    return m ? m[1].replace(/<[^>]+>/g, '') : null;
  }

  function markActive(path) {
    document.querySelectorAll('.wiki-toc a').forEach(a => {
      a.classList.toggle('active', a.dataset.path === path);
    });
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  // Build TOC from wiki-index.json, organised by `type`
  const TOC_SECTIONS = [
    ['overview', 'Start here'],
    ['tour', 'Tours'],
    ['architecture', 'Architecture'],
    ['concept', 'Concepts'],
    ['glossary', 'Glossary'],
    ['monitor', 'Monitors'],
    ['arbiter', 'Arbiters'],
    ['service', 'Services'],
    ['common-util', 'Common'],
    ['module', 'V2 Modules'],
    ['api-domain', 'Web · API'],
    ['route-group', 'Web · Routes'],
    ['pipeline', 'Pipelines'],
    ['repo', 'Repos'],
    ['log', 'Log'],
  ];

  fetch('data/wiki-index.json')
    .then(r => r.json())
    .then(data => {
      window.__wikiIndex = data.pages;
      window.__pathToGraphNode = Object.fromEntries(
        data.pages.filter(p => p.graph_node).map(p => [p.path, p.graph_node])
      );

      const byType = {};
      data.pages.forEach(p => (byType[p.type] = byType[p.type] || []).push(p));

      const html = TOC_SECTIONS
        .filter(([t]) => byType[t])
        .map(([t, label]) => {
          const pages = byType[t].sort((a, b) => a.name.localeCompare(b.name));
          return `<div class="toc-section">${label}</div>` +
            pages.map(p => {
              const stub = (p.tags || []).includes('stub') ? ' <span class="stub-marker">·stub</span>' : '';
              return `<a data-path="${escapeHtml(p.path)}" href="?p=${encodeURIComponent(p.path)}">${escapeHtml(p.name)}${stub}</a>`;
            }).join('');
        }).join('');
      tocEl.innerHTML = html;
      tocEl.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', e => {
          e.preventDefault();
          load(a.dataset.path);
        });
      });
      load(activePath);
    })
    .catch(err => {
      tocEl.innerHTML = `<p style="color: var(--fg-muted)">No index. Run <code>python tools/build_index.py</code>.</p>`;
      load(activePath);
    });
})();
