/* Talk Realty Open House Sign Out Sheet front end */
(function () {
  var cfg = window.SIGN_OUT_CONFIG || {};
  var execUrl = cfg.execUrl || '';

  function $(id) { return document.getElementById(id); }

  function show(el, className, text) {
    if (!el) return;
    el.className = 'msg ' + (className || '');
    el.textContent = text;
    el.classList.remove('hidden');
  }

  function api(action, data, cb) {
    data = data || {};
    data.action = action;
    if (cfg.useGas && typeof google !== 'undefined' && google.script && google.script.run) {
      var fn = { submit: 'submit_', return: 'markReturnedGas_', plan: 'planReturnGas_', get: 'getRecord_' }[action];
      if (!fn) { cb({ ok: false, error: 'unknown_action' }); return; }
      var arg = action === 'return' ? (data.r || data.token)
        : action === 'plan' ? [data.r || data.token, data.planned || data.date]
        : action === 'get' ? (data.r || data.token)
        : data;
      var runner = google.script.run.withSuccessHandler(cb).withFailureHandler(function () { cb({ ok: false, error: 'network' }); });
      if (action === 'plan') runner[fn](arg[0], arg[1]);
      else runner[fn](arg);
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

  function loadNumbers(cb) {
    if (cfg.useGas && typeof google !== 'undefined' && google.script && google.script.run) {
      google.script.run.withSuccessHandler(function (numbers) { cb({ ok: true, numbers: numbers || [] }); })
        .withFailureHandler(function () { cb({ ok: true, numbers: [] }); })
        .readSignNumbers_();
      return;
    }
    if (cfg.mock) {
      fetch((cfg.execUrl || '/mock-exec') + '?action=numbers')
        .then(function (r) { return r.json(); })
        .then(cb)
        .catch(function () { cb({ ok: true, numbers: [] }); });
      return;
    }
    if (!execUrl) { cb({ ok: true, numbers: [] }); return; }
    jsonp('numbers', {}, cb);
  }

  function setupSignField(numbers) {
    var select = $('sign-select');
    var typed = $('sign-typed');
    if (!select || !typed) return;
    if (numbers && numbers.length) {
      select.innerHTML = '<option value="">Select a sign phone number</option>';
      numbers.forEach(function (n) {
        var o = document.createElement('option');
        o.value = n;
        o.textContent = n;
        select.appendChild(o);
      });
      select.classList.remove('hidden');
      select.required = true;
      typed.classList.add('hidden');
      typed.required = false;
      typed.value = '';
    } else {
      select.classList.add('hidden');
      select.required = false;
      typed.classList.remove('hidden');
      typed.required = true;
    }
  }

  function todayISO() {
    var d = new Date();
    var tz = 'Pacific/Honolulu';
    try {
      var parts = new Intl.DateTimeFormat('en-CA', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(d);
      var y = parts.filter(function (p) { return p.type === 'year'; })[0].value;
      var m = parts.filter(function (p) { return p.type === 'month'; })[0].value;
      var day = parts.filter(function (p) { return p.type === 'day'; })[0].value;
      return y + '-' + m + '-' + day;
    } catch (e) {
      return d.toISOString().slice(0, 10);
    }
  }

  function initSignOut() {
    var form = $('sign-out-form');
    if (!form) return;
    var date = $('oh-date');
    if (date && !date.value) date.value = todayISO();
    var end = $('oh-end');
    if (end && !end.value) end.value = '17:00';
    loadNumbers(function (res) {
      setupSignField((res && res.numbers) || []);
    });
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var btn = $('submit-btn');
      var msg = $('form-msg');
      var select = $('sign-select');
      var typed = $('sign-typed');
      var sign = (select && !select.classList.contains('hidden')) ? select.value : (typed ? typed.value : '');
      var payload = {
        sign_number: (sign || '').trim(),
        num_signs: $('num-signs').value,
        agent_name: $('agent-name').value.trim(),
        agent_phone: $('agent-phone').value.trim(),
        address: $('address').value.trim(),
        oh_date: $('oh-date').value,
        oh_end: $('oh-end').value || '17:00'
      };
      btn.disabled = true;
      api('submit', payload, function (res) {
        btn.disabled = false;
        if (!res || !res.ok) {
          if (res && res.error === 'not_configured') {
            show(msg, 'error', 'This preview is not connected to the live sheet yet.');
          } else if (res && res.error === 'sign_number_not_on_list') {
            show(msg, 'error', 'Please choose a sign phone number from the list.');
          } else {
            show(msg, 'error', 'Please check the required fields and try again.');
          }
          return;
        }
        form.classList.add('hidden');
        var done = $('done');
        done.classList.remove('hidden');
        var link = returnLink(res.token);
        var a = $('return-link');
        a.href = link;
        a.textContent = link;
      });
    });
  }

  function returnLink(token) {
    var base = cfg.publicBase || (window.location.origin + window.location.pathname.replace(/index\.html$/, '').replace(/\/$/, ''));
    return base + '/return.html?r=' + encodeURIComponent(token);
  }

  function tokenFromUrl() {
    var q = new URLSearchParams(window.location.search);
    return q.get('r') || q.get('token') || '';
  }

  function initReturn() {
    var box = $('return-page');
    if (!box) return;
    var token = tokenFromUrl();
    var msg = $('return-msg');
    if (!token) {
      show(msg, 'error', 'This return link is missing. Please use the link from your text.');
      $('return-actions').classList.add('hidden');
      return;
    }
    var load = function (res) {
      if (!res || !res.ok) {
        show(msg, 'error', 'We could not find this sign out. Please use the link from your text, or ask the office for help.');
        $('return-actions').classList.add('hidden');
        return;
      }
      var row = res.row || {};
      $('summary').classList.remove('hidden');
      $('summary-text').textContent = (row.agent_name || '') + ' · ' + (row.sign_number || '') + ' · ' + (row.address || '');
      if (row.returned === 'Y') {
        $('return-actions').classList.add('hidden');
        show(msg, 'ok', 'These signs are already marked as returned. Mahalo.');
      }
    };
    if (cfg.useGas && typeof google !== 'undefined' && google.script && google.script.run) {
      google.script.run.withSuccessHandler(load).withFailureHandler(function () {
        show(msg, 'error', 'We could not load this sign out.');
      }).getRecord_(token);
    } else if (cfg.mock) {
      fetch((cfg.execUrl || '/mock-exec') + '?action=get&r=' + encodeURIComponent(token))
        .then(function (r) { return r.json(); }).then(load)
        .catch(function () { show(msg, 'error', 'We could not load this sign out.'); });
    } else if (execUrl) {
      jsonp('get', { r: token }, load);
    } else {
      show(msg, 'error', 'This preview is not connected to the live sheet yet.');
    }

    $('btn-returned').addEventListener('click', function () {
      api('return', { r: token }, function (res) {
        if (!res || !res.ok) {
          show(msg, 'error', 'We could not save that. Please try again.');
          return;
        }
        $('return-actions').classList.add('hidden');
        show(msg, 'ok', 'Mahalo. The signs are marked as returned.');
      });
    });
    $('plan-form').addEventListener('submit', function (ev) {
      ev.preventDefault();
      var date = $('plan-date').value;
      if (!date) {
        show(msg, 'error', 'Please pick the date you plan to return the signs.');
        return;
      }
      api('plan', { r: token, planned: date }, function (res) {
        if (!res || !res.ok) {
          show(msg, 'error', 'We could not save that date. Please try again.');
          return;
        }
        show(msg, 'ok', 'Got it. We will check back after ' + date + '.');
      });
    });
  }

  window.SignOutSheet = { initSignOut: initSignOut, initReturn: initReturn, loadNumbers: loadNumbers };
})();
