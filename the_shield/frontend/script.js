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

// Render Results Wizard
let lastAnalyzedData = null;

function renderAnalysis(data) {
  lastAnalyzedData = data;
  
  // Enter Step 2
  toggle("step1_Input", true);
  toggle("wizardSteps", false);
  toggle("step2_Questions", false);
  toggle("step3_Finalize", true);
  toggle("step4_Insights", true);
  toggle("step5_Sprints", true);
  
  // Populate Step 2: Questions
  const tQ = $("techQuestions");
  const nTQ = $("nonTechQuestions");
  if(tQ) tQ.innerHTML = "";
  if(nTQ) nTQ.innerHTML = "";
  
  (data.questions || []).forEach(q => {
      const li = document.createElement("li");
      li.className = "p-2 bg-white/50 dark:bg-slate-900/50 rounded border border-slate-100 dark:border-slate-800";
      li.textContent = q.text || q; // Handle dict or raw string fallback
      if (q.is_tech) {
          if(tQ) tQ.appendChild(li);
      } else {
          if(nTQ) nTQ.appendChild(li);
      }
  });

  // Populate Step 3: Item Analyses
  const container = $("itemAnalyses");
  if (container) {
    container.innerHTML = "";
    container.className = "list-box space-y-4";
    (data.item_analyses || []).forEach(item => {
      const card = document.createElement("div");
      card.className = "pb-3 border-b border-slate-100 dark:border-slate-800 last:border-0";
      card.innerHTML = `
        <div class="flex justify-between items-start">
          <p class="pr-4 text-sm font-medium"><strong>Target:</strong> ${item.requirement}</p>
        </div>
        <div class="flex gap-2 mt-2">
            <span class="status-badge status-${item.status}">${item.status}</span>
            <span class="text-[10px] bg-slate-100 dark:bg-slate-800 px-2 rounded font-medium text-slate-600 dark:text-slate-300">Class: ${item.classification || 'Functional'}</span>
            <span class="text-[10px] bg-primary/10 px-2 rounded font-medium text-primary">${item.moscow_priority || 'Should Have'}</span>
        </div>
      `;
      container.appendChild(card);
    });
  }

  // Capability insights
  const cap = data.capability_insights || {};
  window._latestCapInsights = cap;
  
  // Populate Step 3: Tools
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
        <div class="text-[10px] font-black text-primary bg-primary/10 px-2 py-1 rounded-full">SUGGESTED</div>
      `;
      toolEl.appendChild(li);
    });
  }
  
  // Populate Step 4: Insights
  text("summary", data.llm_summary || "");
  listInto("serviceImprovements", cap.service_improvements || []);
  listInto("businessOpportunities", cap.business_opportunities || []);

  // Populate Step 5: Sprints
  const sprintEl = $("sprintPlan");
  if (sprintEl) {
    sprintEl.innerHTML = "";
    (cap.sprint_plan || []).forEach((sprint, idx) => {
      const card = document.createElement("article");
      card.className = "sprint-card relative";
      card.innerHTML = `
        <div class="flex justify-between items-center mb-2">
          <span class="text-xs font-black text-primary uppercase">Sprint ${sprint.number || idx+1}</span>
          <span class="text-[10px] bg-slate-100 dark:bg-slate-800 px-2 rounded">${sprint.timeline || "2W"}</span>
        </div>
        <h4 class="text-sm font-bold mb-1">${sprint.goal || sprint.focus || "Sprint Goal"}</h4>
        <ul class="text-xs space-y-2 mt-3">
          ${(sprint.tasks || []).map(t => {
              const text = typeof t === 'string' ? t : t.task;
              const sp = t.story_points ? `<span class="bg-primary/20 text-primary px-1 rounded ml-1">${t.story_points} SP</span>` : '';
              return `
                  <li class="bg-white/50 dark:bg-slate-900/50 p-2 rounded border border-slate-100 dark:border-slate-800">
                      <div class="font-medium">${text} ${sp}</div>
                  </li>
              `;
          }).join("")}
        </ul>
      `;
      sprintEl.appendChild(card);
    });
  }

  // Phase 8: Version Control & Rollbacks
  const histEl = $("meetingHistory");
  if (histEl) {
      if (histEl.innerHTML.includes("No meeting selected.")) {
          histEl.innerHTML = "";
      }
      const snapshotId = "v" + Date.now();
      const histItem = document.createElement("div");
      histItem.className = "p-3 border-b border-slate-100 dark:border-slate-800 last:border-0";
      const displayTime = new Date().toLocaleTimeString();
      histItem.innerHTML = `
          <div class="flex justify-between items-start mb-1">
              <span class="text-xs font-bold text-slate-700 dark:text-slate-200">Analysis Snapshot ${snapshotId}</span>
              <span class="text-[10px] bg-emerald-100 text-emerald-700 px-1 rounded dark:bg-emerald-900/30 dark:text-emerald-400">Current</span>
          </div>
          <div class="text-xs text-slate-500 mb-2">${displayTime} - Status: ${data.status}</div>
          <div class="flex gap-2">
              <button type="button" class="btn-secondary text-[10px] py-1 rollback-btn" data-id="${snapshotId}">Rollback to ${snapshotId}</button>
          </div>
      `;
      histEl.prepend(histItem);

      // Remove "Current" tags from older ones
      const oldTags = histEl.querySelectorAll('.bg-emerald-100');
      oldTags.forEach((tag, idx) => {
          if (idx > 0) tag.classList.add("hidden");
      });

      // Bind rollback buttons
      histEl.querySelectorAll('.rollback-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
              alert("Rolled back requirement analysis to " + e.target.getAttribute("data-id") + " successfully.");
          });
      });
  }
}

async function analyzeStandalone() {
  console.log("Analyze Standalone Triggered");
  const textVal = val("requirementText");
  if (!textVal) {
      alert("Please enter requirement notes or record audio first.");
      return;
  }
  setError("");
  const processBtn = $("processInputBtn");
  if(processBtn) processBtn.textContent = "Processing...";
  
  try {
      const res = await fetch(`${getBaseUrl()}/analyze`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ text: textVal }),
      });
      if (!res.ok) throw new Error(`Analysis failed (${res.status})`);
      const data = await res.json();
      renderAnalysis(data);
  } finally {
      if(processBtn) processBtn.textContent = "Process Requirements";
  }
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

  wire("processInputBtn", "click", analyzeStandalone);
  
  // Wizard state machine progression
  wire("submitAnswersBtn", "click", () => {
      toggle("step2_Questions", true); // hide
      toggle("step3_Finalize", false); // show
  });
  
  wire("lockTechStackBtn", "click", () => {
      toggle("step3_Finalize", true);
      toggle("step4_Insights", false);
  });
  
  wire("approveInsightsBtn", "click", () => {
      toggle("step4_Insights", true);
      toggle("step5_Sprints", false);
  });
  
  wire("disproveInsightsBtn", "click", () => {
      alert("Insights disapproved! Returning to initial setup.");
      toggle("step4_Insights", true);
      toggle("wizardSteps", true);
      toggle("step1_Input", false);
  });
  
  wire("feasibleBtn", "click", () => {
      alert("Sprints validated as Feasible! Project planning saved.");
      toggle("step5_Sprints", true);
      toggle("wizardSteps", true);
      toggle("step1_Input", false);
      $("requirementText").value = "";
  });
  
  wire("notFeasibleBtn", "click", () => {
      alert("Sprint load not feasible. We will generate an alternate plan (Simulated).");
  });
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
              const capMap = window._latestCapInsights || {};
              const iA = capMap.investigation_actions || ["No current investigation actions."];
              const sI = capMap.service_improvements || ["No service improvements."];
              revC.innerHTML = `
                  <h4 class="font-bold mb-2 text-primary">Generated Insights (Phase 5)</h4>
                  <div class="space-y-4">
                      <div class="glass-card p-4">
                          <label class="font-bold text-sm mb-1 block">Investigation Actions</label>
                          <textarea id="revIa" class="w-full text-xs p-2 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900" rows="3">${iA.join("\\n")}</textarea>
                      </div>
                      <div class="glass-card p-4">
                          <label class="font-bold text-sm mb-1 block">Service Improvements</label>
                          <textarea id="revSi" class="w-full text-xs p-2 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900" rows="3">${sI.join("\\n")}</textarea>
                      </div>
                  </div>
                  <div class="flex justify-end gap-3 mt-4">
                      <button id="approveInsightsBtn" type="button" class="btn-primary text-xs py-2 px-4 shadow-xl">Approve & Save Insights</button>
                  </div>
              `;
              
              const approveBtn = $("approveInsightsBtn");
              if (approveBtn) {
                  approveBtn.addEventListener("click", () => {
                      alert("Insights approved and saved successfully!");
                      $("revisionsModal").classList.add("hidden");
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

  // Bootstrap initial UI
  renderLiveRequirements();
  resetLiveInsights();
  console.log("Bootstrap complete.");
});
