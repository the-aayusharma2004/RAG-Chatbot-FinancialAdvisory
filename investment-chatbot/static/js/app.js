/* =====================================================================
   InvestAI Dashboard — app.js
   Handles: status, portfolio, goals, transactions, chat, analysis
   ===================================================================== */

'use strict';

// ── STATE ────────────────────────────────────────────────────────────
let currentTab      = 'dashboard';
let chatMode        = 'general';
let currentUserId   = 1;
let isLoading       = false;
let existingInvestments = [];

// ── STARTERS per chat mode ───────────────────────────────────────────
const STARTERS = {
  general: [
    'How do I open an account?',
    'What is the minimum SIP amount?',
    'Where should I invest Rs.50,000?',
    'What are the tax benefits of ELSS?',
  ],
  faq: [
    'What KYC documents are required?',
    'How long does KYC verification take?',
    'How do I withdraw my investments?',
    'Is my investment insured?',
    'Can I have a joint account?',
  ],
  invest: [
    'What should I invest in?',
    'Compare SIP vs lump sum investment',
    'Best options for tax saving under 80C',
    'Recommend funds for retirement',
    'What is ELSS and how does it work?',
  ],
  portfolio: [
    'Show my portfolio summary',
    'How much have I invested in total?',
    'What are my recent transactions?',
    'How am I progressing on my goals?',
    'Analyze my portfolio and suggest improvements',
  ],
};

const CHAT_BANNERS = {
  general:   { title: 'InvestAI — Smart Financial Assistant',  desc: 'Ask anything — intent is detected automatically.' },
  faq:       { title: 'FAQ Assistant',                          desc: 'Get instant answers on KYC, accounts, withdrawals and policies.' },
  invest:    { title: 'Personalized Investment Advisor',        desc: 'Fill your profile on the left to get tailored recommendations.' },
  portfolio: { title: 'Portfolio Q&A — SQL + RAG Hybrid',      desc: 'Ask about your live portfolio data. Uses your selected user.' },
};

// ── INIT ─────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  checkStatus();
  loadDashboard();
  renderStarters();
  setupTextarea();
  setupTagInput();

  document.getElementById('message-input').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
});

// ── TAB SWITCHING ─────────────────────────────────────────────────────
function switchTab(tab) {
  currentTab = tab;
  ['dashboard', 'chat'].forEach(t => {
    document.getElementById(`tab-${t}`)?.classList.remove('active');
    document.getElementById(`panel-${t}`)?.classList.remove('active');
  });
  document.getElementById(`tab-${tab}`)?.classList.add('active');
  document.getElementById(`panel-${tab}`)?.classList.add('active');
}

function switchTabAndAsk(tab, question) {
  switchTab(tab);
  setTimeout(() => {
    document.getElementById('message-input').value = question;
    sendMessage();
  }, 100);
}

// ── SIDEBAR TOGGLE ────────────────────────────────────────────────────
function toggleSidebar() {
  document.getElementById('sidebar')?.classList.toggle('collapsed');
}

// ── USER CHANGE ───────────────────────────────────────────────────────
function onUserChange() {
  currentUserId = parseInt(document.getElementById('user-select').value);
  loadDashboard();
}

// ── STATUS CHECK ──────────────────────────────────────────────────────
async function checkStatus() {
  try {
    const data = await apiFetch('/status');
    updateStatusUI(data);
  } catch {
    updateStatusUI(null);
  }
}

