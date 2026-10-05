// ============================================================
//  Coursely — Learn Your Way
//  Frontend JavaScript · Cookie-based JWT authentication
// ============================================================

const API_BASE = "http://127.0.0.1:8000";

// ── DOM refs ──
const loginPage      = document.getElementById("login-page");
const registerPage   = document.getElementById("register-page");
const dashboardPage  = document.getElementById("dashboard-page");
const loginForm      = document.getElementById("login-form");
const registerForm   = document.getElementById("register-form");
const loginError     = document.getElementById("login-error");
const loginSuccess   = document.getElementById("login-success");
const registerError  = document.getElementById("register-error");
const showRegisterLink = document.getElementById("show-register");
const showLoginLink    = document.getElementById("show-login");
const logoutBtn        = document.getElementById("logout-btn");
const toastContainer   = document.getElementById("toast-container");

// ============================================================
//  PAGE NAVIGATION
// ============================================================

function showPage(page) {
    loginPage.classList.add("hidden");
    registerPage.classList.add("hidden");
    dashboardPage.classList.add("hidden");
    if (page === "login")     loginPage.classList.remove("hidden");
    if (page === "register")  registerPage.classList.remove("hidden");
    if (page === "dashboard") dashboardPage.classList.remove("hidden");
}

showRegisterLink.addEventListener("click", (e) => {
    e.preventDefault(); clearMessages(); showPage("register");
});
showLoginLink.addEventListener("click", (e) => {
    e.preventDefault(); clearMessages(); showPage("login");
});

// ============================================================
//  TOAST NOTIFICATIONS
// ============================================================

function showToast(message, type = "info", duration = 3200) {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    const icons = { success: "✓", error: "✕", info: "★" };
    toast.innerHTML = `<span>${icons[type] || "★"}</span><span>${escapeHTML(message)}</span>`;
    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = "toastOut 0.3s ease forwards";
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ============================================================
//  HELPERS
// ============================================================

function clearMessages() {
    loginError.textContent = "";
    loginSuccess.textContent = "";
    registerError.textContent = "";
}

function escapeHTML(str) {
    const d = document.createElement("div");
    d.appendChild(document.createTextNode(str));
    return d.innerHTML;
}

function getInitials(name) {
    return name.split(" ").map(w => w.charAt(0)).join("").toUpperCase().slice(0, 2);
}

function capitalize(s) {
    return s.charAt(0).toUpperCase() + s.slice(1);
}

// ============================================================
//  COOKIE-BASED API CALLS
//  credentials:"include" lets the browser automatically
//  send/receive HttpOnly cookies — no manual token handling.
// ============================================================

async function authFetch(url, options = {}) {
    options.credentials = "include";
    const res = await fetch(url, options);
    if (res.status === 401) {
        const refreshed = await tryRefreshToken();
        if (refreshed) {
            const retry = await fetch(url, { ...options, credentials: "include" });
            if (retry.status === 401) { handleSessionExpired(); throw new Error("Unauthorized"); }
            return retry;
        }
        handleSessionExpired();
        throw new Error("Unauthorized");
    }
    return res;
}

async function tryRefreshToken() {
    try {
        const r = await fetch(`${API_BASE}/auth/refresh`, { method: "POST", credentials: "include" });
        return r.ok;
    } catch { return false; }
}

function handleSessionExpired() {
    showPage("login");
    showToast("Session expired — please sign in again.", "error");
}

// ============================================================
//  LOGIN
// ============================================================

loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearMessages();

    const email    = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;
    if (!email || !password) { loginError.textContent = "Please fill in all fields."; return; }

    const btn = document.getElementById("login-btn");
    const origText = btn.textContent;
    btn.innerHTML = '<span class="spinner"></span> Signing in…';
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if (!res.ok) {
            let errorMsg = "Login failed";
            if (typeof data.detail === "string") {
                errorMsg = data.detail;
            } else if (Array.isArray(data.detail)) {
                errorMsg = data.detail.map(e => e.msg).join(", ");
            }
            throw new Error(errorMsg);
        }

        loginForm.reset();
        showToast(`Welcome back, ${data.full_name}!`, "success");
        showDashboard(data);
    } catch (err) {
        loginError.textContent = err.message;
    } finally {
        btn.textContent = origText;
        btn.disabled = false;
    }
});

// ============================================================
//  REGISTER
// ============================================================

registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearMessages();

    const full_name = document.getElementById("reg-name").value.trim();
    const email      = document.getElementById("reg-email").value.trim();
    const password   = document.getElementById("reg-password").value;
    const confirm    = document.getElementById("reg-confirm").value;

    if (!full_name || !email || !password || !confirm) {
        registerError.textContent = "Please fill in all fields."; return;
    }
    if (password.length < 6) {
        registerError.textContent = "Password must be at least 6 characters."; return;
    }
    if (password !== confirm) {
        registerError.textContent = "Passwords do not match."; return;
    }

    const btn = document.getElementById("register-btn");
    const origText = btn.textContent;
    btn.innerHTML = '<span class="spinner"></span> Creating…';
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ full_name, email, password }),
        });
        const data = await res.json();
        if (!res.ok) {
            let errorMsg = "Registration failed";
            if (typeof data.detail === "string") {
                errorMsg = data.detail;
            } else if (Array.isArray(data.detail)) {
                errorMsg = data.detail.map(e => e.msg).join(", ");
            }
            throw new Error(errorMsg);
        }

        registerForm.reset();
        showPage("login");
        loginSuccess.textContent = "Account created! Sign in to start learning.";
        showToast("Welcome to Coursely! 🎉", "success");
    } catch (err) {
        registerError.textContent = err.message;
    } finally {
        btn.textContent = origText;
        btn.disabled = false;
    }
});

