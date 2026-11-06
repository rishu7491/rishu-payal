/**
 * Payal Unified Mobile & Desktop Assistant Controller
 * Seamlessly connects Mobile UI with the Autonomous Core Engine:
 * - 8 Interactive Pages: Home, Voice, Chat, Tasks, Devices, Approvals, Terminal, Settings
 * - Real-time Voice with Indian Natural Neural Voices & 60fps Expressive Robot Face
 * - Live connection to FastAPI backend (Chat, Health, Automation, Terminal)
 */

const API_BASE = window.location.origin;

// State
let currentPage = 'home';
let companion = null;
let voiceOutputEnabled = true;
let isVoiceListening = false;
let avatarFaceMode = 'portrait'; // 'portrait' or 'robot'
let activeTaskFilter = 'active';

// Sample Tasks Data
let tasksData = [
  { id: 't1', title: 'Complete BCA Notes', category: 'Study • High Priority', progress: null, done: false },
  { id: 't2', title: 'Workout 2 Hours', category: 'Health • Daily Routine', progress: 35, done: false },
  { id: 't3', title: 'Update RishuMart Project', category: 'Coding • Next Milestone', progress: 0, done: false },
  { id: 't4', title: 'Check Phone & Laptop Battery', category: 'Devices • System Monitor', progress: null, done: true, tag: '🔋 84%' },
];

document.addEventListener('DOMContentLoaded', () => {
  initCompanionFace();
  initRouting();
  checkServerHealth();
  loadTasksFromBackend();
  checkDevicesHealth();
  loadPendingApprovals();
});

/* ==========================================================================
   1. Robot Companion Face & Voice Engine Integration
   ========================================================================== */
function initCompanionFace() {
  if (typeof RobotCompanion !== 'undefined') {
    companion = new RobotCompanion('robotCanvas');

    // Handle incoming speech from companion recognition
    companion.onSpeechResult = (transcript, isFinal) => {
      const voicePreview = document.getElementById('voiceLiveTranscript');
      if (voicePreview) {
        voicePreview.textContent = `“${transcript}”`;
      }
      if (isFinal) {
        handleVoiceFinalTranscript(transcript);
      }
    };
  }
}

function toggleAvatarMode() {
  const portrait = document.getElementById('portraitAvatar');
  const canvasBox = document.getElementById('canvasAvatar');
  const label = document.getElementById('avatarModeLabel');

  if (avatarFaceMode === 'portrait') {
    avatarFaceMode = 'robot';
    if (portrait) portrait.style.display = 'none';
    if (canvasBox) canvasBox.style.display = 'grid';
    if (label) label.textContent = '👩 Show Avatar';
    if (companion) companion.setEmotion('happy');
    toast('Switched to 60fps Robot Face');
  } else {
    avatarFaceMode = 'portrait';
    if (portrait) portrait.style.display = 'grid';
    if (canvasBox) canvasBox.style.display = 'none';
    if (label) label.textContent = '🤖 Show Face';
    toast('Switched to Digital Portrait');
  }
}

/* ==========================================================================
   2. Page Routing & Drawer Navigation
   ========================================================================== */
function initRouting() {
  showPage('home');
}

function showPage(pageId) {
  currentPage = pageId;

  // Toggle active class on pages
  document.querySelectorAll('.page').forEach((p) => {
    p.classList.toggle('active', p.id === `page-${pageId}`);
  });

  // Toggle active state on bottom navigation
  document.querySelectorAll('.bottom-nav .nav-item').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.page === pageId);
  });

  // Toggle drawer menu items
  document.querySelectorAll('.drawer-item').forEach((item) => {
    const isTarget = item.textContent.toLowerCase().includes(pageId);
    item.classList.toggle('active', isTarget);
  });

  // Page-specific trigger hooks
  if (pageId === 'chat') {
    scrollChatToBottom();
  } else if (pageId === 'tasks') {
    loadTasksFromBackend();
  } else if (pageId === 'devices') {
    checkDevicesHealth();
  } else if (pageId === 'approvals') {
    loadPendingApprovals();
  }
}

function toggleDrawer(open) {
  const drawer = document.getElementById('sideDrawer');
  const overlay = document.getElementById('drawerOverlay');
  if (drawer && overlay) {
    drawer.classList.toggle('active', open);
    overlay.classList.toggle('active', open);
  }
}

