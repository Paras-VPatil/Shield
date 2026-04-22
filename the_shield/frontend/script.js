// Defensive RequiMind AI Frontend Script
console.log("RequiMind Script Loading...");

// Global state
let authToken = localStorage.getItem("shield_token") || "";
let currentUsername = localStorage.getItem("shield_user") || "";
let meetings = [];
let currentSegments = [];
let recognition = null;
let finalTranscript = "";
let speakerProfiles = [];
let liveRequirementTimer = null;
let audioTranscriptLines = [];
let liveAnalysisTimer = null;
let liveAnalysisController = null;
let liveAnalysisSeq = 0;

const voiceCapture = {
  stream: null,
  context: null,
  analyser: null,
  source: null,
  timer: null,
  samples: [],
  recentSamples: [],
  lastSignature: null,
};

// Helper: safe element selection
function $(id) {
  const el = document.getElementById(id);
  if (!el) {
    console.warn(`Element with id "${id}" not found.`);
  }
  return el;
}

// Helper: safe value/text
function val(id, value) {
  const el = $(id);
  if (!el) return "";
  if (arguments.length > 1) el.value = value;
  return (el.value || "").trim();
}

function text(id, content) {
  const el = $(id);
  if (!el) return "";
  if (arguments.length > 1) el.textContent = content;
  return el.textContent;
}

function html(id, content) {
  const el = $(id);
  if (!el) return "";
  if (arguments.length > 1) el.innerHTML = content;
  return el.innerHTML;
}

function toggle(id, isHidden) {
  const el = $(id);
  if (!el) return;
  if (isHidden) el.classList.add("hidden");
  else el.classList.remove("hidden");
}

function getBaseUrl() {
  return val("apiBase") || "http://127.0.0.1:8000";
}

function authHeaders(includeJson = true) {
  const headers = {};
  if (includeJson) headers["Content-Type"] = "application/json";
  if (authToken) headers.Authorization = `Bearer ${authToken}`;
  return headers;
}

function setError(message) {
  const err = $("error");
  if (!err) return;
  if (!message) {
    err.classList.add("hidden");
    return;
  }
  err.textContent = message;
  err.classList.remove("hidden");
}

function listInto(id, items) {
  const el = $(id);
  if (!el) return;
  el.innerHTML = "";
  if (!items || !items.length) {
    const li = document.createElement("li");
    li.textContent = "None";
    el.appendChild(li);
    return;
  }
  items.forEach(item => {
    const li = document.createElement("li");
    li.textContent = item;
    el.appendChild(li);
  });
}

// Analysis Logic
let activeJobId = null;
let pollTimer = null;

function extractRequirementsFromText(rawText) {
  const text = (rawText || "").trim();
  if (!text) return [];
  const stripBullet = line => line.replace(/^\s*(?:[-*•]|\d+[\).\-\:])\s+/, "").replace(/\s+/g, " ").trim();
  let segments = text.split(/\r?\n/).map(stripBullet).filter(Boolean);
  if (segments.length <= 1) {
    segments = text.split(/[.!?]\s+/).map(stripBullet).filter(Boolean);
  }
  const result = [];
  const seen = new Set();
  segments.forEach(item => {
    const key = item.toLowerCase();
    if (item.length >= 3 && !seen.has(key)) {
      seen.add(key);
      result.push(item);
    }
  });
  return result;
}

function liveSourceText() {
  const typedText = val("requirementText");
  const audioText = currentSegments.map(s => `${s.speaker}: ${s.text}`).join("\n").trim();
  const audioPrimary = $("audioAsPrimary");
  if (audioPrimary && audioPrimary.checked) return audioText || typedText;
  return [typedText, audioText].filter(Boolean).join("\n");
}

function renderLiveRequirements() {
  const extracted = extractRequirementsFromText(liveSourceText());
  const el = $("liveRequirements");
  if (!el) return;
  el.innerHTML = "";
  if (!extracted.length) {
    const li = document.createElement("li");
    li.textContent = "No requirement detected yet.";
    el.appendChild(li);
    return;
  }
  extracted.forEach(item => {
    const li = document.createElement("li");
    li.textContent = item;
    el.appendChild(li);
  });
}

function resetLiveInsights(msg = "Waiting for input...") {
  text("liveStatus", msg);
  listInto("liveDomains", []);
  listInto("liveDomainGaps", []);
  renderPrioritizedQuestions("liveQuestions", []);
}

