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
  listInto("liveQuestions", []);
}

function renderLiveInsights(data) {
  text("liveStatus", data?.status || "unknown");
  listInto("liveDomains", data?.domains || []);
  listInto("liveDomainGaps", data?.domain_gaps || []);
  listInto("liveQuestions", data?.questions || []);
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

// Render Results
function renderAnalysis(data) {
  toggle("result", false);
  text("status", data.status || "unknown");
  text("message", data.message || "");
  text("summary", data.llm_summary || "");
  listInto("domains", data.domains || []);
  listInto("extractedRequirements", data.extracted_requirements || []);
  listInto("questions", data.questions || []);
  listInto("openQuestions", data.open_questions || []);
  listInto("resolvedQuestions", data.resolved_questions || []);
  
  // Item analyses
  const container = $("itemAnalyses");
  if (container) {
    container.innerHTML = "";
    (data.item_analyses || []).forEach(item => {
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML = `
        <p><strong>Requirement:</strong> ${item.requirement}</p>
        <p><span class="status-badge status-${item.status}">${item.status}</span></p>
        <p class="mt-2 text-sm">${item.message}</p>
        <p class="text-xs text-slate-500 mt-2">Questions: ${(item.questions || []).join(" | ") || "None"}</p>
      `;
      container.appendChild(card);
    });
  }

  // Capability insights
  const cap = data.capability_insights || {};
  text("complexityScore", String(cap.complexity_score ?? 0));
  text("decisionReadinessScore", String(cap.decision_readiness_score ?? 0));
  const cBar = $("complexityBar"); if (cBar) cBar.style.width = `${cap.complexity_score}%`;
  const drBar = $("decisionReadinessBar"); if (drBar) drBar.style.width = `${cap.decision_readiness_score}%`;
  
  listInto("topConcepts", cap.top_concepts || []);
  listInto("investigationActions", cap.investigation_actions || []);
  listInto("serviceImprovements", cap.service_improvements || []);
  listInto("businessOpportunities", cap.business_opportunities || []);
  listInto("stakeholderComms", cap.stakeholder_communications || []);
  
  // Tools
  const toolEl = $("toolSuggestions");
  if (toolEl) {
    toolEl.innerHTML = "";
    (cap.proprietary_tool_suggestions || []).forEach(tool => {
      const li = document.createElement("li");
      li.className = "glass-card p-4 flex items-center justify-between group";
      li.innerHTML = `
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary"><span class="material-symbols-outlined">construction</span></div>
          <div><div class="text-sm font-bold">${tool.name}</div><div class="text-xs text-slate-500">${tool.category}</div></div>
        </div>
        <div class="text-[10px] font-black text-primary bg-primary/10 px-2 py-1 rounded-full">PROPRIETARY</div>
      `;
      toolEl.appendChild(li);
    });
  }

  // Sprints
  const sprintEl = $("sprintPlan");
  if (sprintEl) {
    sprintEl.innerHTML = "";
    (cap.sprint_plan || []).forEach((sprint, idx) => {
      const card = document.createElement("article");
      card.className = "sprint-card";
      card.innerHTML = `
        <div class="flex justify-between items-center mb-2">
          <span class="text-xs font-black text-primary uppercase">Sprint ${sprint.number || idx+1}</span>
          <span class="text-[10px] bg-slate-100 dark:bg-slate-800 px-2 rounded">${sprint.timeline || "2W"}</span>
        </div>
        <h4 class="text-sm font-bold mb-1">${sprint.goal || sprint.focus}</h4>
        <ul class="text-xs space-y-1">
          ${(sprint.tasks || []).map(t => `<li>\u2022 ${typeof t === 'string' ? t : t.task}</li>`).join("")}
        </ul>
      `;
      sprintEl.appendChild(sprintEl.appendChild(card));
    });
  }
}

async function analyzeStandalone() {
  console.log("Analyze Standalone Triggered");
  const textVal = val("requirementText");
  if (!textVal) throw new Error("Enter requirement text.");
  setError("");
  const res = await fetch(`${getBaseUrl()}/analyze`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ text: textVal }),
  });
  if (!res.ok) throw new Error(`Analysis failed (${res.status})`);
  const data = await res.json();
  renderAnalysis(data);
}

// DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM Loaded. Indexing elements and attaching listeners...");
  
  // Indicators
  const indicator = document.createElement("div");
  indicator.id = "scriptStatusIndicator";
  indicator.textContent = "AI Engine Active";
  indicator.style.cssText = "position:fixed; bottom:10px; right:10px; background:#0d59f2; color:white; padding:4px 8px; border-radius:4px; font-size:10px; z-index:9999;";
  document.body.appendChild(indicator);

  // Wire events
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

  wire("analyzeBtn", "click", analyzeStandalone);

  const reqInput = $("requirementText");
  if (reqInput) {
    reqInput.addEventListener("input", () => {
      renderLiveRequirements();
      scheduleLiveAnalysis();
    });
  }

  // Bootstrap initial UI
  renderLiveRequirements();
  resetLiveInsights();
  console.log("Bootstrap complete.");
});
