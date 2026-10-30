/* ─── AI Lost & Found — Client JavaScript ─── */

// ── Sidebar toggle ──────────────────────────────────────────────────────────
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', (e) => {
  const sidebar = document.getElementById('sidebar');
  const btn = document.querySelector('.mobile-menu-btn, .sidebar-toggle');
  if (
    sidebar &&
    sidebar.classList.contains('open') &&
    !sidebar.contains(e.target) &&
    e.target !== btn &&
    !btn?.contains(e.target)
  ) {
    sidebar.classList.remove('open');
  }
});

// ── Notification panel ──────────────────────────────────────────────────────
function toggleNotifs() {
  const panel = document.getElementById('notifDropdown');
  if (!panel) return;
  const isVisible = panel.style.display !== 'none';
  panel.style.display = isVisible ? 'none' : 'block';
  if (!isVisible) loadNotifications();
}

async function loadNotifications() {
  try {
    const res = await fetch('/api/notifications');
    const data = await res.json();
    const list = document.getElementById('notifList');
    if (!list) return;
    if (data.length === 0) {
      list.innerHTML = '<p class="notif-empty">No notifications yet.</p>';
      return;
    }
    list.innerHTML = data.map(n => `
      <div class="notif-item ${n.is_read ? '' : 'unread'}">
        <i class="fas fa-bell"></i>
        <div>
          <p>${escapeHtml(n.message)}</p>
          <small>${n.created_at}</small>
        </div>
      </div>
    `).join('');
    // Clear badge
    const badge = document.querySelector('.notif-badge');
    if (badge) badge.remove();
  } catch (_) {}
}

async function markRead() {
  await fetch('/api/notifications');   // reading already marks them read server-side
  document.querySelectorAll('.notif-item').forEach(el => el.classList.remove('unread'));
  const badge = document.querySelector('.notif-badge');
  if (badge) badge.remove();
}

// Close notification panel when clicking outside
document.addEventListener('click', (e) => {
  const panel = document.getElementById('notifDropdown');
  const bell  = document.getElementById('notifBell');
  if (panel && panel.style.display !== 'none' && !panel.contains(e.target) && !bell?.contains(e.target)) {
    panel.style.display = 'none';
  }
});

// ── Utilities ────────────────────────────────────────────────────────────────
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ── Auto-refresh stats on dashboard ─────────────────────────────────────────
if (window.location.pathname === '/') {
  setInterval(async () => {
    try {
      const res = await fetch('/api/stats');
      const stats = await res.json();
      const mapping = {
        total_lost:    0,
        total_found:   1,
        total_matched: 2,
        active_cases:  3,
      };
      const numbers = document.querySelectorAll('.stat-number');
      Object.entries(mapping).forEach(([key, idx]) => {
        if (numbers[idx]) numbers[idx].textContent = stats[key];
      });
    } catch (_) {}
  }, 30000);   // refresh every 30s
}

// ── Toast notifications ──────────────────────────────────────────────────────
function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.style.cssText = `
    position:fixed; bottom:24px; right:24px; z-index:9999;
    padding:14px 22px; border-radius:10px; font-weight:600; font-size:.9rem;
    background:${type === 'success' ? '#16a34a' : '#dc2626'}; color:#fff;
    box-shadow:0 4px 20px rgba(0,0,0,.2);
    animation: slideIn .3s ease;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

// ── Keyboard shortcut: ESC closes sidebar & notifications ────────────────────
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.getElementById('sidebar')?.classList.remove('open');
    const nd = document.getElementById('notifDropdown');
    if (nd) nd.style.display = 'none';
  }
});