function updateStatusUI(data) {
  const dot  = document.getElementById('status-dot');
  const text = document.getElementById('status-text');

  if (!data) {
    dot.className    = 'status-dot error';
    text.textContent = 'Offline';
    setSysDot('dot-ollama', 'err'); setVal('val-ollama', 'Unreachable');
    setSysDot('dot-db',     'err'); setVal('val-db',     '—');
    setSysDot('dot-rag',    'err'); setVal('val-rag',    '—');
    return;
  }

  const ollamaOk = data.ollama_status?.status === 'ok';
  const ragOk    = data.rag_status === 'ready';
  const dbOk     = data.db_status?.status === 'ok';
  const allOk    = ollamaOk && ragOk;

  dot.className    = allOk ? 'status-dot ok' : ollamaOk ? 'status-dot warn' : 'status-dot error';
  text.textContent = allOk ? `${data.model || 'llama3'} · Ready` : ollamaOk ? 'RAG loading…' : 'Ollama offline';

  setSysDot('dot-ollama', ollamaOk ? 'ok' : 'err');
  setVal('val-ollama', ollamaOk ? 'ok' : 'offline');
  setSysDot('dot-db', dbOk ? 'ok' : 'err');
  setVal('val-db', dbOk ? 'ok' : 'offline');
  setSysDot('dot-rag', ragOk ? 'ok' : 'warn');
  setVal('val-rag', ragOk ? 'ready' : 'loading');

  setModalVal('sm-ollama', ollamaOk ? 'Connected \u2713' : (data.ollama_status?.status || 'Error'), ollamaOk ? 'ok' : 'err');
  setModalVal('sm-model',  data.model || '\u2014', '');
  setModalVal('sm-rag',    ragOk ? 'Ready \u2713' : (data.rag_status || 'Not ready'), ragOk ? 'ok' : 'warn');
  setModalVal('sm-db',     dbOk ? 'Connected \u2713' : (data.db_status?.status || '\u2014'), dbOk ? 'ok' : 'err');
  setModalVal('sm-models', (data.ollama_status?.available_models || []).join(', ') || '\u2014', '');
}

function setSysDot(id, cls) { const el = document.getElementById(id); if (el) el.className = 'sys-dot ' + cls; }
function setVal(id, val)     { const el = document.getElementById(id); if (el) el.textContent = val; }
function setModalVal(id, val, cls) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = val;
  el.className = 'status-val ' + cls;
}

function openStatusModal() { document.getElementById('status-modal').classList.add('open'); checkStatus(); }
function closeStatusModal(e) {
  if (!e || e.target === document.getElementById('status-modal')) {
    document.getElementById('status-modal').classList.remove('open');
  }
}

// ── DASHBOARD LOAD ────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const [portfolioData, goalsData, txData] = await Promise.all([
      apiFetch(`/portfolio/${currentUserId}`),
      apiFetch(`/goals/${currentUserId}`),
      apiFetch(`/transactions/${currentUserId}?limit=10`),
    ]);
    renderPortfolioSummary(portfolioData);
    renderHoldings(portfolioData.holdings || []);
    renderGoals(goalsData.goals || []);
    renderTransactions(txData.transactions || []);
  } catch (err) {
    console.error('Dashboard load error:', err);
    setText('portfolio-sub', 'Error loading data — is MySQL running?');
  }
}

// ── PORTFOLIO SUMMARY ─────────────────────────────────────────────────
function renderPortfolioSummary(data) {
  const gain    = data.total_gain_loss || 0;
  const gainPct = data.overall_gain_pct || 0;
  const isPos   = gain >= 0;

  setText('val-invested', formatRs(data.total_invested));
  setText('val-current',  formatRs(data.portfolio_value));
  setText('val-gain',     (isPos ? '+' : '') + formatRs(gain));
  setText('val-holdings', data.holdings?.length || 0);

  const pctEl = document.getElementById('val-gain-pct');
  if (pctEl) {
    pctEl.textContent = (isPos ? '+' : '') + gainPct.toFixed(2) + '%';
    pctEl.className   = 'sum-card-pct ' + (isPos ? 'positive' : 'negative');
  }

  const userId = document.getElementById('user-select');
  const name   = userId?.options[userId.selectedIndex]?.text?.split(' (')[0] || '';
  setText('portfolio-sub', `Portfolio for ${name}`);
}

