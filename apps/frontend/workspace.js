/**
 * Payal Unified Workspace Controller
 * Connects AI Chat, Autonomous Orchestrator, ECC Component Browser,
 * Memory Vault, Terminal Console, and Robot Companion.
 */

const API_BASE = window.location.origin;

// State management
let activeTab = 'chat';
let companion = null;
let currentOrchestrationPlan = null;
let voiceOutputEnabled = true;

document.addEventListener('DOMContentLoaded', () => {
  initCompanion();
  initNavigation();
  initChat();
  initOrchestrator();
  initCatalog();
  initMemory();
  initTerminal();
  loadInitialData();
});

/* ==========================================================================
   1. Robot Companion Initialization & Speech Hooks
   ========================================================================== */
function initCompanion() {
  companion = new RobotCompanion('robotCanvas');

  // Mic toggle listener
  const btnMic = document.getElementById('btnMicToggle');
  if (btnMic) {
    btnMic.addEventListener('click', () => {
      companion.toggleListening();
    });
  }

  // Handle transcribed speech
  companion.onSpeechResult = (text, isFinal) => {
    const input = document.getElementById('chatInput');
    if (input) {
      input.value = text;
      if (isFinal) {
        companion.setEmotion('thinking');
        setTimeout(() => sendChatMessage(), 300);
      }
    }
  };

  // Voice output toggle
  const btnVoice = document.getElementById('btnVoiceToggle');
  if (btnVoice) {
    btnVoice.addEventListener('click', () => {
      voiceOutputEnabled = !voiceOutputEnabled;
      btnVoice.classList.toggle('active', voiceOutputEnabled);
      if (!voiceOutputEnabled) companion.stopSpeaking();
    });
  }

  // Floating companion PIP toggle
  const btnFloat = document.getElementById('btnFloatCompanion');
  const floatBox = document.getElementById('floatingCompanionBox');
  if (btnFloat && floatBox) {
    btnFloat.addEventListener('click', () => {
      floatBox.classList.toggle('active');
    });
  }

  // Emotion quick chips
  document.querySelectorAll('.emotion-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      const emo = chip.dataset.emotion;
      companion.setEmotion(emo);
    });
  });
}

/* ==========================================================================
   2. Workspace Navigation (Desktop Tabs & Mobile Nav)
   ========================================================================== */
function initNavigation() {
  const tabs = document.querySelectorAll('.tab-btn');
  const panels = document.querySelectorAll('.tab-panel');
  const mobileNavs = document.querySelectorAll('.mobile-nav-item');

  function switchTab(targetId) {
    activeTab = targetId;
    tabs.forEach((t) => t.classList.toggle('active', t.dataset.tab === targetId));
    panels.forEach((p) => p.classList.toggle('active', p.id === `panel-${targetId}`));
    mobileNavs.forEach((m) => m.classList.toggle('active', m.dataset.tab === targetId));

    // Mobile companion visibility toggle
    const companionStage = document.getElementById('companionStage');
    if (companionStage) {
      if (targetId === 'companion') {
        companionStage.classList.add('mobile-visible');
      } else {
        companionStage.classList.remove('mobile-visible');
      }
    }
  }

  tabs.forEach((tab) => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
  });

  mobileNavs.forEach((item) => {
    item.addEventListener('click', () => switchTab(item.dataset.tab));
  });
}

/* ==========================================================================
   3. AI Chat & Companion Conversation
   ========================================================================== */
function initChat() {
  const btnSend = document.getElementById('btnSendChat');
  const input = document.getElementById('chatInput');

  if (btnSend && input) {
    btnSend.addEventListener('click', sendChatMessage);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });
  }
}

