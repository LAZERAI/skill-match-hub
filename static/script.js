/* ═══════════════════════════════════════════════════════════════════════════
   Skill Match Hub — Frontend Logic
   ═══════════════════════════════════════════════════════════════════════════ */

// ── DOM refs ─────────────────────────────────────────────────────────────
const views = {
  landing: document.getElementById("landingView"),
  recruiter: document.getElementById("recruiterView"),
  seeker: document.getElementById("seekerView"),
};

const jdInput = document.getElementById("jdInput");
const resumeInput = document.getElementById("resumeInput");
const jdCharCount = document.getElementById("jdCharCount");
const resumeCharCount = document.getElementById("resumeCharCount");
const recruiterResults = document.getElementById("recruiterResults");
const seekerResults = document.getElementById("seekerResults");

// File state
let recruiterFile = null;
let seekerFile = null;

// Recruiter candidate state
let recruiterCandidates = [];
let recruiterFilter = "all"; // all | open | hired

// ── Character counters ───────────────────────────────────────────────────
jdInput.addEventListener("input", () => {
  jdCharCount.textContent = jdInput.value.length;
});

resumeInput.addEventListener("input", () => {
  resumeCharCount.textContent = resumeInput.value.length;
});

// ── View switching ───────────────────────────────────────────────────────
function switchView(viewName) {
  Object.values(views).forEach((v) => v.classList.remove("active"));
  views[viewName].classList.add("active");
}

function selectRole(role) {
  switchView(role);
}

function goHome() {
  switchView("landing");
}

// ── Input mode tabs ──────────────────────────────────────────────────────
function switchInputMode(role, mode, tabEl) {
  // Update tabs
  const section = tabEl.closest(".input-section");
  section.querySelectorAll(".input-tab").forEach((t) => t.classList.remove("active"));
  tabEl.classList.add("active");

  // Update modes
  section.querySelectorAll(".input-mode").forEach((m) => m.classList.remove("active"));
  const modeId = `${role}${mode === "text" ? "Text" : "File"}Mode`;
  document.getElementById(modeId).classList.add("active");
}

// ── File handling ────────────────────────────────────────────────────────
function handleFileSelect(role, input) {
  const file = input.files[0];
  if (!file) return;

  const ext = file.name.split(".").pop().toLowerCase();
  if (!["pdf", "txt", "text"].includes(ext)) {
    showToast("Please select a PDF or TXT file.", "error");
    input.value = "";
    return;
  }

  if (file.size > 10 * 1024 * 1024) {
    showToast("File too large (max 10MB).", "error");
    input.value = "";
    return;
  }

  if (role === "recruiter") {
    recruiterFile = file;
    document.getElementById("recruiterFileName").textContent = `✓ ${file.name} (${formatSize(file.size)})`;
    document.getElementById("recruiterDropZone").classList.add("has-file");
    document.getElementById("uploadRecruiterBtn").disabled = false;
    document.getElementById("recruiterFileInfo").textContent = file.name;
  } else {
    seekerFile = file;
    document.getElementById("seekerFileName").textContent = `✓ ${file.name} (${formatSize(file.size)})`;
    document.getElementById("seekerDropZone").classList.add("has-file");
    document.getElementById("uploadSeekerBtn").disabled = false;
    document.getElementById("seekerFileInfo").textContent = file.name;
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

// ── Drag and drop ────────────────────────────────────────────────────────
["recruiterDropZone", "seekerDropZone"].forEach((id) => {
  const zone = document.getElementById(id);
  if (!zone) return;
  const role = id.startsWith("recruiter") ? "recruiter" : "seeker";
  const inputId = role === "recruiter" ? "recruiterFileInput" : "seekerFileInput";

  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("drag-over");
  });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("drag-over");

    const file = e.dataTransfer.files[0];
    if (file) {
      const input = document.getElementById(inputId);
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      handleFileSelect(role, input);
    }
  });
});

// ── Theme toggle ─────────────────────────────────────────────────────────
function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  html.setAttribute("data-theme", next);
  localStorage.setItem("smh-theme", next);
  updateThemeIcons(next);
}