// ── HOLDINGS ──────────────────────────────────────────────────────────
function renderHoldings(holdings) {
  const container = document.getElementById('holdings-list');
  if (!container) return;
  if (!holdings.length) {
    container.innerHTML = '<div class="tx-loading">No holdings found.</div>';
    return;
  }
  container.innerHTML = holdings.map(h => {
    const isPos = h.gain_loss >= 0;
    const riskClass = riskToClass(h.risk_level);
    return `
      <div class="holding-row">
        <div>
          <div class="holding-name">${escapeHtml(h.product_name)}</div>
          <div class="holding-meta">
            <span class="holding-badge ${riskClass}">${escapeHtml(h.risk_level)} risk</span>
            <span>${escapeHtml(h.category)}</span>
            <span>Since ${h.purchase_date}</span>
          </div>
        </div>
        <div class="holding-col">
          <div class="holding-col-label">Invested</div>
          <div class="holding-col-val">${formatRs(h.amount_invested)}</div>
        </div>
        <div class="holding-col">
          <div class="holding-col-label">Current</div>
          <div class="holding-col-val">${formatRs(h.current_value)}</div>
        </div>
        <div class="holding-col">
          <div class="holding-col-label">Gain / Loss</div>
          <div class="holding-gain ${isPos ? 'positive' : 'negative'}">
            ${isPos ? '+' : ''}${formatRs(h.gain_loss)} (${isPos ? '+' : ''}${h.gain_pct}%)
          </div>
        </div>
      </div>`;
  }).join('');
}

// ── GOALS ─────────────────────────────────────────────────────────────
function renderGoals(goals) {
  const container = document.getElementById('goals-grid');
  if (!container) return;
  if (!goals.length) {
    container.innerHTML = '<div class="tx-loading">No goals found.</div>';
    return;
  }
  container.innerHTML = goals.map(g => {
    const pct    = Math.min(g.progress_pct, 100);
    const almost = pct >= 75;
    return `
      <div class="goal-card">
        <div class="goal-header">
          <div class="goal-name">${escapeHtml(g.goal_name)}</div>
          <div class="goal-pct-badge">${pct.toFixed(1)}%</div>
        </div>
        <div class="goal-progress-wrap">
          <div class="goal-bar-track">
            <div class="goal-bar-fill${almost ? ' almost' : ''}" style="width:${pct}%"></div>
          </div>
          <div class="goal-amounts">
            <span>Progress: ${formatRs(g.current_progress)}</span>
            <span>Target: ${formatRs(g.target_amount)}</span>
          </div>
        </div>
        <div class="goal-footer">
          <div class="goal-date">🗓 Target: ${g.target_date}</div>
          <div class="goal-remaining">${formatRs(g.remaining)} remaining</div>
        </div>
      </div>`;
  }).join('');
}

// ── TRANSACTIONS ──────────────────────────────────────────────────────
function renderTransactions(txs) {
  const tbody = document.getElementById('tx-tbody');
  if (!tbody) return;
  if (!txs.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="tx-loading">No transactions found.</td></tr>';
    return;
  }
  tbody.innerHTML = txs.map(t => `
    <tr>
      <td>${t.date ? t.date.slice(0,10) : '\u2014'}</td>
      <td>${escapeHtml(t.product_name)}</td>
      <td><span class="tx-type ${t.type}">${t.type}</span></td>
      <td class="tx-amount">${formatRs(t.amount)}</td>
    </tr>`).join('');
}

// ── PORTFOLIO ANALYSIS ────────────────────────────────────────────────
async function triggerPortfolioAnalysis() {
  const modal  = document.getElementById('analysis-modal');
  const result = document.getElementById('analysis-result');
  modal.classList.add('open');
  result.innerHTML = `
    <div class="analysis-loading">
      <div class="spinner"></div>
      <p>Analyzing your portfolio with AI&hellip;<br>
         <small style="color:var(--text-muted)">This may take 30&ndash;60 seconds</small>
      </p>
    </div>`;

  try {
    const data = await apiFetch('/portfolio-analysis', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        user_id: currentUserId,
        message: 'Analyze my portfolio and suggest improvements based on my goals and risk profile.',
      }),
    });
    result.innerHTML = '<div>' + formatMessage(data.response || 'No response received.') + '</div>';
  } catch (err) {
    result.innerHTML = `<div style="color:var(--red)">\u26A0\uFE0F Error: ${escapeHtml(err.message)}</div>`;
  }
}

function closeAnalysisModal(e) {
  if (!e || e.target === document.getElementById('analysis-modal')) {
    document.getElementById('analysis-modal').classList.remove('open');
  }
}

