/* SmartSort — front-end controller */
(() => {
  'use strict';

  // ── Helpers ────────────────────────────────────────────────────────────
  const $ = (sel, root = document) => root.querySelector(sel);
  const page = $('#page');
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
  const fmtNum = n => Number(n || 0).toLocaleString();
  const plural = (n, word, many) => `${fmtNum(n)} ${n === 1 ? word : (many || word + 's')}`;
  const baseName = p => {
    const clean = String(p || '').replace(/[\\/]+$/, '');
    return clean.split(/[\\/]/).pop() || clean;
  };
  function fmtSize(b) {
    b = Number(b || 0);
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let i = 0;
    while (b >= 1024 && i < units.length - 1) { b /= 1024; i++; }
    return `${b < 10 && i > 0 ? b.toFixed(1) : Math.round(b)} ${units[i]}`;
  }
  function relTime(iso) {
    const d = new Date(iso);
    if (isNaN(d)) return '';
    const s = (Date.now() - d.getTime()) / 1000;
    if (s < 60) return 'Just now';
    if (s < 3600) return `${Math.floor(s / 60)} min ago`;
    if (s < 86400) return `${Math.floor(s / 3600)} hr ago`;
    if (s < 86400 * 2) return 'Yesterday';
    if (s < 86400 * 7) return `${Math.floor(s / 86400)} days ago`;
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  }
  const fullTime = iso => { const d = new Date(iso); return isNaN(d) ? '' : d.toLocaleString(); };

  // ── Icons ──────────────────────────────────────────────────────────────
  const I = {
    folder: '<svg viewBox="0 0 24 24"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>',
    folderPlus: '<svg viewBox="0 0 24 24"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M12 11v5M9.5 13.5h5"/></svg>',
    folderCheck: '<svg viewBox="0 0 24 24"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="m9 13 2 2 4-4"/></svg>',
    file: '<svg viewBox="0 0 24 24"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/></svg>',
    files: '<svg viewBox="0 0 24 24"><path d="M15 3H9a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7z"/><path d="M15 3v4h4"/><path d="M5 8v11a2 2 0 0 0 2 2h8"/></svg>',
    disk: '<svg viewBox="0 0 24 24"><ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/></svg>',
    layers: '<svg viewBox="0 0 24 24"><path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/></svg>',
    chart: '<svg viewBox="0 0 24 24"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg>',
    copy: '<svg viewBox="0 0 24 24"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1"/></svg>',
    skip: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="m5.6 5.6 12.8 12.8"/></svg>',
    check: '<svg viewBox="0 0 24 24"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>',
    checkCircle: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="m8 12.5 3 3 5-6"/></svg>',
    alert: '<svg viewBox="0 0 24 24"><path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 2.4 17.5A2 2 0 0 0 4.1 20.5h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg>',
    info: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>',
    x: '<svg viewBox="0 0 24 24"><path d="M18 6 6 18M6 6l12 12"/></svg>',
    undo: '<svg viewBox="0 0 24 24"><path d="M9 14 4 9l5-5"/><path d="M4 9h11a5 5 0 0 1 0 10h-3"/></svg>',
    refresh: '<svg viewBox="0 0 24 24"><path d="M20 11a8 8 0 0 0-14.3-4.9L4 8"/><path d="M4 3v5h5"/><path d="M4 13a8 8 0 0 0 14.3 4.9L20 16"/><path d="M20 21v-5h-5"/></svg>',
    external: '<svg viewBox="0 0 24 24"><path d="M14 4h6v6"/><path d="M20 4 11 13"/><path d="M19 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h4"/></svg>',
    trash: '<svg viewBox="0 0 24 24"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>',
    broom: '<svg viewBox="0 0 24 24"><path d="m14 4 6 6"/><path d="M17 7 9.5 14.5"/><path d="M9.5 14.5 4 20h6l3-3z"/><path d="M7 17l2 2"/></svg>',
    chevron: '<svg viewBox="0 0 24 24"><path d="m9 6 6 6-6 6"/></svg>',
    arrow: '<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    eye: '<svg viewBox="0 0 24 24"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>',
    shield: '<svg viewBox="0 0 24 24"><path d="M12 3 4 6v6c0 4.4 3.4 8.3 8 9 4.6-.7 8-4.6 8-9V6z"/><path d="m9 12 2 2 4-4"/></svg>',
    sliders: '<svg viewBox="0 0 24 24"><path d="M4 6h10M4 12h16M4 18h7"/><circle cx="17" cy="6" r="2"/><circle cx="14" cy="18" r="2"/></svg>',
    clock: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  };

  // ── Category colours ───────────────────────────────────────────────────
  const CAT_COLORS = {
    images: '#a78bfa', photos: '#f472b6', documents: '#60a5fa', audio: '#34d399',
    videos: '#fb923c', archives: '#facc15', installers: '#f87171', code: '#22d3ee',
    finance: '#4ade80', 'design & fonts': '#e879f9', unsorted: '#94a3b8', duplicates: '#fbbf24',
  };
  const PALETTE = ['#818cf8', '#2dd4bf', '#f9a8d4', '#fcd34d', '#93c5fd', '#c4b5fd', '#86efac', '#fdba74'];
  function catColor(name) {
    const key = String(name || '').split('/')[0].trim().toLowerCase();
    if (CAT_COLORS[key]) return CAT_COLORS[key];
    let h = 0;
    for (const ch of key) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
    return PALETTE[h % PALETTE.length];
  }
  function fileBadge(name, category) {
    const c = catColor(category);
    const m = /\.([a-z0-9]{1,5})$/i.exec(name || '');
    const label = m ? esc(m[1].slice(0, 4)) : I.file;
    return `<div class="file-icon" style="background:${c}1f;color:${c}">${label}</div>`;
  }
  const folderBadge = (color = '#a78bfa') =>
    `<div class="file-icon" style="background:${color}1f;color:${color}">${I.folder}</div>`;

  // ── State ──────────────────────────────────────────────────────────────
  const state = {
    folder: localStorage.getItem('smartsort.folder') || '',
    view: 'overview',
    scan: null,      // { folder, data }
    preview: null,   // { folder, data }
    lastRun: null,   // organize result shown on the Organize page
    busy: false,     // a file-moving job is running
  };
  let viewToken = 0;
  let previewGroups = [];
  let subfolderLimit = 8;

  // ── API ────────────────────────────────────────────────────────────────
  async function api(endpoint, data) {
    const opts = data === undefined
      ? { method: 'GET' }
      : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) };
    try {
      const res = await fetch('/api/' + endpoint, opts);
      const json = await res.json().catch(() => ({ success: false, error: `Unexpected response (${res.status})` }));
      if (!res.ok) json.success = false;
      return json;
    } catch (e) {
      return { success: false, error: 'Lost connection to the SmartSort engine. Try restarting the app.' };
    }
  }

  let desktopReady = null;
  function waitForDesktop() {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.browse_folder) return Promise.resolve(true);
    if (!window.pywebview) return Promise.resolve(false);
    if (!desktopReady) {
      desktopReady = new Promise(resolve => {
        window.addEventListener('pywebviewready', () => resolve(true), { once: true });
        setTimeout(() => resolve(!!(window.pywebview && window.pywebview.api)), 3000);
      });
    }
    return desktopReady;
  }

  // ── Toasts ─────────────────────────────────────────────────────────────
  function toast(type, title, msg = '', action = null) {
    const icon = { success: I.checkCircle, error: I.alert, info: I.info }[type] || I.info;
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = `
      <div class="toast-icon">${icon}</div>
      <div class="toast-body">
        <div class="toast-title">${esc(title)}</div>
        ${msg ? `<div class="toast-msg">${esc(msg)}</div>` : ''}
      </div>
      ${action ? `<button class="toast-action">${esc(action.label)}</button>` : ''}
      <button class="icon-btn" aria-label="Dismiss" style="width:22px;height:22px">${I.x}</button>`;
    const close = () => {
      if (el.classList.contains('leaving')) return;
      el.classList.add('leaving');
      setTimeout(() => el.remove(), 200);
    };
    el.querySelector('.icon-btn').onclick = close;
    if (action) el.querySelector('.toast-action').onclick = () => { close(); action.fn(); };
    $('#toasts').appendChild(el);
    setTimeout(close, type === 'error' ? 7000 : 4500);
  }

  // ── Modal ──────────────────────────────────────────────────────────────
  function confirmModal({ title, message, confirm = 'Confirm', danger = false, icon = I.info }) {
    return new Promise(resolve => {
      const root = $('#modalRoot');
      root.innerHTML = `
        <div class="modal-overlay">
          <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modalTitle">
            <div class="modal-icon ${danger ? 'danger' : ''}">${icon}</div>
            <h2 id="modalTitle">${esc(title)}</h2>
            <p>${esc(message)}</p>
            <div class="modal-actions">
              <button class="btn btn-ghost" id="modalCancel">Cancel</button>
              <button class="btn ${danger ? 'btn-danger-solid' : 'btn-primary'}" id="modalConfirm">${esc(confirm)}</button>
            </div>
          </div>
        </div>`;
      const finish = val => {
        document.removeEventListener('keydown', onKey, true);
        root.innerHTML = '';
        resolve(val);
      };
      const onKey = e => {
        if (e.key === 'Escape') { e.stopPropagation(); finish(false); }
        if (e.key === 'Enter') { e.preventDefault(); finish(true); }
      };
      document.addEventListener('keydown', onKey, true);
      $('#modalCancel').onclick = () => finish(false);
      $('#modalConfirm').onclick = () => finish(true);
      $('.modal-overlay', root).addEventListener('mousedown', e => { if (e.target.classList.contains('modal-overlay')) finish(false); });
      $('#modalConfirm').focus();
    });
  }

  // ── Rendering primitives ───────────────────────────────────────────────
  function mount(html) {
    page.innerHTML = `<div class="view">${html}</div>`;
  }
  function header(title, subtitle, actions = '') {
    return `
      <div class="page-header">
        <div class="page-header-text">
          <h1 class="page-title">${esc(title)}</h1>
          ${subtitle ? `<p class="page-subtitle">${subtitle}</p>` : ''}
        </div>
        ${actions ? `<div class="page-actions">${actions}</div>` : ''}
      </div>`;
  }
  const stat = (label, value, sub = '', icon = '', cls = '') => `
    <div class="stat ${cls}">
      <div class="stat-label">${icon}${esc(label)}</div>
      <div class="stat-value" title="${esc(value)}">${esc(value)}</div>
      ${sub ? `<div class="stat-sub" title="${esc(sub)}">${esc(sub)}</div>` : ''}
    </div>`;
  const emptyState = (icon, title, text, button = '') => `
    <div class="empty-state">
      <div class="empty-icon">${icon}</div>
      <h3>${esc(title)}</h3>
      <p>${text}</p>
      ${button}
    </div>`;
  const errorState = msg => `<div class="card">${emptyState(I.alert, "Couldn't open this folder", esc(msg || 'Something went wrong.'),
    `<button class="btn btn-secondary" data-action="browse">${I.folderPlus}Choose another folder</button>`)}</div>`;
  const rowActions = path => path ? `
    <div class="row-actions">
      <button class="icon-btn" title="Show in File Explorer" data-action="reveal" data-path="${esc(path)}">${I.external}</button>
    </div>` : '';

  // ── Progress (background jobs) ─────────────────────────────────────────
  function renderProgress(ui) {
    mount(`
      <div class="card progress-card">
        <div class="progress-title">${esc(ui.title)}</div>
        <div class="progress-sub" id="pgSub">${esc(ui.sub || 'Starting…')}</div>
        <div class="progress-track indeterminate" id="pgTrack"><div class="progress-fill" id="pgFill"></div></div>
        <div class="progress-meta"><span id="pgCount">&nbsp;</span><span id="pgPct"></span></div>
        ${ui.cancellable ? `<button class="btn btn-secondary btn-sm" id="pgCancel">${esc(ui.cancelLabel || 'Cancel')}</button>` : ''}
      </div>`);
  }
  function updateProgress(job) {
    const track = $('#pgTrack');
    if (!track || !job.total) return;
    track.classList.remove('indeterminate');
    const pct = Math.min(100, (job.done / job.total) * 100);
    $('#pgFill').style.width = pct.toFixed(1) + '%';
    $('#pgCount').textContent = `${fmtNum(job.done)} of ${fmtNum(job.total)} files`;
    $('#pgPct').textContent = `${Math.floor(pct)}%`;
    if (job.current) $('#pgSub').textContent = job.current;
  }

  async function runJob(endpoint, payload, ui, token) {
    const start = await api(endpoint, payload);
    if (!start.success) {
      toast('error', ui.errorTitle || 'Something went wrong', start.error);
      return null;
    }
    const id = start.job.id;
    if (token === viewToken) renderProgress(ui);
    const cancelBtn = $('#pgCancel');
    if (cancelBtn) {
      cancelBtn.onclick = () => {
        cancelBtn.disabled = true;
        cancelBtn.textContent = 'Stopping…';
        api('job/cancel', { id });
      };
    }
    let delay = 100;
    for (;;) {
      await sleep(delay);
      delay = Math.min(350, delay + 50);
      const r = await api('job?id=' + encodeURIComponent(id));
      if (!r.success) { toast('error', ui.errorTitle || 'Something went wrong', r.error); return null; }
      const job = r.job;
      if (job.status === 'running') { if (token === viewToken) updateProgress(job); continue; }
      if (job.status === 'error') { toast('error', ui.errorTitle || 'Something went wrong', job.error); return null; }
      return job;
    }
  }

  // ── Folder selection ───────────────────────────────────────────────────
  function updateFolderBar() {
    const bar = $('#folderBar');
    const has = !!state.folder;
    bar.classList.toggle('has-folder', has);
    bar.classList.toggle('no-folder', !has);
    bar.title = has ? state.folder : 'Choose a folder';
    $('#folderName').textContent = has ? baseName(state.folder) : 'No folder selected';
    $('#folderPath').textContent = has ? state.folder : 'Choose a folder to scan and organize';
    $('#revealFolderBtn').classList.toggle('hidden', !has);
  }
  function recentFolders() {
    try { return JSON.parse(localStorage.getItem('smartsort.recent') || '[]'); } catch { return []; }
  }
  function setFolder(path) {
    state.folder = path;
    state.scan = state.preview = state.lastRun = null;
    subfolderLimit = 8;
    localStorage.setItem('smartsort.folder', path);
    const recent = [path, ...recentFolders().filter(p => p.toLowerCase() !== path.toLowerCase())].slice(0, 5);
    localStorage.setItem('smartsort.recent', JSON.stringify(recent));
    updateFolderBar();
    if (state.view === 'overview' || state.view === 'organize') render();
    else setView('overview');
  }
  async function chooseFolder() {
    if (state.busy) return;
    let path = '';
    if (await waitForDesktop()) {
      try { path = await window.pywebview.api.browse_folder(); } catch (e) { path = ''; }
    } else {
      const r = await api('browse', {});
      path = (r && r.path) || '';
    }
    if (path) setFolder(path);
  }

  // ── Navigation ─────────────────────────────────────────────────────────
  const views = {};
  function setView(view) {
    if (state.busy) { toast('info', 'Please wait', 'An operation is still running.'); return; }
    state.view = view;
    document.querySelectorAll('.nav-item[data-view]').forEach(n => n.classList.toggle('active', n.dataset.view === view));
    render();
  }
  function render() {
    hideContextMenu();
    const token = ++viewToken;
    page.scrollTop = 0;
    (views[state.view] || views.overview)(token);
  }

  // ── Welcome ────────────────────────────────────────────────────────────
  function renderWelcome() {
    const recent = recentFolders();
    mount(`
      <div class="hero">
        <img class="hero-logo" src="SS_1.png" alt="SmartSort logo">
        <h1>Tidy up any folder in seconds</h1>
        <p>SmartSort sorts loose files into clear category folders. You'll see a full preview first, and every change can be undone.</p>
        <button class="btn btn-primary btn-lg" data-action="browse">${I.folderPlus}Choose a folder</button>
        ${recent.length ? `
          <div class="recent">
            <div class="section-title">Recent folders</div>
            <div class="card list">
              ${recent.map(p => `
                <div class="row" data-action="open-recent" data-folder="${esc(p)}">
                  ${folderBadge()}
                  <div class="row-main"><div class="row-title">${esc(baseName(p))}</div><div class="row-sub">${esc(p)}</div></div>
                  <span class="faint">${I.chevron}</span>
                </div>`).join('')}
            </div>
          </div>` : ''}
        <div class="features">
          <div class="card feature"><div class="feature-icon">${I.eye}</div><h3>Preview first</h3><p>See exactly where every file will go before anything moves.</p></div>
          <div class="card feature"><div class="feature-icon">${I.undo}</div><h3>Undo anytime</h3><p>Each run is saved in History and can be reversed in one click.</p></div>
          <div class="card feature"><div class="feature-icon">${I.shield}</div><h3>Safe by default</h3><p>Duplicates are set aside and system or in-progress files are left alone.</p></div>
        </div>
      </div>`);
  }

  // ── Overview ───────────────────────────────────────────────────────────
  views.overview = async token => {
    if (!state.folder) return renderWelcome();
    const refresh = `<button class="btn btn-ghost btn-sm" data-action="refresh-scan">${I.refresh}Refresh</button>`;

    if (!state.scan || state.scan.folder !== state.folder) {
      mount(header('Folder Overview', esc(state.folder), refresh) + `
        <div class="workflow-steps">
          <div class="workflow-step active"><span class="step-bubble">1</span> Folder Overview</div>
          <span class="workflow-sep">→</span>
          <div class="workflow-step"><span class="step-bubble">2</span> Preview Plan</div>
          <span class="workflow-sep">→</span>
          <div class="workflow-step"><span class="step-bubble">3</span> Organized</div>
        </div>
        <div class="skeleton" style="height:100px;margin-bottom:16px"></div>
        <div class="stats">${'<div class="skeleton" style="height:86px"></div>'.repeat(4)}</div>
        <div class="skeleton section" style="height:160px"></div>
        <div class="grid-2 section"><div class="skeleton" style="height:260px"></div><div class="skeleton" style="height:260px"></div></div>`);
      const res = await api('scan', { path: state.folder });
      if (token !== viewToken) return;
      if (!res.success) return mount(header('Folder Overview', esc(state.folder)) + errorState(res.error));
      state.scan = { folder: state.folder, data: res };
    }

    const d = state.scan.data;
    const cats = Object.entries(d.categories).sort((a, b) => b[1].size - a[1].size);
    const subs = d.subfolders || [];
    const subTotal = subs.reduce((s, x) => s + x.size, 0);
    const topCat = cats[0];

    const actions = `
      ${refresh}
      <button class="btn btn-secondary btn-sm" data-action="clean-empty" title="Delete empty subfolders">${I.broom}Clean empty folders</button>
      ${d.total_files ? `<button class="btn btn-primary btn-sm" data-action="goto-organize">${I.folderCheck}Organize ${plural(d.total_files, 'file')}</button>` : ''}`;

    const workflowSteps = `
      <div class="workflow-steps">
        <div class="workflow-step active"><span class="step-bubble">1</span> Folder Overview</div>
        <span class="workflow-sep">→</span>
        <div class="workflow-step"><span class="step-bubble">2</span> Preview Plan</div>
        <span class="workflow-sep">→</span>
        <div class="workflow-step"><span class="step-bubble">3</span> Organized</div>
      </div>`;

    const banner = d.total_files > 0 ? `
      <div class="action-banner">
        <div class="action-banner-body">
          <span class="action-banner-badge">Step 1: Scanned</span>
          <div class="action-banner-title">Found ${plural(d.total_files, 'file')} ready to organize in “${esc(baseName(state.folder))}”</div>
          <div class="action-banner-text">SmartSort can group these files into clean folders by type & date. You will see a full interactive preview before anything moves.</div>
        </div>
        <div class="action-banner-btns">
          <button class="btn btn-primary btn-lg" data-action="goto-organize">
            ${I.folderCheck} Preview &amp; Organize Files →
          </button>
        </div>
      </div>` : `
      <div class="action-banner ok">
        <div class="action-banner-body">
          <span class="action-banner-badge" style="background:var(--success)">All Clean</span>
          <div class="action-banner-title">No loose files in “${esc(baseName(state.folder))}”</div>
          <div class="action-banner-text">This folder is already neat and organized! Choose another folder to scan and organize.</div>
        </div>
        <div class="action-banner-btns">
          <button class="btn btn-secondary" data-action="browse">${I.folderPlus}Choose another folder</button>
        </div>
      </div>`;

    const composition = d.total_files ? `
      <div class="stack-bar">
        ${cats.map(([c, v]) => `<span style="flex:${Math.max(v.size, 1)};background:${catColor(c)}" title="${esc(c)} · ${esc(v.formatted_size)}"></span>`).join('')}
      </div>
      <div class="legend">
        ${cats.map(([c, v]) => `
          <div class="legend-item">
            <span class="legend-dot" style="background:${catColor(c)}"></span>
            <span class="legend-name">${esc(c)}</span>
            <span class="legend-val">${plural(v.count, 'file')} · ${esc(v.formatted_size)}</span>
            <span class="legend-pct">${d.total_size ? Math.round(v.size / d.total_size * 100) : 0}%</span>
          </div>`).join('')}
      </div>`
      : emptyState(I.checkCircle, 'Nothing loose here', 'There are no files directly in this folder — it\'s already tidy.');

    const largest = d.top_files.length ? d.top_files.map((f, i) => `
      <div class="row" data-path="${esc(f.path)}" data-title="${esc(f.name)}">
        <span class="row-rank">${i + 1}</span>
        ${fileBadge(f.name, f.category)}
        <div class="row-main"><div class="row-title" title="${esc(f.name)}">${esc(f.name)}</div><div class="row-sub">${esc(f.category)}</div></div>
        ${rowActions(f.path)}
        <span class="row-num">${esc(f.formatted_size)}</span>
      </div>`).join('')
      : emptyState(I.file, 'No files', 'There are no loose files in this folder.');

    const subRows = subs.slice(0, subfolderLimit).map(s => `
      <div class="row" data-path="${esc(s.path)}" data-title="${esc(s.name)}">
        ${folderBadge('#a78bfa')}
        <div class="row-main"><div class="row-title" title="${esc(s.name)}">${esc(s.name)}</div><div class="row-sub">${plural(s.count, 'file')}</div></div>
        ${rowActions(s.path)}
        <div class="meter"><span style="width:${subTotal ? Math.max(2, s.size / subTotal * 100) : 0}%"></span></div>
        <span class="row-num" style="width:70px">${esc(s.formatted_size)}</span>
      </div>`).join('');

    mount(header('Folder Overview', esc(state.folder), actions) + `
      ${workflowSteps}
      ${banner}

      <div class="stats">
        ${stat('Files to organize', fmtNum(d.total_files), 'In this root directory', I.files, 'accent')}
        ${stat('Total files size', d.formatted_size, d.total_files ? `Avg ${fmtSize(d.total_size / d.total_files)} per file` : '—', I.disk)}
        ${stat('Subfolders', fmtNum(subs.length), subs.length ? `${fmtSize(subTotal)} inside` : 'None', I.folder)}
        ${stat('Largest type', topCat ? topCat[0] : '—', topCat ? `${topCat[1].formatted_size} · ${plural(topCat[1].count, 'file')}` : 'No files', I.chart)}
      </div>

      <div class="card section">
        <div class="card-header">
          <span class="card-title">What's in this folder</span>
          <span class="card-meta">${plural(d.total_files, 'file')} · ${esc(d.formatted_size)}</span>
        </div>
        <div class="card-pad">${composition}</div>
      </div>

      <div class="grid-2 section">
        <div class="card">
          <div class="card-header"><span class="card-title">Largest files</span><span class="card-meta">Right-click for options</span></div>
          <div class="list">${largest}</div>
        </div>
        <div class="card">
          <div class="card-header"><span class="card-title">Subfolders</span><span class="card-meta">${subs.length ? 'By size' : ''}</span></div>
          <div class="list">
            ${subRows || emptyState(I.folder, 'No subfolders', 'This folder has no subfolders yet.')}
          </div>
          ${subs.length > subfolderLimit ? `<button class="show-more" data-action="more-subs">Show ${fmtNum(subs.length - subfolderLimit)} more</button>` : ''}
        </div>
      </div>`);
  };

  // ── Organize ───────────────────────────────────────────────────────────
  views.organize = async token => {
    if (!state.folder) return renderWelcome();
    if (state.lastRun && state.lastRun.target === state.folder) return renderRunResult();

    if (!state.preview || state.preview.folder !== state.folder) {
      const job = await runJob('preview', { path: state.folder }, {
        title: 'Preparing preview', sub: 'Working out where each file belongs…', cancellable: true,
        errorTitle: "Couldn't prepare the preview",
      }, token);
      if (token !== viewToken) return;
      if (!job) return mount(header('Organize', esc(state.folder)) + errorState('The preview could not be created.'));
      if (job.status === 'cancelled') {
        return mount(header('Organize', esc(state.folder)) + `<div class="card">${emptyState(I.skip, 'Preview stopped',
          'The preview was cancelled before it finished.', `<button class="btn btn-secondary" data-action="refresh-preview">${I.refresh}Try again</button>`)}</div>`);
      }
      state.preview = { folder: state.folder, data: job.result };
    }
    renderPreview();
  };

  function buildGroups(items) {
    const map = new Map();
    const skipped = [];
    for (const it of items) {
      if (it.status === 'moved' || it.status === 'duplicate') {
        const key = it.folder || '.';
        if (!map.has(key)) map.set(key, { key, name: key, items: [], size: 0, color: catColor(key), limit: 100, open: false });
        const g = map.get(key);
        g.items.push(it);
        g.size += it.size || 0;
      } else {
        skipped.push(it);
      }
    }
    const groups = [...map.values()].sort((a, b) => b.items.length - a.items.length);
    if (skipped.length) {
      groups.push({ key: '__skipped', name: 'Left in place', items: skipped, size: 0, color: '#6c6c7c', limit: 100, open: false, skipped: true });
    }
    if (groups.length && !groups[0].skipped) groups[0].open = true;
    return groups;
  }

  function groupRows(g) {
    const rows = g.items.slice(0, g.limit).map(it => {
      const sub = g.skipped ? esc(it.reason || 'Skipped')
        : it.status === 'duplicate' ? `<span style="color:var(--warning)">Duplicate</span> · ${esc(it.reason)}`
        : esc(it.rule || '');
      return `
        <div class="row" data-path="${esc(it.source)}" data-title="${esc(it.file)}">
          ${fileBadge(it.file, g.skipped ? '' : it.folder)}
          <div class="row-main"><div class="row-title" title="${esc(it.file)}">${esc(it.file)}</div><div class="row-sub">${sub}</div></div>
          <span class="row-num">${it.size != null ? fmtSize(it.size) : ''}</span>
        </div>`;
    }).join('');
    const more = g.items.length > g.limit
      ? `<button class="show-more" data-action="group-more" data-key="${esc(g.key)}">Show ${fmtNum(Math.min(500, g.items.length - g.limit))} more of ${fmtNum(g.items.length - g.limit)}</button>` : '';
    return rows + more;
  }

  function groupCard(g) {
    const parts = g.name.split('/');
    const label = g.skipped ? esc(g.name)
      : parts.length > 1 ? `<span class="faint">${esc(parts.slice(0, -1).join(' / '))} / </span>${esc(parts[parts.length - 1])}` : esc(g.name);
    return `
      <div class="card group ${g.open ? 'open' : ''}" data-group="${esc(g.key)}">
        <button class="group-head" data-action="toggle-group" data-key="${esc(g.key)}">
          <span class="group-chevron">${I.chevron}</span>
          ${g.skipped ? `<div class="file-icon" style="background:var(--surface-3);color:var(--text-3)">${I.skip}</div>` : folderBadge(g.color)}
          <span class="group-name">${label}</span>
          <span class="pill ${g.skipped ? '' : 'accent'}">${plural(g.items.length, 'file')}</span>
          ${g.skipped ? '' : `<span class="row-num" style="width:64px">${fmtSize(g.size)}</span>`}
        </button>
        <div class="group-body">${g.open ? groupRows(g) : ''}</div>
      </div>`;
  }

  function renderPreview() {
    const d = state.preview.data;
    const toMove = d.moved + d.duplicates;
    previewGroups = buildGroups(d.items);
    const destCount = previewGroups.filter(g => !g.skipped).length;
    const left = d.skipped + d.errors;

    const actions = `
      <button class="btn btn-ghost" data-action="refresh-preview">${I.refresh}Refresh</button>
      <button class="btn btn-primary" data-action="organize" ${toMove ? '' : 'disabled'}>${I.folderCheck}Organize ${plural(toMove, 'file')}</button>`;

    if (!d.total) {
      return mount(header('Preview Organization Plan', esc(state.folder), actions) + `<div class="card">${emptyState(I.checkCircle, 'Nothing to organize',
        'There are no loose files in this folder. Files inside subfolders are never touched.')}</div>`);
    }

    const workflowSteps = `
      <div class="workflow-steps">
        <div class="workflow-step done"><span class="step-bubble">✓</span> 1. Folder Scanned</div>
        <span class="workflow-sep">→</span>
        <div class="workflow-step active"><span class="step-bubble">2</span> 2. Preview Plan</div>
        <span class="workflow-sep">→</span>
        <div class="workflow-step"><span class="step-bubble">3</span> 3. Organized</div>
      </div>`;

    const banner = `
      <div class="action-banner">
        <div class="action-banner-body">
          <span class="action-banner-badge">Step 2: Preview Plan</span>
          <div class="action-banner-title">Ready to organize ${plural(toMove, 'file')} into ${plural(destCount, 'folder')}?</div>
          <div class="action-banner-text">Click any category folder below to see what files will go inside. <strong>No files are moved until you click Start Organizing.</strong> You can undo this entire run anytime from History.</div>
        </div>
        <div class="action-banner-btns">
          <button class="btn btn-primary btn-lg" data-action="organize" ${toMove ? '' : 'disabled'}>
            ${I.folderCheck} Start Organizing (${plural(toMove, 'file')})
          </button>
        </div>
      </div>`;

    mount(header('Preview Organization Plan', 'Check where files will move — nothing changes until you confirm.', actions) + `
      ${workflowSteps}
      ${banner}

      <div class="stats">
        ${stat('Files to move', fmtNum(toMove), d.moved_size, I.files, 'accent')}
        ${stat('Destination folders', fmtNum(destCount), destCount ? 'Created inside target' : '—', I.layers)}
        ${stat('Exact duplicates', fmtNum(d.duplicates), d.duplicates ? 'Moved to “Duplicates”' : 'No duplicates found', I.copy, d.duplicates ? 'warn' : '')}
        ${stat('Left in place', fmtNum(left), left ? 'System or in-progress files' : 'Nothing skipped', I.skip)}
      </div>

      <div class="section">
        <div class="section-title">
          <span>Categorized Folders (Click to inspect files)</span>
          <span style="display:flex;gap:4px;text-transform:none;letter-spacing:0">
            <button class="btn btn-ghost btn-sm" data-action="expand-all">Expand all</button>
            <button class="btn btn-ghost btn-sm" data-action="collapse-all">Collapse all</button>
          </span>
        </div>
        <div class="groups" id="groups">${previewGroups.map(groupCard).join('')}</div>
      </div>

      <div class="notice section">${I.shield}
        <div><strong>Zero Risk:</strong> Files inside existing subfolders are never touched. You can safely revert all movements anytime with 1-click Undo from the History tab.</div>
      </div>`);
  }

  function rerenderGroup(key) {
    const g = previewGroups.find(x => x.key === key);
    const el = document.querySelector(`.group[data-group="${CSS.escape(key)}"]`);
    if (!g || !el) return;
    el.outerHTML = groupCard(g);
  }

  async function doOrganize() {
    const d = state.preview && state.preview.data;
    if (!d) return;
    const n = d.moved + d.duplicates;
    const ok = await confirmModal({
      title: `Organize ${plural(n, 'file')}?`,
      message: `Files in “${baseName(state.folder)}” will be moved into category folders. You can undo this at any time from History.`,
      confirm: 'Organize', icon: I.folderCheck,
    });
    if (!ok) return;

    state.busy = true;
    const token = ++viewToken;
    const job = await runJob('organize', { path: state.folder }, {
      title: 'Organizing files', sub: 'Moving files into place…', cancellable: true, cancelLabel: 'Stop',
      errorTitle: 'Organizing failed',
    }, token);
    state.busy = false;
    state.preview = null;
    state.scan = null;

    if (!job) return render();
    state.lastRun = { ...job.result, cancelled: job.status === 'cancelled' };
    render();
  }

  function renderRunResult() {
    const r = state.lastRun;
    const moved = r.moved + r.duplicates;
    const folders = new Map();
    r.items.forEach(it => {
      if (it.status === 'moved' || it.status === 'duplicate') folders.set(it.folder, (folders.get(it.folder) || 0) + 1);
    });
    const failed = r.items.filter(it => it.status === 'error');
    const title = r.cancelled ? `Stopped after ${plural(moved, 'file')}` : moved ? `${plural(moved, 'file')} organized` : 'Nothing was moved';

    const workflowSteps = `
      <div class="workflow-steps">
        <div class="workflow-step done"><span class="step-bubble">✓</span> 1. Scanned</div>
        <span class="workflow-sep">→</span>
        <div class="workflow-step done"><span class="step-bubble">✓</span> 2. Previewed</div>
        <span class="workflow-sep">→</span>
        <div class="workflow-step active done" style="color:var(--accent-text)"><span class="step-bubble" style="background:var(--gradient);color:#fff">✓</span> 3. Organized!</div>
      </div>`;

    mount(`
      ${workflowSteps}
      <div class="card" style="margin-top:8px">
        <div class="hero" style="padding:40px 24px 30px">
          <div class="result-icon ${r.cancelled || failed.length ? 'warn' : ''}">${r.cancelled || failed.length ? I.alert : I.check}</div>
          <h1>${esc(title)}</h1>
          <p>${moved ? `Moved into ${plural(folders.size, 'folder')} inside “${esc(baseName(r.target))}” · ${esc(r.moved_size)}` : 'No files needed to be moved.'}</p>
          <div class="result-actions">
            ${moved && r.batch_id ? `<button class="btn btn-secondary" data-action="undo-batch" data-id="${r.batch_id}" data-count="${moved}" data-label="${esc(baseName(r.target))}">${I.undo}Undo All</button>` : ''}
            <button class="btn btn-secondary" data-action="reveal" data-path="${esc(r.target)}">${I.external}Show in File Explorer</button>
            <button class="btn btn-primary" data-action="done">Back to Overview</button>
          </div>
        </div>
      </div>

      ${failed.length ? `
        <div class="card section">
          <div class="card-header"><span class="card-title">Couldn't be moved</span><span class="pill danger">${plural(failed.length, 'file')}</span></div>
          <div class="list">
            ${failed.slice(0, 200).map(it => `
              <div class="row" data-path="${esc(it.source)}" data-title="${esc(it.file)}">
                ${fileBadge(it.file, '')}
                <div class="row-main"><div class="row-title">${esc(it.file)}</div><div class="row-sub">${esc(it.reason)}</div></div>
              </div>`).join('')}
          </div>
        </div>` : ''}

      ${folders.size ? `
        <div class="card section">
          <div class="card-header"><span class="card-title">Folders updated</span><span class="card-meta">${plural(folders.size, 'folder')}</span></div>
          <div class="list">
            ${[...folders.entries()].sort((a, b) => b[1] - a[1]).map(([f, c]) => {
              const full = r.target.replace(/[\\/]+$/, '') + '\\' + f.replace(/\//g, '\\');
              return `
                <div class="row" data-path="${esc(full)}" data-title="${esc(f)}">
                  ${folderBadge(catColor(f))}
                  <div class="row-main"><div class="row-title">${esc(f.replace(/\//g, ' / '))}</div></div>
                  ${rowActions(full)}
                  <span class="row-num">${plural(c, 'file')}</span>
                </div>`;
            }).join('')}
          </div>
        </div>` : ''}`);
  }

  // ── Undo ───────────────────────────────────────────────────────────────
  async function doUndo(batchId, count, label) {
    const ok = await confirmModal({
      title: `Undo ${plural(count, 'move')}?`,
      message: `Files will be returned to where they were${label ? ` in “${label}”` : ''}. Folders created by SmartSort are removed if they end up empty.`,
      confirm: 'Undo', icon: I.undo,
    });
    if (!ok) return;

    state.busy = true;
    const token = ++viewToken;
    const job = await runJob('undo', { batch_id: batchId }, {
      title: 'Restoring files', sub: 'Putting files back where they were…', errorTitle: 'Undo failed',
    }, token);
    state.busy = false;
    state.scan = state.preview = state.lastRun = null;

    if (job) {
      const r = job.result;
      const notes = [];
      if (r.renamed) notes.push(`${plural(r.renamed, 'file')} renamed to avoid overwriting`);
      if (r.missing) notes.push(`${plural(r.missing, 'file')} no longer existed`);
      if (r.failed) notes.push(`${plural(r.failed, 'file')} could not be restored`);
      toast(r.failed ? 'error' : 'success', `Restored ${plural(r.restored, 'file')}`, notes.join(' · '));
    }
    setView('history');
  }

  // ── History ────────────────────────────────────────────────────────────
  views.history = async token => {
    const head = header('History & Undo', 'Every organize run is saved here and can be undone with one click.');
    const guidance = `
      <div class="notice" style="margin-bottom:16px">${I.shield}
        <div><strong>Revert anytime:</strong> Made a mistake or want files back where they came from? Click the <strong>Undo</strong> button next to any session below to restore all files immediately.</div>
      </div>`;

    mount(head + guidance + `<div class="card">${'<div class="row"><div class="skeleton" style="height:30px;flex:1;border:0"></div></div>'.repeat(4)}</div>`);
    const r = await api('history', { limit: 100 });
    if (token !== viewToken) return;
    if (!r.success) return mount(head + guidance + errorState(r.error));
    if (!r.batches.length) {
      return mount(head + guidance + `<div class="card">${emptyState(I.clock, 'No past organize sessions yet',
        'When you organize a folder, a snapshot will appear here with a 1-click Undo button.',
        `<button class="btn btn-secondary" data-action="goto-organize">${I.folderCheck}Go to Organize</button>`)}</div>`);
    }

    mount(head + guidance + `<div class="card list">${r.batches.map(b => {
      const undone = b.remaining === 0;
      const partial = !undone && b.remaining < b.total;
      const name = b.target_dir ? baseName(b.target_dir) : 'Earlier activity';
      const status = undone ? '<span class="pill">Undone</span>'
        : partial ? '<span class="pill warn"><span class="dot"></span>Partly undone</span>'
        : '<span class="pill ok"><span class="dot"></span>Applied</span>';
      return `
        <div data-batch="${b.id}">
          <div class="row" style="${undone ? 'opacity:.6' : ''}">
            ${folderBadge(undone ? '#6c6c7c' : '#a78bfa')}
            <div class="row-main">
              <div class="row-title">${esc(name)}</div>
              <div class="row-sub" title="${esc(fullTime(b.created_at))}">${esc(relTime(b.created_at))}${b.target_dir ? ' · ' + esc(b.target_dir) : ''}</div>
            </div>
            <span class="row-num">${plural(b.total, 'file')}</span>
            ${status}
            <button class="btn btn-ghost btn-sm" data-action="batch-details" data-id="${b.id}">Details</button>
            ${undone ? '<span style="width:70px"></span>' : `<button class="btn btn-secondary btn-sm" style="width:70px" data-action="undo-batch" data-id="${b.id}" data-count="${b.remaining}" data-label="${esc(name)}">${I.undo}Undo</button>`}
          </div>
          <div class="batch-details hidden" style="background:var(--bg-side);border-bottom:1px solid var(--border)"></div>
        </div>`;
    }).join('')}</div>`);
  };

  async function toggleBatchDetails(id) {
    const wrap = document.querySelector(`[data-batch="${id}"] .batch-details`);
    if (!wrap) return;
    if (!wrap.classList.contains('hidden')) { wrap.classList.add('hidden'); return; }
    wrap.classList.remove('hidden');
    if (wrap.dataset.loaded) return;
    wrap.innerHTML = '<div class="row"><div class="spinner"></div><span class="muted">Loading…</span></div>';
    const r = await api('history/batch', { id });
    if (!r.success) { wrap.innerHTML = `<div class="row muted">${esc(r.error)}</div>`; return; }
    wrap.dataset.loaded = '1';
    const LIMIT = 300;
    wrap.innerHTML = r.moves.slice(0, LIMIT).map(m => {
      const name = baseName(m.src);
      const destFolder = baseName(m.dest.slice(0, Math.max(m.dest.lastIndexOf('\\'), m.dest.lastIndexOf('/'))));
      return `
        <div class="row" style="padding-left:62px" data-path="${esc(m.undone ? m.src : m.dest)}" data-title="${esc(name)}">
          ${fileBadge(name, destFolder)}
          <div class="row-main"><div class="row-title">${esc(name)}</div><div class="row-sub">→ ${esc(destFolder)}${m.rule ? ' · ' + esc(m.rule) : ''}</div></div>
          ${m.undone ? '<span class="pill">Restored</span>' : rowActions(m.dest)}
        </div>`;
    }).join('') + (r.moves.length > LIMIT ? `<div class="row faint" style="padding-left:62px">and ${fmtNum(r.moves.length - LIMIT)} more…</div>` : '');
  }

  // ── Rules ──────────────────────────────────────────────────────────────
  views.rules = async token => {
    const sub = 'Rules are checked from top to bottom — the first one that matches decides where a file goes.';
    mount(header('Rules', sub) + '<div class="skeleton" style="height:380px"></div>');
    const r = await api('rules', {});
    if (token !== viewToken) return;
    if (!r.success) return mount(header('Rules', sub) + errorState(r.error));

    const chips = (list, max = 14) => list.slice(0, max).map(x => `<span class="chip">${esc(x)}</span>`).join('')
      + (list.length > max ? `<span class="chip">+${list.length - max}</span>` : '');
    const rows = r.rules.map((rule, i) => `
      <div class="rule">
        <div class="rule-index">${i + 1}</div>
        <div class="rule-main">
          <div class="rule-top">
            <span class="rule-name">${esc(rule.name)}</span>
            <span class="rule-arrow">${I.arrow}</span>
            <span class="pill" style="background:${catColor(rule.destination)}1f;color:${catColor(rule.destination)}">${I.folder}${esc(rule.destination)}</span>
          </div>
          ${rule.name_contains.length ? `<div class="chips" style="margin-bottom:6px"><span class="rule-cond">Name contains</span>${chips(rule.name_contains)}</div>` : ''}
          ${rule.extensions.length ? `<div class="chips" style="margin-bottom:6px"><span class="rule-cond">File types</span>${chips(rule.extensions)}</div>` : ''}
          ${rule.has_exif_date ? '<div class="chips"><span class="rule-cond">Only photos with a capture date</span></div>' : ''}
        </div>
      </div>`).join('');

    mount(header('Rules', sub, `<button class="btn btn-secondary" data-action="reveal" data-path="${esc(r.path)}">${I.external}Open rules file</button>`) + `
      <div class="card">
        ${rows}
        <div class="rule">
          <div class="rule-index">${r.rules.length + 1}</div>
          <div class="rule-main"><div class="rule-top" style="margin:0">
            <span class="rule-name">Everything else</span><span class="rule-arrow">${I.arrow}</span>
            <span class="pill">${I.folder}Unsorted</span>
          </div></div>
        </div>
      </div>
      <div class="notice section">${I.info}
        <div>To change rules, edit <strong>rules.yaml</strong> in any text editor, save it, then reopen this page.
        Destinations can use <span class="chip">{year}</span> <span class="chip">{month}</span> <span class="chip">{day}</span> from the photo's capture date (or the file date).</div>
      </div>`);
  };

  // ── Help ───────────────────────────────────────────────────────────────
  views.help = () => {
    mount(header('Help', 'Everything you need to know to get started.') + `
      <div class="steps">
        <div class="card step"><div class="step-num">1</div><h3>Choose a folder</h3><p>Pick a messy folder such as Downloads or Desktop. The Overview shows what's inside.</p></div>
        <div class="card step"><div class="step-num">2</div><h3>Review the preview</h3><p>Organize shows exactly where each file will go. Nothing moves until you confirm.</p></div>
        <div class="card step"><div class="step-num">3</div><h3>Organize or undo</h3><p>Files are moved instantly. Changed your mind? Undo the whole run from History.</p></div>
      </div>
      <div class="section-title section" style="margin-top:26px">Common questions</div>
      <div class="card faq">
        <div class="faq-item"><h4>Which files are moved?</h4><p>Only files directly inside the selected folder. Existing subfolders and their contents are never touched.</p></div>
        <div class="faq-item"><h4>What gets left alone?</h4><p>System files (like desktop.ini), hidden files, Office lock files and unfinished downloads (.crdownload, .part, .tmp). Files open in another program are skipped and listed after the run.</p></div>
        <div class="faq-item"><h4>How are duplicates handled?</h4><p>If an identical file (same content) already exists in the destination, the new copy goes into a “Duplicates” folder so you can review it. Nothing is ever deleted.</p></div>
        <div class="faq-item"><h4>What if a file name already exists?</h4><p>SmartSort never overwrites. It adds a number, e.g. “report (1).pdf”. Undo works the same way and adds “(restored)” if needed.</p></div>
        <div class="faq-item"><h4>Shortcuts</h4><p><kbd>Ctrl</kbd> + <kbd>O</kbd> choose a folder · right-click any file or folder for more options.</p></div>
      </div>`);
  };

  // ── Context menu ───────────────────────────────────────────────────────
  const menu = $('#contextMenu');
  let menuPath = '';
  function hideContextMenu() { menu.classList.add('hidden'); menuPath = ''; }
  page.addEventListener('contextmenu', e => {
    const row = e.target.closest('[data-path]');
    e.preventDefault();
    if (!row || state.busy) return hideContextMenu();
    menuPath = row.dataset.path;
    $('#contextTitle').textContent = row.dataset.title || baseName(menuPath);
    menu.classList.remove('hidden');
    const w = menu.offsetWidth, h = menu.offsetHeight;
    menu.style.left = Math.max(8, Math.min(e.clientX, innerWidth - w - 8)) + 'px';
    menu.style.top = Math.max(8, Math.min(e.clientY, innerHeight - h - 8)) + 'px';
  });
  document.addEventListener('contextmenu', e => { if (!page.contains(e.target)) e.preventDefault(); });
  document.addEventListener('mousedown', e => { if (!menu.contains(e.target)) hideContextMenu(); });
  window.addEventListener('blur', hideContextMenu);
  window.addEventListener('resize', hideContextMenu);
  page.addEventListener('scroll', hideContextMenu, { passive: true });

  menu.addEventListener('click', async e => {
    const item = e.target.closest('[data-menu]');
    if (!item || !menuPath) return;
    const path = menuPath;
    hideContextMenu();
    if (item.dataset.menu === 'reveal') reveal(path);
    if (item.dataset.menu === 'copy') {
      try { await navigator.clipboard.writeText(path); toast('success', 'Path copied'); }
      catch { toast('error', "Couldn't copy the path"); }
    }
    if (item.dataset.menu === 'delete') deleteItem(path);
  });

  async function reveal(path) {
    let ok;
    if (await waitForDesktop()) ok = await window.pywebview.api.open_location(path);
    else ok = (await api('open-location', { path })).success;
    if (!ok) toast('error', "Couldn't open File Explorer", 'The item may have been moved or deleted.');
  }

  async function deleteItem(path) {
    const name = baseName(path);
    const ok = await confirmModal({
      title: `Move “${name}” to the Recycle Bin?`,
      message: 'You can restore it from the Recycle Bin later.',
      confirm: 'Move to Recycle Bin', danger: true, icon: I.trash,
    });
    if (!ok) return;
    let success;
    if (await waitForDesktop()) success = await window.pywebview.api.delete_item(path);
    else success = (await api('delete-item', { path })).success;
    if (success) {
      toast('success', 'Moved to Recycle Bin', name);
      state.scan = state.preview = null;
      if (state.view === 'overview' || state.view === 'organize') render();
    } else {
      toast('error', "Couldn't delete", `“${name}” may be open in another program.`);
    }
  }

  // ── Actions (event delegation) ─────────────────────────────────────────
  const actions = {
    'browse': chooseFolder,
    'open-recent': el => setFolder(el.dataset.folder),
    'reveal': el => reveal(el.dataset.path),
    'refresh-scan': () => { state.scan = null; render(); },
    'refresh-preview': () => { state.preview = null; render(); },
    'goto-organize': () => setView('organize'),
    'more-subs': () => { subfolderLimit += 50; render(); },
    'organize': doOrganize,
    'done': () => { state.lastRun = null; setView('overview'); },
    'undo-batch': el => doUndo(Number(el.dataset.id), Number(el.dataset.count), el.dataset.label),
    'batch-details': el => toggleBatchDetails(el.dataset.id),
    'toggle-group': el => {
      const g = previewGroups.find(x => x.key === el.dataset.key);
      if (!g) return;
      g.open = !g.open;
      rerenderGroup(g.key);
    },
    'group-more': el => {
      const g = previewGroups.find(x => x.key === el.dataset.key);
      if (!g) return;
      g.limit += 500;
      rerenderGroup(g.key);
    },
    'expand-all': () => { previewGroups.forEach(g => { g.open = true; }); $('#groups').innerHTML = previewGroups.map(groupCard).join(''); },
    'collapse-all': () => { previewGroups.forEach(g => { g.open = false; }); $('#groups').innerHTML = previewGroups.map(groupCard).join(''); },
    'clean-empty': async () => {
      const ok = await confirmModal({
        title: 'Remove empty folders?',
        message: `Empty subfolders inside “${baseName(state.folder)}” will be deleted. Folders that contain anything are kept.`,
        confirm: 'Remove empty folders', icon: I.broom,
      });
      if (!ok) return;
      const r = await api('clean-empty', { path: state.folder });
      if (!r.success) return toast('error', "Couldn't remove folders", r.error);
      toast('success', r.removed.length ? `Removed ${plural(r.removed.length, 'empty folder')}` : 'No empty folders found');
      state.scan = null;
      render();
    },
  };

  page.addEventListener('click', e => {
    const el = e.target.closest('[data-action]');
    if (!el || el.disabled) return;
    e.stopPropagation();
    const fn = actions[el.dataset.action];
    if (fn) fn(el);
  });

  // ── Global bindings ────────────────────────────────────────────────────
  document.querySelectorAll('.nav-item[data-view]').forEach(n => n.addEventListener('click', () => setView(n.dataset.view)));
  $('#browseBtn').addEventListener('click', chooseFolder);
  $('#folderBar').addEventListener('click', chooseFolder);
  $('#revealFolderBtn').addEventListener('click', e => { e.stopPropagation(); if (state.folder) reveal(state.folder); });
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'o') { e.preventDefault(); chooseFolder(); }
    if (e.key === 'Escape') hideContextMenu();
  });

  api('info').then(r => { if (r.success) $('#appVersion').textContent = `Version ${r.version}`; });

  updateFolderBar();
  setView('overview');
})();