function updateThemeIcons(theme) {
  const icon = theme === "dark" ? "☀️" : "🌙";
  document.getElementById("fabIcon").textContent = icon;

  const t1 = document.getElementById("topThemeIcon1");
  const t2 = document.getElementById("topThemeIcon2");
  if (t1) t1.textContent = icon;
  if (t2) t2.textContent = icon;
}

// Load saved theme (default: light)
(function () {
  const saved = localStorage.getItem("smh-theme") || "light";
  document.documentElement.setAttribute("data-theme", saved);
  updateThemeIcons(saved);
})();

// ── Load health stats on landing ────────────────────────────────────────
(async function loadStats() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();

    // If indexes are still building or not loaded, show a friendly message
    document.getElementById("statResumes").textContent = data.resume_index_loaded ? data.resume_count : "building…";
    document.getElementById("statJobs").textContent = data.job_index_loaded ? data.job_count : "building…";
  } catch {
    // silently fail for stats
  }
})();

// ── Recruiter: Search via text ───────────────────────────────────────────
async function searchCandidates() {
  const text = jdInput.value.trim();
  if (!text) {
    showToast("Please paste a job description first.", "error");
    return;
  }

  const btn = document.getElementById("searchCandidatesBtn");
  btn.disabled = true;
  showRecruiterLoading();

  try {
    const res = await fetch("/api/recruiter/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_description: text }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${res.status}`);
    }

    const data = await res.json();
    renderCandidates(data);
  } catch (err) {
    recruiterResults.innerHTML = `<div class="error-state">⚠ ${escapeHtml(err.message)}</div>`;
  } finally {
    btn.disabled = false;
  }
}

