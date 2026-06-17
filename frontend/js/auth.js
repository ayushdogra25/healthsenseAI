// Session guard and auth utilities for HealthSenseAI

document.addEventListener('DOMContentLoaded', () => {
  const currentPath = window.location.pathname;
  const filename = currentPath.substring(currentPath.lastIndexOf('/') + 1);
  
  const publicPages = ['index.html', 'login.html', 'register.html', ''];
  const authPages = ['login.html', 'register.html'];
  const protectedPages = ['dashboard.html', 'check.html', 'history.html', 'profile.html', 'hospitals.html', 'admin.html'];
  
  const isAuth = api.isAuthenticated();
  const user = api.getUser();
  
  // Guard logic
  if (protectedPages.some(page => filename.includes(page))) {
    if (!isAuth) {
      window.location.href = 'login.html?redirect=' + encodeURIComponent(filename);
      return;
    }
    
    // Admin page specific guard
    if (filename.includes('admin.html') && (!user || !user.is_admin)) {
      window.location.href = 'dashboard.html';
      return;
    }
  }
  
  if (authPages.some(page => filename.includes(page))) {
    if (isAuth) {
      window.location.href = 'dashboard.html';
      return;
    }
  }
  
  // Update header / user elements across pages if they exist
  updateUserUI(user);
});

function updateUserUI(user) {
  const userNameElements = document.querySelectorAll('.user-name-display');
  const userEmailElements = document.querySelectorAll('.user-email-display');
  const adminLinks = document.querySelectorAll('.admin-only-link');
  const logoutBtn = document.getElementById('logout-btn');
  
  if (user) {
    userNameElements.forEach(el => el.textContent = user.full_name);
    userEmailElements.forEach(el => el.textContent = user.email);
    
    if (user.is_admin) {
      adminLinks.forEach(el => el.classList.remove('hidden'));
    } else {
      adminLinks.forEach(el => el.classList.add('hidden'));
    }
  }
  
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      api.logout();
      window.location.href = 'index.html';
    });
  }
}
