/* ============================================================
   Smart Campus — Main JavaScript
   ============================================================ */

(function () {
  'use strict';

  /* ---------- Dark Mode Toggle ---------- */
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('sc-theme', theme);

    var toggleBtn = document.getElementById('themeToggle');
    if (toggleBtn) {
      toggleBtn.textContent = theme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode';
    }
  }

  function toggleTheme() {
    var current = document.documentElement.getAttribute('data-theme') || 'light';
    applyTheme(current === 'dark' ? 'light' : 'dark');
  }

  // Apply saved theme on page load
  var savedTheme = localStorage.getItem('sc-theme') || 'light';
  applyTheme(savedTheme);

  // Expose toggle globally
  window.toggleTheme = toggleTheme;

  /* ---------- Modal Open / Close ---------- */
  function openModal(id) {
    var modal = document.getElementById(id);
    if (modal) {
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  }

  function closeModal(id) {
    var modal = document.getElementById(id);
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  }

  // Close modal on overlay click
  document.addEventListener('click', function (e) {
    if (e.target.classList.contains('modal-overlay')) {
      e.target.classList.remove('active');
      document.body.style.overflow = '';
    }
  });

  // Expose globally
  window.openModal = openModal;
  window.closeModal = closeModal;

  /* ---------- Auto-Dismiss Flash Messages ---------- */
  document.addEventListener('DOMContentLoaded', function () {
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
      setTimeout(function () {
        alert.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-8px)';
        setTimeout(function () {
          alert.remove();
        }, 300);
      }, 4000);
    });

    /* ---------- Progress Bar Color Assignment ---------- */
    var bars = document.querySelectorAll('.progress-bar[data-percentage]');
    bars.forEach(function (bar) {
      var pct = parseFloat(bar.getAttribute('data-percentage')) || 0;
      bar.style.width = pct + '%';
      if (pct < 75) {
        bar.classList.add('red');
      } else if (pct <= 85) {
        bar.classList.add('yellow');
      } else {
        bar.classList.add('green');
      }
    });

    /* ---------- Mobile Sidebar Toggle ---------- */
    var sidebarToggle = document.getElementById('sidebarToggle');
    var sidebar = document.querySelector('.sidebar');
    if (sidebarToggle && sidebar) {
      sidebarToggle.addEventListener('click', function () {
        sidebar.classList.toggle('open');
      });

      // Close sidebar when clicking outside on mobile
      document.addEventListener('click', function (e) {
        if (window.innerWidth <= 768 &&
            sidebar.classList.contains('open') &&
            !sidebar.contains(e.target) &&
            e.target !== sidebarToggle) {
          sidebar.classList.remove('open');
        }
      });
    }
  });
})();
