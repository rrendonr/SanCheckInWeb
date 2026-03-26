const STORAGE_KEY = 'visitors_onsite';

function loadVisitors() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    return [];
  }
}

function saveVisitors(visitors) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(visitors));
}

function renderVisitors() {
  const visitors = loadVisitors();
  const list = document.getElementById('visitorList');
  const count = document.getElementById('count');

  count.textContent = visitors.length;

  if (visitors.length === 0) {
    list.innerHTML = '<p class="empty-msg">No active visitors right now.</p>';
    return;
  }

  list.innerHTML = visitors.map((v) => `
    <div class="visitor-card">
      <div class="visitor-info">
        <div class="visitor-name">${escape(v.name)}</div>
        <div class="visitor-meta">Visiting ${escape(v.host)}${v.company ? ' &middot; ' + escape(v.company) : ''}</div>
      </div>
      <button class="btn-checkout" onclick="checkOut('${v.id}')">Check out</button>
    </div>
  `).join('');
}

function escape(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function checkOut(id) {
  const visitors = loadVisitors().filter((v) => v.id !== id);
  saveVisitors(visitors);
  renderVisitors();
  showFlash('Checked out.');
}

function showFlash(msg) {
  const flash = document.getElementById('flash');
  flash.textContent = msg;
  flash.classList.remove('hidden');
  clearTimeout(flash._timer);
  flash._timer = setTimeout(() => flash.classList.add('hidden'), 3000);
}

document.getElementById('checkinForm').addEventListener('submit', (e) => {
  e.preventDefault();

  const nameEl = document.getElementById('name');
  const hostEl = document.getElementById('host');

  let valid = true;

  [nameEl, hostEl].forEach((el) => {
    el.classList.remove('error');
    if (!el.value.trim()) {
      el.classList.add('error');
      valid = false;
    }
  });

  if (!valid) return;

  const visitor = {
    id: Date.now().toString(),
    name: nameEl.value.trim(),
    company: document.getElementById('company').value.trim(),
    email: document.getElementById('email').value.trim(),
    phone: document.getElementById('phone').value.trim(),
    host: hostEl.value.trim(),
    badge: document.getElementById('badge').value.trim(),
    purpose: document.getElementById('purpose').value.trim(),
    checkedInAt: new Date().toISOString(),
  };

  const visitors = loadVisitors();
  visitors.push(visitor);
  saveVisitors(visitors);

  e.target.reset();
  renderVisitors();
  showFlash(`${visitor.name} checked in successfully.`);
});

// Init
renderVisitors();
