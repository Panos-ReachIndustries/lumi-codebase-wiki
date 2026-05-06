// Cytoscape graph for the Lumi Codebase Wiki.
// Loads three layers in parallel:
//   1. Structural   — app/data/graph.json   (imports, pubsub, depends_on, …)
//   2. Similarity   — app/data/similarity.json (TF-IDF mutual top-K)
//   3. Relations    — app/data/relations.json  (LLM-extracted typed triples)
// Each is independently toggleable in the sidebar.
(() => {
  const cyEl = document.getElementById('cy');
  const panel = document.getElementById('panel');
  const layerChips = document.getElementById('layer-chips');
  const repoChips = document.getElementById('repo-chips');
  const typeChips = document.getElementById('type-chips');
  const edgeChips = document.getElementById('edge-chips');
  const counts = document.getElementById('counts');
  const layoutBtns = document.querySelectorAll('.layout-toggle button');

  if (typeof cytoscape === 'undefined') {
    cyEl.innerHTML = '<div style="padding:40px;color:#fff">Cytoscape failed to load.</div>';
    return;
  }

  const TYPE_COLORS = {
    'repo':         '#60a5fa', 'repo-missing': '#6b7280',
    'monitor':      '#3b82f6', 'arbiter':      '#2563eb',
    'service':      '#1d4ed8', 'common-util':  '#1e40af',
    'v2-module':    '#a78bfa', 'api-domain':   '#10b981',
    'route-group':  '#34d399', 'pipeline':     '#06b6d4',
    'kafka-topic':  '#fbbf24',
  };
  const TYPE_LABELS = {
    'repo': 'Repos', 'repo-missing': 'External (missing)',
    'monitor': 'Monitors', 'arbiter': 'Arbiters', 'service': 'Services',
    'common-util': 'Common utils', 'v2-module': 'V2 modules',
    'api-domain': 'Web API domains', 'route-group': 'Web routes',
    'pipeline': 'Pipelines', 'kafka-topic': 'Kafka topics',
  };
  const STRUCT_KINDS = {
    'imports':       '#60a5fa', 'pubsub':        '#fbbf24',
    'consumes_api':  '#10b981', 'depends_on':    '#a78bfa',
    'submodule':     '#9ca3af',
  };
  // Predicate colours for the relations layer
  const REL_COLORS = {
    'USES':           '#60a5fa', 'COMPOSES':       '#06b6d4',
    'PUBLISHES_TO':   '#fbbf24', 'SUBSCRIBES_TO':  '#f59e0b',
    'DEPENDS_ON':     '#a78bfa', 'IS_A_KIND_OF':   '#ec4899',
    'EXAMPLE_OF':     '#34d399', 'ALTERNATIVE_TO': '#f472b6',
    'MAINTAINED_BY':  '#94a3b8', 'DOCUMENTED_BY':  '#64748b',
    'REFERENCED_BY':  '#475569',
  };

  // Built-in cose layout — no extension needed, no version-skew bugs.
  const FORCE_OPTS = {
    name: 'cose', animate: true, randomize: true,
    nodeRepulsion: () => 600000, idealEdgeLength: () => 110,
    gravity: 60, numIter: 1500, componentSpacing: 80,
    nodeOverlap: 16, edgeElasticity: () => 100,
    nestingFactor: 1.2, fit: true, padding: 30,
  };

  Promise.all([
    fetch('data/graph.json').then(r => r.json()),
    fetch('data/similarity.json').then(r => r.ok ? r.json() : { edges: [] }).catch(() => ({ edges: [] })),
    fetch('data/relations.json').then(r => r.ok ? r.json() : { edges: [] }).catch(() => ({ edges: [] })),
  ]).then(([graph, sim, rel]) => {

    const elements = [];

    // Nodes
    graph.nodes.forEach(n => elements.push({
      data: {
        id: n.id, label: n.label, type: n.type, repo: n.repo,
        color: TYPE_COLORS[n.type] || n.color || '#9ca3af',
        shape: n.type === 'kafka-topic' ? 'round-rectangle'
              : n.type === 'repo' || n.type === 'repo-missing' ? 'round-octagon'
              : 'ellipse',
        size: n.type === 'repo' ? 60 : n.type === 'kafka-topic' ? 32 : 36,
        wiki: n.wiki, summary: n.summary, file: n.file,
      }
    }));

    // Structural edges (filter belongs_to which we no longer emit, defensive)
    graph.edges.forEach((e, i) => {
      if (e.kind === 'belongs_to' || e.kind === 'openapi') return;
      elements.push({
        data: {
          id: `s${i}`, source: e.source, target: e.target,
          kind: e.kind, layer: 'structural', label: e.label || '',
          color: STRUCT_KINDS[e.kind] || '#374151',
          style: e.kind === 'pubsub' ? 'dashed' : e.kind === 'consumes_api' ? 'dotted' : 'solid',
          width: 1.4,
        }
      });
    });

    // Similarity edges
    (sim.edges || []).forEach((e, i) => {
      elements.push({
        data: {
          id: `sim${i}`, source: e.source, target: e.target,
          kind: 'similar', layer: 'similarity',
          weight: e.weight,
          label: `${(e.shared_terms || []).slice(0, 2).join(', ')}`,
          color: '#7c3aed',
          style: 'solid',
          width: Math.max(0.6, e.weight * 3.0),
        }
      });
    });

    // Relations edges (LLM-typed)
    (rel.edges || []).forEach((e, i) => {
      const pred = e.predicate || (e.kind || '').replace(/^rel:/, '');
      elements.push({
        data: {
          id: `r${i}`, source: e.source, target: e.target,
          kind: e.kind || `rel:${pred}`, layer: 'relations',
          predicate: pred, label: pred.replace(/_/g, ' ').toLowerCase(),
          color: REL_COLORS[pred] || '#94a3b8',
          style: 'solid',
          width: 1.6,
        }
      });
    });

    const cy = cytoscape({
      container: cyEl,
      elements,
      wheelSensitivity: 0.2,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)', 'label': 'data(label)',
            'shape': 'data(shape)', 'width': 'data(size)', 'height': 'data(size)',
            'color': '#e6ecff', 'font-size': 11, 'text-valign': 'bottom',
            'text-margin-y': 6, 'text-outline-width': 2, 'text-outline-color': '#0b1020',
            'border-width': 1, 'border-color': 'rgba(255,255,255,0.12)',
          }
        },
        {
          selector: 'node[type = "repo"]',
          style: { 'font-size': 14, 'font-weight': 'bold',
                   'border-width': 2, 'border-color': 'rgba(255,255,255,0.4)' }
        },
        {
          selector: 'node[type = "repo-missing"]',
          style: { 'opacity': 0.45, 'border-style': 'dashed' }
        },
        {
          selector: 'node:selected',
          style: { 'border-width': 3, 'border-color': '#fbbf24', 'overlay-opacity': 0 }
        },
        {
          selector: 'edge',
          style: {
            'curve-style': 'bezier', 'width': 'data(width)',
            'line-color': 'data(color)', 'line-style': 'data(style)',
            'target-arrow-color': 'data(color)', 'target-arrow-shape': 'triangle',
            'arrow-scale': 0.7, 'opacity': 0.6,
          }
        },
        {
          selector: 'edge[layer = "similarity"]',
          style: {
            'opacity': 0.32, 'curve-style': 'bezier',
            'target-arrow-shape': 'none', 'line-color': '#7c3aed',
          }
        },
        {
          selector: 'edge[layer = "relations"]',
          style: {
            'label': 'data(label)', 'font-size': 8, 'color': '#cbd5e1',
            'text-rotation': 'autorotate', 'text-background-color': '#0b1020',
            'text-background-opacity': 0.85, 'text-background-padding': '2px',
            'text-background-shape': 'roundrectangle',
          }
        },
        { selector: '.dimmed', style: { 'opacity': 0.08 } },
        { selector: '.highlighted', style: { 'opacity': 1, 'z-index': 9 } },
        { selector: 'edge.highlighted', style: { 'width': 3.0 } },
      ],
      layout: FORCE_OPTS,
    });

    counts.innerHTML = `<strong>${graph.meta.counts.nodes}</strong> nodes ·
      <strong>${graph.edges.filter(e => e.kind !== 'belongs_to' && e.kind !== 'openapi').length}</strong> structural ·
      <strong>${(sim.edges || []).length}</strong> similar ·
      <strong>${(rel.edges || []).length}</strong> relations`;

    // ---------------- Layer toggles ----------------
    const layerState = { structural: true, similarity: false, relations: false };
    const layerColors = { structural: '#60a5fa', similarity: '#7c3aed', relations: '#34d399' };
    Object.keys(layerState).forEach(layer => {
      const chip = mkChip(layer.charAt(0).toUpperCase() + layer.slice(1),
                          layerColors[layer], () => toggleLayer(layer, chip));
      if (!layerState[layer]) chip.classList.add('off');
      layerChips.appendChild(chip);
    });
    applyLayerVisibility();

    function applyLayerVisibility() {
      ['structural', 'similarity', 'relations'].forEach(layer => {
        cy.edges(`[layer = "${layer}"]`).style('display', layerState[layer] ? 'element' : 'none');
      });
    }
    function toggleLayer(layer, chip) {
      layerState[layer] = !layerState[layer];
      chip.classList.toggle('off', !layerState[layer]);
      applyLayerVisibility();
    }

    // ---------------- Repo / type / edge-kind chips ----------------
    [...new Set(graph.nodes.map(n => n.repo))].forEach(repo => {
      const chip = mkChip(repo, graph.meta.repo_colors?.[repo] || '#9ca3af',
                          () => toggleSelector(`node[repo = "${repo}"]`, chip));
      repoChips.appendChild(chip);
    });
    Object.entries(TYPE_LABELS).forEach(([type, label]) => {
      if (!graph.nodes.some(n => n.type === type)) return;
      const chip = mkChip(label, TYPE_COLORS[type] || '#9ca3af',
                          () => toggleSelector(`node[type = "${type}"]`, chip));
      typeChips.appendChild(chip);
    });
    const edgeKinds = [...new Set(elements.filter(e => e.data.source).map(e => e.data.kind))];
    edgeKinds.forEach(kind => {
      const isRel = kind.startsWith('rel:');
      const color = STRUCT_KINDS[kind] || (isRel ? REL_COLORS[kind.slice(4)] || '#94a3b8' : '#7c3aed');
      const display = isRel ? kind.slice(4).toLowerCase().replace(/_/g, ' ') : kind;
      const chip = mkChip(display, color, () => toggleSelector(`edge[kind = "${kind}"]`, chip));
      edgeChips.appendChild(chip);
    });

    function mkChip(label, color, onClick) {
      const el = document.createElement('span');
      el.className = 'chip';
      el.innerHTML = `<span class="swatch" style="background:${color}"></span>${escapeHtml(label)}`;
      el.addEventListener('click', onClick);
      return el;
    }
    function toggleSelector(selector, chip) {
      chip.classList.toggle('off');
      const off = chip.classList.contains('off');
      cy.$(selector).style('display', off ? 'none' : 'element');
    }

    // ---------------- Click handler ----------------
    cy.on('tap', 'node', evt => {
      const n = evt.target.data();
      cy.elements().removeClass('highlighted dimmed');
      cy.elements().addClass('dimmed');
      evt.target.closedNeighborhood().removeClass('dimmed').addClass('highlighted');

      panel.classList.remove('empty');
      panel.innerHTML = `
        <div class="crumbs">${escapeHtml(n.repo)} · ${escapeHtml(n.type)}</div>
        <h2>${escapeHtml(n.label)}</h2>
        ${n.summary ? `<p style="color: var(--fg-muted)">${escapeHtml(n.summary)}</p>` : ''}
        ${n.file ? `<p style="font-size: 12px;"><code>${escapeHtml(n.file)}</code></p>` : ''}
        <div class="actions">
          ${n.wiki ? `<a href="wiki.html?p=${encodeURIComponent(n.wiki.split('#')[0])}" target="_blank">Open in wiki ↗</a>` : ''}
        </div>
        <div id="panel-md"><div class="empty-state"><span class="spinner"></span></div></div>
      `;
      if (n.wiki) {
        const path = n.wiki.split('#')[0];
        fetch('../' + path).then(r => r.ok ? r.text() : null).then(text => {
          if (!text) {
            document.getElementById('panel-md').innerHTML = '<p style="color:var(--fg-muted)">(no wiki page yet)</p>';
            return;
          }
          const body = text.replace(/^---\n[\s\S]*?\n---\n/, '');
          document.getElementById('panel-md').innerHTML = marked.parse(body);
        });
      }
    });
    cy.on('tap', evt => {
      if (evt.target === cy) cy.elements().removeClass('highlighted dimmed');
    });

    // ---------------- Layout toggle ----------------
    layoutBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        layoutBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const name = btn.dataset.layout;
        const opts = name === 'fcose' ? FORCE_OPTS
                   : name === 'cose' ? { name: 'cose', animate: true, idealEdgeLength: () => 160, nodeOverlap: 20, nodeRepulsion: () => 1200000, gravity: 30, componentSpacing: 120 }
                   : { name: 'concentric', concentric: n => n.data('type') === 'repo' ? 10 : n.data('type') === 'kafka-topic' ? 5 : 1, levelWidth: () => 1, animate: true };
        cy.layout(opts).run();
      });
    });

    // Hash deep-link
    if (location.hash) {
      const id = decodeURIComponent(location.hash.replace(/^#/, ''));
      const node = cy.getElementById(id);
      if (node && node.length) {
        setTimeout(() => { cy.center(node); cy.zoom(1.3); node.trigger('tap'); }, 700);
      }
    }
  }).catch(err => {
    cyEl.innerHTML = `<div style="padding:40px;color:#fff">Failed to load graph data: ${err.message}<br><br>Run <code>python tools/build_graph.py && python tools/build_similarity.py</code> from the repo root.</div>`;
  });

  function escapeHtml(s) {
    return String(s || '').replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }
})();
