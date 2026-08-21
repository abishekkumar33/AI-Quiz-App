/* Dark/Light mode toggle + mobile sidebar toggle, shared across all pages */
(function () {
  const root = document.documentElement;
  const themeBtn = document.getElementById('themeToggle');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');

  function applyTheme(theme) {
    root.setAttribute('data-bs-theme', theme);
    if (themeBtn) {
      const icon = themeBtn.querySelector('i');
      if (icon) icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
    }
    localStorage.setItem('theme', theme);
  }

  const savedTheme = localStorage.getItem('theme') ||
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  applyTheme(savedTheme);

  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      const current = root.getAttribute('data-bs-theme');
      applyTheme(current === 'dark' ? 'light' : 'dark');
    });
  }

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('show');
    });
    document.addEventListener('click', function (e) {
      if (window.innerWidth < 992 && sidebar.classList.contains('show') &&
          !sidebar.contains(e.target) && e.target !== sidebarToggle && !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove('show');
      }
    });
  }
})();