function renderPrioritizedQuestions(id, questions) {
  const el = $(id);
  if (!el) return;
  el.innerHTML = "";
  if (!questions || !questions.length) {
    const li = document.createElement("li");
    li.className = "py-2 px-3 bg-slate-50 dark:bg-slate-900/50 rounded-lg text-slate-400 italic text-xs border border-dashed border-slate-200 dark:border-slate-800";
    li.textContent = "No clarification questions currently.";
    el.appendChild(li);
    return;
  }

  questions.forEach(q => {
    const qText = typeof q === 'string' ? q : q.text;
    const priority = q.priority || 3;
    const isTech = q.is_tech || false;
    
    let priorityClass = "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400";
    let priorityLabel = "Standard";
    let icon = "info";
    let borderClass = "border-slate-200 dark:border-slate-800";
    
    if (priority === 1) { 
      priorityClass = "bg-red-500 text-white shadow-lg shadow-red-500/20"; 
      priorityLabel = "Urgent / Critical"; 
      icon = "warning";
      borderClass = "border-red-500/30 ring-1 ring-red-500/10";
    }
    else if (priority === 2) { 
      priorityClass = "bg-orange-500 text-white shadow-lg shadow-orange-500/20"; 
      priorityLabel = "High Priority"; 
      icon = "priority_high";
      borderClass = "border-orange-500/30";
    }

    const li = document.createElement("li");
    li.className = `group relative p-4 rounded-2xl border ${borderClass} bg-white dark:bg-slate-900/40 hover:shadow-xl hover:translate-y-[-2px] transition-all duration-300`;
    li.innerHTML = `
      <div class="flex justify-between items-start gap-4 mb-3">
        <div class="flex gap-2 items-center">
            <span class="flex items-center justify-center h-5 w-5 rounded-full ${priorityClass}">
                <span class="material-symbols-outlined text-[12px] font-black">${icon}</span>
            </span>
            <span class="text-[10px] uppercase font-black tracking-widest ${priority === 1 ? 'text-red-500' : (priority === 2 ? 'text-orange-500' : 'text-slate-500')}">${priorityLabel}</span>
        </div>
        <div class="flex gap-1">
            ${isTech ? '<span class="text-[9px] uppercase font-bold bg-blue-500/10 text-primary px-2 py-0.5 rounded-full border border-primary/20">Technical</span>' : '<span class="text-[9px] uppercase font-bold bg-purple-500/10 text-purple-500 px-2 py-0.5 rounded-full border border-purple-500/20">Functional</span>'}
        </div>
      </div>
      <p class="text-[13px] text-slate-700 dark:text-slate-200 leading-relaxed font-semibold">${qText}</p>
      <div class="absolute right-3 bottom-3 opacity-0 group-hover:opacity-100 transition-opacity">
          <span class="material-symbols-outlined text-primary/40 text-sm">edit_note</span>
      </div>
    `;
    el.appendChild(li);
  });
}

function renderLiveInsights(data) {
  text("liveStatus", data?.status || "unknown");
  listInto("liveDomains", data?.domains || []);
  listInto("liveDomainGaps", data?.domain_gaps || []);
  renderPrioritizedQuestions("liveQuestions", data?.questions || []);
}