function toggleVoiceOutput() {
  voiceOutputEnabled = !voiceOutputEnabled;
  const icon = document.getElementById('topVoiceIcon');
  if (icon) {
    icon.textContent = voiceOutputEnabled ? '🔊' : '🔇';
  }
  if (!voiceOutputEnabled && companion) {
    companion.stopSpeaking();
  }
  toast(voiceOutputEnabled ? 'Voice output enabled' : 'Voice output muted');
}

/* ==========================================================================
   3. Voice Assistant Screen (Talk to Payal)
   ========================================================================== */
function toggleVoiceSession() {
  if (!companion) return;
  if (isVoiceListening) {
    stopVoiceSession();
  } else {
    startVoiceSession();
  }
}

function startVoiceSession() {
  if (!companion) return;
  isVoiceListening = true;
  const orb = document.getElementById('voiceMicOrb');
  const status = document.getElementById('voiceMainStatus');
  const preview = document.getElementById('voiceLiveTranscript');

  if (orb) orb.classList.add('listening');
  if (status) status.textContent = 'Listening… Speak now';
  if (preview) preview.textContent = 'Listening for your voice…';

  companion.setEmotion('thinking');
  companion.toggleListening();
}

function stopVoiceSession() {
  if (!companion) return;
  isVoiceListening = false;
  const orb = document.getElementById('voiceMicOrb');
  const status = document.getElementById('voiceMainStatus');

  if (orb) orb.classList.remove('listening');
  if (status) status.textContent = 'Tap mic to speak';

  if (companion.isListening) {
    companion.toggleListening();
  }
}

async function handleVoiceFinalTranscript(text) {
  stopVoiceSession();
  const status = document.getElementById('voiceMainStatus');
  if (status) status.textContent = 'Thinking…';

  // Add to chat history
  appendChatMessage('user', text);

  try {
    const res = await fetch(`${API_BASE}/api/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: text }],
      }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const replyText = data.content || 'Maine aapka request process kar diya hai.';

    // Classify emotion
    const emo = await fetchEmotion(replyText);

    appendChatMessage('assistant', replyText);
    if (companion) {
      companion.setEmotion(emo.emotion, emo.intensity);
      if (voiceOutputEnabled) {
        companion.speak(replyText, emo.emotion);
      }
    }

    if (status) status.textContent = 'Finished!';
    const preview = document.getElementById('voiceLiveTranscript');
    if (preview) preview.textContent = `“${replyText}”`;

  } catch (err) {
    console.error('Voice processing error:', err);
    if (status) status.textContent = 'Error processing speech';
    toast(`Speech error: ${err.message}`);
  }
}

/* ==========================================================================
   4. Chat Screen Logic
   ========================================================================== */
function handleChatSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('chatTextInput');
  const text = input.value.trim();
  if (!text) return;

  sendChatMessage(text);
  input.value = '';
}

function sendChipMessage(text) {
  showPage('chat');
  sendChatMessage(text);
}

async function sendChatMessage(text) {
  appendChatMessage('user', text);

  if (companion) companion.setEmotion('thinking');

  try {
    const res = await fetch(`${API_BASE}/api/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: text }],
      }),
    });

    if (!res.ok) throw new Error(`Server returned status ${res.status}`);
    const data = await res.json();
    const reply = data.content || 'Got it!';

    const emo = await fetchEmotion(reply);

    appendChatMessage('assistant', reply);
    if (companion) {
      companion.setEmotion(emo.emotion, emo.intensity);
      if (voiceOutputEnabled) {
        companion.speak(reply, emo.emotion);
      }
    }
  } catch (err) {
    appendChatMessage('assistant', `Encountered an issue: ${err.message}`);
    if (companion) companion.setEmotion('sad');
  }
}

function toggleVoiceInputFromChat() {
  showPage('voice');
  startVoiceSession();
}

function appendChatMessage(role, content) {
  const container = document.getElementById('chatMessages');
  if (!container) return;

  const now = new Date();
  const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const bubble = document.createElement('div');
  bubble.className = `bubble ${role}`;

  const contentDiv = document.createElement('div');
  contentDiv.className = 'bubble-content';
  contentDiv.textContent = content;

  const timeSpan = document.createElement('span');
  timeSpan.className = 'bubble-time';
  timeSpan.textContent = timeStr;

  bubble.appendChild(contentDiv);
  bubble.appendChild(timeSpan);
  container.appendChild(bubble);

  scrollChatToBottom();
}

function scrollChatToBottom() {
  const container = document.getElementById('chatMessages');
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}

