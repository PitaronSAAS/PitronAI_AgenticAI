/* PitronAgent Widget v1.0 — drop-in chat bubble for any website
   Usage: <script src="https://api.pitronai.pro/widget/widget.js" data-agent-slug="your-slug"></script>
*/
(function () {
  'use strict';

  /* ── Config ──────────────────────────────────────────────────────────────── */
  var script = document.currentScript || (function () {
    var s = document.getElementsByTagName('script');
    return s[s.length - 1];
  })();

  var SLUG     = script.getAttribute('data-agent-slug') || '';
  var POSITION = script.getAttribute('data-position') || 'bottom-right';
  var API_BASE = script.getAttribute('data-api') || 'https://api.pitronai.pro';

  if (!SLUG) { console.warn('[PitronAgent] data-agent-slug is required.'); return; }

  /* ── Session ─────────────────────────────────────────────────────────────── */
  var SESSION_KEY = 'pitronai_sid_' + SLUG;
  var sessionId = sessionStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 8);
    sessionStorage.setItem(SESSION_KEY, sessionId);
  }

  /* ── State ───────────────────────────────────────────────────────────────── */
  var cfg = { primary_color: '#6366f1', agent_name: 'Assistant', welcome_message: 'Hi! How can I help?', api_key: '' };
  var isOpen    = false;
  var isBusy    = false;
  var el        = {};   // references to DOM nodes

  /* ── Shadow DOM & HTML ───────────────────────────────────────────────────── */
  var host = document.createElement('div');
  host.id  = 'pitronai-widget-host';
  document.body.appendChild(host);

  var shadow = host.attachShadow({ mode: 'open' });

  shadow.innerHTML = [
    '<style>',
    ':host { position: fixed; z-index: 2147483647; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }',
    '.pos-br { bottom: 24px; right: 24px; }',
    '.pos-bl { bottom: 24px; left:  24px; }',

    /* Toggle button */
    '#toggle { width:58px; height:58px; border-radius:50%; background:var(--c,#6366f1); border:none; cursor:pointer;',
    '  display:flex; align-items:center; justify-content:center;',
    '  box-shadow:0 4px 20px rgba(0,0,0,0.25); transition:transform .2s; padding:0; }',
    '#toggle:hover { transform:scale(1.08); }',
    '#toggle svg { width:26px; height:26px; fill:#fff; transition:opacity .2s; }',
    '#toggle .ic-close { display:none; }',
    '#toggle.open .ic-chat  { display:none; }',
    '#toggle.open .ic-close { display:block; }',

    /* Unread badge */
    '#badge { position:absolute; top:-4px; right:-4px; background:#ef4444; color:#fff;',
    '  border-radius:10px; font-size:11px; font-weight:700; padding:1px 6px; display:none; }',

    /* Window */
    '#win { position:absolute; width:360px; background:#fff; border-radius:16px;',
    '  box-shadow:0 20px 60px rgba(0,0,0,0.18); display:none; flex-direction:column; overflow:hidden;',
    '  bottom:72px; right:0; height:520px; }',
    '.pos-bl #win { right:auto; left:0; }',
    '#win.open { display:flex; }',

    /* Header */
    '#header { background:var(--c,#6366f1); padding:14px 16px; display:flex; align-items:center; gap:10px; flex-shrink:0; }',
    '.avatar { width:34px; height:34px; border-radius:50%; background:rgba(255,255,255,0.2);',
    '  display:flex; align-items:center; justify-content:center; font-size:16px; flex-shrink:0; }',
    '.hinfo { flex:1; min-width:0; }',
    '.hname { color:#fff; font-weight:700; font-size:14px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }',
    '.hstatus { color:rgba(255,255,255,0.8); font-size:11px; }',
    '.hstatus::before { content:"● "; }',

    /* Messages */
    '#msgs { flex:1; overflow-y:auto; padding:14px; display:flex; flex-direction:column; gap:8px; background:#f8fafc; }',
    '.msg { max-width:82%; padding:9px 13px; border-radius:14px; font-size:13.5px; line-height:1.5; word-break:break-word; }',
    '.msg.bot  { background:#fff; color:#1e293b; border-bottom-left-radius:3px; box-shadow:0 1px 2px rgba(0,0,0,0.07); align-self:flex-start; }',
    '.msg.user { background:var(--c,#6366f1); color:#fff; border-bottom-right-radius:3px; align-self:flex-end; }',

    /* Typing indicator */
    '.typing { display:flex; gap:5px; align-self:flex-start; background:#fff; padding:10px 14px; border-radius:14px; border-bottom-left-radius:3px; box-shadow:0 1px 2px rgba(0,0,0,0.07); }',
    '.typing span { width:7px; height:7px; background:#94a3b8; border-radius:50%; animation:bounce 1.2s infinite; }',
    '.typing span:nth-child(2) { animation-delay:.2s; }',
    '.typing span:nth-child(3) { animation-delay:.4s; }',
    '@keyframes bounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-6px)} }',

    /* Footer */
    '#footer { padding:10px; background:#fff; border-top:1px solid #e2e8f0; display:flex; gap:8px; flex-shrink:0; }',
    '#inp { flex:1; border:1px solid #e2e8f0; border-radius:10px; padding:9px 12px; font-size:13.5px;',
    '  outline:none; resize:none; font-family:inherit; max-height:80px; line-height:1.4; }',
    '#inp:focus { border-color:var(--c,#6366f1); }',
    '#send { background:var(--c,#6366f1); border:none; border-radius:10px; padding:9px 14px; color:#fff;',
    '  cursor:pointer; font-size:17px; transition:opacity .2s; display:flex; align-items:center; }',
    '#send:hover { opacity:.85; }',
    '#send:disabled { opacity:.45; cursor:not-allowed; }',

    /* Branding */
    '#brand { text-align:center; font-size:10.5px; color:#94a3b8; padding:4px 0 6px; background:#fff; flex-shrink:0; }',
    '#brand a { color:#6366f1; text-decoration:none; }',
    '</style>',

    '<div class="pos-' + (POSITION === 'bottom-left' ? 'bl' : 'br') + '">',
    '  <div id="win">',
    '    <div id="header">',
    '      <div class="avatar">🤖</div>',
    '      <div class="hinfo">',
    '        <div class="hname" id="aname">Assistant</div>',
    '        <div class="hstatus">Online</div>',
    '      </div>',
    '    </div>',
    '    <div id="msgs"></div>',
    '    <div id="footer">',
    '      <textarea id="inp" placeholder="Type a message…" rows="1"></textarea>',
    '      <button id="send" title="Send">',
    '        <svg viewBox="0 0 24 24" width="18" height="18" fill="white"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>',
    '      </button>',
    '    </div>',
    '    <div id="brand">Powered by <a href="https://pitronai.pro" target="_blank">PitronAI</a></div>',
    '  </div>',
    '  <button id="toggle" title="Chat with us">',
    '    <span id="badge"></span>',
    '    <svg class="ic-chat"  viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>',
    '    <svg class="ic-close" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
    '  </button>',
    '</div>',
  ].join('');

  /* ── Grab element refs ───────────────────────────────────────────────────── */
  el.win    = shadow.getElementById('win');
  el.toggle = shadow.getElementById('toggle');
  el.badge  = shadow.getElementById('badge');
  el.msgs   = shadow.getElementById('msgs');
  el.inp    = shadow.getElementById('inp');
  el.send   = shadow.getElementById('send');
  el.aname  = shadow.getElementById('aname');
  el.header = shadow.getElementById('header');

  /* ── Apply brand color ───────────────────────────────────────────────────── */
  function applyColor(hex) {
    shadow.host.style.setProperty('--c', hex);
    shadow.querySelectorAll('[style]').forEach(function (n) {
      n.style.removeProperty('--c');
    });
  }

  /* ── Fetch agent config ──────────────────────────────────────────────────── */
  fetch(API_BASE + '/v1/widget/' + SLUG + '/config')
    .then(function (r) { return r.json(); })
    .then(function (c) {
      cfg = Object.assign(cfg, c);
      el.aname.textContent = cfg.agent_name;
      applyColor(cfg.primary_color);
      addMsg('bot', cfg.welcome_message);
    })
    .catch(function () {
      addMsg('bot', cfg.welcome_message);
    });

  /* ── Message helpers ─────────────────────────────────────────────────────── */
  function addMsg(role, text) {
    var d = document.createElement('div');
    d.className = 'msg ' + role;
    d.textContent = text;
    el.msgs.appendChild(d);
    el.msgs.scrollTop = el.msgs.scrollHeight;
  }

  var _typingEl = null;
  function showTyping() {
    _typingEl = document.createElement('div');
    _typingEl.className = 'typing';
    _typingEl.innerHTML = '<span></span><span></span><span></span>';
    el.msgs.appendChild(_typingEl);
    el.msgs.scrollTop = el.msgs.scrollHeight;
  }
  function hideTyping() {
    if (_typingEl) { _typingEl.remove(); _typingEl = null; }
  }

  /* ── Toggle widget ───────────────────────────────────────────────────────── */
  function toggleWidget() {
    isOpen = !isOpen;
    el.win.classList.toggle('open', isOpen);
    el.toggle.classList.toggle('open', isOpen);
    if (isOpen) {
      el.badge.style.display = 'none';
      el.inp.focus();
    }
  }

  /* ── Send message ────────────────────────────────────────────────────────── */
  function sendMessage() {
    var text = el.inp.value.trim();
    if (!text || isBusy || !cfg.api_key) return;

    el.inp.value = '';
    el.inp.style.height = 'auto';
    addMsg('user', text);
    isBusy = true;
    el.send.disabled = true;
    showTyping();

    fetch(API_BASE + '/v1/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': cfg.api_key,
      },
      body: JSON.stringify({
        session_id: sessionId,
        message: text,
        metadata: { page_url: window.location.href, referrer: document.referrer },
      }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        hideTyping();
        addMsg('bot', data.message || 'Sorry, something went wrong.');
        if (!isOpen) {
          el.badge.textContent = '1';
          el.badge.style.display = 'block';
        }
      })
      .catch(function () {
        hideTyping();
        addMsg('bot', "Sorry, I'm having connection issues. Please try again.");
      })
      .finally(function () {
        isBusy = false;
        el.send.disabled = false;
        el.inp.focus();
      });
  }

  /* ── Events ──────────────────────────────────────────────────────────────── */
  el.toggle.addEventListener('click', toggleWidget);
  el.send.addEventListener('click', sendMessage);
  el.inp.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
  el.inp.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 80) + 'px';
  });

})();
