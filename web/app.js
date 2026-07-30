document.addEventListener('DOMContentLoaded', () => {
  const BANNER_ASCII = `
  ███████╗███╗   ███╗█████╗ ██████╗ ████████╗███████╗██████╗ ██████╗ ████████╗
  ██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔══██╗██╔══██╗╚══██╔══╝
  ███████╗██╔████╔██║███████║██████╔╝   ██║   ███████╗██║  ██║██████╔╝   ██║   
  ╚════██║██║╚██╔╝██║██╔══██║██╔══██╗   ██║   ╚════██║██║  ██║██╔══██╗   ██║   
  ███████║██║ ╚═╝ ██║██║  ██║██║  ██║   ██║   ███████║╚██████╔╝██║  ██║   ██║   
  ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
`;

  const targetPathInput = document.getElementById('targetPath');
  const cmdInput = document.getElementById('cmdInput');
  const terminalBody = document.getElementById('terminalBody');

  const browseBtn = document.getElementById('browseBtn');
  const organizeBtn = document.getElementById('organizeBtn');
  const dryRunBtn = document.getElementById('dryRunBtn');
  const scanBtn = document.getElementById('scanBtn');
  const topFilesBtn = document.getElementById('topFilesBtn');
  const cleanEmptyBtn = document.getElementById('cleanEmptyBtn');
  const undoBtn = document.getElementById('undoBtn');
  const historyBtn = document.getElementById('historyBtn');
  const clearBtn = document.getElementById('clearBtn');
  const helpBtn = document.getElementById('helpBtn');

  function printLine(text, colorClass = '') {
    const div = document.createElement('div');
    div.className = `log-line ${colorClass}`;
    div.textContent = text;
    terminalBody.appendChild(div);
    terminalBody.scrollTop = terminalBody.scrollHeight;
  }

  function printBanner() {
    printLine(BANNER_ASCII, 'green');
    printLine("  [+] Click [ Browse Folder ] or type 'browse' to select target directory.", 'blue');
    printLine("  [+] Type 'help' at the prompt to view full command documentation.\n", 'muted');
  }

  function clearTerminal() {
    terminalBody.innerHTML = '';
    printBanner();
  }

  // API Call Helper
  async function apiCall(endpoint, payload = {}) {
    try {
      const res = await fetch(`/api/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      return await res.json();
    } catch (err) {
      printLine(`[-] Network error: ${err.message}`, 'red');
      return { success: false, error: err.message };
    }
  }

  // Actions
  async function browseFolder() {
    printLine("\n[*] Opening Windows folder picker...", 'blue');
    const res = await apiCall('browse');
    if (res.success && res.path) {
      targetPathInput.value = res.path;
      const timestamp = new Date().toLocaleTimeString();
      printLine(`[${timestamp}] [+] Target directory set: ${res.path}`, 'blue');
      printLine(`[${timestamp}]     Ready! Click [ Dry Run ], [ Scan Storage ], or [ Organize ].`, 'muted');
    } else {
      printLine("[-] Folder selection cancelled.", 'amber');
    }
  }

  async function runSort(dryRun = false, overridePath = '') {
    const target = overridePath || targetPathInput.value;
    if (!target) {
      printLine("[-] Please select a valid folder path.", 'red');
      return;
    }

    const timestamp = new Date().toLocaleTimeString();
    const mode = dryRun ? "DRY RUN SIMULATION" : "EXECUTING SORT";
    printLine(`\n[${timestamp}] [*] Starting [${mode}] on: ${target}`, dryRun ? 'amber' : 'green');
    printLine("────────────────────────────────────────────────────────────────", 'muted');

    const res = await apiCall('sort', { path: target, dry_run: dryRun });
    if (res.success) {
      const endStamp = new Date().toLocaleTimeString();
      printLine("────────────────────────────────────────────────────────────────", 'muted');
      printLine(`[${endStamp}] [+] Complete! Moved: ${res.moved} | Duplicates: ${res.duplicates} | Errors: ${res.errors} | Total: ${res.total}\n`, res.errors === 0 ? 'green' : 'amber');
    }
  }

  async function runScan(overridePath = '') {
    const target = overridePath || targetPathInput.value;
    if (!target) {
      printLine("[-] Please select a folder to scan.", 'red');
      return;
    }

    const timestamp = new Date().toLocaleTimeString();
    printLine(`\n[${timestamp}] [*] Scanning folder storage breakdown: ${target}`, 'blue');
    printLine("────────────────────────────────────────────────────────────────", 'muted');

    const res = await apiCall('scan', { path: target });
    if (res.success) {
      if (res.total_files === 0) {
        printLine("[!] Folder is empty.", 'amber');
        return;
      }

      printLine(`Total Folder Size: ${res.formatted_size} (${res.total_files} files)\n`, 'green');
      printLine(`  ${'CATEGORY'.padEnd(18)} ${'FILES'.padEnd(8)} ${'SIZE'.padEnd(10)} ${'% SIZE'.padEnd(8)} VISUAL DISTRIBUTION`, 'muted');
      printLine(`  ${'─'.repeat(18)} ${'─'.repeat(8)} ${'─'.repeat(10)} ${'─'.repeat(8)} ${'─'.repeat(22)}`, 'muted');

      Object.entries(res.categories).forEach(([cat, data]) => {
        const pct = res.total_size > 0 ? ((data.size / res.total_size) * 100) : 0;
        const filled = Math.min(Math.max(Math.round(16 * (pct / 100)), 0), 16);
        const bar = "█".repeat(filled) + "░".repeat(16 - filled);
        printLine(`  ${cat.padEnd(18)} ${String(data.count).padEnd(8)} ${data.formatted_size.padEnd(10)} ${pct.toFixed(1).padStart(5)}%   [${bar}]`, 'text');
      });

      printLine("────────────────────────────────────────────────────────────────\n", 'muted');
    }
  }

  async function runTopFiles(overridePath = '') {
    const target = overridePath || targetPathInput.value;
    if (!target) {
      printLine("[-] Please select a folder.", 'red');
      return;
    }

    const timestamp = new Date().toLocaleTimeString();
    printLine(`\n[${timestamp}] [*] Top 10 Largest Files in: ${target}`, 'blue');
    printLine("────────────────────────────────────────────────────────────────", 'muted');

    const res = await apiCall('scan', { path: target });
    if (res.success && res.top_files.length > 0) {
      res.top_files.forEach((f, idx) => {
        printLine(`  #${String(idx + 1).padEnd(2)} ${f.formatted_size.padEnd(10)}  ${f.name}  --> (${f.category})`, 'text');
      });
      printLine("────────────────────────────────────────────────────────────────\n", 'muted');
    }
  }

  async function cleanEmpty(overridePath = '') {
    const target = overridePath || targetPathInput.value;
    if (!target) {
      printLine("[-] Please select a folder.", 'red');
      return;
    }

    const timestamp = new Date().toLocaleTimeString();
    printLine(`\n[${timestamp}] [*] Scanning for empty subdirectories in: ${target}`, 'blue');
    const res = await apiCall('clean-empty', { path: target });

    if (res.success) {
      if (res.removed.length === 0) {
        printLine(`[${timestamp}] [!] No empty subdirectories found.`, 'amber');
      } else {
        res.removed.forEach(d => printLine(`  [REMOVED] Empty folder: ${d}`, 'red'));
        printLine(`[${timestamp}] [+] Cleaned ${res.removed.length} empty subfolder(s).\n`, 'green');
      }
    }
  }

  async function undoLast() {
    printLine("\n[*] Undoing last file movement...", 'purple');
    const res = await apiCall('undo');
    if (res.success && res.undone.length > 0) {
      res.undone.forEach(name => printLine(`  [UNDONE] Restored: ${name}`, 'green'));
    } else {
      printLine("[!] Nothing to undo.", 'amber');
    }
  }

  async function showHistory() {
    const res = await apiCall('history');
    if (res.success && res.records.length > 0) {
      printLine("\n=== RECENT MOVE HISTORY ===", 'purple');
      res.records.forEach(r => {
        printLine(`  #${r.id} | ${r.src.split(/[\\\\/]/).pop()} ──> ${r.dest.split(/[\\\\/]/).pop()} [${r.timestamp}]`, 'text');
      });
      printLine("===========================\n", 'purple');
    } else {
      printLine("[!] No move history recorded.", 'amber');
    }
  }

  const helpModal = document.getElementById('helpModal');
  const closeHelpModalBtn = document.getElementById('closeHelpModalBtn');
  const closeHelpModalDot = document.getElementById('closeHelpModalDot');

  function openHelpModal() {
    if (helpModal) helpModal.classList.remove('hidden');
  }

  function closeHelpModal() {
    if (helpModal) helpModal.classList.add('hidden');
  }

  if (closeHelpModalBtn) closeHelpModalBtn.addEventListener('click', closeHelpModal);
  if (closeHelpModalDot) closeHelpModalDot.addEventListener('click', closeHelpModal);
  if (helpModal) {
    helpModal.addEventListener('click', (e) => {
      if (e.target === helpModal) closeHelpModal();
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeHelpModal();
  });

  // Bind Buttons
  browseBtn.addEventListener('click', browseFolder);
  organizeBtn.addEventListener('click', () => runSort(false));
  dryRunBtn.addEventListener('click', () => runSort(true));
  scanBtn.addEventListener('click', () => runScan());
  topFilesBtn.addEventListener('click', () => runTopFiles());
  cleanEmptyBtn.addEventListener('click', () => cleanEmpty());
  undoBtn.addEventListener('click', undoLast);
  historyBtn.addEventListener('click', showHistory);
  clearBtn.addEventListener('click', clearTerminal);
  helpBtn.addEventListener('click', openHelpModal);

  // Command Prompt Input Handler
  cmdInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const raw = cmdInput.value.trim();
      cmdInput.value = '';
      if (!raw) return;

      const timestamp = new Date().toLocaleTimeString();
      printLine(`\n[${timestamp}] smartsort $ ${raw}`, 'green');

      const parts = raw.split(/\s+/);
      const cmd = parts[0].lowerCase || parts[0].toLowerCase();
      const arg = parts.slice(1).join(' ');

      if (cmd === 'help' || cmd === '?') openHelpModal();
      else if (cmd === 'sort' || cmd === 'run' || cmd === 'organize') runSort(false, arg);
      else if (cmd === 'dry-run' || cmd === 'dryrun' || cmd === 'sim') runSort(true, arg);
      else if (cmd === 'scan' || cmd === 'analyze') runScan(arg);
      else if (cmd === 'top-files' || cmd === 'topfiles' || cmd === 'largest') runTopFiles(arg);
      else if (cmd === 'clean-empty' || cmd === 'clean' || cmd === 'rmdir') cleanEmpty(arg);
      else if (cmd === 'browse' || cmd === 'select') browseFolder();
      else if (cmd === 'history') showHistory();
      else if (cmd === 'undo') undoLast();
      else if (cmd === 'clear' || cmd === 'cls') clearTerminal();
      else printLine(`[-] Unknown command '${cmd}'. Type 'help' for available commands.`, 'red');
    }
  });

  // Print initial banner
  printBanner();
});