// ── Recruiter: Search via file upload ────────────────────────────────────
async function uploadRecruiterFile() {
  if (!recruiterFile) {
    showToast("Please select a file first.", "error");
    return;
  }

  const btn = document.getElementById("uploadRecruiterBtn");
  btn.disabled = true;
  showRecruiterLoading();

  try {
    const formData = new FormData();
    formData.append("file", recruiterFile);

    const res = await fetch("/api/recruiter/upload", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${res.status}`);
    }

    const data = await res.json();
    renderCandidates(data);
  } catch (err) {
    recruiterResults.innerHTML = `<div class="error-state">⚠ ${escapeHtml(err.message)}</div>`;
  } finally {
    btn.disabled = false;
  }
}

function showRecruiterLoading() {
  recruiterResults.innerHTML = `
    <div class="loading-indicator">
      <div class="loading-spinner"></div>
      <div class="loading-text">Searching talent pool...</div>
      <div class="loading-sub">Embedding JD → FAISS search → LLM evaluation</div>
    </div>
  `;
}

function setRecruiterFilter(filter) {
  recruiterFilter = filter;
  renderCandidateList();
}

function toggleHired(index) {
  const candidate = recruiterCandidates[index];
  if (!candidate) return;
  candidate.hired = !candidate.hired;
  renderCandidateList();
}

function renderCandidateList() {
  const filtered = recruiterCandidates.filter((c) => {
    if (recruiterFilter === "hired") return c.hired;
    if (recruiterFilter === "open") return !c.hired;
    return true;
  });

  if (filtered.length === 0) {
    recruiterResults.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🔍</div>
        <div class="empty-title">No matching candidates found</div>
        <div class="empty-desc">Try broadening your job requirements or adjusting the required experience level.</div>
      </div>
    `;
    return;
  }

  let html = `
    <div class="results-header">
      <div class="results-meta-group">
        <h3>Top Candidates</h3>
        <span class="results-meta">${filtered.length} shown • ${recruiterCandidates.length} total</span>
      </div>
      <div class="filter-tabs">
        <button class="filter-tab ${recruiterFilter === 'all' ? 'active' : ''}" onclick="setRecruiterFilter('all')">All</button>
        <button class="filter-tab ${recruiterFilter === 'open' ? 'active' : ''}" onclick="setRecruiterFilter('open')">Open</button>
        <button class="filter-tab ${recruiterFilter === 'hired' ? 'active' : ''}" onclick="setRecruiterFilter('hired')">Hired</button>
      </div>
    </div>
  `;

  filtered.forEach((cand, i) => {
    const rank = i + 1;
    const rankClass = rank <= 3 ? `rank-${rank}` : "rank-default";
    const rec = parseRecommendation(cand.llm_evaluation || "");
    const matchedSkills = cand.matched_skills || [];
    const allSkills = cand.skills || [];

    html += `
      <div class="candidate-card" style="animation-delay: ${i * 0.08}s">
        <div class="card-header">
          <div class="card-rank ${rankClass}">#${rank}</div>
          <div class="card-info">
            <div class="card-name">${escapeHtml(cand.name)}</div>
            <div class="card-email">${escapeHtml(cand.email)}</div>
          </div>
          <div style="display:flex;gap:8px;align-items:center;">
            ${cand.hired ? '<span class="hired-badge">HIRED</span>' : ''}
            ${rec.badge}
            <span class="card-score">${(cand.final_score || 0).toFixed(2)}</span>
          </div>
        </div>
        <div class="card-stats">
          <div class="stat-item">
            <div class="stat-label">Experience</div>
            <div class="stat-value">${cand.experience_years || 0}y</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Internship</div>
            <div class="stat-value">${cand.internship_years || 0}y</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Total</div>
            <div class="stat-value">${cand.total_experience_years || 0}y</div>
          </div>
        </div>
        <div class="card-skills">
          ${matchedSkills.map((s) => `<span class="skill-tag matched">✓ ${escapeHtml(s)}</span>`).join("")}
          ${allSkills.filter((s) => !matchedSkills.includes(s.toLowerCase())).slice(0, 8).map((s) => `<span class="skill-tag">${escapeHtml(s)}</span>`).join("")}
        </div>
        <div class="card-eval">
          <div class="eval-title">🤖 AI Evaluation</div>
          <div class="eval-content">${formatLLMText(cand.llm_evaluation || "No evaluation available.")}</div>
        </div>
        <div class="card-actions">
          <button class="outline-btn" onclick="toggleHired(${cand._internalId})">${cand.hired ? 'Mark as Open' : 'Mark as Hired'}</button>
        </div>
      </div>
    `;
  });

  recruiterResults.innerHTML = html;
}

function renderCandidates(data) {
  recruiterCandidates = (data.candidates || []).map((cand, idx) => ({
    ...cand,
    hired: false,
    _internalId: idx,
  }));
  recruiterFilter = 'all';
  renderCandidateList();
}

    html += `
      <div class="candidate-card" style="animation-delay: ${i * 0.08}s">
        <div class="card-header">
          <div class="card-rank ${rankClass}">#${rank}</div>
          <div class="card-info">
            <div class="card-name">${escapeHtml(cand.name)}</div>
            <div class="card-email">${escapeHtml(cand.email)}</div>
          </div>
          <div style="display:flex;gap:8px;align-items:center;">
            ${rec.badge}
            <span class="card-score">${(cand.final_score || 0).toFixed(2)}</span>
          </div>
        </div>
        <div class="card-stats">
          <div class="stat-item">
            <div class="stat-label">Experience</div>
            <div class="stat-value">${cand.experience_years || 0}y</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Internship</div>
            <div class="stat-value">${cand.internship_years || 0}y</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">Total</div>
            <div class="stat-value">${cand.total_experience_years || 0}y</div>
          </div>
        </div>
        <div class="card-skills">
          ${matchedSkills.map((s) => `<span class="skill-tag matched">✓ ${escapeHtml(s)}</span>`).join("")}
          ${allSkills.filter((s) => !matchedSkills.includes(s.toLowerCase())).slice(0, 8).map((s) => `<span class="skill-tag">${escapeHtml(s)}</span>`).join("")}
        </div>
        <div class="card-eval">
          <div class="eval-title">🤖 AI Evaluation</div>
          <div class="eval-content">${formatLLMText(cand.llm_evaluation || "No evaluation available.")}</div>
        </div>
      </div>
    `;
  });

  recruiterResults.innerHTML = html;
}

