/* Talk Realty Open House Sign Out Sheet front end */
(function () {
  var cfg = window.SIGN_OUT_CONFIG || {};
  var execUrl = cfg.execUrl || '';
  var LS_NAME = 'talkrealty-oh-agent-name';
  var LS_PHONE = 'talkrealty-oh-agent-phone';

  function $(id) { return document.getElementById(id); }

  function show(el, className, text) {
    if (!el) return;
    el.className = 'msg ' + (className || '');
    el.textContent = text;
    el.classList.remove('hidden');
  }

  function digits(s) {
    return String(s || '').replace(/\D/g, '');
  }

  function tenDigits(s) {
    var d = digits(s);
    if (d.length === 11 && d.charAt(0) === '1') d = d.slice(1);
    return d.length === 10 ? d : '';
  }

  function formatPhone(s) {
    var d = tenDigits(s);
    if (!d) return '';
    return '(' + d.slice(0, 3) + ') ' + d.slice(3, 6) + '-' + d.slice(6);
  }

  function todayISO() {
    var d = new Date();
    try {
      var parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'Pacific/Honolulu', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(d);
      var y = parts.filter(function (p) { return p.type === 'year'; })[0].value;
      var m = parts.filter(function (p) { return p.type === 'month'; })[0].value;
      var day = parts.filter(function (p) { return p.type === 'day'; })[0].value;
      return y + '-' + m + '-' + day;
    } catch (e) {
      return d.toISOString().slice(0, 10);
    }
  }

  function prefersReducedMotion() {
    try {
      return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch (e) {
      return false;
    }
  }

  function contrastText(hex) {
    var h = String(hex || '').replace('#', '');
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    if (h.length !== 6) return '#FFFFFF';
    var r = parseInt(h.slice(0, 2), 16) / 255;
    var g = parseInt(h.slice(2, 4), 16) / 255;
    var b = parseInt(h.slice(4, 6), 16) / 255;
    var lin = function (c) { return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
    var L = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
    return L > 0.45 ? '#1A1A1A' : '#FFFFFF';
  }

  function rememberAgent() {
    try {
      var n = $('agent-name');
      var p = $('agent-phone');
      if (n && n.value.trim()) localStorage.setItem(LS_NAME, n.value.trim());
      if (p && p.value.trim()) localStorage.setItem(LS_PHONE, p.value.trim());
    } catch (e) {}
  }

  function restoreAgent() {
    try {
      var n = $('agent-name');
      var p = $('agent-phone');
      if (n && !n.value) n.value = localStorage.getItem(LS_NAME) || '';
      if (p && !p.value) p.value = localStorage.getItem(LS_PHONE) || '';
    } catch (e) {}
  }

  function api(action, data, cb) {
    data = data || {};
    data.action = action;
    if (cfg.useGas && typeof google !== 'undefined' && google.script && google.script.run) {
      google.script.run.withSuccessHandler(cb).withFailureHandler(function () { cb({ ok: false, error: 'network' }); }).submit_(data);
      return;
    }
    if (cfg.mock) {
      fetch((cfg.execUrl || '/mock-exec') + '?action=' + encodeURIComponent(action), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }).then(function (r) { return r.json(); }).then(cb).catch(function (err) {
        cb({ ok: false, error: 'network', detail: String(err) });
      });
      return;
    }
    if (!execUrl) {
      cb({ ok: false, error: 'not_configured' });
      return;
    }
    fetch(execUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify(data),
      redirect: 'follow'
    }).then(function (r) { return r.text(); }).then(function (text) {
      try { cb(JSON.parse(text)); }
      catch (e) { jsonp(action, data, cb); }
    }).catch(function () { jsonp(action, data, cb); });
  }

  function jsonp(action, data, cb) {
    var name = 'so_' + Math.random().toString(36).slice(2);
    window[name] = function (res) {
      delete window[name];
      if (script.parentNode) script.parentNode.removeChild(script);
      cb(res);
    };
    var params = [];
    data = data || {};
    data.action = action;
    data.callback = name;
    Object.keys(data).forEach(function (k) {
      if (data[k] === undefined || data[k] === null) return;
      params.push(encodeURIComponent(k) + '=' + encodeURIComponent(data[k]));
    });
    var script = document.createElement('script');
    script.src = execUrl + (execUrl.indexOf('?') >= 0 ? '&' : '?') + params.join('&');
    script.onerror = function () {
      delete window[name];
      cb({ ok: false, error: 'network' });
    };
    document.head.appendChild(script);
  }

  function showAllOut(message) {
    var box = $('all-out');
    var p = $('all-out-msg');
    if (p) p.textContent = message || 'All sign colors are currently signed out. Please call Christopher at Talk Realty.';
    if (box) {
      box.hidden = false;
      box.classList.remove('hidden');
    }
    var main = $('page-main');
    var header = $('page-header');
    if (main) main.classList.add('hidden');
    if (header) header.classList.add('hidden');
  }

  function showAssigned(res) {
    var color = res.color || {};
    var hex = color.hex || '#1B365D';
    var text = color.text || contrastText(hex);
    var name = String(color.name || res.color_name || '').trim() || 'assigned';
    var number = res.sign_display || formatPhone(res.sign_number) || res.sign_number || '';
    var msg = res.message || ('Go to the ' + name.toUpperCase() + ' section of the wall for your signs.');
    var screen = $('confirm-screen');
    if (!screen) return;
    screen.style.setProperty('--fill-color', hex);
    screen.style.setProperty('--fill-text', text);
    $('confirm-color').textContent = name;
    $('confirm-number').textContent = number;
    $('confirm-msg').textContent = msg;
    screen.hidden = false;
    screen.classList.remove('hidden');
    var start = function () { screen.classList.add('lit'); };
    if (prefersReducedMotion()) {
      start();
      screen.classList.add('ready');
      return;
    }
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(start);
    });
    window.setTimeout(function () { screen.classList.add('ready'); }, 1900);
  }

  function initSignOut() {
    var form = $('sign-out-form');
    if (!form) return;
    restoreAgent();
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var btn = $('submit-btn');
      var msg = $('form-msg');
      var payload = {
        agent_name: $('agent-name').value.trim(),
        agent_phone: $('agent-phone').value.trim(),
        address: $('address').value.trim(),
        oh_date: todayISO(),
        oh_end: '17:00',
        num_signs: '1'
      };
      if (!payload.agent_name || digits(payload.agent_phone).length < 10 || !payload.address) {
        show(msg, 'error', 'Please check the required fields and try again.');
        return;
      }
      btn.disabled = true;
      api('submit', payload, function (res) {
        btn.disabled = false;
        if (res && res.error === 'all_out') {
          rememberAgent();
          showAllOut(res.message);
          return;
        }
        if (!res || !res.ok) {
          if (res && res.error === 'not_configured') {
            show(msg, 'error', 'This preview is not connected to the live sheet yet.');
          } else if (res && res.error === 'busy') {
            show(msg, 'error', 'Please try again in a moment.');
          } else {
            show(msg, 'error', 'Please check the required fields and try again.');
          }
          return;
        }
        rememberAgent();
        showAssigned(res);
      });
    });
  }

  window.SignOutSheet = {
    initSignOut: initSignOut,
    formatPhone: formatPhone,
    tenDigits: tenDigits
  };
})();
