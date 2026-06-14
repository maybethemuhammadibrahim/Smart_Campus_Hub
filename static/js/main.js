/* ============================================================
   Nexora Campus Portal — Main JavaScript
   ============================================================ */

(function () {
  'use strict';

  /* ---------- Dark Mode Toggle ---------- */
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('sc-theme', theme);

    var toggleBtn = document.getElementById('themeToggle');
    if (toggleBtn) {
      toggleBtn.innerHTML = theme === 'dark'
        ? '<i data-lucide="sun" style="width:14px;height:14px;"></i> Light Mode'
        : '<i data-lucide="moon" style="width:14px;height:14px;"></i> Dark Mode';
      if (typeof lucide !== 'undefined') lucide.createIcons();
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
        alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateX(-20px)';
        setTimeout(function () {
          alert.remove();
        }, 400);
      }, 5000);
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

      document.addEventListener('click', function (e) {
        if (window.innerWidth <= 768 &&
            sidebar.classList.contains('open') &&
            !sidebar.contains(e.target) &&
            e.target !== sidebarToggle) {
          sidebar.classList.remove('open');
        }
      });
    }

    /* ---------- Course + Section Cascading Selectors ---------- */
    var coursePickers = document.querySelectorAll('.course-picker');
    coursePickers.forEach(function (picker) {
      var courseSel = picker.querySelector('.course-code-select');
      var sectionSel = picker.querySelector('.section-select');
      if (!courseSel || !sectionSel) return;

      var allCourses = JSON.parse(picker.getAttribute('data-courses') || '[]');
      var baseUrl = picker.getAttribute('data-base-url') || '';
      var selectedId = parseInt(picker.getAttribute('data-selected')) || 0;

      // Get unique course codes
      var uniqueCodes = [];
      var codeNames = {};
      allCourses.forEach(function (c) {
        if (uniqueCodes.indexOf(c.code) === -1) {
          uniqueCodes.push(c.code);
          codeNames[c.code] = c.name;
        }
      });

      // Find the currently selected course code
      var selectedCode = '';
      allCourses.forEach(function (c) {
        if (c.id === selectedId) selectedCode = c.code;
      });
      if (!selectedCode && uniqueCodes.length > 0) selectedCode = uniqueCodes[0];

      // Populate course dropdown
      courseSel.innerHTML = '';
      uniqueCodes.forEach(function (code) {
        var opt = document.createElement('option');
        opt.value = code;
        opt.textContent = code + ' \u2014 ' + codeNames[code];
        if (code === selectedCode) opt.selected = true;
        courseSel.appendChild(opt);
      });

      // Populate sections for selected course
      function populateSections(code, doNavigate) {
        sectionSel.innerHTML = '';
        var sections = allCourses.filter(function (c) { return c.code === code; });
        sections.forEach(function (s) {
          var opt = document.createElement('option');
          opt.value = s.id;
          opt.textContent = 'Section ' + s.section;
          if (s.id === selectedId) opt.selected = true;
          sectionSel.appendChild(opt);
        });
        // Never truly disable — disabled selects don't submit values.
        // Use a CSS class for the muted look instead.
        if (sections.length <= 1) {
          sectionSel.classList.add('select-locked');
        } else {
          sectionSel.classList.remove('select-locked');
        }

        // Auto-navigate when course changes (not on init)
        if (doNavigate && baseUrl && sections.length > 0) {
          window.location.href = baseUrl + '/' + sections[0].id;
        }
      }

      // Initialize sections (no navigation)
      populateSections(selectedCode, false);

      // Course change → repopulate sections and navigate
      courseSel.addEventListener('change', function () {
        populateSections(this.value, true);
      });

      // Section change → navigate
      sectionSel.addEventListener('change', function () {
        if (this.value && baseUrl) {
          window.location.href = baseUrl + '/' + this.value;
        }
      });
    });

    /* ---------- Legacy single course selector (fallback) ---------- */
    var courseSelectors = document.querySelectorAll('.course-selector');
    courseSelectors.forEach(function (sel) {
      sel.addEventListener('change', function () {
        var baseUrl = this.getAttribute('data-base-url');
        var courseId = this.value;
        if (courseId && baseUrl) {
          window.location.href = baseUrl + '/' + courseId;
        }
      });
    });

    /* ---------- Attendance: Custom Radio Styling ---------- */
    initAttendanceRadios();

    /* ---------- Attendance: Bulk Actions ---------- */
    initBulkActions();

    /* ---------- Attendance: Live Counter ---------- */
    updateAttendanceCounter();

    /* ---------- Live Grade Calculator ---------- */
    initGradeCalculator();

    /* ---------- Unsaved Changes Detection ---------- */
    initUnsavedDetection();

    /* ---------- Roster Search/Filter ---------- */
    initTableSearch();

    /* ---------- Animated Number Counters ---------- */
    initNumberCounters();

    /* ---------- Chart Bar Animation ---------- */
    initChartBars();

    /* ---------- Confirmation Dialogs ---------- */
    initConfirmDialogs();
  });

  /* ============================================================
     ATTENDANCE FUNCTIONS
     ============================================================ */

  function initAttendanceRadios() {
    var radios = document.querySelectorAll('.radio-group input[type="radio"]');
    radios.forEach(function (radio) {
      radio.addEventListener('change', function () {
        // Clear sibling labels
        var group = this.closest('.radio-group');
        if (!group) return;
        group.querySelectorAll('label').forEach(function (lbl) {
          lbl.classList.remove('present-checked', 'absent-checked', 'late-checked');
        });
        // Color the selected label
        var label = this.closest('label');
        if (label) {
          label.classList.add(this.value + '-checked');
        }
        updateAttendanceCounter();
      });

      // Apply initial state
      if (radio.checked) {
        var label = radio.closest('label');
        if (label) label.classList.add(radio.value + '-checked');
      }
    });
  }

  function initBulkActions() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-mark-all]');
      if (!btn) return;
      var status = btn.getAttribute('data-mark-all');
      var radios = document.querySelectorAll('.radio-group input[type="radio"][value="' + status + '"]');
      radios.forEach(function (radio) {
        radio.checked = true;
        radio.dispatchEvent(new Event('change', { bubbles: true }));
      });
    });
  }

  function updateAttendanceCounter() {
    var presentEl = document.getElementById('count-present');
    var absentEl  = document.getElementById('count-absent');
    var lateEl    = document.getElementById('count-late');
    if (!presentEl) return;

    var present = document.querySelectorAll('.radio-group input[value="present"]:checked').length;
    var absent  = document.querySelectorAll('.radio-group input[value="absent"]:checked').length;
    var late    = document.querySelectorAll('.radio-group input[value="late"]:checked').length;

    presentEl.textContent = present;
    absentEl.textContent  = absent;
    lateEl.textContent    = late;
  }

  /* ============================================================
     GRADE CALCULATOR
     ============================================================ */

  function getLetterGrade(marks) {
    if (marks >= 90) return { letter: 'A',  cls: 'grade-a' };
    if (marks >= 85) return { letter: 'A-', cls: 'grade-a' };
    if (marks >= 80) return { letter: 'B+', cls: 'grade-b' };
    if (marks >= 75) return { letter: 'B',  cls: 'grade-b' };
    if (marks >= 70) return { letter: 'B-', cls: 'grade-b' };
    if (marks >= 65) return { letter: 'C+', cls: 'grade-c' };
    if (marks >= 60) return { letter: 'C',  cls: 'grade-c' };
    return { letter: 'F', cls: 'grade-f' };
  }

  function initGradeCalculator() {
    var marksInputs = document.querySelectorAll('input[name^="marks_"]');
    marksInputs.forEach(function (input) {
      var previewEl = input.closest('tr');
      if (!previewEl) return;
      var preview = previewEl.querySelector('.grade-preview');
      if (!preview) return;

      input.addEventListener('input', function () {
        var val = parseFloat(this.value);
        if (isNaN(val) || val < 0 || val > 100) {
          preview.textContent = '—';
          preview.className = 'grade-preview';
          return;
        }
        var g = getLetterGrade(val);
        preview.textContent = g.letter;
        preview.className = 'grade-preview ' + g.cls;
      });

      // Initialize on load
      if (input.value) {
        var val = parseFloat(input.value);
        if (!isNaN(val) && val >= 0 && val <= 100) {
          var g = getLetterGrade(val);
          preview.textContent = g.letter;
          preview.className = 'grade-preview ' + g.cls;
        }
      }
    });
  }

  /* ============================================================
     UNSAVED CHANGES
     ============================================================ */

  function initUnsavedDetection() {
    var gradeForm = document.getElementById('gradeForm');
    if (!gradeForm) return;

    var unsavedDot = document.getElementById('unsavedDot');
    var originalValues = {};

    var marksInputs = gradeForm.querySelectorAll('input[name^="marks_"]');
    marksInputs.forEach(function (input) {
      originalValues[input.name] = input.value;
      input.addEventListener('input', function () {
        checkUnsaved();
      });
    });

    function checkUnsaved() {
      var hasChanges = false;
      marksInputs.forEach(function (input) {
        if (input.value !== originalValues[input.name]) {
          hasChanges = true;
        }
      });
      if (unsavedDot) {
        unsavedDot.classList.toggle('visible', hasChanges);
      }
    }
  }

  /* ============================================================
     TABLE SEARCH / FILTER
     ============================================================ */

  function initTableSearch() {
    var searchInput = document.getElementById('rosterSearch');
    if (!searchInput) return;

    searchInput.addEventListener('input', function () {
      var query = this.value.toLowerCase();
      var rows = document.querySelectorAll('#rosterTable tbody tr');
      rows.forEach(function (row) {
        var text = row.textContent.toLowerCase();
        row.style.display = text.indexOf(query) > -1 ? '' : 'none';
      });
    });
  }

  /* ============================================================
     ANIMATED NUMBER COUNTERS
     ============================================================ */

  function initNumberCounters() {
    var counters = document.querySelectorAll('[data-count]');
    counters.forEach(function (el) {
      var target = parseFloat(el.getAttribute('data-count')) || 0;
      var isFloat = target % 1 !== 0;
      var duration = 800;
      var start = 0;
      var startTime = null;

      function animate(timestamp) {
        if (!startTime) startTime = timestamp;
        var progress = Math.min((timestamp - startTime) / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        var current = start + (target - start) * eased;
        el.textContent = isFloat ? current.toFixed(1) : Math.round(current);
        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      }

      // Use IntersectionObserver for scroll-triggered animation
      if ('IntersectionObserver' in window) {
        var observer = new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              requestAnimationFrame(animate);
              observer.unobserve(el);
            }
          });
        }, { threshold: 0.5 });
        observer.observe(el);
      } else {
        requestAnimationFrame(animate);
      }
    });
  }

  /* ============================================================
     CHART BAR ANIMATION
     ============================================================ */

  function initChartBars() {
    var chartBars = document.querySelectorAll('.chart-bar-fill[data-width]');
    chartBars.forEach(function (bar) {
      var width = bar.getAttribute('data-width');
      setTimeout(function () {
        bar.style.width = width + '%';
      }, 200);
    });
  }

  /* ============================================================
     CONFIRMATION DIALOGS
     ============================================================ */

  function initConfirmDialogs() {
    var confirmForms = document.querySelectorAll('[data-confirm]');
    confirmForms.forEach(function (form) {
      form.addEventListener('submit', function (e) {
        var msg = this.getAttribute('data-confirm');
        if (msg) {
          openModal('confirmModal');
          var confirmBtn = document.getElementById('confirmModalSubmit');
          var confirmMsg = document.getElementById('confirmModalMessage');
          if (confirmMsg) confirmMsg.textContent = msg;
          if (confirmBtn) {
            e.preventDefault();
            var self = this;
            confirmBtn.onclick = function () {
              closeModal('confirmModal');
              self.removeAttribute('data-confirm');
              self.submit();
            };
          }
        }
      });
    });
  }

})();