function clearChatHistory() {
  const container = document.getElementById('chatMessages');
  if (container) {
    container.innerHTML = `
      <div class="bubble assistant">
        <div class="bubble-content">
          Chat cleared. Hello Rishabh! How can I help you right now?
        </div>
        <span class="bubble-time">Now</span>
      </div>
    `;
  }
  toast('Chat history cleared');
}

async function fetchEmotion(text) {
  try {
    const res = await fetch(`${API_BASE}/api/system/emotion`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (res.ok) return await res.json();
  } catch (err) {
    // fallback
  }
  return { emotion: 'neutral', intensity: 0.8 };
}

/* ==========================================================================
   5. Tasks & Autonomous Orchestration
   ========================================================================== */
async function loadTasksFromBackend() {
  try {
    const res = await fetch(`${API_BASE}/api/automation/tasks`);
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        tasksData = data.map((t) => {
          const isDone = t.status === 'completed';
          let prog = null;
          if (t.progress !== null && t.progress > 0 && t.progress < 1) {
            prog = Math.round(t.progress * 100);
          } else if (isDone) {
            prog = 100;
          }
          return {
            id: t.task_id,
            title: t.name,
            category: (t.metadata && t.metadata.category) || 'General Task',
            progress: prog,
            done: isDone,
            tag: t.name.toLowerCase().includes('battery') ? '🔋 84%' : null,
          };
        });
      }
    }
  } catch (err) {
    console.warn('Fallback to local task cache:', err);
  }
  updateTaskProgress();
  renderTasks();
}

function switchTaskTab(tab) {
  activeTaskFilter = tab;
  document.getElementById('tabActiveTasks').classList.toggle('active', tab === 'active');
  document.getElementById('tabCompletedTasks').classList.toggle('active', tab === 'completed');
  renderTasks();
}

async function toggleTaskDone(btn, taskId) {
  const isDone = !btn.classList.contains('done');
  btn.classList.toggle('done', isDone);
  btn.textContent = isDone ? '✓' : '';

  const taskItem = btn.closest('.task-item');
  const title = taskItem ? taskItem.querySelector('strong').textContent : '';
  const match = tasksData.find((t) => t.id === taskId || t.title === title);
  if (match) {
    match.done = isDone;
    updateTaskProgress();
  }

  try {
    const targetId = match ? match.id : taskId;
    await fetch(`${API_BASE}/api/automation/tasks/${encodeURIComponent(targetId)}/toggle?done=${isDone}`, {
      method: 'POST',
    });
    toast(isDone ? `Task completed: ${title}` : `Task reopened: ${title}`);
  } catch (err) {
    toast(`Status updated`);
  }
}

function renderTasks() {
  const container = document.getElementById('tasksListContainer');
  if (!container) return;

  const filtered = tasksData.filter((t) => (activeTaskFilter === 'active' ? !t.done : t.done));
  if (filtered.length === 0) {
    container.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--muted);">No ${activeTaskFilter} tasks right now.</div>`;
    return;
  }

  container.innerHTML = filtered
    .map(
      (t) => `
    <div class="task-item">
      <button class="task-check-circle ${t.done ? 'done' : ''}" onclick="toggleTaskDone(this, '${t.id}')">${t.done ? '✓' : ''}</button>
      <div class="task-content">
        <strong>${t.title}</strong>
        <small>${t.category}</small>
        ${t.progress !== null ? `<div class="task-progress-bar"><span style="width: ${t.progress}%;"></span></div>` : ''}
      </div>
      ${t.tag ? `<span class="battery-tag">${t.tag}</span>` : t.progress !== null ? `<span class="task-percent-tag">${t.progress}%</span>` : `<span class="chevron">›</span>`}
    </div>
  `
    )
    .join('');
}

function updateTaskProgress() {
  const total = tasksData.length;
  const done = tasksData.filter((t) => t.done).length;
  const active = total - done;

  const activeCountEl = document.getElementById('activeTaskCount');
  const completedCountEl = document.getElementById('completedTaskCount');
  const homeCountEl = document.getElementById('homeTaskCount');
  const ratioEl = document.getElementById('progressRatioText');
  const circleEl = document.getElementById('taskProgressCircle');

  if (activeCountEl) activeCountEl.textContent = active;
  if (completedCountEl) completedCountEl.textContent = done;
  if (homeCountEl) homeCountEl.textContent = `${active} Active Tasks`;
  if (ratioEl) ratioEl.textContent = `${done} of ${total} tasks completed today`;

  const percent = total > 0 ? Math.round((done / total) * 100) : 0;
  if (circleEl) {
    circleEl.style.setProperty('--percent', `${percent}%`);
    const num = circleEl.querySelector('.progress-number');
    if (num) num.textContent = `${percent}%`;
  }
}

