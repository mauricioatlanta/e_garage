(function () {
  "use strict";

  var TRACKED_PATH = "/cl/desarmadurias/";
  var ENDPOINT = "/analytics/public/event/";
  var sent = Object.create(null);
  var scrollFramePending = false;

  if (window.location.pathname !== TRACKED_PATH) {
    return;
  }

  function getCookie(name) {
    var prefix = name + "=";
    var parts = document.cookie ? document.cookie.split(";") : [];
    for (var i = 0; i < parts.length; i += 1) {
      var value = parts[i].trim();
      if (value.indexOf(prefix) === 0) {
        return decodeURIComponent(value.slice(prefix.length));
      }
    }
    return "";
  }

  function postEvent(eventType, dedupeKey, metadata) {
    if (sent[dedupeKey]) {
      return;
    }

    var csrfToken = getCookie("csrftoken");
    if (!csrfToken || typeof window.fetch !== "function") {
      return;
    }

    sent[dedupeKey] = true;
    window.fetch(ENDPOINT, {
      method: "POST",
      credentials: "same-origin",
      keepalive: true,
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken
      },
      body: JSON.stringify({
        event_type: eventType,
        path: TRACKED_PATH,
        dedupe_key: dedupeKey,
        metadata: metadata || {}
      })
    }).catch(function () {});
  }

  function scrollPercent() {
    var doc = document.documentElement;
    var body = document.body;
    var scrollTop = window.pageYOffset || doc.scrollTop || body.scrollTop || 0;
    var scrollHeight = Math.max(
      body.scrollHeight,
      body.offsetHeight,
      doc.clientHeight,
      doc.scrollHeight,
      doc.offsetHeight
    );
    var viewportHeight = window.innerHeight || doc.clientHeight || 0;
    if (scrollHeight <= viewportHeight) {
      return null;
    }
    var scrollable = scrollHeight - viewportHeight;
    return {
      percent: Math.min(100, Math.round((scrollTop / scrollable) * 100)),
      viewportHeight: viewportHeight,
      documentHeight: scrollHeight
    };
  }

  function checkScroll() {
    var state = scrollPercent();
    if (!state) {
      return;
    }
    if (state.percent >= 50) {
      postEvent("scroll_50", TRACKED_PATH + ":scroll_50", {
        scroll_percent: 50,
        viewport_height: state.viewportHeight,
        document_height: state.documentHeight
      });
    }
    if (state.percent >= 90) {
      postEvent("scroll_90", TRACKED_PATH + ":scroll_90", {
        scroll_percent: 90,
        viewport_height: state.viewportHeight,
        document_height: state.documentHeight
      });
    }
  }

  function scheduleScrollCheck() {
    if (scrollFramePending) {
      return;
    }
    scrollFramePending = true;
    var raf = window.requestAnimationFrame || function (callback) {
      return window.setTimeout(callback, 16);
    };
    raf(function () {
      scrollFramePending = false;
      checkScroll();
    });
  }

  function handleTrialClick(event) {
    var link = event.target.closest("[data-public-funnel-trial-cta]");
    if (!link) {
      return;
    }
    var ctaId = link.getAttribute("data-public-funnel-trial-cta") || "trial";
    postEvent("cta_trial_30_click", TRACKED_PATH + ":" + ctaId, {
      cta_id: ctaId,
      cta_label: (link.textContent || "").trim().slice(0, 120),
      href: link.getAttribute("href") || ""
    });
  }

  window.addEventListener("scroll", scheduleScrollCheck, { passive: true });
  window.addEventListener("resize", scheduleScrollCheck);
  document.addEventListener("click", handleTrialClick);
  document.addEventListener("DOMContentLoaded", function () {
    scheduleScrollCheck();
  });
})();
