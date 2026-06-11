// Modal helpers
function openModal(id) {
  document.getElementById(id).classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
  document.body.style.overflow = '';
}

// Close on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) closeModal(overlay.id);
  });
});

// Close on Escape
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => closeModal(m.id));
    closeDropdown();
  }
});

// Delivery modal
var deliveryBtn = document.getElementById('deliveryBtn');
if (deliveryBtn) deliveryBtn.addEventListener('click', () => openModal('deliveryModal'));
document.getElementById('deliveryClose').addEventListener('click', () => closeModal('deliveryModal'));
document.getElementById('deliveryModalClose').addEventListener('click', () => closeModal('deliveryModal'));

// Auth modal
var userBtn = document.getElementById('userBtn');
if (userBtn) userBtn.addEventListener('click', () => openModal('authModal'));
var authClose = document.getElementById('authClose');
if (authClose) authClose.addEventListener('click', () => closeModal('authModal'));

// Auth tab switching
const tabs = document.querySelectorAll('.auth-tab');
tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    tabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    const target = tab.dataset.tab;
    document.querySelectorAll('.auth-panel').forEach(p => p.classList.remove('active'));
    document.getElementById(target).classList.add('active');
  });
});

// Categories dropdown
const dropdown = document.querySelector('.dropdown');
function closeDropdown() {
  if (dropdown) dropdown.classList.remove('open');
}

if (dropdown) {
  dropdown.querySelector('.navbar__categories-btn').addEventListener('click', e => {
    e.stopPropagation();
    dropdown.classList.toggle('open');
  });
  document.addEventListener('click', closeDropdown);
}

// Toast notification
function showToast(message, type) {
  const toast = document.createElement('div');
  toast.className = 'toast' + (type === 'info' ? ' toast--info' : '');
  toast.textContent = message;
  document.body.appendChild(toast);
  void toast.offsetHeight; // force reflow so transition fires
  toast.classList.add('toast--show');
  setTimeout(() => {
    toast.classList.remove('toast--show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Favourite toggle
document.querySelectorAll('.product-card__btn--fav[data-product-id], .pd-fav-btn[data-product-id]').forEach(function(btn) {
  btn.addEventListener('click', function() {
    if (!window._userAuthenticated) {
      openModal('authModal');
      return;
    }
    var id = btn.getAttribute('data-product-id');
    var csrf = getCookie('csrftoken');
    fetch('/favourite/toggle/' + id + '/', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf, 'X-Requested-With': 'XMLHttpRequest' }
    }).then(function(r) {
      return r.json();
    }).then(function(data) {
      var svg = btn.querySelector('svg');
      if (data.status === 'added') {
        btn.classList.add('active');
        svg.setAttribute('fill', 'currentColor');
        showToast('Товар добавлен в избранное ❤️');
      } else {
        btn.classList.remove('active');
        svg.setAttribute('fill', 'none');
        showToast('Товар удалён из избранного', 'info');
      }
    }).catch(function() {
      showToast('Ошибка. Попробуйте ещё раз.', 'info');
    });
  });
});

function getCookie(name) {
  if (name === 'csrftoken') {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
  }
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

// Phone input — digits only, max 9
document.querySelectorAll('.phone-digits-input').forEach(function(input) {
  input.addEventListener('input', function() {
    var pos = input.selectionStart;
    var raw = input.value.replace(/\D/g, '').slice(0, 9);
    input.value = raw;
    input.setSelectionRange(pos, pos);
  });
  input.addEventListener('keydown', function(e) {
    var allowed = ['Backspace','Delete','ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Tab','Home','End'];
    if (allowed.indexOf(e.key) === -1 && !/^\d$/.test(e.key)) {
      e.preventDefault();
    }
  });
  input.addEventListener('paste', function(e) {
    e.preventDefault();
    var text = (e.clipboardData || window.clipboardData).getData('text');
    var digits = text.replace(/\D/g, '');
    // strip leading 992 if full number pasted
    if (digits.startsWith('992') && digits.length === 12) digits = digits.slice(3);
    input.value = digits.slice(0, 9);
  });
});

// Logout confirmation modal
(function() {
  var pendingLogoutForm = null;
  var logoutModal = document.getElementById('logoutModal');

  document.querySelectorAll('form[action*="logout"]').forEach(function(form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      pendingLogoutForm = form;
      logoutModal.classList.add('open');
      document.body.style.overflow = 'hidden';
    });
  });

  document.getElementById('logoutConfirm').addEventListener('click', function() {
    if (pendingLogoutForm) pendingLogoutForm.submit();
  });

  document.getElementById('logoutCancel').addEventListener('click', function() {
    pendingLogoutForm = null;
    logoutModal.classList.remove('open');
    document.body.style.overflow = '';
  });

  logoutModal.addEventListener('click', function(e) {
    if (e.target === logoutModal) {
      pendingLogoutForm = null;
      logoutModal.classList.remove('open');
      document.body.style.overflow = '';
    }
  });
})();

// Search panel toggle
(function() {
  var searchBtn = document.getElementById('searchBtn');
  var searchPanel = document.getElementById('searchPanel');
  var searchClose = document.getElementById('searchClose');
  var searchInput = document.getElementById('searchInput');

  function openSearch() {
    searchPanel.classList.add('open');
    setTimeout(function() { if (searchInput) searchInput.focus(); }, 80);
  }
  function closeSearch() {
    searchPanel.classList.remove('open');
  }

  if (searchBtn) searchBtn.addEventListener('click', function() {
    searchPanel.classList.contains('open') ? closeSearch() : openSearch();
  });
  if (searchClose) searchClose.addEventListener('click', closeSearch);

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeSearch();
  });

  var searchForm = document.getElementById('searchForm');
  if (searchForm) {
    searchForm.addEventListener('submit', function(e) {
      var q = searchInput ? searchInput.value.trim() : '';
      if (!q) { e.preventDefault(); return; }
    });
  }
})();