// ── Seeker: Search via text ──────────────────────────────────────────────
async function searchJobs() {
  const text = resumeInput.value.trim();
  if (!text) {
    showToast("Please paste your resume text first.", "error");
    return;
  }

  const btn = document.getElementById("searchJobsBtn");
  btn.disabled = true;
  showSeekerLoading();

  try {
    const res = await fetch("/api/seeker/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_text: text }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${res.status}`);
    }

    const data = await res.json();
    renderJobs(data);
  } catch (err) {
    seekerResults.innerHTML = `<div class="error-state">⚠ ${escapeHtml(err.message)}</div>`;
  } finally {
    btn.disabled = false;
  }
}

// ── Seeker: Search via file upload ───────────────────────────────────────
async function uploadSeekerFile() {
  if (!seekerFile) {
    showToast("Please select a file first.", "error");
    return;
  }

  const btn = document.getElementById("uploadSeekerBtn");
  btn.disabled = true;
  showSeekerLoading();

  try {
    const formData = new FormData();
    formData.append("file", seekerFile);

    const res = await fetch("/api/seeker/upload", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${res.status}`);
    }

    const data = await res.json();
    renderJobs(data);
  } catch (err) {
    seekerResults.innerHTML = `<div class="error-state">⚠ ${escapeHtml(err.message)}</div>`;
  } finally {
    btn.disabled = false;
  }
}

function showSeekerLoading() {
  seekerResults.innerHTML = `
    <div class="loading-indicator">
      <div class="loading-spinner"></div>
      <div class="loading-text">Finding matching jobs...</div>
      <div class="loading-sub">Embedding resume → FAISS search → Career analysis</div>
    </div>
  `;
}

function renderJobs(data) {
  if (!data.jobs || data.jobs.length === 0) {
    seekerResults.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📄</div>
        <div class="empty-title">No matching jobs found</div>
        <div class="empty-desc">Try including more details about your skills and experience in your resume.</div>
      </div>
    `;
    return;
  }

  let html = `
    <div class="results-header">
      <h3>Top Job Matches</h3>
      <span class="results-meta">${data.jobs.length} matches · ${data.elapsed_seconds}s</span>
    </div>
  `;

  data.jobs.forEach((job, i) => {
    html += `
      <div class="job-card" style="animation-delay: ${i * 0.08}s">
        <div class="job-header">
          <div class="job-title-area">
            <div class="job-title">${escapeHtml(job.job_title)}</div>
            <div class="job-company">${escapeHtml(job.company)}</div>
            <div class="job-location">📍 ${escapeHtml(job.location)}</div>
          </div>
          <span class="job-score">${(job.similarity_score || 0).toFixed(2)} match</span>
        </div>
        <div class="job-preview">${escapeHtml(job.description_preview)}...</div>
        <div class="job-analysis">
          <div class="analysis-title">🤖 Career Analysis</div>
          <div class="analysis-content">${formatLLMText(job.llm_analysis || "No analysis available.")}</div>
        </div>
      </div>
    `;
  });

  seekerResults.innerHTML = html;
}

// ── Utilities ────────────────────────────────────────────────────────────
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function formatLLMText(text) {
  let html = escapeHtml(text);
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/^(\d+)\.\s+(.+)$/gm, "<strong>$1.</strong> $2");
  html = html.replace(/^[-•]\s+(.+)$/gm, "• $1");
  return html;
}

function parseRecommendation(evalText) {
  const lower = evalText.toLowerCase();
  if (lower.includes("hire") && !lower.includes("not hire")) {
    return { badge: '<span class="rec-badge rec-hire">✓ Hire</span>' };
  }
  if (lower.includes("consider")) {
    return { badge: '<span class="rec-badge rec-consider">◐ Consider</span>' };
  }
  if (lower.includes("reject")) {
    return { badge: '<span class="rec-badge rec-reject">✗ Reject</span>' };
  }
  return { badge: "" };
}

function showToast(msg, type = "error") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}
