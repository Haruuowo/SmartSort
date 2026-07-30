document.addEventListener('DOMContentLoaded', () => {
  // Navigation Tabs
  const navItems = document.querySelectorAll('.nav-item');
  const tabContents = document.querySelectorAll('.tab-content');

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetTab = item.getAttribute('data-tab');

      navItems.forEach(n => n.classList.remove('active'));
      tabContents.forEach(t => t.classList.remove('active'));

      item.classList.add('active');
      document.getElementById(`tab-${targetTab}`).classList.add('active');

      if (targetTab === 'history') {
        fetchHistory();
      }
    });
  });

  // DOM Elements
  const targetPathInput = document.getElementById('targetPath');
  const browseBtn = document.getElementById('browseBtn');
  const organizeBtn = document.getElementById('organizeBtn');
  const dryRunBtn = document.getElementById('dryRunBtn');
  const scanBtn = document.getElementById('scanBtn');
  const cleanEmptyBtn = document.getElementById('cleanEmptyBtn');
  const undoBtn = document.getElementById('undoBtn');
  const consoleLog = document.getElementById('consoleLog');
  const logCountBadge = document.getElementById('logCountBadge');
  const clearLogBtn = document.getElementById('clearLogBtn');
  const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');

  let logCount = 1;

  function appendLog(message, type = 'info') {
    const time = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.innerHTML = `<span class="time">[${time}]</span> ${message}`;
    consoleLog.appendChild(entry);
    consoleLog.scrollTop = consoleLog.scrollHeight;
    logCount++;
    logCountBadge.textContent = `${logCount} events`;
  }

  clearLogBtn.addEventListener('click', () => {
    consoleLog.innerHTML = '';
    logCount = 0;
    logCountBadge.textContent = '0 events';
  });

  // API Call Helpers
  async function apiCall(endpoint, payload = {}) {
    try {
      const res = await fetch(`/api/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      return await res.json();
    } catch (err) {
      appendLog(`Network error: ${err.message}`, 'error');
      return { success: false, error: err.message };
    }
  }

  // Browse Folder
  browseBtn.addEventListener('click', async () => {
    appendLog('Opening folder picker dialog...', 'info');
    const res = await apiCall('browse');
    if (res.success && res.path) {
      targetPathInput.value = res.path;
      appendLog(`Target directory set to: ${res.path}`, 'success');
      runScan(res.path);
    } else {
      appendLog('Folder selection cancelled.', 'warning');
    }
  });

  // Scan Storage
  async function runScan(path) {
    const target = path || targetPathInput.value;
    if (!target) {
      appendLog('Please select a folder first.', 'error');
      return;
    }

    appendLog(`Scanning storage distribution for: ${target}`, 'info');
    const data = await apiCall('scan', { path: target });

    if (data.success) {
      document.getElementById('statTotalFiles').textContent = data.total_files;
      document.getElementById('statTotalSize').textContent = data.formatted_size;
      document.getElementById('statCategories').textContent = Object.keys(data.categories).length;

      // Render Category Bars
      const categoryBars = document.getElementById('categoryBars');
      categoryBars.innerHTML = '';

      if (Object.keys(data.categories).length === 0) {
        categoryBars.innerHTML = '<div class="empty-placeholder">No files found in directory.</div>';
      } else {
        Object.entries(data.categories).forEach(([cat, info]) => {
          const pct = data.total_size > 0 ? ((info.size / data.total_size) * 100).toFixed(1) : 0;
          const barItem = document.createElement('div');
          barItem.className = 'cat-bar-item';
          barItem.innerHTML = `
            <div class="cat-bar-meta">
              <span>${cat} (${info.count} files)</span>
              <span>${info.formatted_size} (${pct}%)</span>
            </div>
            <div class="cat-bar-track">
              <div class="cat-bar-fill" style="width: ${pct}%"></div>
            </div>
          `;
          categoryBars.appendChild(barItem);
        });
      }

      // Render Top Files Table
      const topFilesTable = document.getElementById('topFilesTable');
      topFilesTable.innerHTML = '';
      if (data.top_files.length === 0) {
        topFilesTable.innerHTML = '<tr><td colspan="4" class="empty-placeholder">No files found.</td></tr>';
      } else {
        data.top_files.forEach((f, idx) => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>#${idx + 1}</td>
            <td><strong>${f.name}</strong></td>
            <td>${f.formatted_size}</td>
            <td><span class="badge">${f.category}</span></td>
          `;
          topFilesTable.appendChild(tr);
        });
      }

      appendLog(`Scan complete! Found ${data.total_files} files (${data.formatted_size}).`, 'success');
    }
  }

  scanBtn.addEventListener('click', () => runScan());

  // Organize Files
  organizeBtn.addEventListener('click', async () => {
    const target = targetPathInput.value;
    if (!target) {
      appendLog('Please select a folder first.', 'error');
      return;
    }

    appendLog(`Executing file organization on: ${target}`, 'info');
    const res = await apiCall('sort', { path: target, dry_run: false });

    if (res.success) {
      appendLog(`Organization Complete! Moved: ${res.moved} | Duplicates: ${res.duplicates} | Errors: ${res.errors}`, 'success');
      document.getElementById('statDuplicates').textContent = res.duplicates;
      runScan(target);
    }
  });

  // Dry Run Simulation
  dryRunBtn.addEventListener('click', async () => {
    const target = targetPathInput.value;
    if (!target) {
      appendLog('Please select a folder first.', 'error');
      return;
    }

    appendLog(`Running Dry-Run simulation on: ${target}`, 'warning');
    const res = await apiCall('sort', { path: target, dry_run: true });

    if (res.success) {
      appendLog(`Dry Run Complete! Files to move: ${res.moved} | Duplicates: ${res.duplicates}`, 'info');
    }
  });

  // Clean Empty Folders
  cleanEmptyBtn.addEventListener('click', async () => {
    const target = targetPathInput.value;
    if (!target) {
      appendLog('Please select a folder first.', 'error');
      return;
    }

    appendLog(`Scanning for empty subfolders in: ${target}`, 'info');
    const res = await apiCall('clean-empty', { path: target });

    if (res.success) {
      if (res.removed.length === 0) {
        appendLog('No empty subfolders found.', 'warning');
      } else {
        appendLog(`Cleaned ${res.removed.length} empty subfolder(s).`, 'success');
      }
    }
  });

  // Undo Last Move
  undoBtn.addEventListener('click', async () => {
    appendLog('Undoing last file movement...', 'warning');
    const res = await apiCall('undo');

    if (res.success && res.undone.length > 0) {
      res.undone.forEach(f => appendLog(`Restored file: ${f}`, 'success'));
      runScan(targetPathInput.value);
    } else {
      appendLog('Nothing to undo.', 'warning');
    }
  });

  // Fetch History
  async function fetchHistory() {
    const res = await apiCall('history');
    const historyTable = document.getElementById('historyTable');
    historyTable.innerHTML = '';

    if (res.success && res.records.length > 0) {
      res.records.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>#${r.id}</td>
          <td class="font-mono">${r.src}</td>
          <td class="font-mono">${r.dest}</td>
          <td>${r.timestamp}</td>
          <td><button class="btn-sm btn-outline undo-single-btn" data-id="${r.id}">Undo</button></td>
        `;
        historyTable.appendChild(tr);
      });
    } else {
      historyTable.innerHTML = '<tr><td colspan="5" class="empty-placeholder">No history records found.</td></tr>';
    }
  }

  if (refreshHistoryBtn) {
    refreshHistoryBtn.addEventListener('click', fetchHistory);
  }
});
