/**
 * workspace_briefing.js — AI Briefing panel loader
 *
 * Fetches the briefing JSON endpoint and populates the panel.
 * Failures are silent: the panel hides itself instead of showing an error.
 * No chat, no streaming, no history.
 */
(function () {
  'use strict';

  var panel    = document.getElementById('briefing-panel');
  if (!panel) return;

  var url      = panel.dataset.url;
  var skeleton = document.getElementById('briefing-skeleton');
  var content  = document.getElementById('briefing-content');

  if (!url || !skeleton || !content) return;

  fetch(url, {
    method: 'GET',
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
    credentials: 'same-origin',
  })
    .then(function (resp) {
      if (!resp.ok) return Promise.reject('HTTP ' + resp.status);
      return resp.json();
    })
    .then(function (data) {
      var greeting        = document.getElementById('briefing-greeting');
      var summaryList     = document.getElementById('briefing-summary');
      var recommendation  = document.getElementById('briefing-recommendation');
      var meta            = document.getElementById('briefing-meta');

      if (!greeting || !summaryList || !recommendation) return;

      greeting.textContent = data.greeting || '';

      summaryList.replaceChildren();   // clears without touching innerHTML
      var lines = Array.isArray(data.summary) ? data.summary : [];
      lines.forEach(function (line) {
        var li = document.createElement('li');
        li.textContent = line;
        summaryList.appendChild(li);
      });

      recommendation.textContent = data.recommendation || '';

      if (meta) {
        var src = data.source === 'ai' ? 'IA' : 'análisis local';
        var cached = data.cached ? ' · desde caché' : '';
        meta.textContent = src + cached;
      }

      skeleton.style.display = 'none';
      content.style.display  = 'block';
    })
    .catch(function () {
      panel.style.display = 'none';
    });
})();