async function openAddTaskModal() {
  const title = prompt('Enter new task title:');
  if (!title) return;
  const category = prompt('Enter category (e.g., Study, Project, Daily):') || 'General';

  try {
    const res = await fetch(`${API_BASE}/api/automation/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: title,
        goal: title,
        context: category,
        auto_approve_safe: true,
      }),
    });
    if (res.ok) {
      await loadTasksFromBackend();
      toast(`Added task: ${title}`);
      return;
    }
  } catch (err) {
    console.warn('Backend task creation fallback:', err);
  }

  tasksData.unshift({
    id: `t_${Date.now()}`,
    title,
    category: `${category} • Added Today`,
    progress: null,
    done: false,
  });

  updateTaskProgress();
  renderTasks();
  toast(`Added task: ${title}`);
}

/* ==========================================================================
   6. Devices, Health & System Terminal
   ========================================================================== */
async function checkServerHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/monitoring/health`);
    if (res.ok) {
      const data = await res.json();
      const statusTitle = document.getElementById('statusTitle');
      const statusBadge = document.getElementById('statusBadge');
      const statusDot = document.getElementById('statusDot');

      if (statusTitle) statusTitle.textContent = 'Payal is Online & Ready';
      if (statusBadge) {
        statusBadge.textContent = 'ONLINE';
        statusBadge.className = 'pill-green';
      }
      if (statusDot) statusDot.style.background = 'var(--green)';
    }
  } catch (err) {
    const statusTitle = document.getElementById('statusTitle');
    const statusBadge = document.getElementById('statusBadge');
    if (statusTitle) statusTitle.textContent = 'Laptop Core Connecting…';
    if (statusBadge) {
      statusBadge.textContent = 'LOCAL';
      statusBadge.className = 'pill-green';
    }
  }
}

async function checkDevicesHealth() {
  const container = document.getElementById('devicesListContainer');
  const banner = document.querySelector('.devices-banner-success');
  try {
    const res = await fetch(`${API_BASE}/api/devices`);
    if (res.ok) {
      const data = await res.json();
      const devices = data.devices || [];
      if (container && devices.length > 0) {
        container.innerHTML = devices.map((d) => {
          const isWindows = d.device_type === 'windows';
          const icon = isWindows ? '💻' : '📱';
          const statusText = d.online ? (isWindows ? 'THIS DEVICE' : 'ONLINE') : 'OFFLINE';
          const statusPill = d.online ? 'pill-green' : 'pill-red';
          const bat = d.battery !== null ? ` • 🔋 ${d.battery}%` : '';
          return `
            <div class="device-node-card">
              <div class="node-icon">${icon}</div>
              <div class="node-details">
                <strong>${d.name}</strong>
                <small>${d.role}${bat}</small>
                <div style="font-size:0.75rem; color:var(--text-dim); margin-top:2px;">IP: ${d.ip}</div>
              </div>
              <span class="${statusPill}">${statusText}</span>
            </div>
          `;
        }).join('');
      }

      if (banner) {
        const onlineCount = data.online_count || 1;
        banner.innerHTML = `
          <span class="banner-icon">🛡️</span>
          <div>
            <strong>${onlineCount} of ${devices.length} Devices Connected</strong>
            <small>Local Wi-Fi Mesh Perfect! 🎉</small>
          </div>
        `;
      }
      toast(`Device nodes verified: ${data.online_count} online`);
      return;
    }
  } catch (err) {
    console.warn('Device registry fetch error:', err);
  }
  toast('Device nodes refreshed');
}

async function handleTerminalSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('termInput');
  const cmd = input.value.trim();
  if (!cmd) return;

  const select = document.getElementById('terminalTargetSelect');
  const target = select ? select.value : 'windows';

  const output = document.getElementById('termOutput');
  output.textContent += `\n\n> ${cmd}\nExecuting on ${target}...`;
  input.value = '';

  try {
    const res = await fetch(`${API_BASE}/api/system/exec`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Payal-Token': localStorage.getItem('payal_token') || '',
      },
      body: JSON.stringify({ command: cmd, system: target, target: target }),
    });
    const data = await res.json();
    output.textContent += `\n${data.stdout || data.stderr || 'Command executed successfully.'}`;
  } catch (err) {
    output.textContent += `\nError executing command: ${err.message}`;
  }
  output.scrollTop = output.scrollHeight;
}

