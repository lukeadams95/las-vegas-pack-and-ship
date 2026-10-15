/* Las Vegas Pack and Ship — shared behaviour.
 *
 * This replaces the Design Components runtime the prototypes ran on. Every
 * interaction below is a direct port of the .dc.html component logic:
 * condition blocks (<sc-if>) became .dc-if elements, {{ handler }} bindings
 * became data-dc-<event> attributes, and component state lives in `state`.
 */
(function () {
  'use strict';

  var state = {
    mobileNavOpen: false,
    testimonial: 0,
    slide: 0,
    lightboxSrc: null,
    submitted: false
  };

  /* ---------------------------------------------------------------- render */

  function conditions() {
    var c = {
      mobileNavOpen: state.mobileNavOpen,
      lightboxSrc: !!state.lightboxSrc,
      submitted: state.submitted,
      notSubmitted: !state.submitted
    };
    for (var i = 0; i < 10; i++) {
      c['isT' + i] = state.testimonial === i;
      c['isG' + i] = state.slide === i;
    }
    return c;
  }

  function render() {
    var c = conditions();
    document.querySelectorAll('.dc-if').forEach(function (el) {
      el.hidden = !c[el.getAttribute('data-cond')];
    });
    document.querySelectorAll('.dc-dot').forEach(function (dot) {
      var group = dot.getAttribute('data-dot-group');
      var index = parseInt(dot.getAttribute('data-dot-index'), 10);
      var active = group === 'g' ? state.slide : state.testimonial;
      dot.classList.toggle('is-active', index === active);
    });
    var img = document.getElementById('lightbox-img');
    if (img && state.lightboxSrc) img.src = state.lightboxSrc;
  }

  function setState(patch) {
    Object.assign(state, patch);
    render();
  }

  /* ------------------------------------------------------- slide carousels */

  function count(group) {
    var n = document.querySelectorAll('.dc-dot[data-dot-group="' + group + '"]').length;
    return n || 1;
  }

  var autoPaused = false;

  function stepTestimonial(delta) {
    var n = count('t');
    setState({ testimonial: (state.testimonial + delta + n) % n });
  }

  function stepSlide(delta) {
    var n = count('g');
    setState({ slide: (state.slide + delta + n) % n });
  }

  function startAutoplay() {
    if (document.querySelector('.dc-dot[data-dot-group="t"]')) {
      setInterval(function () {
        if (!autoPaused) stepTestimonial(1);
      }, 5000);
    }
    if (document.querySelector('.dc-dot[data-dot-group="g"]')) {
      setInterval(function () {
        if (!autoPaused) stepSlide(1);
      }, 4000);
    }
  }

  /* --------------------------------------------------- swipe / drag advance */

  var swipeX = null;
  var dragX = null;

  function advance(dx) {
    if (Math.abs(dx) < 30) return;
    stepTestimonial(dx < 0 ? 1 : -1);
  }

  /* ------------------------------------------------------- arrow galleries */
  /* Filmstrip sections (#<prefix>-track inside #<prefix>-wrap): slow
     auto-scroll that pauses on hover, plus prev/next arrow buttons. */

  var galleries = {};

  function initGalleries() {
    document.querySelectorAll('[id$="-track"]').forEach(function (track) {
      var prefix = track.id.replace(/-track$/, '');
      var wrap = document.getElementById(prefix + '-wrap');
      if (!wrap) return;
      var g = { track: track, hover: false, paused: false, resumeTimer: null };
      galleries[prefix] = g;
      wrap.addEventListener('mouseenter', function () { g.hover = true; });
      wrap.addEventListener('mouseleave', function () { g.hover = false; });
      setInterval(function () {
        if (g.hover || g.paused) return;
        if (track.scrollLeft + track.clientWidth >= track.scrollWidth - 1) track.scrollLeft = 0;
        else track.scrollLeft += 1;
      }, 30);
    });
  }

  function galleryStep(prefix, dir) {
    var g = galleries[prefix];
    if (!g) return;
    var track = g.track;
    clearTimeout(g.resumeTimer);
    g.paused = true;
    var card = track.firstElementChild;
    var width = card ? card.getBoundingClientRect().width + 24 : 400;
    var target = track.scrollLeft + dir * width;
    if (target >= track.scrollWidth - track.clientWidth - 4) target = 0;
    if (target < 0) target = track.scrollWidth - track.clientWidth;
    track.scrollTo({ left: target, behavior: 'smooth' });
    g.resumeTimer = setTimeout(function () { g.paused = false; }, 900);
  }

  /* -------------------------------------------------------- sticky top bar */

  function initStickyBar() {
    var bar = document.getElementById('sticky-bar');
    var hero = document.getElementById('home');
    if (!bar || !hero) return;
    var onScroll = function () {
      var barActive = getComputedStyle(bar).display !== 'none';
      var past = barActive && window.scrollY > hero.offsetTop + hero.offsetHeight - 120;
      bar.style.transform = past ? 'translateY(0)' : 'translateY(-100%)';
      var head = document.querySelector('header');
      if (head) {
        head.style.visibility = past ? 'hidden' : 'visible';
        head.style.position = past ? 'relative' : 'sticky';
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    onScroll();
  }

  /* ------------------------------------------------------------ image slots */
  /* Reproduces the <image-slot> geometry: a cover-fit baseline scaled by the
     stored zoom, offset by the stored pan (both expressed in frame percent). */

  function layoutSlot(img) {
    var frame = img.parentElement;
    var fw = frame.clientWidth;
    var fh = frame.clientHeight;
    var iw = img.naturalWidth;
    var ih = img.naturalHeight;
    if (!fw || !fh || !iw || !ih) return;
    var view = {
      s: parseFloat(img.getAttribute('data-view-s')) || 1,
      x: parseFloat(img.getAttribute('data-view-x')) || 0,
      y: parseFloat(img.getAttribute('data-view-y')) || 0
    };
    var k = Math.max(fw / iw, fh / ih) * view.s;
    img.style.width = (iw * k / fw * 100) + '%';
    img.style.height = (ih * k / fh * 100) + '%';
    img.style.left = (50 + view.x) + '%';
    img.style.top = (50 + view.y) + '%';
    img.style.objectFit = 'fill';
  }

  function layoutSlots() {
    document.querySelectorAll('.img-slot-img').forEach(layoutSlot);
  }

  function initSlots() {
    document.querySelectorAll('.img-slot-img').forEach(function (img) {
      if (img.complete) layoutSlot(img);
      else img.addEventListener('load', function () { layoutSlot(img); });
    });
    window.addEventListener('resize', layoutSlots);
  }

  /* --------------------------------------------------------------- leads */

  // Fire-and-forget POST. A failure is logged and never thrown, so the
  // success state is not blocked by the email or by a webhook on the form.
  function postLead(url, payload, label) {
    var body;
    try {
      body = JSON.stringify(payload);
    } catch (err) {
      console.error('[lead] ' + label + ' failed:', err);
      return;
    }
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body,
      keepalive: true
    }).then(function (res) {
      if (res.ok) return;
      return res.text().then(function (text) {
        console.error('[lead] ' + label + ' failed:', res.status, text);
      });
    }).catch(function (err) {
      console.error('[lead] ' + label + ' failed:', err);
    });
  }

  function inferFieldKey(el) {
    var parent = el.parentNode;
    var label = parent && parent.querySelector ? parent.querySelector('label') : null;
    var text = label ? label.textContent.replace(/\*/g, ' ').replace(/\s+/g, ' ').trim().toLowerCase() : '';
    if (text.indexOf('email') !== -1) return 'email';
    if (text.indexOf('phone') !== -1 || text.indexOf('mobile') !== -1) return 'phone';
    if (text.indexOf('message') !== -1 || text.indexOf('comment') !== -1) return 'message';
    if (text.indexOf('subject') !== -1) return 'subject';
    if (text.indexOf('ship') !== -1 || text.indexOf('item') !== -1) return 'item';
    if (text.indexOf('name') !== -1) return 'name';
    return text.replace(/[^a-z0-9]+/g, ' ').trim().replace(/\s+/g, '_');
  }

  function leadPayload(form) {
    var data = {};
    var fields = form.querySelectorAll('input, textarea, select');
    for (var i = 0; i < fields.length; i++) {
      var el = fields[i];
      var type = (el.type || '').toLowerCase();
      if (type === 'submit' || type === 'button' || type === 'reset' || type === 'file' || type === 'image') continue;
      if ((type === 'checkbox' || type === 'radio') && !el.checked) continue;
      var key = (el.getAttribute('name') || inferFieldKey(el) || '').trim();
      if (!key) continue;
      var value = (el.value || '').replace(/^\s+|\s+$/g, '');
      if (!value) continue;
      data[key.slice(0, 60)] = value.slice(0, 2000);
    }
    if (location && location.pathname) data.page = location.pathname;
    var title = (document.title || '').split('|')[0].replace(/^\s+|\s+$/g, '');
    if (title) data.form = title;
    return data;
  }

  function deliverLead(form) {
    var payload = leadPayload(form);
    // Started together and not awaited, so neither call blocks the other
    // or the success UI. Email failure is console-only.
    postLead('/send-lead-notification', payload, 'Email notification');
    var webhook = form.getAttribute('data-webhook');
    if (webhook) postLead(webhook, payload, 'Webhook');
  }

  /* ---------------------------------------------------------- event wiring */

  var handlers = {
    toggleNav: function () { setState({ mobileNavOpen: !state.mobileNavOpen }); },
    closeNav: function () { setState({ mobileNavOpen: false }); },

    prevSlide: function () { stepSlide(-1); },
    nextSlide: function () { stepSlide(1); },

    pauseAuto: function () { autoPaused = true; },
    resumeAuto: function () { autoPaused = false; },

    onSwipeStart: function (e) {
      swipeX = e.touches && e.touches[0] ? e.touches[0].clientX : null;
    },
    onSwipeEnd: function (e) {
      if (swipeX == null) return;
      var t = e.changedTouches && e.changedTouches[0];
      if (!t) return;
      var dx = t.clientX - swipeX;
      swipeX = null;
      advance(dx);
    },
    onDragStart: function (e) { dragX = e.clientX; },
    onDragEnd: function (e) {
      if (dragX == null) return;
      var dx = e.clientX - dragX;
      dragX = null;
      advance(dx);
    },

    openLightbox1: function () { setState({ lightboxSrc: 'assets/price-list-page1.webp' }); },
    openLightbox2: function () { setState({ lightboxSrc: 'assets/price-list-page2.webp' }); },
    closeLightbox: function (e) { if (e) e.stopPropagation(); setState({ lightboxSrc: null }); },

    onSubmit: function (e) {
      e.preventDefault();
      var form = e.target;
      try {
        if (form && String(form.tagName).toUpperCase() === 'FORM') deliverLead(form);
      } catch (err) {
        console.error('[lead] Email notification failed:', err);
      }
      setState({ submitted: true });
      var target = document.querySelector('.dc-if[data-cond="submitted"]');
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  function resolve(name) {
    if (handlers[name]) return handlers[name];
    var m = /^([A-Za-z0-9]+?)(Prev|Next)$/.exec(name);
    if (m) {
      var prefix = m[1];
      var dir = m[2] === 'Next' ? 1 : -1;
      return function () { galleryStep(prefix, dir); };
    }
    var dot = /^set([TG])(\d+)$/.exec(name);
    if (dot) {
      var index = parseInt(dot[2], 10);
      var key = dot[1] === 'T' ? 'testimonial' : 'slide';
      return function () {
        var patch = {};
        patch[key] = index;
        setState(patch);
      };
    }
    return null;
  }

  function bindEvents() {
    // Only walk nodes that actually carry a data-dc-* hook (was querySelectorAll('*')).
    var nodes = document.querySelectorAll(
      '[data-dc-click],[data-dc-mousedown],[data-dc-mouseup],[data-dc-mousemove],' +
      '[data-dc-mouseenter],[data-dc-mouseleave],[data-dc-touchstart],[data-dc-touchend],' +
      '[data-dc-submit],[data-dc-input],[data-dc-change],[data-dc-keydown]'
    );
    nodes.forEach(function (el) {
      Array.prototype.slice.call(el.attributes).forEach(function (attr) {
        if (attr.name.indexOf('data-dc-') !== 0) return;
        var event = attr.name.slice('data-dc-'.length);
        var fn = resolve(attr.value);
        if (fn) el.addEventListener(event, fn);
      });
    });
  }

  function init() {
    bindEvents();
    initStickyBar();
    initGalleries();
    initSlots();
    startAutoplay();
    render();
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && state.lightboxSrc) setState({ lightboxSrc: null });
    });
  }

  function scheduleInit() {
    var run = function () { init(); };
    if ('requestIdleCallback' in window) {
      requestIdleCallback(run, { timeout: 1200 });
    } else {
      setTimeout(run, 1);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', scheduleInit);
  } else {
    scheduleInit();
  }
})();
