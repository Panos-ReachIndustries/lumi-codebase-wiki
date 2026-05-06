// Conversational layer over the Lumi Codebase Wiki.
// Loads every wiki page + graph + relations into memory once, then sends
// the full context to Gemini on each turn. No retrieval, no embeddings —
// at 85 pages (~70k tokens) this fits in Gemini 2.5 Flash's 1M window.
//
// Implicit prompt caching (default-on for Gemini 2.5) discounts the
// repeated context after the first turn — no extra code needed.
(() => {
  const cfg = window.LUMI_GEMINI;
  const statusEl = document.getElementById('status');
  const streamEl = document.getElementById('stream');
  const emptyEl  = document.getElementById('empty');
  const form     = document.getElementById('form');
  const input    = document.getElementById('input');
  const sendBtn  = document.getElementById('send');
  const suggestionsEl = document.getElementById('suggestions');

  // -------------- Config validation -------------- //
  if (window.__configMissing || !cfg) {
    return showFatal(
      'app/config.js is missing.',
      'Copy <code>app/config.example.js</code> to <code>app/config.js</code> and paste your Gemini API key.'
    );
  }
  if (!cfg.apiKey || cfg.apiKey === 'PASTE_YOUR_GEMINI_API_KEY_HERE') {
    return showFatal(
      'No Gemini API key set.',
      'Edit <code>app/config.js</code> and paste your key. Get one at <a target="_blank" href="https://aistudio.google.com/apikey">aistudio.google.com/apikey</a>.'
    );
  }
  const MODEL = cfg.model || 'gemini-2.5-flash';

  // -------------- Context loader -------------- //
  let CONTEXT = null;          // assembled once, reused every turn
  let CITATION_INDEX = {};     // path → page meta, for citation links
  const history = [];          // [{role: 'user'|'model', parts: [{text}]}]

  init();

  async function init() {
    try {
      const [graph, sim, rel, idx] = await Promise.all([
        fetchJson('data/graph.json'),
        fetchJson('data/similarity.json').catch(() => ({ edges: [] })),
        fetchJson('data/relations.json').catch(() => ({ edges: [] })),
        fetchJson('data/wiki-index.json'),
      ]);

      // fetch all wiki pages in parallel
      statusEl.innerHTML = `<span class="spinner"></span><span>Loading ${idx.pages.length} wiki pages…</span>`;
      const pages = await Promise.all(idx.pages.map(async p => {
        const text = await fetch('../' + p.path).then(r => r.ok ? r.text() : '');
        return { ...p, text: text.replace(/^---\n[\s\S]*?\n---\n/, '') };
      }));
      pages.forEach(p => { CITATION_INDEX[p.path] = p; });

      CONTEXT = buildContext(pages, graph, sim, rel);
      const tokens = approxTokens(CONTEXT);

      statusEl.innerHTML = `
        <span class="pill ok">${MODEL}</span>
        <span class="pill">${idx.pages.length} pages</span>
        <span class="pill">${graph.meta.counts.nodes} nodes</span>
        <span class="pill">${(rel.edges || []).length} relations</span>
        <span class="pill">~${(tokens / 1000).toFixed(0)}k context tokens</span>
        <span style="margin-left:auto;font-size:11px">Prompt caching is automatic for 2.5 — costs drop after turn 1.</span>
      `;
      sendBtn.disabled = false;
      input.focus();
    } catch (err) {
      showFatal('Could not load context.', escapeHtml(err.message));
    }
  }

  function buildContext(pages, graph, sim, rel) {
    const wikiBlock = pages.map(p =>
      `\n--- BEGIN ${p.path} ---\n# ${p.name}\n${p.text.trim()}\n--- END ${p.path} ---\n`
    ).join('');

    const graphSummary = JSON.stringify({
      nodes: graph.nodes.map(n => ({ id: n.id, label: n.label, type: n.type, repo: n.repo, summary: n.summary, wiki: n.wiki })),
      structural_edges: graph.edges
        .filter(e => e.kind !== 'belongs_to' && e.kind !== 'openapi')
        .map(e => ({ source: e.source, target: e.target, kind: e.kind, label: e.label })),
    });
    const relBlock = JSON.stringify((rel.edges || []).map(e => ({
      subject: e.source, predicate: e.predicate, object: e.target, evidence: e.evidence,
    })));
    const simBlock = JSON.stringify((sim.edges || []).slice(0, 60).map(e => ({
      a: e.source, b: e.target, weight: e.weight, shared: e.shared_terms,
    })));

    return [
      '=== WIKI PAGES (truth) ===',
      wikiBlock,
      '',
      '=== GRAPH (structural — auto-detected from code) ===',
      graphSummary,
      '',
      '=== TYPED RELATIONS (LLM-extracted from wiki, with evidence path) ===',
      relBlock,
      '',
      '=== TOP TF-IDF SIMILARITY EDGES (lexical only — for "what is similar to X") ===',
      simBlock,
    ].join('\n');
  }

  const SYSTEM_PROMPT = `You are a senior engineer pair-helping a new hire navigate the Lumi codebase. There are three repos:
- Lumi-AI-Continuous (Python + Go monitoring backend; monitors, arbiters, monitor_relay, Common utils)
- Lumi-AI-Core (Python V2 modules — Detection, Tracking, Vessels, Colours, …)
- lumi-web-v2 (Next.js 15 web app — routes, API hooks, Kubb-generated types)

You are given:
1. Every page of the onboarding wiki (the source of truth).
2. The structural code graph (imports, Kafka pubsub edges, web ↔ backend bridges).
3. LLM-extracted typed relations (subject, predicate, object) with evidence paths.
4. The top TF-IDF similarity edges, useful only for "what's similar to X" questions.

Rules:
- Answer strictly using the provided material. Do NOT invent functions, files, or behaviours that the material doesn't mention.
- Cite pages inline like [wiki/path/to/page.md] whenever you make a substantive claim. The viewer turns these into clickable links.
- If something isn't in the material, say so explicitly. Don't speculate.
- Be concise. New hires want the spine, not a textbook.
- When tracing a flow, list it as numbered steps with citations on each step.
- For "where do I start" questions, point at the day-1 tour and the exemplar pages (colour monitor, V2.Detection, web/api/devices).`;

  // -------------- Send / stream -------------- //
  form.addEventListener('submit', e => { e.preventDefault(); send(); });
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  });
  input.addEventListener('input', () => {
    sendBtn.disabled = !input.value.trim() || !CONTEXT;
    autosize();
  });
  suggestionsEl.querySelectorAll('button').forEach(b => {
    b.addEventListener('click', () => {
      input.value = b.dataset.q;
      autosize();
      send();
    });
  });

  function autosize() {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 200) + 'px';
  }

  async function send() {
    const text = input.value.trim();
    if (!text || !CONTEXT) return;
    input.value = '';
    autosize();
    sendBtn.disabled = true;
    if (emptyEl && emptyEl.parentNode) emptyEl.remove();
    suggestionsEl.style.display = 'none';

    appendMessage('user', text);
    history.push({ role: 'user', parts: [{ text }] });

    const assistantEl = appendMessage('assistant', '');
    assistantEl.querySelector('.body').classList.add('chat-typing');

    let full = '';
    try {
      // Build the request: stitch context onto the very first user turn.
      const turns = [];
      const firstUserIdx = history.findIndex(t => t.role === 'user');
      history.forEach((t, i) => {
        if (i === firstUserIdx) {
          turns.push({
            role: 'user',
            parts: [{ text: CONTEXT + '\n\n=== USER QUESTION ===\n' + t.parts[0].text }]
          });
        } else {
          turns.push(t);
        }
      });

      const url = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(MODEL)}:streamGenerateContent?alt=sse&key=${encodeURIComponent(cfg.apiKey)}`;
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: turns,
          systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
          generationConfig: {
            temperature: cfg.temperature ?? 0.4,
            maxOutputTokens: cfg.maxOutputTokens ?? 4096,
          },
        }),
      });

      if (!resp.ok) {
        const errText = await resp.text();
        throw new Error(`Gemini ${resp.status}: ${errText.slice(0, 400)}`);
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split('\n');
        buf = lines.pop() || '';
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const payload = line.slice(6).trim();
          if (!payload) continue;
          try {
            const json = JSON.parse(payload);
            const chunk = json.candidates?.[0]?.content?.parts?.map(p => p.text || '').join('') || '';
            if (chunk) {
              full += chunk;
              assistantEl.querySelector('.body').innerHTML = renderMarkdownWithCitations(full);
              streamEl.scrollTop = streamEl.scrollHeight;
            }
          } catch (_) { /* skip bad chunk */ }
        }
      }
      assistantEl.querySelector('.body').classList.remove('chat-typing');
      addCitationFooter(assistantEl, full);
      history.push({ role: 'model', parts: [{ text: full }] });
    } catch (err) {
      assistantEl.querySelector('.body').classList.remove('chat-typing');
      assistantEl.querySelector('.body').innerHTML =
        `<p style="color: var(--amber)">⚠ ${escapeHtml(err.message)}</p>`;
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  // -------------- Render helpers -------------- //
  function appendMessage(role, text) {
    const el = document.createElement('div');
    el.className = `chat-msg ${role}`;
    el.innerHTML = `
      <div class="role">${role === 'user' ? 'You' : 'Lumi assistant'}</div>
      <div class="body">${role === 'user' ? escapeHtml(text) : renderMarkdownWithCitations(text)}</div>
    `;
    streamEl.appendChild(el);
    streamEl.scrollTop = streamEl.scrollHeight;
    return el;
  }

  function renderMarkdownWithCitations(text) {
    if (!text) return '';
    const cited = text.replace(/\[(wiki\/[^\]]+\.md)(#[^\]]*)?\]/g, (_, path, frag) => {
      const safe = escapeHtml(path);
      return `<a href="wiki.html?p=${encodeURIComponent(path)}" target="_blank">[${safe}${frag || ''}]</a>`;
    });
    return marked.parse(cited, { gfm: true, breaks: false });
  }

  function addCitationFooter(msgEl, text) {
    const seen = new Set();
    const matches = [...text.matchAll(/\[(wiki\/[^\]]+?\.md)/g)];
    matches.forEach(m => seen.add(m[1]));
    if (!seen.size) return;
    const cites = document.createElement('div');
    cites.className = 'citations';
    cites.innerHTML = '<strong>Sources:</strong> ' +
      [...seen].map(p => {
        const meta = CITATION_INDEX[p];
        const label = meta ? meta.name : p;
        return `<a href="wiki.html?p=${encodeURIComponent(p)}" target="_blank">${escapeHtml(label)}</a>`;
      }).join('');
    msgEl.appendChild(cites);
  }

  // -------------- Misc -------------- //
  function approxTokens(text) {
    // rough: 4 chars per token
    return Math.round(text.length / 4);
  }
  function showFatal(title, html) {
    statusEl.innerHTML = `<span class="pill warn">setup needed</span><span><strong>${escapeHtml(title)}</strong></span>`;
    streamEl.innerHTML = `<div class="chat-empty"><h2>${escapeHtml(title)}</h2><p>${html}</p></div>`;
    sendBtn.disabled = true;
    input.disabled = true;
  }
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }
  function fetchJson(url) {
    return fetch(url).then(r => r.ok ? r.json() : Promise.reject(`${url}: ${r.status}`));
  }
})();