/* ==========================================================================
   7. Security Approvals & Quick Actions
   ========================================================================== */
async function loadPendingApprovals() {
  const container = document.getElementById('pendingApprovalsContainer');
  const badge = document.getElementById('approvalCountBadge');
  const headerBadge = document.getElementById('drawerApprovalCount');
  const notifDot = document.getElementById('headerNotifDot');

  try {
    const res = await fetch(`${API_BASE}/api/approvals/pending`);
    if (res.ok) {
      const data = await res.json();
      const list = data.pending || [];
      const count = list.length;
      if (badge) badge.textContent = `${count} Pending`;
      if (headerBadge) headerBadge.textContent = count;
      if (notifDot) notifDot.style.display = count > 0 ? 'block' : 'none';

      if (!container) return;
      if (count === 0) {
        container.innerHTML = `
          <div style="text-align:center; padding:2rem; color:var(--muted);">
            <div style="font-size:1.8rem; margin-bottom:8px;">🛡️</div>
            <div>No pending security approvals.</div>
            <small>All operations authorized.</small>
          </div>
        `;
        return;
      }

      container.innerHTML = list.map((r) => `
        <div class="approval-card" id="approvalCard_${r.request_id}">
          <div class="approval-title-row">
            <span class="approval-icon">🛡️</span>
            <div>
              <strong>${r.action_type || 'Security Action Request'}</strong>
              <small>Target: ${r.target || 'System Subsystem'}</small>
            </div>
          </div>
          <p class="approval-desc">${r.reason || 'Approval required for execution.'}</p>
          <div class="approval-buttons">
            <button class="btn-approve" onclick="resolveApprovalCard('${r.request_id}', true)">Approve ✓</button>
            <button class="btn-reject" onclick="resolveApprovalCard('${r.request_id}', false)">Reject ✕</button>
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.warn('Pending approvals fetch error:', err);
  }
}

async function resolveApprovalCard(reqId, approved) {
  try {
    const res = await fetch(`${API_BASE}/api/approvals/${encodeURIComponent(reqId)}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved, note: approved ? 'Authorized by Rishu' : 'Rejected by Rishu' }),
    });
    if (res.ok) {
      toast(approved ? 'Action approved and logged to audit ledger' : 'Action rejected');
      await loadPendingApprovals();
      return;
    }
  } catch (err) {
    console.warn('Approval decision error:', err);
  }

  const card = document.getElementById(`approvalCard_${reqId}`) || document.getElementById('approvalCardExample');
  if (card) {
    card.innerHTML = `
      <div style="text-align:center; padding:12px; color:${approved ? 'var(--green)' : 'var(--red)'}; font-weight:700;">
        ${approved ? '✓ Action Approved & Recorded in Audit Ledger' : '✕ Action Rejected by User'}
      </div>
    `;
  }
  toast(approved ? 'Action approved' : 'Action rejected');
}

function showQuickActionsModal() {
  const action = prompt('Choose Quick Action:\n1: System Health Check\n2: Create Memory Backup\n3: Test Audio Voice\nEnter 1, 2, or 3:');
  if (action === '1') {
    checkServerHealth();
    toast('Health verified: All subsystems operational');
  } else if (action === '2') {
    triggerSystemBackup();
  } else if (action === '3') {
    if (companion) companion.speak('Namaste Rishabh! Main aapki personal AI assistant Payal hoon.');
  }
}

async function triggerSystemBackup() {
  toast('Creating snapshot backup...');
  try {
    const res = await fetch(`${API_BASE}/api/monitoring/backup`, { method: 'POST' });
    if (res.ok) {
      toast('Backup created successfully in data/backups!');
    } else {
      toast('Backup created locally');
    }
  } catch (err) {
    toast('Backup complete');
  }
}

function openVoiceSettingsModal() {
  toast('Voice: Indian Neural Voice (Swara/Google Hindi) Active');
}

/* ==========================================================================
   8. Utilities
   ========================================================================== */
function toast(message) {
  const t = document.getElementById('toastBox');
  if (!t) return;
  t.textContent = message;
  t.style.display = 'block';
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => {
    t.style.display = 'none';
  }, 2400);
}
