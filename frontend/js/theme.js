// Light-only theme behavior for HealthSenseAI

(function () {
  document.documentElement.classList.remove('dark');
  localStorage.setItem('hs_theme', 'light');
})();

document.addEventListener('DOMContentLoaded', () => {
  document.documentElement.classList.remove('dark');
  localStorage.setItem('hs_theme', 'light');
});