async function sendChatMessage() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  appendChatMessage('user', text);
  input.value = '';

  // Trigger thinking face
  companion.setEmotion('thinking');

  try {
    // 1. Send chat completion request
    const res = await fetch(`${API_BASE}/api/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: text }],
      }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const replyText = data.content || 'I have processed your request.';

    // 2. Classify emotion of reply
    const emoRes = await fetch(`${API_BASE}/api/system/emotion`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: replyText }),
    });
    const emoData = emoRes.ok ? await emoRes.json() : { emotion: 'neutral' };

    // 3. Display response & speak with dynamic emotion
    appendChatMessage('assistant', replyText, emoData.emotion);
    companion.setEmotion(emoData.emotion, emoData.intensity);

    if (voiceOutputEnabled) {
      companion.speak(replyText, emoData.emotion);
    }
  } catch (err) {
    console.error('Chat error:', err);
    appendChatMessage('assistant', `Error connecting to engine: ${err.message}`, 'sad');
    companion.setEmotion('sad');
  }
}

function appendChatMessage(role, content, emotion = null) {
  const container = document.getElementById('chatMessages');
  if (!container) return;

  const msgDiv = document.createElement('div');
  msgDiv.className = `message-bubble ${role}`;

  const avatarDiv = document.createElement('div');
  avatarDiv.className = 'bubble-avatar';
  avatarDiv.textContent = role === 'user' ? '👤' : '✨';

  const contentDiv = document.createElement('div');
  contentDiv.className = 'bubble-content';
  contentDiv.innerHTML = formatMarkdown(content);

  if (emotion && role === 'assistant') {
    const tag = document.createElement('span');
    tag.className = 'emotion-tag-pill';
    tag.style.display = 'block';
    tag.style.marginTop = '0.5rem';
    tag.style.width = 'fit-content';
    tag.textContent = `MOOD: ${emotion.toUpperCase()}`;
    contentDiv.appendChild(tag);
  }

  msgDiv.appendChild(avatarDiv);
  msgDiv.appendChild(contentDiv);
  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

/* ==========================================================================
   4. Autonomous Orchestrator Integration
   ========================================================================== */
function initOrchestrator() {
  const btnPlan = document.getElementById('btnPreviewPlan');
  const btnRun = document.getElementById('btnRunOrchestration');

  if (btnPlan) {
    btnPlan.addEventListener('click', async () => {
      const goal = document.getElementById('orchGoalInput').value.trim();
      if (!goal) return alert('Please enter a goal.');

      companion.setEmotion('thinking');
      try {
        const res = await fetch(`${API_BASE}/api/orchestrate/plan`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ goal }),
        });
        const plan = await res.json();
        currentOrchestrationPlan = plan;
        renderPlanSteps(plan.steps);
        companion.setEmotion('serious');
      } catch (err) {
        alert('Plan generation failed: ' + err.message);
      }
    });
  }

  if (btnRun) {
    btnRun.addEventListener('click', async () => {
      const goal = document.getElementById('orchGoalInput').value.trim();
      if (!goal) return alert('Please enter a goal.');

      companion.setEmotion('excited');
      const btn = btnRun;
      btn.disabled = true;
      btn.textContent = 'Executing...';

      try {
        const res = await fetch(`${API_BASE}/api/orchestrate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ goal, auto_approve_safe: true, record_memory: true }),
        });
        const result = await res.json();

        renderExecutionResults(result);
        if (result.success) {
          companion.setEmotion('proud');
          if (voiceOutputEnabled) companion.speak('Task successfully executed and recorded in memory!', 'proud');
        } else {
          companion.setEmotion('sad');
        }
      } catch (err) {
        alert('Execution failed: ' + err.message);
        companion.setEmotion('alert');
      } finally {
        btn.disabled = false;
        btn.textContent = 'Execute Autonomous Pipeline';
      }
    });
  }
}

function renderPlanSteps(steps) {
  const container = document.getElementById('orchStepTimeline');
  if (!container) return;
  container.innerHTML = '';

  steps.forEach((step, idx) => {
    const card = document.createElement('div');
    card.className = 'step-card pending';
    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <strong>${idx + 1}. ${step.title}</strong>
        <span class="status-badge" style="background:rgba(251,191,36,0.1); color:var(--color-warning);">RISK: ${step.risk_level}</span>
      </div>
      <div style="font-size:0.8rem; color:var(--text-secondary);">Target: <code>${step.target_name}</code> (${step.action_type})</div>
    `;
    container.appendChild(card);
  });
}

function renderExecutionResults(result) {
  const container = document.getElementById('orchStepTimeline');
  const reportBox = document.getElementById('orchFinalOutput');
  if (container) {
    container.innerHTML = '';
    result.step_results.forEach((r, idx) => {
      const card = document.createElement('div');
      card.className = `step-card ${r.success ? 'success' : 'failed'}`;
      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <strong>${idx + 1}. ${r.target_name} (${r.action_type})</strong>
          <span class="status-badge" style="${r.success ? '' : 'color:var(--color-danger); background:rgba(248,113,113,0.1);'}">${r.success ? 'PASSED' : 'FAILED'}</span>
        </div>
        <div style="font-size:0.75rem; color:var(--text-muted);">${r.duration_seconds.toFixed(2)}s | ${r.approval_status}</div>
      `;
      container.appendChild(card);
    });
  }

  if (reportBox) {
    reportBox.textContent = result.final_output;
  }
}

/* ==========================================================================
   5. ECC Component Catalog Browser
   ========================================================================== */
function initCatalog() {
  const searchInput = document.getElementById('catalogSearchInput');
  const filterSelect = document.getElementById('catalogFilterSelect');

  if (searchInput) {
    searchInput.addEventListener('input', () => debounce(loadCatalogItems, 300)());
  }
  if (filterSelect) {
    filterSelect.addEventListener('change', loadCatalogItems);
  }
}

