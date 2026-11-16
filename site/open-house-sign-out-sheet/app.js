/* Talk Realty Open House Sign Out Sheet front end */
(function () {
  var cfg = window.SIGN_OUT_CONFIG || {};
  var execUrl = cfg.execUrl || '';
  var LS_NAME = 'talkrealty-oh-agent-name';
  var LS_PHONE = 'talkrealty-oh-agent-phone';
  var testMode = false;

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

  function isTestMode() {
    try {
      var q = new URLSearchParams(window.location.search);
      if (q.get('test') === '1' || String(q.get('mode') || '').toLowerCase() === 'test') return true;
      var path = String(window.location.pathname || '');
      return /\/open-house-sign-out-sheet\/test\/?$/.test(path);
    } catch (e) {
      return false;
    }
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

  function reveal(el) {
    if (!el) return;
    el.hidden = false;
    el.classList.remove('hidden');
  }

  function hide(el) {
    if (!el) return;
    el.hidden = true;
    el.classList.add('hidden');
  }

  function applyTestMode() {
    testMode = isTestMode();
    if (!testMode) return;
    document.body.classList.add('test-mode');
    reveal($('test-badge'));
    reveal($('test-reset-wrap'));
    reveal($('confirm-reset-wrap'));
    reveal($('all-out-reset-wrap'));
  }

  function renderSetsLeft(res) {
    var wrap = $('sign-sets-left');
    var countEl = $('sign-sets-left-count');
    var totalEl = $('sign-sets-left-total');
    var noneEl = $('sign-sets-none');
    var total = 5;
    var left = null;
    if (testMode) {
      left = 3;
      total = 5;
    } else {
      if (res && res.total != null && res.total !== '') total = Number(res.total);
      if (res && res.ok && res.left != null && res.left !== '') left = Number(res.left);
    }
    if (totalEl) totalEl.textContent = String(total);
    if (countEl) countEl.textContent = left === null || isNaN(left) ? '—' : String(left);
    if (wrap) {
      wrap.classList.toggle('is-zero', left === 0);
      reveal(wrap);
    }
    if (noneEl) {
      if (left === 0) reveal(noneEl);
      else hide(noneEl);
    }
    var allOutLeft = $('all-out-left');
    if (allOutLeft && total) {
      allOutLeft.textContent = 'Sign sets left: ' + (left === 0 ? '0' : (left === null || isNaN(left) ? '—' : String(left))) + ' of ' + total;
      allOutLeft.classList.toggle('is-zero', left === 0);
    }
  }

  function refreshSetsLeft() {
    if (testMode) {
      renderSetsLeft({ ok: true, left: 3, total: 5 });
      return;
    }
    api('available', {}, function (res) {
      renderSetsLeft(res);
    });
  }

  function showFormAgain() {
    var screen = $('confirm-screen');
    if (screen) {
      screen.classList.remove('lit', 'ready');
      hide(screen);
    }
    hide($('all-out'));
    var main = $('page-main');
    var header = $('page-header');
    if (main) main.classList.remove('hidden');
    if (header) header.classList.remove('hidden');
  }

  function resetTestColors(cb) {
    api('test-reset', { test: '1' }, function (res) {
      showFormAgain();
      var msg = $('form-msg');
      if (res && res.ok) {
        show(msg, 'ok', res.message || 'Test colors are free again. You can sign out once more.');
      } else {
        show(msg, 'error', 'Could not reset test colors. Please try again.');
      }
      if (res && res.ok && res.left != null) renderSetsLeft(res);
      refreshSetsLeft();
      if (cb) cb(res);
    });
  }

  function bindReset(id) {
    var el = $(id);
    if (!el) return;
    el.addEventListener('click', function (ev) {
      ev.preventDefault();
      resetTestColors();
    });
  }

  function api(action, data, cb) {
    data = data || {};
    data.action = action;
    if (testMode) data.test = '1';
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
    if (testMode) data.test = '1';
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
    var fallback = testMode
      ? 'All test sign colors are currently signed out. Reset test colors to free them and try again.'
      : 'All sign colors are currently signed out. Please call Christopher at Talk Realty.';
    if (p) p.textContent = message || fallback;
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
    var colorEl = $('confirm-color-name');
    var line = $('confirm-line');
    var screen = $('confirm-screen');
    if (!screen) return;
    screen.style.setProperty('--fill-color', hex);
    screen.style.setProperty('--fill-text', text);
    if (colorEl) {
      colorEl.textContent = name.toUpperCase();
    } else if (line) {
      line.textContent = 'Your open house signs are the ones under the ' + name.toUpperCase() + ' label.';
    }
    $('confirm-number').textContent = number;
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

  function maybeAutoReset() {
    try {
      var q = new URLSearchParams(window.location.search);
      if (!testMode || q.get('reset') !== '1') return;
      resetTestColors(function () {
        try {
          q.delete('reset');
          var qs = q.toString();
          var next = window.location.pathname + (qs ? '?' + qs : '');
          window.history.replaceState({}, '', next);
        } catch (e) {}
      });
    } catch (e) {}
  }


  function saveDataOrSlow() {
    try {
      var c = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
      if (!c) return false;
      if (c.saveData) return true;
      var t = String(c.effectiveType || '').toLowerCase();
      return t === 'slow-2g' || t === '2g';
    } catch (e) {
      return false;
    }
  }

  function initBgVideo() {
    var video = $('bg-video');
    var posterEl = $('bg-poster');
    var srcDesktop = (cfg && cfg.bgVideo) || '';
    var srcMobile = (cfg && cfg.bgVideoMobile) || '';
    var posterSrc = (cfg && cfg.bgPoster) || '';
    if (posterEl && posterSrc) posterEl.setAttribute('src', posterSrc);
    if (video && posterSrc) video.setAttribute('poster', posterSrc);
    if (!video || !srcDesktop) return;
    if (prefersReducedMotion() || saveDataOrSlow()) return;
    var useMobile = false;
    try { useMobile = window.innerWidth < 768; } catch (e) {}
    var src = (useMobile && srcMobile) ? srcMobile : srcDesktop;
    var start = function () {
      if (!video.getAttribute('src')) {
        video.muted = true;
        video.defaultMuted = true;
        video.loop = true;
        video.autoplay = true;
        video.playsInline = true;
        video.setAttribute('muted', '');
        video.setAttribute('autoplay', '');
        video.setAttribute('loop', '');
        video.setAttribute('playsinline', '');
        video.setAttribute('src', src);
        video.load();
      }
      var play = video.play();
      if (play && play.then) {
        play.then(function () { video.classList.add('is-on'); }).catch(function () {});
      } else {
        video.classList.add('is-on');
      }
    };
    if ('requestIdleCallback' in window) {
      window.requestIdleCallback(start, { timeout: 1200 });
    } else {
      window.setTimeout(start, 200);
    }
  }

  function initSignOut() {
    var form = $('sign-out-form');
    if (!form) return;
    applyTestMode();
    initBgVideo();
    restoreAgent();
    bindReset('test-reset-link');
    bindReset('confirm-reset-link');
    bindReset('all-out-reset-link');
    refreshSetsLeft();
    maybeAutoReset();
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
          if (res.left != null) renderSetsLeft(res);
          showAllOut(res.message);
          refreshSetsLeft();
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
        if (res.left != null) renderSetsLeft(res);
        showAssigned(res);
        refreshSetsLeft();
      });
    });
  }

  window.SignOutSheet = {
    initSignOut: initSignOut,
    formatPhone: formatPhone,
    tenDigits: tenDigits
  };
})();
