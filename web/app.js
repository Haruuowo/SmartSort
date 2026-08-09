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

  // ── Context Menu Elements ──
  const contextMenu = document.getElementById('contextMenu');
  const menuItemTitle = document.getElementById('menuItemTitle');
  const menuOpenLocation = document.getElementById('menuOpenLocation');
  const menuCopyPath = document.getElementById('menuCopyPath');
  const menuDeleteItem = document.getElementById('menuDeleteItem');
  let activeItemPath = '';

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

  async function apiCall(endpoint, data = null, retries = 2) {
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const options = {
          method: data ? 'POST' : 'GET',
          headers: { 'Content-Type': 'application/json' }
        };
        if (data) options.body = JSON.stringify(data);

        const res = await fetch(`/api/${endpoint}`, options);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
      } catch (err) {
        if (attempt < retries) {
          await new Promise(r => setTimeout(r, 350));
          continue;
        }
        setStatus('Local Engine Disconnected', false);
        return { success: false, error: err.message };
      }
    }
  }

  // ── WizTree Context Menu & Item Action Handlers ──
  function hideContextMenu() {
    if (contextMenu) contextMenu.classList.add('hidden');
    activeItemPath = '';
  }

  function showContextMenu(e, itemPath, titleName) {
    e.preventDefault();
    e.stopPropagation();
    if (!itemPath || !contextMenu) return;

    activeItemPath = itemPath;
    menuItemTitle.textContent = titleName || itemPath.split(/[/\\]/).pop();

    contextMenu.classList.remove('hidden');

    let x = e.clientX;
    let y = e.clientY;
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;
    const menuWidth = 220;
    const menuHeight = 140;

    if (x + menuWidth > windowWidth) x = windowWidth - menuWidth - 10;
    if (y + menuHeight > windowHeight) y = windowHeight - menuHeight - 10;

    contextMenu.style.left = `${Math.max(10, x)}px`;
    contextMenu.style.top = `${Math.max(10, y)}px`;
  }

  document.addEventListener('click', hideContextMenu);
  document.addEventListener('contextmenu', (e) => {
    if (!e.target.closest('[data-path]')) hideContextMenu();
  });

  window.openLocation = async function(path) {
    if (!path) return;
    setStatus(`Opening Explorer for ${path.split(/[/\\]/).pop()}...`, true);
    if (window.pywebview && window.pywebview.api && window.pywebview.api.open_location) {
      await window.pywebview.api.open_location(path);
    } else {
      await apiCall('open-location', { path: path });
    }
    setStatus('Explorer opened', false);
  };

  window.deleteItem = async function(path) {
    if (!path) return;
    const itemName = path.split(/[/\\]/).pop();
    if (!confirm(`Are you sure you want to send "${itemName}" to the Recycle Bin?`)) return;

    setStatus(`Sending ${itemName} to Recycle Bin...`, true);
    let success = false;
    if (window.pywebview && window.pywebview.api && window.pywebview.api.delete_item) {
      success = await window.pywebview.api.delete_item(path);
    } else {
      const res = await apiCall('delete-item', { path: path });
      success = res.success;
    }

    if (success) {
      setStatus(`Sent "${itemName}" to Recycle Bin`, false);
      const activeNav = document.querySelector('.nav-item.active');
      if (activeNav) {
        const view = activeNav.getAttribute('data-view');
        if (view === 'overview') runScan();
        else if (view === 'organize') runSort(false);
      } else {
        runScan();
      }
    } else {
      setStatus(`Failed to delete "${itemName}"`, false);
    }
  };

  if (menuOpenLocation) {
    menuOpenLocation.addEventListener('click', () => {
      if (activeItemPath) window.openLocation(activeItemPath);
      hideContextMenu();
    });
  }

  if (menuCopyPath) {
    menuCopyPath.addEventListener('click', () => {
      if (!activeItemPath) return;
      navigator.clipboard.writeText(activeItemPath);
      setStatus('Full path copied to clipboard', false);
      hideContextMenu();
    });
  }

  if (menuDeleteItem) {
    menuDeleteItem.addEventListener('click', () => {
      if (activeItemPath) window.deleteItem(activeItemPath);
      hideContextMenu();
    });
  }

  // Event delegation for right click on table rows
  contentArea.addEventListener('contextmenu', (e) => {
    const row = e.target.closest('[data-path]');
    if (row) {
      const path = row.getAttribute('data-path');
      const title = row.getAttribute('data-title');
      showContextMenu(e, path, title);
    }
  });

  // Action buttons HTML generator
  function renderRowActions(path) {
    if (!path) return '';
    const safePath = path.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
    return `
      <div class="row-actions">
        <button class="action-icon-btn" title="Reveal in File Explorer" onclick="event.stopPropagation(); window.openLocation('${safePath}')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/><line x1="12" y1="11" x2="12" y2="17"/><polyline points="9 14 12 11 15 14"/></svg>
        </button>
        <button class="action-icon-btn danger" title="Send to Recycle Bin" onclick="event.stopPropagation(); window.deleteItem('${safePath}')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
        </button>
      </div>
    `;
  }

  // ── Welcome View ──
  function renderWelcome() {
    contentArea.innerHTML = `
      <div class="welcome-card">
        <div class="app-brand-logo" style="width: 56px; height: 56px; margin: 0 auto 16px auto; background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
          <img src="SS_1.png" alt="SmartSort" style="width: 38px; height: 38px; object-fit: contain;">
        </div>
        <h2>Welcome to SmartSort</h2>
        <p>Intelligent file organization, storage inspection, and WizTree-style file management built for maximum performance.</p>

        <div class="welcome-steps">
          <div class="welcome-step">
            <div class="step-num">1</div>
            <div>
              <strong>Browse Directory</strong>
              <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">Select target drive or folder using native Windows picker.</div>
            </div>
          </div>
          <div class="welcome-step">
            <div class="step-num">2</div>
            <div>
              <strong>Scan Breakdown & Manage Files</strong>
              <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">Inspect subfolder sizes and right-click files/folders to delete or reveal in Explorer.</div>
            </div>
          </div>
          <div class="welcome-step">
            <div class="step-num">3</div>
            <div>
              <strong>Organize Safely</strong>
              <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">Sort files by EXIF dates, extensions, or rules with 1-click Undo.</div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // ── User Documentation View ──
  function renderDocumentation() {
    contentArea.innerHTML = `
      <div class="welcome-card" style="text-align: left; max-width: 800px;">
        <h2 style="margin-bottom: 8px;">SmartSort User Guide & Features</h2>
        <p style="margin-bottom: 24px;">Complete reference for managing your storage, scanning subdirectories, and organizing files.</p>

        <div class="welcome-steps" style="grid-template-columns: 1fr;">
          <div class="welcome-step">
            <div class="step-num">1</div>
            <div>
              <strong>Target Folder Selection</strong>
              <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Click <code>Browse Folder</code> in the top bar to choose any directory or drive (e.g. <code>C:\</code>, <code>D:\</code>, <code>Downloads</code>).</p>
            </div>
          </div>

          <div class="welcome-step">
            <div class="step-num">2</div>
            <div>
              <strong>WizTree-Style Context Menu & Quick Delete</strong>
              <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Right-click any subfolder or file in the scanner tables to <strong>Reveal in Explorer</strong>, <strong>Copy Path</strong>, or <strong>Send to Recycle Bin</strong>.</p>
            </div>
          </div>

          <div class="welcome-step">
            <div class="step-num">3</div>
            <div>
              <strong>C-Level Win32 Drive Scanning</strong>
              <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Click <code>Scan Directory</code> to inspect total size, file counts, and subfolder storage share across all CPU cores.</p>
            </div>
          </div>

          <div class="welcome-step">
            <div class="step-num">4</div>
            <div>
              <strong>Dry Run & Safe Organization</strong>
              <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Run <code>Dry Run</code> to preview move operations without altering files, or click <code>Organize Files</code> to execute automatic rule sorting.</p>
            </div>
          </div>

          <div class="welcome-step">
            <div class="step-num">5</div>
            <div>
              <strong>Transaction History & Undo</strong>
              <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Click <code>Undo</code> in the ribbon bar anytime to revert recent file moves safely from the SQLite database log.</p>
            </div>
          </div>
        </div>
      </div>
    `;
  }

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
      runScan();
    } else {
      setStatus('Ready', false);
    }
  }

  // 2. Scan Storage Breakdown
  async function runScan() {
    const target = targetPathInput.value;
    if (!target) {
      renderWelcome();
      return;
    }

    setLoading(true, 'Scanning storage breakdown...');
    const res = await apiCall('scan', { path: target });
    setLoading(false);

    if (!res.success) return;

    if (res.total_files === 0 && (!res.subfolders || res.subfolders.length === 0)) {
      setStatus('Scan complete', false);
      contentArea.innerHTML = `
        <div class="welcome-card">
          <h2>Empty Directory</h2>
          <p>No files or subfolders found in <code>${target}</code>.</p>
        </div>
      `;
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
        const subPath = target.replace(/[/\\]$/, '') + '\\' + sub.name;
        folderRows += `
          <tr data-path="${subPath.replace(/"/g, '&quot;')}" data-title="${sub.name}">
            <td style="font-weight: 600; font-family:var(--font-mono);">
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
            <td style="text-align:right;">${renderRowActions(subPath)}</td>
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
          <span style="font-weight:normal; font-family:var(--font-mono); font-size:11px; color:var(--text-muted);">${res.subfolders.length} subdirectories (Right-click to manage)</span>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>Subfolder Name</th>
              <th>Total Files</th>
              <th>Storage Size</th>
              <th>Subfolder Share</th>
              <th style="text-align:right;">Actions</th>
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
      renderWelcome();
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

        const itemPath = item.destination || (target.replace(/[/\\]$/, '') + '\\' + item.file);

        itemRows += `
          <tr data-path="${itemPath.replace(/"/g, '&quot;')}" data-title="${item.file}">
            <td style="font-family:var(--font-mono); color:var(--text-muted); width:40px;">#${idx + 1}</td>
            <td>${statusBadge}</td>
            <td style="font-family:var(--font-mono); font-weight:600; color:var(--text-primary);">${item.file || 'File'}</td>
            <td style="font-family:var(--font-mono); color:var(--accent-light);">→ ${destDisplay}</td>
            <td><span class="badge" style="font-size:11px;">${item.rule || 'Default'}</span></td>
            <td style="text-align:right;">${renderRowActions(itemPath)}</td>
          </tr>
        `;
      });
    } else {
      itemRows = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No files found to organize.</td></tr>`;
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
              <th style="text-align:right;">Actions</th>
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
      renderWelcome();
      return;
    }

    setLoading(true, 'Finding top files...');
    const res = await apiCall('scan', { path: target });
    setLoading(false);

    if (!res.success || !res.top_files || res.top_files.length === 0) {
      setStatus('No files found', false);
      contentArea.innerHTML = `
        <div class="welcome-card">
          <h2>No Files Found</h2>
          <p>No large files located in <code>${target}</code>.</p>
        </div>
      `;
      return;
    }

    setStatus('Top files loaded', false);

    let rows = '';
    res.top_files.forEach((f, idx) => {
      const fullPath = target.replace(/[/\\]$/, '') + '\\' + f.name;
      rows += `
        <tr data-path="${fullPath.replace(/"/g, '&quot;')}" data-title="${f.name}">
          <td style="font-family:var(--font-mono); color:var(--text-muted); width:40px;">#${idx + 1}</td>
          <td style="font-family:var(--font-mono); font-weight:600;">${f.name}</td>
          <td><span class="badge accent">${f.formatted_size}</span></td>
          <td style="color:var(--text-muted);">${f.category}</td>
          <td style="text-align:right;">${renderRowActions(fullPath)}</td>
        </tr>
      `;
    });

    contentArea.innerHTML = `
      <div class="data-table-container">
        <div class="table-title">Top 10 Largest Files (Right-click or use actions to open/delete)</div>
        <table class="data-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>File Name</th>
              <th>Size</th>
              <th>Category</th>
              <th style="text-align:right;">Actions</th>
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
      renderWelcome();
      return;
    }

    setLoading(true, 'Scanning for empty folders...');
    const res = await apiCall('clean-empty', { path: target });
    setLoading(false);

    if (res.success) {
      setStatus(`Cleaned ${res.removed.length} empty folders`, false);
      let listItems = '';
      if (res.removed.length > 0) {
        res.removed.forEach(folder => {
          listItems += `<li>📁 ${folder}</li>`;
        });
      } else {
        listItems = `<li>No empty folders were found.</li>`;
      }

      contentArea.innerHTML = `
        <div class="welcome-card" style="text-align:left;">
          <h2>Clean Empty Folders Result</h2>
          <p>Removed <strong>${res.removed.length}</strong> empty subdirectories.</p>
          <ul style="margin-top:12px; font-family:var(--font-mono); font-size:12px; line-height:1.8; color:var(--text-muted); max-height:300px; overflow-y:auto; padding-left:16px;">
            ${listItems}
          </ul>
        </div>
      `;
    }
  }

  // 6. Undo Last Move
  async function undoLast() {
    setLoading(true, 'Reverting last operations...');
    const res = await apiCall('undo');
    setLoading(false);

    if (res.success) {
      if (res.undone && res.undone.length > 0) {
        setStatus(`Reverted ${res.undone.length} files`, false);
        contentArea.innerHTML = `
          <div class="welcome-card" style="text-align:left;">
            <h2>Undo Operation Successful</h2>
            <p>Reverted <strong>${res.undone.length}</strong> files back to original paths.</p>
          </div>
        `;
      } else {
        setStatus('Nothing to undo', false);
        contentArea.innerHTML = `
          <div class="welcome-card">
            <h2>Nothing to Undo</h2>
            <p>No recent file moves recorded in transaction log.</p>
          </div>
        `;
      }
    }
  }

  // 7. Show History
  async function showHistory() {
    setLoading(true, 'Loading move history...');
    const res = await apiCall('history');
    setLoading(false);

    if (!res.success || !res.records || res.records.length === 0) {
      setStatus('History empty', false);
      contentArea.innerHTML = `
        <div class="welcome-card">
          <h2>No History Found</h2>
          <p>No file moves have been recorded yet.</p>
        </div>
      `;
      return;
    }

    setStatus('History loaded', false);

    let rows = '';
    res.records.forEach(r => {
      const srcName = r.src.split(/[/\\]/).pop();
      const destName = r.dest.split(/[/\\]/).pop();
      rows += `
        <tr data-path="${r.dest.replace(/"/g, '&quot;')}" data-title="${destName}">
          <td style="font-family:var(--font-mono); color:var(--text-muted);">${r.id}</td>
          <td style="font-family:var(--font-mono);">${srcName}</td>
          <td style="font-family:var(--font-mono); color:var(--accent-light);">→ ${destName}</td>
          <td style="font-family:var(--font-mono); color:var(--text-muted); font-size:11px;">${r.timestamp}</td>
          <td style="text-align:right;">${renderRowActions(r.dest)}</td>
        </tr>
      `;
    });

    contentArea.innerHTML = `
      <div class="data-table-container">
        <div class="table-title">Recent Move Transaction History</div>
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Source File</th>
              <th>Destination</th>
              <th>Timestamp</th>
              <th style="text-align:right;">Actions</th>
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
