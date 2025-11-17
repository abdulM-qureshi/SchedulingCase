// admin_dashboard.js (full script)

// CSRF helper
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}
const CSRF_TOKEN = getCookie("csrftoken");

// Use URL set in template (prefer). Fallback to this path:
const USERS_API = window.ADMIN_API_USERS || "/admin/dashboard/tables/users/";
const USER_DETAIL_API_BASE = USERS_API; // we'll append id + '/'

// ---------- UI helpers ----------
function showToast(msg, isError=false) {
  const t = document.getElementById("toast");
  if (!t) {
    alert(msg);
    return;
  }
  t.textContent = msg;
  t.className = isError ? "toast toast-error" : "toast toast-success";
  t.style.display = "block";
  setTimeout(()=>{ t.style.display = "none"; }, 3000);
}

function closeModal() {
  const m = document.getElementById("userModal");
  if (m) {
    m.style.display = "none";
  }
}


function openModal() {
  const m = document.getElementById("userModal");
  if (m) {
    m.style.display = "flex"; // use flex to center it
  }
}

// ---------- Render functions ----------
function renderUsers(users) {
  const tbody = document.getElementById("usersTableBody");
  tbody.innerHTML = "";

  if (!users || users.length === 0) {
    tbody.innerHTML = `<tr><td colspan="3" class="loading"><i class="fas fa-info-circle"></i> No users found</td></tr>`;
    document.getElementById("totalUsers").textContent = 0;
    return;
  }

  document.getElementById("totalUsers").textContent = users.length;

  users.forEach(u => {
    const tr = document.createElement("tr");
    const nameTd = document.createElement("td");
    nameTd.textContent = u.full_name || u.username || "(no name)";
    const emailTd = document.createElement("td");
    emailTd.textContent = u.email || "";
    const actionsTd = document.createElement("td");

    const editBtn = document.createElement("button");
    editBtn.className = "btn btn-sm btn-primary";
    editBtn.textContent = "Edit";
    editBtn.onclick = () => openEditModal(u);

    const delBtn = document.createElement("button");
    delBtn.className = "btn btn-sm btn-danger ms-2";
    delBtn.textContent = "Delete";
    delBtn.onclick = () => confirmDelete(u);

    actionsTd.appendChild(editBtn);
    actionsTd.appendChild(delBtn);

    tr.appendChild(nameTd);
    tr.appendChild(emailTd);
    tr.appendChild(actionsTd);
    tbody.appendChild(tr);
  });
}

// ---------- API calls ----------
async function loadUsers() {
  try {
    const res = await fetch(USERS_API, { credentials: "same-origin" });
    if (!res.ok) throw new Error("Failed to load users");
    const data = await res.json();
    renderUsers(data.users || []);
  } catch (err) {
    console.error("Error loading users:", err);
    document.getElementById("usersTableBody").innerHTML = `<tr><td colspan="3">Error loading users</td></tr>`;
  }
}

async function createUserAPI(payload) {
  const res = await fetch(USERS_API, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": CSRF_TOKEN,
    },
    credentials: "same-origin",
    body: JSON.stringify(payload),
  });
  if (res.status === 201) return res.json();
  const err = await res.json().catch(()=>({error: 'unknown'}));
  throw new Error(err.error || JSON.stringify(err));
}

async function updateUserAPI(id, payload) {
  const url = USER_DETAIL_API_BASE + id + "/";
  const res = await fetch(url, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": CSRF_TOKEN,
    },
    credentials: "same-origin",
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(()=>({error:'unknown'}));
    throw new Error(err.error || JSON.stringify(err));
  }
  return res.json();
}

async function deleteUserAPI(id) {
  const url = USER_DETAIL_API_BASE + id + "/";
  const res = await fetch(url, {
    method: "DELETE",
    headers: {
      "X-CSRFToken": CSRF_TOKEN,
    },
    credentials: "same-origin"
  });
  if (!res.ok) {
    const err = await res.json().catch(()=>({error:'unknown'}));
    throw new Error(err.error || JSON.stringify(err));
  }
  return res.json();
}

// ---------- Modal behaviour ----------
function openCreateModal() {
  document.getElementById("modalTitle").textContent = "Create User";
  document.getElementById("fullName").value = "";
  document.getElementById("email").value = "";
  document.getElementById("userForm").dataset.editId = "";
  openModal();
}

function openEditModal(user) {
  document.getElementById("modalTitle").textContent = "Edit User";
  document.getElementById("fullName").value = user.full_name || "";
  document.getElementById("email").value = user.email || "";
  // store id so submit handler performs update
  document.getElementById("userForm").dataset.editId = user.id;
  openModal();
}

function confirmDelete(user) {
  if (!confirm(`Delete ${user.full_name || user.username}? This cannot be undone.`)) return;
  deleteUser(user.id);
}

// ---------- Submit handler for create or edit ----------
async function handleSubmit(ev) {
  ev.preventDefault();
  const fullName = document.getElementById("fullName").value.trim();
  const email = document.getElementById("email").value.trim();
  if (!fullName || !email) {
    showToast("Full name and email are required", true);
    return;
  }

  const form = document.getElementById("userForm");
  const editId = form.dataset.editId;

  try {
    if (!editId) {
      // create
      await createUserAPI({ fullName, email });
      showToast("User created");
    } else {
      await updateUserAPI(editId, { fullName, email });
      showToast("User updated");
    }
    closeModal();
    await loadUsers();
  } catch (err) {
    console.error(err);
    showToast("Error: " + err.message, true);
  }
}

async function deleteUser(id) {
  try {
    await deleteUserAPI(id);
    showToast("User deleted");
    await loadUsers();
  } catch (err) {
    console.error("Delete error:", err);
    showToast("Error deleting user: " + err.message, true);
  }
}

// ---------- wire up on DOM ready ----------
document.addEventListener("DOMContentLoaded", () => {
  loadUsers();
  const form = document.getElementById("userForm");
  if (form) form.addEventListener("submit", handleSubmit);
});
