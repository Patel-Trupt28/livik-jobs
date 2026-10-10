/**
 * LIVIK JOBS - UNIFIED CINEMA DARK MODE & THEME CONTROLLER
 * Zero-flicker bootstrap, cross-app localStorage & cookie synchronization,
 * input state alignment, and custom themeChanged events.
 */

(function () {
  'use strict';

  // 1. Resolve initial theme preference
  function getPreferredTheme() {
    try {
      var saved = localStorage.getItem('layout');
      if (saved === 'dark' || saved === 'light') return saved;
    } catch (e) {}

    // Fallback to cookie
    var m = document.cookie.match(/(?:^|;\s*)version=(dark|light)/);
    if (m && m[1]) return m[1];

    // Fallback to data-theme-pref on body if set by backend
    var pref = document.body ? document.body.getAttribute('data-theme-pref') : null;
    if (pref === 'dark' || pref === 'light') return pref;

    // Fallback to system OS preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }

    return 'light';
  }

  // 2. Apply theme to DOM
  function applyTheme(theme, animate) {
    var isDark = (theme === 'dark');
    var html = document.documentElement;
    var body = document.body;

    if (isDark) {
      html.classList.add('layout-dark');
      html.classList.add('dark-layout');
      html.setAttribute('data-theme', 'dark');
      if (body) {
        body.classList.add('layout-dark');
        body.classList.add('dark-layout');
        body.setAttribute('data-theme', 'dark');
      }
    } else {
      html.classList.remove('layout-dark');
      html.classList.remove('dark-layout');
      html.setAttribute('data-theme', 'light');
      if (body) {
        body.classList.remove('layout-dark');
        body.classList.remove('dark-layout');
        body.setAttribute('data-theme', 'light');
      }
    }

    // Persist to storage and cookie
    try {
      localStorage.setItem('layout', theme);
    } catch (e) {}
    document.cookie = 'version=' + theme + '; path=/; max-age=31536000; SameSite=Lax';

    // Synchronize all toggle elements in the DOM
    syncToggles(isDark);

    // Dispatch event
    window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: theme, isDark: isDark } }));
  }

  // 3. Synchronize all checkboxes and toggle buttons
  function syncToggles(isDark) {
    // Standard .layout-btn containers
    var layoutBtns = document.querySelectorAll('.layout-btn');
    layoutBtns.forEach(function (btn) {
      if (isDark) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
      var inp = btn.querySelector('input[type="checkbox"]');
      if (inp) {
        inp.checked = isDark;
      }
    });

    // Dashboard #layout-toggle
    var dashToggle = document.getElementById('layout-toggle');
    if (dashToggle) {
      dashToggle.checked = isDark;
    }

    // Floating dock theme button icon
    var dockIcon = document.getElementById('dockThemeIcon');
    if (dockIcon) {
      dockIcon.className = isDark ? 'fa fa-sun' : 'fa fa-moon';
    }
  }

  // 4. Toggle handler
  function toggleTheme() {
    var current = (document.documentElement.classList.contains('layout-dark') || 
                   (document.body && document.body.classList.contains('layout-dark'))) ? 'dark' : 'light';
    var next = (current === 'dark') ? 'light' : 'dark';
    applyTheme(next, true);
  }

  // 5. Initialize listeners once DOM is ready
  function initListeners() {
    var theme = getPreferredTheme();
    applyTheme(theme, false);

    // Bind layout-btn clicks (prevent double event bubbles from inside input)
    var layoutBtns = document.querySelectorAll('.layout-btn');
    layoutBtns.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        // If clicked on input itself, input will trigger change
        if (e.target.tagName.toLowerCase() === 'input') {
          return;
        }
        e.preventDefault();
        toggleTheme();
      });

      var inp = btn.querySelector('input[type="checkbox"]');
      if (inp) {
        inp.addEventListener('change', function () {
          applyTheme(this.checked ? 'dark' : 'light', true);
        });
      }
    });

    // Dashboard toggle
    var dashToggle = document.getElementById('layout-toggle');
    if (dashToggle) {
      dashToggle.addEventListener('change', function () {
        applyTheme(this.checked ? 'dark' : 'light', true);
      });
    }

    // Floating dock button
    var dockBtn = document.getElementById('dockThemeBtn');
    if (dockBtn) {
      dockBtn.addEventListener('click', function (e) {
        e.preventDefault();
        toggleTheme();
      });
    }
  }

  // Run immediately for instant early application
  var earlyTheme = getPreferredTheme();
  document.documentElement.classList.toggle('layout-dark', earlyTheme === 'dark');
  document.documentElement.classList.toggle('dark-layout', earlyTheme === 'dark');
  document.documentElement.setAttribute('data-theme', earlyTheme);

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initListeners);
  } else {
    initListeners();
  }

  // Expose global API
  window.CinemaTheme = {
    toggle: toggleTheme,
    set: applyTheme,
    get: getPreferredTheme
  };
})();