// ── CHAT MODE ─────────────────────────────────────────────────────────
function setChatMode(mode) {
  chatMode = mode;
  ['general','faq','invest','portfolio'].forEach(m => {
    document.getElementById('cmode-' + m)?.classList.remove('active');
  });
  document.getElementById('cmode-' + mode)?.classList.add('active');

  const form = document.getElementById('chat-profile-form');
  if (form) form.classList.toggle('visible', mode === 'invest');

  const banner = CHAT_BANNERS[mode];
  if (banner) {
    setText('chat-banner-title', banner.title);
    setText('chat-banner-desc',  banner.desc);
  }
  renderStarters();
}

function renderStarters() {
  const container = document.getElementById('starter-list');
  if (!container) return;
  container.innerHTML = '';
  (STARTERS[chatMode] || []).forEach(s => {
    const btn = document.createElement('button');
    btn.className   = 'starter-btn';
    btn.textContent = s;
    btn.onclick     = () => {
      document.getElementById('message-input').value = s;
      sendMessage();
    };
    container.appendChild(btn);
  });
}

// ── SCROLL TO SECTION ─────────────────────────────────────────────────
function scrollToSection(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  ['overview','holdings','goals','transactions'].forEach(s => {
    document.getElementById('sl-' + s)?.classList.remove('active');
  });
  document.getElementById('sl-' + id)?.classList.add('active');
}

// ── TAG INPUT ─────────────────────────────────────────────────────────
function setupTagInput() {
  const tagInput = document.getElementById('tag-input');
  if (!tagInput) return;
  tagInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag(tagInput.value.trim());
      tagInput.value = '';
    } else if (e.key === 'Backspace' && tagInput.value === '' && existingInvestments.length > 0) {
      removeTag(existingInvestments.length - 1);
    }
  });
}

function addTag(val) { if (!val || existingInvestments.includes(val)) return; existingInvestments.push(val); renderTags(); }
function removeTag(idx) { existingInvestments.splice(idx, 1); renderTags(); }
function renderTags() {
  const wrapper = document.getElementById('tag-wrapper');
  const input   = document.getElementById('tag-input');
  if (!wrapper || !input) return;
  wrapper.innerHTML = '';
  existingInvestments.forEach((t, i) => {
    const tag = document.createElement('span');
    tag.className = 'tag';
    tag.innerHTML = escapeHtml(t) + `<span class="tag-remove" onclick="removeTag(${i})">\u2715</span>`;
    wrapper.appendChild(tag);
  });
  wrapper.appendChild(input);
}

// ── TEXTAREA AUTO-RESIZE ──────────────────────────────────────────────
function setupTextarea() {
  const ta = document.getElementById('message-input');
  if (!ta) return;
  ta.addEventListener('input', () => {
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
  });
}

// ── SEND MESSAGE ──────────────────────────────────────────────────────
async function sendMessage() {
  if (isLoading) return;
  const input = document.getElementById('message-input');
  const text  = input.value.trim();
  if (!text) return;

  const welcome = document.getElementById('welcome-state');
  if (welcome) welcome.style.display = 'none';

  appendMessage('user', text);
  input.value = '';
  input.style.height = 'auto';

  const typing = appendTypingIndicator();
  setLoading(true);

  try {
    let endpoint, body;

    if (chatMode === 'invest' && hasProfile()) {
      endpoint = '/profile-chat';
      body = { message: text, profile: buildProfile() };
    } else if (chatMode === 'portfolio') {
      endpoint = '/chat';
      body = { message: text, user_id: currentUserId };
    } else {
      endpoint = '/chat';
      body = { message: text };
      if (chatMode === 'invest' && hasProfile()) body.user_profile = buildProfile();
    }

    const data = await apiFetch(endpoint, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(body),
    });

    typing.remove();
    if (data.error) {
      appendMessage('ai', '\u26A0\uFE0F ' + data.error, null, true);
    } else {
      appendMessage('ai', data.response, data.intent);
    }
  } catch (err) {
    typing.remove();
    appendMessage('ai', '\u26A0\uFE0F Network error: ' + err.message, null, true);
  } finally {
    setLoading(false);
  }
}

function hasProfile() {
  return (
    document.getElementById('p-age')?.value &&
    document.getElementById('p-income')?.value &&
    document.getElementById('p-risk')?.value &&
    document.getElementById('p-goal')?.value &&
    document.getElementById('p-horizon')?.value
  );
}

