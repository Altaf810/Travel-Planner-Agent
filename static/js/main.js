/**
 * TravelMind AI — Main JavaScript
 * Global utilities: dark mode, navbar, shared helpers
 */

/* ── Dark Mode ─────────────────────────────────────────────── */
const DARK_KEY = "tm-dark-mode";

function applyTheme(dark) {
  document.documentElement.setAttribute("data-bs-theme", dark ? "dark" : "light");
  const btn = document.getElementById("darkModeToggle");
  if (btn) {
    btn.innerHTML = dark
      ? '<i class="bi bi-sun-fill"></i>'
      : '<i class="bi bi-moon-stars-fill"></i>';
    btn.title = dark ? "Switch to light mode" : "Switch to dark mode";
  }
}

function toggleDark() {
  const isDark = document.documentElement.getAttribute("data-bs-theme") === "dark";
  const next = !isDark;
  localStorage.setItem(DARK_KEY, next);
  applyTheme(next);
}

// Init dark mode on load
(function () {
  const saved = localStorage.getItem(DARK_KEY);
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyTheme(saved !== null ? saved === "true" : prefersDark);
})();

document.addEventListener("DOMContentLoaded", function () {
  const btn = document.getElementById("darkModeToggle");
  if (btn) btn.addEventListener("click", toggleDark);

  // Active nav link
  const path = window.location.pathname;
  document.querySelectorAll(".tm-navbar .nav-link").forEach((a) => {
    const href = a.getAttribute("href");
    if (href === path || (href !== "/" && path.startsWith(href))) {
      a.classList.add("active");
      a.style.background = "rgba(255,255,255,0.2)";
      a.style.color = "#fff";
    }
  });
});

/* ── Markdown Renderer ─────────────────────────────────────── */
function renderMarkdown(text, targetId) {
  const el = document.getElementById(targetId);
  if (!el) return;
  if (typeof marked !== "undefined") {
    el.innerHTML = marked.parse(text || "");
  } else {
    el.innerHTML = `<pre style="white-space:pre-wrap">${escapeHtml(text || "")}</pre>`;
  }
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/* ── Toast notifications ───────────────────────────────────── */
function showToast(message, type = "info") {
  const colors = {
    success: "#22c55e",
    error: "#ef4444",
    info: "#3b82f6",
    warning: "#f59e0b",
  };
  const toast = document.createElement("div");
  toast.style.cssText = `
    position:fixed; bottom:24px; right:24px; z-index:9999;
    background:${colors[type] || colors.info}; color:white;
    padding:14px 20px; border-radius:12px;
    box-shadow:0 4px 20px rgba(0,0,0,.2);
    font-size:14px; font-weight:500;
    transform:translateX(120px); opacity:0;
    transition:all .35s cubic-bezier(.34,1.56,.64,1);
    max-width:320px;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);
  requestAnimationFrame(() => {
    toast.style.transform = "translateX(0)";
    toast.style.opacity = "1";
  });
  setTimeout(() => {
    toast.style.transform = "translateX(120px)";
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}

/* ── API helper ─────────────────────────────────────────────── */
async function apiPost(endpoint, data) {
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/* ── Format date ────────────────────────────────────────────── */
function formatDate(dateStr) {
  if (!dateStr) return "Flexible";
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" });
}

/* ── Status check ───────────────────────────────────────────── */
async function checkStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    return data;
  } catch {
    return { status: "error", configured: false };
  }
}
