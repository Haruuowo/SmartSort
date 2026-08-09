document.addEventListener('DOMContentLoaded', () => {
  // ── DOM Elements ──
  const targetPathInput = document.getElementById('targetPath');
  const contentArea = document.getElementById('contentArea');
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');

  const browseBtn = document.getElementById('browseBtn');
  const scanBtn = document.getElementById('scanBtn');
  const dryRunBtn = document.getElementById('dryRunBtn');
  const organizeBtn = document.getElementById('organizeBtn');
  const topFilesBtn = document.getElementById('topFilesBtn');
  const cleanEmptyBtn = document.getElementById('cleanEmptyBtn');
  const undoBtn = document.getElementById('undoBtn');
  const helpNavBtn = document.getElementById('helpNavBtn');
  const helpModal = document.getElementById('helpModal');
  const closeHelpBtn = document.getElementById('closeHelpBtn');

  const navItems = document.querySelectorAll('.nav-item[data-view]');
  const actionBtns = document.querySelectorAll('.ribbon-btn, .btn-primary');

  // ── Status Helper ──
  function setStatus(text, busy = false) {
    statusText.textContent = text;
    if (busy) {
      statusDot.classList.add('busy');
    } else {
      statusDot.classList.remove('busy');
    }
  }

  function setLoading(loading, message = 'Processing...') {
    actionBtns.forEach(btn => {
      if (loading) btn.classList.add('disabled');
      else btn.classList.remove('disabled');
    });

    if (loading) {
      setStatus(message, true);
      contentArea.innerHTML = `
        <div class="loading-state">
          <div class="spinner"></div>
          <p>${message}</p>
        </div>
      `;
    }
  }

  // ── Welcome View ──
  function renderWelcome() {
    contentArea.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
          </svg>
        </div>
        <h3>Select a folder to organize</h3>
        <p>Choose a target directory using the Browse Folder button above, then scan or organize your files.</p>
      </div>
    `;
  }

  // ── Documentation View ──
  function renderDocumentation() {
    setStatus('Documentation', false);
    contentArea.innerHTML = `
      <div style="max-width: 800px; margin: 0 auto; display: flex; flex-direction: column; gap: 24px;">
        <div style="border-bottom: 1px solid var(--border-subtle); padding-bottom: 12px;">
          <h2 style="font-size: 18px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">SmartSort User Manual & Workflow Guide</h2>
          <p style="color: var(--text-muted); font-size: 13px;">Complete step-by-step visual workflow for organizing your files safely.</p>
        </div>

        <!-- Step 1 Card -->
        <div class="metric-card" style="padding: 20px;">
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
            <span class="badge accent" style="font-size: 12px; padding: 4px 10px;">Step 1</span>
            <h3 style="font-size: 15px; font-weight: 600;">Select Target Directory</h3>
          </div>
          <p style="color: var(--text-secondary); font-size: 13px; line-height: 1.6; margin-bottom: 12px;">
            Click the <strong style="color: var(--text-primary);">Browse Folder</strong> button in the top bar to open the Windows folder browser dialog. Choose any directory (e.g. <code>Downloads</code>, <code>Desktop</code>, or <code>Unsorted</code>) you wish to clean up.
          </p>
          <div class="folder-selector" style="max-width: 100%; pointer-events: none; opacity: 0.85;">
            <span class="icon-wrap">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>
            </span>
            <input type="text" value="C:/Users/Downloads" readonly />
            <button class="btn-secondary" style="height: 28px; font-size: 11px;">Browse Folder</button>
          </div>
        </div>

        <!-- Step 2 Card -->
        <div class="metric-card" style="padding: 20px;">
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
            <span class="badge accent" style="font-size: 12px; padding: 4px 10px;">Step 2</span>
            <h3 style="font-size: 15px; font-weight: 600;">Scan Storage Breakdown</h3>
          </div>
          <p style="color: var(--text-secondary); font-size: 13px; line-height: 1.6; margin-bottom: 12px;">
            Click <strong style="color: var(--text-primary);">Scan Directory</strong> to inspect category size breakdown and find your largest files before moving anything. SmartSort classifies files by content signature (file magic bytes), not just extensions.
          </p>
          <div class="metrics-grid" style="margin-bottom: 0;">
            <div class="metric-card" style="background: var(--bg-surface-raised);">
              <div class="label">Total Size</div>
              <div class="value" style="font-size: 18px;">14.2 GB</div>
            </div>
            <div class="metric-card" style="background: var(--bg-surface-raised);">
              <div class="label">Total Files</div>
              <div class="value" style="font-size: 18px;">342</div>
            </div>
            <div class="metric-card" style="background: var(--bg-surface-raised);">
              <div class="label">Categories</div>
              <div class="value" style="font-size: 18px;">6</div>
            </div>
          </div>
        </div>

        <!-- Step 3 Card -->
        <div class="metric-card" style="padding: 20px;">
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
            <span class="badge accent" style="font-size: 12px; padding: 4px 10px;">Step 3</span>
            <h3 style="font-size: 15px; font-weight: 600;">Test with Dry Run (Simulation)</h3>
          </div>
          <p style="color: var(--text-secondary); font-size: 13px; line-height: 1.6; margin-bottom: 12px;">
            Click <strong style="color: var(--text-primary);">Dry Run (Test)</strong> to simulate rule execution safely. SmartSort will show you exactly where each file would be moved without modifying any files on disk.
          </p>
          <div style="background: var(--bg-surface-raised); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle); padding: 12px; font-family: var(--font-mono); font-size: 12px; color: var(--text-secondary);">
            [SIMULATION] Sample_Report.pdf ──> Documents/Sample_Report.pdf<br>
            [SIMULATION] Photo_2026.jpg ──> Photos/2026/08/Photo_2026.jpg (EXIF Date)
          </div>
        </div>

        <!-- Step 4 Card -->
        <div class="metric-card" style="padding: 20px;">
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
            <span class="badge accent" style="font-size: 12px; padding: 4px 10px;">Step 4</span>
            <h3 style="font-size: 15px; font-weight: 600;">Organize Files Automatically</h3>
          </div>
          <p style="color: var(--text-secondary); font-size: 13px; line-height: 1.6;">
            Click <strong style="color: var(--text-primary);">Organize Files</strong> to execute sorting. Files are grouped into clean subfolders (Documents, Photos by EXIF year/month, Installers, Videos, Music) and exact duplicates are automatically detected and skipped.
          </p>
        </div>

        <!-- Step 5 Card -->
        <div class="metric-card" style="padding: 20px;">
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
            <span class="badge accent" style="font-size: 12px; padding: 4px 10px;">Step 5</span>
            <h3 style="font-size: 15px; font-weight: 600;">History & One-Click Undo</h3>
          </div>
          <p style="color: var(--text-secondary); font-size: 13px; line-height: 1.6;">
            Every file move is logged into an internal SQLite database. Click <strong style="color: var(--text-primary);">Undo</strong> or visit the <strong style="color: var(--text-primary);">History & Undo</strong> tab anytime to restore moved files to their original location.
          </p>
        </div>
      </div>
    `;
  }

  // ── API Call Helper ──
  async function apiCall(endpoint, payload = {}) {
    try {
      let port = window.API_PORT || window.location.port || 7860;
      if (window.pywebview && window.pywebview.api && window.pywebview.api.get_api_port) {
        try {
          const apiPort = await window.pywebview.api.get_api_port();
          if (apiPort) port = apiPort;
        } catch (e) {}
      }

      const baseUrl = window.location.protocol.startsWith('http') ? '' : `http://127.0.0.1:${port}`;
      const res = await fetch(`${baseUrl}/api/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const text = await res.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch (e) {
        throw new Error(`Server returned invalid response (${res.status})`);
      }
      if (!res.ok) {
        throw new Error(data.error || `HTTP Error ${res.status}`);
      }
      return data;
    } catch (err) {
      setLoading(false);
      setStatus('Error', false);
      renderMessage('Error', `Operation failed: ${err.message}`);
      return { success: false, error: err.message };
    }
  }

  function renderMessage(title, text) {
    contentArea.innerHTML = `
      <div class="data-table-container" style="padding: 20px;">
        <h4 style="margin-bottom: 6px; font-weight: 600;">${title}</h4>
        <p style="color: var(--text-secondary); font-size: 13px;">${text}</p>
      </div>
    `;
  }

  // ── Actions ──

  // 1. Browse Folder
  async function browseFolder() {
    setStatus('Opening folder browser...', true);
    let selectedPath = '';

    if (window.pywebview && window.pywebview.api && window.pywebview.api.browse_folder) {
      try {
        selectedPath = await window.pywebview.api.browse_folder();
      } catch (e) {
        console.warn('PyWebView browse fallback:', e);
      }
    }

    if (!selectedPath) {
      const res = await apiCall('browse');
      if (res.success && res.path) selectedPath = res.path;
    }

    if (selectedPath) {
      targetPathInput.value = selectedPath;
      setStatus('Target directory set', false);
    } else {
      setStatus('Ready', false);
    }
  }

  // 2. Scan Storage Breakdown
  async function runScan() {
    const target = targetPathInput.value;
    if (!target) {
      renderMessage('Select Directory First', 'Please click Browse Folder to choose a directory before scanning.');
      return;
    }

    setLoading(true, 'Scanning storage breakdown...');
    const res = await apiCall('scan', { path: target });
    setLoading(false);

    if (!res.success) return;

    if (res.total_files === 0 && (!res.subfolders || res.subfolders.length === 0)) {
      setStatus('Scan complete', false);
      renderMessage('Empty Directory', 'No files or subfolders found in the target directory.');
      return;
    }

    setStatus('Scan complete', false);

    const catEntries = Object.entries(res.categories).sort((a, b) => b[1].size - a[1].size);

    let catRows = '';
    catEntries.forEach(([cat, data]) => {
      const pct = res.total_size > 0 ? ((data.size / res.total_size) * 100) : 0;
      catRows += `
        <tr>
          <td style="font-weight: 600;">${cat}</td>
          <td><span class="badge">${data.count} files</span></td>
          <td style="font-family:var(--font-mono);">${data.formatted_size}</td>
          <td>
            <div class="progress-bar-wrap">
              <div class="progress-track"><div class="progress-fill" style="width:${pct.toFixed(1)}%;"></div></div>
              <span style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted);">${pct.toFixed(1)}%</span>
            </div>
          </td>
        </tr>
      `;
    });

    let folderRows = '';
    let totalSubfolderSize = 0;
    if (res.subfolders && res.subfolders.length > 0) {
      res.subfolders.forEach(sub => totalSubfolderSize += sub.size);
      
      res.subfolders.forEach(sub => {
        const pct = totalSubfolderSize > 0 ? ((sub.size / totalSubfolderSize) * 100) : 0;
        folderRows += `
          <tr>
            <td style="font-weight: 600; font-family:var(--font-mono); display:flex; align-items:center; gap:8px;">
              <span style="color:var(--accent-light);">📁</span> ${sub.name}/
            </td>
            <td><span class="badge accent">${sub.count.toLocaleString()} items</span></td>
            <td style="font-family:var(--font-mono); font-weight:600;">${sub.formatted_size}</td>
            <td>
              <div class="progress-bar-wrap">
                <div class="progress-track"><div class="progress-fill" style="width:${pct.toFixed(1)}%;"></div></div>
                <span style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted);">${pct.toFixed(1)}%</span>
              </div>
            </td>
          </tr>
        `;
      });
    }

    contentArea.innerHTML = `
      <div class="metrics-grid" style="margin-bottom:16px;">
        <div class="metric-card">
          <div class="label">Root Directory Files</div>
          <div class="value">${res.total_files.toLocaleString()}</div>
        </div>
        <div class="metric-card">
          <div class="label">Root Files Size</div>
          <div class="value">${res.formatted_size}</div>
        </div>
        <div class="metric-card">
          <div class="label">Subfolders Count</div>
          <div class="value">${res.subfolders ? res.subfolders.length : 0}</div>
        </div>
      </div>

      ${folderRows ? `
      <div class="data-table-container" style="margin-bottom: 24px;">
        <div class="table-title">
          <span>Subfolders & Storage Explorer</span>
          <span style="font-weight:normal; font-family:var(--font-mono); font-size:11px; color:var(--text-muted);">${res.subfolders.length} subdirectories</span>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>Subfolder Name</th>
              <th>Total Files</th>
              <th>Storage Size</th>
              <th>Subfolder Share</th>
            </tr>
          </thead>
          <tbody>${folderRows}</tbody>
        </table>
      </div>
      ` : ''}

      <div class="data-table-container">
        <div class="table-title">
          <span>Root Files Category Distribution</span>
          <span style="font-weight:normal; font-family:var(--font-mono); font-size:11px; color:var(--text-muted);">${res.total_files} items</span>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Count</th>
              <th>Total Size</th>
              <th>Storage Share</th>
            </tr>
          </thead>
          <tbody>${catRows}</tbody>
        </table>
      </div>
    `;
  }

  // 3. Sort / Dry Run
  async function runSort(dryRun = false) {
    const target = targetPathInput.value;
    if (!target) {
      renderMessage('Select Directory First', 'Please click Browse Folder to choose a directory first.');
      return;
    }

    const label = dryRun ? 'Simulating dry run...' : 'Organizing files...';
    setLoading(true, label);
    const res = await apiCall('sort', { path: target, dry_run: dryRun });
    setLoading(false);

    if (!res.success) return;

    setStatus(dryRun ? 'Dry run complete' : 'Organize complete', false);

    let itemRows = '';
    if (res.items && res.items.length > 0) {
      res.items.forEach((item, idx) => {
        const statusBadge = item.status === 'moved' 
          ? `<span class="badge accent" style="font-size:11px;">Moved</span>`
          : item.status === 'duplicate'
          ? `<span class="badge" style="background:rgba(245,158,11,0.15); color:#f59e0b; border:1px solid rgba(245,158,11,0.3); font-size:11px;">Duplicate</span>`
          : `<span class="badge" style="background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); font-size:11px;">Skipped</span>`;

        let destDisplay = '';
        if (item.destination) {
          const parts = item.destination.replace(/\\/g, '/').split('/');
          destDisplay = parts.length > 2 ? parts.slice(-2).join('/') : item.destination;
        } else {
          destDisplay = item.reason || 'Skipped';
        }

        itemRows += `
          <tr>
            <td style="font-family:var(--font-mono); color:var(--text-muted); width:40px;">#${idx + 1}</td>
            <td>${statusBadge}</td>
            <td style="font-family:var(--font-mono); font-weight:600; color:var(--text-primary);">${item.file || 'File'}</td>
            <td style="font-family:var(--font-mono); color:var(--accent-light);">→ ${destDisplay}</td>
            <td><span class="badge" style="font-size:11px;">${item.rule || 'Default'}</span></td>
          </tr>
        `;
      });
    } else {
      itemRows = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">No files found to organize.</td></tr>`;
    }

    contentArea.innerHTML = `
      <div class="metrics-grid" style="margin-bottom: 16px;">
        <div class="metric-card">
          <div class="label">Files Moved</div>
          <div class="value" style="color:var(--text-primary);">${res.moved}</div>
        </div>
        <div class="metric-card">
          <div class="label">Duplicates Detected</div>
          <div class="value" style="color:#f59e0b;">${res.duplicates}</div>
        </div>
        <div class="metric-card">
          <div class="label">Skipped / Errors</div>
          <div class="value" style="color:var(--text-muted);">${res.errors}</div>
        </div>
        <div class="metric-card">
          <div class="label">Total Processed</div>
          <div class="value">${res.total}</div>
        </div>
      </div>

      <div class="data-table-container">
        <div class="table-title">
          <span>${dryRun ? 'Dry Run Simulation Log' : 'Live Sorting Activity Log'}</span>
          <span class="badge ${dryRun ? '' : 'accent'}">${dryRun ? 'Simulation Mode' : 'Completed'}</span>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Status</th>
              <th>File Name</th>
              <th>Destination Path</th>
              <th>Rule Applied</th>
            </tr>
          </thead>
          <tbody>${itemRows}</tbody>
        </table>
      </div>
    `;
  }

  // 4. Top Files
  async function runTopFiles() {
    const target = targetPathInput.value;
    if (!target) {
      renderMessage('Select Directory First', 'Please click Browse Folder to choose a directory first.');
      return;
    }

    setLoading(true, 'Finding top files...');
    const res = await apiCall('scan', { path: target });
    setLoading(false);

    if (!res.success || !res.top_files || res.top_files.length === 0) {
      setStatus('No files found', false);
      renderMessage('No Files Found', 'No files in directory.');
      return;
    }

    setStatus('Top files loaded', false);

    let rows = '';
    res.top_files.forEach((f, idx) => {
      rows += `
        <tr>
          <td style="font-family:var(--font-mono); color:var(--text-muted); width:40px;">#${idx + 1}</td>
          <td style="font-family:var(--font-mono); font-weight:600;">${f.name}</td>
          <td><span class="badge accent">${f.formatted_size}</span></td>
          <td style="color:var(--text-muted);">${f.category}</td>
        </tr>
      `;
    });

    contentArea.innerHTML = `
      <div class="data-table-container">
        <div class="table-title">Top 10 Largest Files</div>
        <table class="data-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>File Name</th>
              <th>Size</th>
              <th>Category</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;
  }

  // 5. Clean Empty Folders
  async function cleanEmpty() {
    const target = targetPathInput.value;
    if (!target) {
      renderMessage('Select Directory First', 'Please click Browse Folder to choose a directory first.');
      return;
    }

    setLoading(true, 'Scanning for empty folders...');
    const res = await apiCall('clean-empty', { path: target });
    setLoading(false);

    if (!res.success) return;

    if (res.removed.length === 0) {
      setStatus('No empty subfolders', false);
      renderMessage('Clean Empty Folders', 'No empty subdirectories found in selected directory.');
    } else {
      setStatus(`Removed ${res.removed.length} folder(s)`, false);
      renderMessage('Clean Complete', `Successfully removed ${res.removed.length} empty subfolder(s).`);
    }
  }

  // 6. Undo Last
  async function undoLast() {
    setLoading(true, 'Reverting last move...');
    const res = await apiCall('undo');
    setLoading(false);

    if (!res.success) return;

    if (res.undone && res.undone.length > 0) {
      setStatus('Undo complete', false);
      renderMessage('Undo Successful', `Restored ${res.undone.length} file(s) to original location.`);
    } else {
      setStatus('Nothing to undo', false);
      renderMessage('Undo History', 'No file movement history available to undo.');
    }
  }

  // 7. Show History
  async function showHistory() {
    setLoading(true, 'Loading move history...');
    const res = await apiCall('history');
    setLoading(false);

    if (!res.success || !res.records || res.records.length === 0) {
      setStatus('No history', false);
      renderMessage('Move History', 'No move history recorded yet.');
      return;
    }

    setStatus(`${res.records.length} records loaded`, false);

    let rows = '';
    res.records.forEach(r => {
      const srcName = r.src.replace(/\\/g, '/').split('/').pop();
      const destName = r.dest.replace(/\\/g, '/').split('/').pop();
      rows += `
        <tr>
          <td style="font-family:var(--font-mono); color:var(--text-muted);">${r.id}</td>
          <td style="font-family:var(--font-mono);">${srcName}</td>
          <td style="font-family:var(--font-mono); color:var(--accent-light);">→ ${destName}</td>
          <td style="font-family:var(--font-mono); color:var(--text-muted); font-size:11px;">${r.timestamp}</td>
        </tr>
      `;
    });

    contentArea.innerHTML = `
      <div class="data-table-container">
        <div class="table-title">Recent Move History</div>
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Source File</th>
              <th>Destination</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;
  }

  // ── Sidebar Navigation Binding ──
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      navItems.forEach(n => n.classList.remove('active'));
      item.classList.add('active');

      const view = item.getAttribute('data-view');
      if (view === 'overview') runScan();
      else if (view === 'organize') runSort(false);
      else if (view === 'history') showHistory();
      else if (view === 'docs') renderDocumentation();
    });
  });

  // ── Toolbar Button Bindings ──
  browseBtn.addEventListener('click', browseFolder);
  scanBtn.addEventListener('click', runScan);
  dryRunBtn.addEventListener('click', () => runSort(true));
  organizeBtn.addEventListener('click', () => runSort(false));
  topFilesBtn.addEventListener('click', runTopFiles);
  cleanEmptyBtn.addEventListener('click', cleanEmpty);
  undoBtn.addEventListener('click', undoLast);

  // Modal & Sidebar Help
  helpNavBtn.addEventListener('click', () => {
    navItems.forEach(n => n.classList.remove('active'));
    helpNavBtn.classList.add('active');
    renderDocumentation();
  });

  closeHelpBtn.addEventListener('click', () => helpModal.classList.add('hidden'));

  // Init
  renderWelcome();
});