async function requestLiveAnalysis() {
  const textVal = liveSourceText();
  if (!textVal || textVal.length < 3) {
    resetLiveInsights();
    return;
  }
  if (liveAnalysisController) liveAnalysisController.abort();
  liveAnalysisController = new AbortController();
  const seq = ++liveAnalysisSeq;

  try {
    const response = await fetch(`${getBaseUrl()}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: textVal }),
      signal: liveAnalysisController.signal,
    });
    if (!response.ok) {
      if (response.status === 401) resetLiveInsights("Login required.");
      else resetLiveInsights(`Error (${response.status})`);
      return;
    }
    const data = await response.json();
    if (seq === liveAnalysisSeq) renderLiveInsights(data);
  } catch (e) {
    if (e.name !== "AbortError") resetLiveInsights("Live analysis unavailable.");
  }
}

function scheduleLiveAnalysis() {
  if (liveAnalysisTimer) clearTimeout(liveAnalysisTimer);
  liveAnalysisTimer = setTimeout(requestLiveAnalysis, 550);
}

// Render Results Wizard
let lastAnalyzedData = null;

function renderAnalysis(data) {
  toggle("wizardSteps", false);
  toggle("step2_Questions", false);
  
  text("summary", data.llm_summary || "Requirement analysis complete. See details below.");
  
  // Split questions by Tech vs Functional for the UI
  const questions = data.questions || [];
  const tech = questions.filter(q => q.is_tech);
  const nonTech = questions.filter(q => !q.is_tech);
  
  renderPrioritizedQuestions("techQuestions", tech);
  renderPrioritizedQuestions("nonTechQuestions", nonTech);

  // Item analyses
  const container = $("itemAnalyses");
  if (container) {
    container.innerHTML = "";
    container.className = "grid gap-4 sm:grid-cols-2";
    (data.item_analyses || []).forEach(item => {
      const card = document.createElement("div");
      card.className = "p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 hover:bg-white dark:hover:bg-slate-900 transition-all";
      card.innerHTML = `
        <p class="text-sm font-bold mb-2">${item.requirement}</p>
        <div class="flex flex-wrap gap-2">
            <span class="text-[10px] px-2 py-0.5 rounded font-black uppercase bg-primary/10 text-primary">${item.moscow_priority || 'Should Have'}</span>
            <span class="text-[10px] px-2 py-0.5 rounded font-black uppercase bg-slate-200 dark:bg-slate-800 text-slate-500">${item.classification || 'Functional'}</span>
            <span class="text-[10px] px-2 py-0.5 rounded font-black uppercase status-badge status-${item.status}">${item.status}</span>
        </div>
      `;
      container.appendChild(card);
    });
  }

  // Tools
  const toolEl = $("toolSuggestions");
  if (toolEl) {
    toolEl.innerHTML = "";
    const cap = data.capability_insights || {};
    (cap.proprietary_tool_suggestions || []).forEach(tool => {
      const li = document.createElement("li");
      li.className = "glass-card p-4 flex items-center justify-between group";
      li.innerHTML = `
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary"><span class="material-symbols-outlined">construction</span></div>
          <div><div class="text-sm font-bold">${tool.name}</div><div class="text-xs text-slate-500">${tool.category}</div></div>
        </div>
        <div class="text-[10px] font-black text-primary bg-primary/10 px-2 py-1 rounded-full">SUGGESTED</div>
      `;
      toolEl.appendChild(li);
    });
  }

  // Sprints
  const sprintEl = $("sprintPlan");
  if (sprintEl) {
    sprintEl.innerHTML = "";
    const cap = data.capability_insights || {};
    (cap.sprint_plan || []).forEach((sprint, idx) => {
      const card = document.createElement("article");
      card.className = "sprint-card relative p-5 bg-card-dark rounded-3xl border border-slate-800";
      card.innerHTML = `
        <div class="flex justify-between items-center mb-3">
          <span class="text-xs font-black text-primary uppercase">Sprint ${sprint.number || idx + 1}</span>
          <span class="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-400 font-bold">${sprint.timeline || "2W"}</span>
        </div>
        <h4 class="text-base font-bold mb-3">${sprint.goal || sprint.focus}</h4>
        <ul class="text-xs space-y-2 text-slate-400">
          ${(sprint.tasks || []).map(t => `<li class="flex gap-2"><span class="text-primary">•</span> <span>${typeof t === 'string' ? t : t.task}</span></li>`).join("")}
        </ul>
      `;
      sprintEl.appendChild(card);
    });
  }

  // Feature Insights
  const svcEl = $("serviceImprovements");
  if (svcEl) listInto("serviceImprovements", data.capability_insights?.service_improvements || []);
  const bizEl = $("businessOpportunities");
  if (bizEl) listInto("businessOpportunities", data.capability_insights?.business_opportunities || []);
}

async function startBulkAnalysis() {
  const meetingId = val("meetingSelect");
  if (!meetingId) throw new Error("Select a meeting first.");
  
  const fileInput = $("bulkFile");
  if (!fileInput.files.length) throw new Error("Please select a .txt or .csv file.");
  
  const file = fileInput.files[0];
  const content = await file.text();
  const requirements = content.split(/\r?\n/).filter(line => line.trim().length > 5);
  
  if (requirements.length === 0) throw new Error("No valid requirements found in file.");
  
  setError("");
  toggle("jobStatusBadge", false);
  toggle("jobProgressContainer", false);
  
  const res = await fetch(`${getBaseUrl()}/meetings/${meetingId}/bulk`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ requirements }),
  });
  
  if (!res.ok) throw new Error(`Bulk upload failed (${res.status})`);
  
  const job = await res.json();
  activeJobId = job.job_id;
  
  // Update UI
  text("jobProgressLabel", "Progress: 0%");
  text("jobProgressCount", `0/${job.total_count}`);
  $("jobProgressBar").style.width = "0%";
  
  pollJobStatus();
}

async function pollJobStatus() {
  if (!activeJobId) return;
  
  try {
    const res = await fetch(`${getBaseUrl()}/meetings/jobs/${activeJobId}`, {
      headers: authHeaders(),
    });
    
    if (!res.ok) {
      console.error("Polling failed");
      return;
    }
    
    const job = await res.json();
    
    // Update Progress
    text("jobProgressLabel", `Progress: ${Math.round(job.progress)}%`);
    text("jobProgressCount", `${job.processed_count}/${job.total_count}`);
    $("jobProgressBar").style.width = `${job.progress}%`;
    
    if (job.status === "completed") {
      activeJobId = null;
      toggle("jobStatusBadge", true);
      alert("Bulk analysis complete!");
      // For bulk, results are in job.result.item_analyses
      // We can trigger a full UI refresh or just show a summary
      refreshMeetings();
    } else if (job.status === "failed") {
      activeJobId = null;
      toggle("jobStatusBadge", true);
      setError(`Job failed: ${job.error}`);
    } else {
      pollTimer = setTimeout(pollJobStatus, 2000);
    }
  } catch (e) {
    console.error("Polling error", e);
  }
}

async function analyzeStandalone() {
  console.log("Analyze Standalone Triggered");
  const meetingId = val("meetingSelect");
  if (!meetingId) throw new Error("Select a meeting first.");
  
  const textVal = val("requirementText");
  if (!textVal) throw new Error("Enter requirement text.");
  
  setError("");
  const res = await fetch(`${getBaseUrl()}/meetings/${meetingId}/analyze`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ text: textVal, speaker_segments: [] }),
  });
  
  if (!res.ok) throw new Error(`Analysis failed (${res.status})`);
  const data = await res.json();
  renderAnalysis(data);
}

// Meeting Management
async function refreshMeetings() {
  const res = await fetch(`${getBaseUrl()}/meetings`, { headers: authHeaders() });
  if (!res.ok) return;
  meetings = await res.json();
  const sel = $("meetingSelect");
  if (!sel) return;
  sel.innerHTML = '<option value="">-- Choose Meeting --</option>';
  meetings.forEach(m => {
    const opt = document.createElement("option");
    opt.value = m.id;
    opt.textContent = m.title;
    sel.appendChild(opt);
  });
}

// DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM Loaded.");

  refreshMeetings();

  const wire = (id, event, fn) => {
    const el = $(id);
    if (el) el.addEventListener(event, async (e) => {
      try { await fn(e); } catch (err) {
        console.error(`Error in ${id} ${event}:`, err);
        setError(err.message);
      }
    });
  };

  wire("getStartedBtn", "click", () => {
    toggle("landingView", true);
    toggle("appView", false);
  });

  wire("processInputBtn", "click", analyzeStandalone);
  wire("bulkUploadBtn", "click", startBulkAnalysis);
  wire("refreshMeetingsBtn", "click", refreshMeetings);

  const reqInput = $("requirementText");
  if (reqInput) {
    reqInput.addEventListener("input", () => {
      renderLiveRequirements();
      scheduleLiveAnalysis();
    });
  }

  // Phase 5 Revisions UI
  const revBtn = $("viewRevisionsBtn");
  if (revBtn) {
    revBtn.addEventListener("click", () => {
      const revC = $("revisionsContent");
      if (revC) {
        revC.innerHTML = `
          <h4 class="font-bold mb-2 text-primary">Generated Insights (Phase 5)</h4>
          <div class="space-y-4">
              <div class="glass-card p-4">
                   <label class="font-bold text-sm mb-1 block">Domain Strategy</label>
                  <textarea id="revIa" class="w-full text-xs p-2 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900" rows="3">Extrapolating multi-domain architecture for large-scale requirement processing...</textarea>
              </div>
              <div class="glass-card p-4">
                  <label class="font-bold text-sm mb-1 block">Service Scaling</label>
                  <textarea id="revSi" class="w-full text-xs p-2 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900" rows="3">Optimization targeted for 100k+ requirement ingestion using asynchronous worker pools.</textarea>
              </div>
          </div>
          <div class="flex justify-end gap-3 mt-4">
              <button id="approveRevisedBtn" type="button" class="btn-primary text-xs py-2 px-4 shadow-xl">Confirm Implementation</button>
          </div>
        `;

        const approveBtn = $("approveRevisedBtn");
        if (approveBtn) {
          approveBtn.addEventListener("click", () => {
            alert("Scale architecture confirmed!");
            $("revisionsModal")?.classList.add("hidden");
          });
        }
      }
      $("revisionsModal")?.classList.remove("hidden");
    });
  }

  const closeRev = $("closeRevisionsBtn");
  if (closeRev) {
    closeRev.addEventListener("click", () => {
      $("revisionsModal")?.classList.add("hidden");
    });
  }

  console.log("Bootstrap complete.");
});