async function loadCatalogItems() {
  const grid = document.getElementById('catalogGrid');
  const query = document.getElementById('catalogSearchInput')?.value || '';
  const filter = document.getElementById('catalogFilterSelect')?.value || 'agents';
  if (!grid) return;

  grid.innerHTML = '<div style="color:var(--text-muted);">Loading catalog...</div>';

  try {
    let url = `${API_BASE}/api/components/${filter}?limit=30`;
    if (query) url += `&q=${encodeURIComponent(query)}`;

    const res = await fetch(url);
    const items = await res.json();

    grid.innerHTML = '';
    if (items.length === 0) {
      grid.innerHTML = '<div style="color:var(--text-muted);">No components matched your query.</div>';
      return;
    }

    items.forEach((item) => {
      const card = document.createElement('div');
      card.className = 'component-item-card';
      card.innerHTML = `
        <span class="component-badge" style="background:rgba(56,189,248,0.15); color:var(--color-primary);">${filter.toUpperCase()}</span>
        <strong style="font-size:0.95rem;">${item.name}</strong>
        <p style="font-size:0.8rem; color:var(--text-secondary); line-height:1.4;">${(item.description || 'Specialized ECC Component').slice(0, 120)}...</p>
      `;
      grid.appendChild(card);
    });
  } catch (err) {
    grid.innerHTML = `<div style="color:var(--color-danger);">Failed to load catalog: ${err.message}</div>`;
  }
}

/* ==========================================================================
   6. Memory & Knowledge Vault
   ========================================================================== */
function initMemory() {
  const btnRefresh = document.getElementById('btnRefreshMemory');
  const btnSaveMem = document.getElementById('btnSaveMemory');

  if (btnRefresh) btnRefresh.addEventListener('click', loadMemoryItems);

  if (btnSaveMem) {
    btnSaveMem.addEventListener('click', async () => {
      const title = document.getElementById('memTitleInput').value.trim();
      const content = document.getElementById('memContentInput').value.trim();
      const kind = document.getElementById('memKindSelect').value;
      if (!title || !content) return alert('Please enter title and content.');

      try {
        const res = await fetch(`${API_BASE}/api/memory`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, content, kind }),
        });
        if (res.ok) {
          alert('Memory stored successfully!');
          document.getElementById('memTitleInput').value = '';
          document.getElementById('memContentInput').value = '';
          loadMemoryItems();
        }
      } catch (err) {
        alert('Save error: ' + err.message);
      }
    });
  }
}

async function loadMemoryItems() {
  const container = document.getElementById('memoryListContainer');
  if (!container) return;
  container.innerHTML = 'Loading memories...';

  try {
    const res = await fetch(`${API_BASE}/api/memory?limit=25`);
    const memories = await res.json();
    container.innerHTML = '';

    memories.forEach((m) => {
      const itemDiv = document.createElement('div');
      itemDiv.className = 'step-card';
      itemDiv.style.marginBottom = '0.75rem';
      itemDiv.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <strong>[${m.kind.toUpperCase()}] ${m.title}</strong>
          <span style="font-size:0.75rem; color:var(--text-muted);">${m.uri || 'Local'}</span>
        </div>
        <p style="font-size:0.85rem; color:var(--text-secondary); margin-top:0.3rem;">${m.content.slice(0, 180)}...</p>
      `;
      container.appendChild(itemDiv);
    });
  } catch (err) {
    container.innerHTML = `<div style="color:var(--color-danger);">${err.message}</div>`;
  }
}

/* ==========================================================================
   7. System & Terminal Execution (Windows / Kali)
   ========================================================================== */
function initTerminal() {
  const btnRun = document.getElementById('btnRunTerminal');
  const input = document.getElementById('terminalInput');

  if (btnRun && input) {
    btnRun.addEventListener('click', executeTerminalCommand);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') executeTerminalCommand();
    });
  }
}

async function executeTerminalCommand() {
  const input = document.getElementById('terminalInput');
  const system = document.getElementById('terminalSystemSelect').value;
  const output = document.getElementById('terminalOutput');
  const cmd = input.value.trim();
  if (!cmd) return;

  output.textContent += `\n> [${system.toUpperCase()}] ${cmd}\n`;
  input.value = '';

  try {
    const res = await fetch(`${API_BASE}/api/system/exec`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ system, command: cmd }),
    });
    const data = await res.json();
    output.textContent += data.stdout || data.stderr || 'Command executed with no output.';
    output.scrollTop = output.scrollHeight;
  } catch (err) {
    output.textContent += `Error: ${err.message}\n`;
  }
}

/* ==========================================================================
   8. Helpers & Initial Data Loading
   ========================================================================== */
async function loadInitialData() {
  loadCatalogItems();
  loadMemoryItems();

  // Load component stats into sidebar
  try {
    const res = await fetch(`${API_BASE}/api/components/stats`);
    if (res.ok) {
      const stats = await res.json();
      const elSkills = document.getElementById('statSkills');
      const elAgents = document.getElementById('statAgents');
      if (elSkills) elSkills.textContent = stats.total_skills;
      if (elAgents) elAgents.textContent = stats.total_agents;
    }
  } catch (err) {}
}

function formatMarkdown(text) {
  return text
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*)\*/gim, '<em>$1</em>')
    .replace(/```([\s\S]*?)```/gim, '<pre><code>$1</code></pre>')
    .replace(/`([^`]+)`/gim, '<code>$1</code>')
    .replace(/\n/gim, '<br>');
}

function debounce(func, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}