function buildProfile() {
  return {
    age:                  parseInt(document.getElementById('p-age').value),
    monthly_income:       parseFloat(document.getElementById('p-income').value),
    risk_appetite:        document.getElementById('p-risk').value,
    investment_goal:      document.getElementById('p-goal').value,
    investment_horizon:   document.getElementById('p-horizon').value,
    existing_investments: [...existingInvestments],
  };
}

// ── MESSAGE RENDERING ─────────────────────────────────────────────────
function appendMessage(role, text, intent, isError) {
  const list   = document.getElementById('messages-list');
  const msg    = document.createElement('div');
  msg.className = 'message ' + (role === 'user' ? 'user' : 'ai');

  const avatar = document.createElement('div');
  avatar.className   = 'message-avatar';
  avatar.textContent = role === 'user' ? '\uD83D\uDC64' : '\uD83E\uDD16';

  const body = document.createElement('div');
  body.className = 'message-body';

  const meta = document.createElement('div');
  meta.className = 'message-meta';

  const name = document.createElement('span');
  name.className   = 'message-name';
  name.textContent = role === 'user' ? 'You' : 'InvestAI';

  const time = document.createElement('span');
  time.className   = 'message-time';
  time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  meta.appendChild(name);
  meta.appendChild(time);

  if (intent && role === 'ai') {
    const badge = document.createElement('span');
    badge.className   = 'intent-badge ' + intent;
    badge.textContent = intentLabel(intent);
    meta.appendChild(badge);
  }

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble' + (isError ? ' error' : '');
  bubble.innerHTML = formatMessage(text);

  body.appendChild(meta);
  body.appendChild(bubble);
  msg.appendChild(avatar);
  msg.appendChild(body);

  list.appendChild(msg);
  list.scrollTop = list.scrollHeight;
  return msg;
}

function appendTypingIndicator() {
  const list = document.getElementById('messages-list');
  const msg  = document.createElement('div');
  msg.className = 'message ai typing-indicator';
  msg.innerHTML = `
    <div class="message-avatar">\uD83E\uDD16</div>
    <div class="message-body">
      <div class="message-meta"><span class="message-name">InvestAI</span></div>
      <div class="message-bubble">
        <div class="typing-dots"><span></span><span></span><span></span></div>
      </div>
    </div>`;
  list.appendChild(msg);
  list.scrollTop = list.scrollHeight;
  return msg;
}

function intentLabel(intent) {
  return { faq: '\u2753 FAQ', investment: '\uD83D\uDCC8 Investment', sql: '\uD83D\uDDC4 Portfolio Data', hybrid: '\uD83D\uDD17 Hybrid', general: '\uD83D\uDCAC General' }[intent] || intent;
}

// ── FORMAT HELPERS ────────────────────────────────────────────────────
function formatMessage(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g,  '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,      '<em>$1</em>')
    .replace(/`(.+?)`/g,        '<code>$1</code>')
    .replace(/^#{1,3} (.+)$/gm, '<strong>$1</strong>')
    .replace(/^- (.+)$/gm,      '&bull; $1')
    .replace(/\n/g,             '<br />');
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g,  '&amp;')
    .replace(/</g,  '&lt;')
    .replace(/>/g,  '&gt;')
    .replace(/"/g,  '&quot;');
}

function formatRs(n) {
  if (n === undefined || n === null) return '\u2014';
  return '\u20B9' + Number(Math.round(n)).toLocaleString('en-IN');
}

function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }

function riskToClass(risk) {
  const r = (risk || '').toLowerCase().replace(/\s+/g, '-');
  if (r === 'high')     return 'risk-high';
  if (r === 'medium')   return 'risk-medium';
  if (r === 'low')      return 'risk-low';
  if (r === 'very-low') return 'risk-very-low';
  if (r === 'none')     return 'risk-none';
  return 'risk-low';
}

// ── API HELPER ────────────────────────────────────────────────────────
async function apiFetch(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) { const t = await res.text(); throw new Error(`HTTP ${res.status}: ${t}`); }
  return res.json();
}

function setLoading(val) {
  isLoading = val;
  const btn = document.getElementById('send-btn');
  if (btn) btn.disabled = val;
}
