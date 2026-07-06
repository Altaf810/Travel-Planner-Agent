/**
 * TravelMind AI — Planner Page JavaScript
 * Handles multi-step form, plan generation, and result rendering
 */

let currentStep = 1;
const TOTAL_STEPS = 4;
let lastPlanData = null;

/* ── Step navigation ─────────────────────────────────────────── */
function showStep(n) {
  for (let i = 1; i <= TOTAL_STEPS; i++) {
    const el = document.getElementById(`step-${i}`);
    const ind = document.getElementById(`step-ind-${i}`);
    const sn = document.getElementById(`sn-${i}`);
    if (!el) continue;

    if (i === n) {
      el.classList.remove("d-none");
      ind && ind.classList.add("active");
      sn && Object.assign(sn.style, { background: "var(--tm-primary)", color: "white" });
    } else {
      el.classList.add("d-none");
      ind && ind.classList.remove("active");
      if (i < n) {
        ind && ind.classList.add("done");
        if (sn) {
          sn.style.background = "#22c55e";
          sn.style.color = "white";
          sn.innerHTML = '<i class="bi bi-check-lg" style="font-size:14px"></i>';
        }
      } else {
        ind && ind.classList.remove("done");
        if (sn && sn.innerHTML.includes("bi-check")) {
          sn.innerHTML = i;
          sn.style.background = "";
          sn.style.color = "";
        }
      }
    }
  }
  currentStep = n;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function nextStep(from) {
  // Basic validation
  if (from === 1) {
    const source = document.querySelector('[name="source"]');
    if (!source || !source.value.trim()) {
      source && source.classList.add("is-invalid");
      showToast("Please enter your source location", "error");
      return;
    }
    source.classList.remove("is-invalid");
    if (from < TOTAL_STEPS) {
      showStep(from + 1);
      if (from + 1 === 4) buildSummary();
    }
  } else if (from < TOTAL_STEPS) {
    showStep(from + 1);
    if (from + 1 === 4) buildSummary();
  }
}

function prevStep(from) {
  if (from > 1) showStep(from - 1);
}

/* ── Build summary card ─────────────────────────────────────── */
function buildSummary() {
  const f = getFormData();
  const el = document.getElementById("tripSummary");
  if (!el) return;

  const interests = f.interests.length
    ? f.interests.map((x) => `<span class="badge bg-primary-subtle text-primary-emphasis rounded-pill me-1">${x}</span>`).join("")
    : '<span class="text-muted">None selected</span>';

  el.innerHTML = `
    <h6 class="fw-bold mb-3"><i class="bi bi-receipt me-2 text-primary"></i>Trip Summary</h6>
    <div class="row g-2 small">
      <div class="col-md-6"><b>From:</b> ${f.source || "—"}</div>
      <div class="col-md-6"><b>To:</b> ${f.destination || '<i class="bi bi-stars text-warning me-1"></i>AI will recommend'}</div>
      <div class="col-md-3"><b>Travelers:</b> ${f.travelers}</div>
      <div class="col-md-3"><b>Days:</b> ${f.duration}</div>
      <div class="col-md-6"><b>Start Date:</b> ${formatDate(f.start_date)}</div>
      <div class="col-md-6"><b>Budget:</b> ${f.budget}</div>
      <div class="col-md-6"><b>Purpose:</b> ${f.purpose}</div>
      <div class="col-md-6"><b>Transport:</b> ${f.transport}</div>
      <div class="col-md-6"><b>Stay:</b> ${f.accommodation}</div>
      <div class="col-md-6"><b>Food:</b> ${f.food_pref}</div>
      <div class="col-12"><b>Interests:</b> ${interests}</div>
    </div>`;
}

/* ── Form data collector ─────────────────────────────────────── */
function getFormData() {
  const form = document.getElementById("plannerForm");
  if (!form) return {};
  const fd = new FormData(form);
  return {
    source:        fd.get("source") || "",
    destination:   fd.get("destination") || "",
    travelers:     parseInt(fd.get("travelers")) || 2,
    budget:        fd.get("budget") || "Economy",
    start_date:    fd.get("start_date") || "",
    duration:      parseInt(fd.get("duration")) || 5,
    purpose:       fd.get("purpose") || "Vacation",
    transport:     fd.get("transport") || "Any",
    accommodation: fd.get("accommodation") || "Hotel",
    food_pref:     fd.get("food_pref") || "Any",
    weather_pref:  fd.get("weather_pref") || "Mild / Pleasant",
    interests:     fd.getAll("interests"),
    special:       fd.get("special") || "",
  };
}

/* ── Plan generation ─────────────────────────────────────────── */
const loadingMessages = [
  "Analyzing your preferences with IBM Granite AI...",
  "Researching the best destinations for your profile...",
  "Building your personalized day-wise itinerary...",
  "Calculating budget breakdown and cost estimates...",
  "Finding the best accommodation options...",
  "Planning optimal transportation routes...",
  "Generating local guide and cultural tips...",
  "Creating your smart packing checklist...",
  "Finalizing travel tips and safety alerts...",
  "Almost done — polishing your travel plan...",
];

let loadMsgInterval = null;

function startLoadingMessages() {
  let idx = 0;
  const el = document.getElementById("loadingMsg");
  if (!el) return;
  el.textContent = loadingMessages[0];
  loadMsgInterval = setInterval(() => {
    idx = (idx + 1) % loadingMessages.length;
    el.textContent = loadingMessages[idx];
  }, 3000);
}

function stopLoadingMessages() {
  if (loadMsgInterval) {
    clearInterval(loadMsgInterval);
    loadMsgInterval = null;
  }
}

async function generatePlan(e) {
  if (e) e.preventDefault();
  const data = getFormData();
  lastPlanData = data;

  // Hide form, show loading
  document.getElementById("plannerForm").classList.add("d-none");
  document.getElementById("loadingSection").classList.remove("d-none");
  document.getElementById("resultsSection").classList.add("d-none");
  startLoadingMessages();

  try {
    const result = await apiPost("/api/plan", data);
    stopLoadingMessages();
    document.getElementById("loadingSection").classList.add("d-none");

    if (result.success) {
      renderResults(result.results, result.travel_data);
      document.getElementById("resultsSection").classList.remove("d-none");
      // Init map after rendering
      const dest = result.travel_data.destination || extractFirstDestination(result.results);
      if (dest && typeof initResultMap === "function") {
        setTimeout(() => initResultMap(dest, result.travel_data), 500);
      }
      showToast("Your travel plan is ready! ✈️", "success");
    } else {
      showError(result.error || "Failed to generate plan.");
    }
  } catch (err) {
    stopLoadingMessages();
    document.getElementById("loadingSection").classList.add("d-none");
    showError("Connection error: " + err.message);
  }
}

function showError(msg) {
  document.getElementById("plannerForm").classList.remove("d-none");
  document.getElementById("loadingSection").classList.add("d-none");
  const banner = document.createElement("div");
  banner.className = "alert alert-danger alert-dismissible fade show mt-4 rounded-3";
  banner.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-2"></i><strong>Error:</strong> ${msg}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
  document.getElementById("plannerForm").prepend(banner);
  showToast(msg, "error");
}

/* ── Render results ──────────────────────────────────────────── */
function renderResults(results, travelData) {
  const md = typeof marked !== "undefined" ? marked.parse.bind(marked) : (t) => `<pre>${t}</pre>`;
  const { destination, destinations, itinerary, budget, accommodation, transport, local_guide, packing_list, travel_tips } = results;

  // Determine primary content
  if (destinations) {
    // No destination provided — show recommendations
    setTab("main", md(destinations));
    setTab("budget", emptyMsg("budget", travelData));
    setTab("stays", emptyMsg("accommodation", travelData));
    setTab("transport", emptyMsg("transport", travelData));
    setTab("guide", emptyMsg("local_guide", travelData));
    setTab("packing", emptyMsg("packing_list", travelData));
    setTab("tips", emptyMsg("travel_tips", travelData));
  } else {
    setTab("main", md(itinerary || "No itinerary generated."));
    setTab("budget", md(budget || ""));
    setTab("stays", md(accommodation || ""));
    setTab("transport", md(transport || ""));
    setTab("guide", md(local_guide || ""));
    setTab("packing", md(packing_list || ""));
    setTab("tips", md(travel_tips || ""));
  }
}

function setTab(id, html) {
  const el = document.getElementById(`content-${id}`);
  if (el) el.innerHTML = html;
}

function emptyMsg(section, travelData) {
  return `<div class="text-center py-4 text-muted">
    <i class="bi bi-info-circle fs-2 d-block mb-3"></i>
    <p>First, select a destination from the recommendations above, then generate a full plan.</p>
    <a href="/planner" class="btn btn-primary rounded-pill mt-2">Start with a Destination</a>
  </div>`;
}

function extractFirstDestination(results) {
  const text = results.destinations || results.itinerary || "";
  const match = text.match(/\*\*([^*]+)\*\*/);
  return match ? match[1].split(",")[0] : null;
}

/* ── Print ───────────────────────────────────────────────────── */
function printPlan() { window.print(); }

/* ── Pre-fill from URL params ────────────────────────────────── */
document.addEventListener("DOMContentLoaded", function () {
  const params = new URLSearchParams(window.location.search);
  if (params.get("source")) {
    const el = document.querySelector('[name="source"]');
    if (el) el.value = params.get("source");
  }
  if (params.get("destination")) {
    const el = document.querySelector('[name="destination"]');
    if (el) el.value = params.get("destination");
  }
  if (params.get("travelers")) {
    const el = document.querySelector('[name="travelers"]');
    if (el) el.value = params.get("travelers");
  }
  if (params.get("duration")) {
    const el = document.querySelector('[name="duration"]');
    if (el) el.value = params.get("duration");
  }

  // Set min date to today
  const dateEl = document.querySelector('[name="start_date"]');
  if (dateEl) dateEl.min = new Date().toISOString().split("T")[0];

  // Attach form submit
  const form = document.getElementById("plannerForm");
  if (form) form.addEventListener("submit", generatePlan);

  showStep(1);
});