// ============================================================
//  DASHBOARD — populate with user data
// ============================================================

function showDashboard(user) {
    showPage("dashboard");

    const initials = getInitials(user.full_name);
    const firstName = user.full_name.split(" ")[0];

    // Navbar
    document.getElementById("nav-avatar").textContent   = initials;
    document.getElementById("nav-username").textContent  = user.full_name;
    document.getElementById("nav-role").textContent      = capitalize(user.role);

    // Welcome
    document.getElementById("welcome-heading").textContent = `Welcome back, ${firstName}! 👋`;
    document.getElementById("stat-role").textContent       = capitalize(user.role);

    const subs = {
        student: "Pick up where you left off and keep learning.",
        creator: "Manage your courses, create lessons, and help students grow.",
        admin:   "Oversee the platform, manage users and courses.",
    };
    document.getElementById("welcome-subtext").textContent = subs[user.role] || subs.student;

    // Profile
    document.getElementById("profile-avatar").textContent = initials;
    document.getElementById("profile-name").textContent   = user.full_name;
    document.getElementById("profile-email").textContent  = user.email;
    const roleEl = document.getElementById("profile-role");
    roleEl.textContent = capitalize(user.role);
    roleEl.className = `profile-role ${user.role}`;
}

// ============================================================
//  LOGOUT
// ============================================================

logoutBtn.addEventListener("click", async () => {
    try {
        await fetch(`${API_BASE}/auth/logout`, { method: "POST", credentials: "include" });
    } catch { /* clear UI anyway */ }
    showPage("login");
    clearMessages();
    showToast("Signed out successfully", "info");
});

// ============================================================
//  INIT — check existing session on page load
// ============================================================

async function init() {
    try {
        const res = await fetch(`${API_BASE}/auth/me`, { credentials: "include" });
        if (res.ok) { showDashboard(await res.json()); return; }
        if (res.status === 401) {
            if (await tryRefreshToken()) {
                const retry = await fetch(`${API_BASE}/auth/me`, { credentials: "include" });
                if (retry.ok) { showDashboard(await retry.json()); return; }
            }
        }
    } catch { /* network error → show login */ }
    showPage("login");
}

init();

// ============================================================
//  PASSWORD TOGGLE
// ============================================================

document.querySelectorAll(".password-toggle").forEach(btn => {
    btn.addEventListener("click", () => {
        const inp = document.getElementById(btn.getAttribute("data-target"));
        if (inp.type === "password") { inp.type = "text";     btn.textContent = "🙈"; }
        else                         { inp.type = "password"; btn.textContent = "👁"; }
    });
});

// ============================================================
//  TRAIL MAP — interactive waypoint clicks
// ============================================================

document.querySelectorAll(".trail-node").forEach(node => {
    node.style.cursor = "pointer";
    node.addEventListener("click", () => {
        if (node.classList.contains("completed")) {
            showToast("Lesson completed — great work!", "success");
        } else if (node.classList.contains("active")) {
            showToast("Resuming lesson…", "info");
        } else if (node.classList.contains("locked")) {
            showToast("Complete earlier lessons to unlock this one.", "error");
        }
    });
});

// ============================================================
//  QUICK ACTION CLICKS  (placeholder — features coming later)
// ============================================================

document.getElementById("action-resume")?.addEventListener("click", () => {
    showToast("Resuming: APIs & Fetch — Chapter 2", "info");
});
document.getElementById("action-browse")?.addEventListener("click", () => {
    showToast("Course catalog coming soon!", "info");
});
document.getElementById("action-schedule")?.addEventListener("click", () => {
    showToast("Schedule view coming soon!", "info");
});

// ============================================================
//  CONFETTI — fires on module completion events
// ============================================================

function launchConfetti() {
    const canvas = document.getElementById("confetti-canvas");
    canvas.classList.remove("hidden");
    const ctx = canvas.getContext("2d");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const colors = ["#fbb17a", "#f09565", "#7b83c9", "#5ed8a8", "#fcc89e", "#6da8e0"];
    const pieces = [];
    const count = 80;

    for (let i = 0; i < count; i++) {
        pieces.push({
            x: canvas.width / 2 + (Math.random() - 0.5) * 200,
            y: canvas.height / 2,
            vx: (Math.random() - 0.5) * 12,
            vy: -(Math.random() * 14 + 4),
            w: Math.random() * 8 + 4,
            h: Math.random() * 6 + 3,
            color: colors[Math.floor(Math.random() * colors.length)],
            rotation: Math.random() * 360,
            rotSpeed: (Math.random() - 0.5) * 12,
            gravity: 0.25 + Math.random() * 0.15,
            opacity: 1,
        });
    }

    let frame = 0;
    const maxFrames = 120;

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        let alive = false;
        pieces.forEach(p => {
            p.x += p.vx;
            p.vy += p.gravity;
            p.y += p.vy;
            p.rotation += p.rotSpeed;
            if (frame > maxFrames * 0.6) p.opacity -= 0.025;
            if (p.opacity <= 0) return;
            alive = true;
            ctx.save();
            ctx.translate(p.x, p.y);
            ctx.rotate((p.rotation * Math.PI) / 180);
            ctx.globalAlpha = Math.max(0, p.opacity);
            ctx.fillStyle = p.color;
            ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
            ctx.restore();
        });
        frame++;
        if (alive && frame < maxFrames) {
            requestAnimationFrame(draw);
        } else {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            canvas.classList.add("hidden");
        }
    }

    requestAnimationFrame(draw);
}

// Demo: clicking a completed trail node fires confetti
document.querySelectorAll(".trail-node.completed").forEach(node => {
    node.addEventListener("dblclick", () => {
        launchConfetti();
        showToast("🎉 Module complete!", "success");
    });
});
