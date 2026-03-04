const landingView = document.getElementById("landingView");
const appView = document.getElementById("appView");
const getStartedBtn = document.getElementById("getStartedBtn");

const apiBase = document.getElementById("apiBase");
const errorPanel = document.getElementById("error");
const resultPanel = document.getElementById("result");
const meetingHistory = document.getElementById("meetingHistory");
const liveRequirements = document.getElementById("liveRequirements");
const liveStatus = document.getElementById("liveStatus");
const liveDomains = document.getElementById("liveDomains");
const liveDomainGaps = document.getElementById("liveDomainGaps");
const liveQuestions = document.getElementById("liveQuestions");

const openLoginBtn = document.getElementById("openLoginBtn");
const switchAccountBtn = document.getElementById("switchAccountBtn");
const logoutBtn = document.getElementById("logoutBtn");
const profileBox = document.getElementById("profileBox");
const profileAvatar = document.getElementById("profileAvatar");
const profileName = document.getElementById("profileName");

const loginModal = document.getElementById("loginModal");
const closeLoginBtn = document.getElementById("closeLoginBtn");
const registerBtn = document.getElementById("registerBtn");
const loginBtn = document.getElementById("loginBtn");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const loginError = document.getElementById("loginError");

const meetingTitle = document.getElementById("meetingTitle");
const meetingSelect = document.getElementById("meetingSelect");
const createMeetingBtn = document.getElementById("createMeetingBtn");
const refreshMeetingsBtn = document.getElementById("refreshMeetingsBtn");
const uploadPdfBtn = document.getElementById("uploadPdfBtn");
const minutesPdf = document.getElementById("minutesPdf");
const downloadTranscriptBtn = document.getElementById("downloadTranscriptBtn");

const requirementText = document.getElementById("requirementText");
const analyzeBtn = document.getElementById("analyzeBtn");
const analyzeMeetingBtn = document.getElementById("analyzeMeetingBtn");

const autoSpeakerToggle = document.getElementById("autoSpeakerToggle");
const audioAsPrimary = document.getElementById("audioAsPrimary");
const speakerName = document.getElementById("speakerName");
const speakerSelect = document.getElementById("speakerSelect");
const addSpeakerBtn = document.getElementById("addSpeakerBtn");
const audioStartBtn = document.getElementById("audioStartBtn");
const audioStopBtn = document.getElementById("audioStopBtn");
const audioStatus = document.getElementById("audioStatus");
const detectedSpeaker = document.getElementById("detectedSpeaker");
const transcriptPreview = document.getElementById("transcriptPreview");
const speakerSegmentsList = document.getElementById("speakerSegments");

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

function getBaseUrl() {
  return apiBase.value.trim().replace(/\/$/, "") || "http://127.0.0.1:8000";
}

function authHeaders(includeJson = true) {
  const headers = {};
  if (includeJson) {
    headers["Content-Type"] = "application/json";
  }
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }
  return headers;
}

function setError(message) {
  if (!message) {
    errorPanel.classList.add("hidden");
    return;
  }
  errorPanel.textContent = message;
  errorPanel.classList.remove("hidden");
}

function setLoginError(message) {
  if (!message) {
    loginError.classList.add("hidden");
    loginError.textContent = "";
    return;
  }
  loginError.textContent = message;
  loginError.classList.remove("hidden");
}

function listInto(elementId, items) {
  const el = document.getElementById(elementId);
  el.innerHTML = "";
  if (!items || !items.length) {
    const li = document.createElement("li");
    li.textContent = "None";
    el.appendChild(li);
    return;
  }
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    el.appendChild(li);
  });
}

function extractRequirementsFromText(rawText) {
  const text = (rawText || "").trim();
  if (!text) {
    return [];
  }

  const stripBullet = (line) =>
    line
      .replace(/^\s*(?:[-*•]|\d+[\).\-\:])\s+/, "")
      .replace(/\s+/g, " ")
      .trim();

  let segments = [];
  const lines = text
    .split(/\r?\n/)
    .map((line) => stripBullet(line))
    .filter(Boolean);

  if (lines.length > 1) {
    segments = lines;
  } else {
    segments = text
      .split(/(?<=[.!?])\s+/)
      .map((part) => stripBullet(part))
      .filter(Boolean);
  }

  const result = [];
  const seen = new Set();
  segments.forEach((item) => {
    const key = item.toLowerCase();
    if (item.length >= 3 && !seen.has(key)) {
      seen.add(key);
      result.push(item);
    }
  });
  return result;
}

function renderLiveRequirements() {
  const extracted = extractRequirementsFromText(liveSourceText());
  liveRequirements.innerHTML = "";
  if (!extracted.length) {
    const li = document.createElement("li");
    li.textContent = "No requirement detected yet.";
    liveRequirements.appendChild(li);
    return;
  }
  extracted.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    liveRequirements.appendChild(li);
  });
}

function liveSourceText() {
  const typedText = requirementText.value.trim();
  const audioText = currentSegments.map((segment) => `${segment.speaker}: ${segment.text}`).join("\n").trim();
  if (audioAsPrimary.checked) {
    return audioText || typedText;
  }
  return [typedText, audioText].filter(Boolean).join("\n");
}

function resetLiveInsights(message = "Waiting for input...") {
  liveStatus.textContent = message;
  listInto("liveDomains", []);
  listInto("liveDomainGaps", []);
  listInto("liveQuestions", []);
}

function renderLiveInsights(data) {
  liveStatus.textContent = data?.status || "unknown";
  listInto("liveDomains", data?.domains || []);
  listInto("liveDomainGaps", data?.domain_gaps || []);
  listInto("liveQuestions", data?.questions || []);
}

function scheduleLiveAnalysis() {
  if (liveAnalysisTimer) {
    clearTimeout(liveAnalysisTimer);
  }
  liveAnalysisTimer = setTimeout(() => {
    requestLiveAnalysis();
  }, 550);
}

async function requestLiveAnalysis() {
  const text = liveSourceText();
  if (!text || text.length < 3) {
    resetLiveInsights("Waiting for input...");
    return;
  }

  if (liveAnalysisController) {
    liveAnalysisController.abort();
  }
  liveAnalysisController = new AbortController();
  const seq = ++liveAnalysisSeq;

  try {
    const response = await fetch(`${getBaseUrl()}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
      signal: liveAnalysisController.signal,
    });
    if (!response.ok) {
      if (response.status === 401) {
        resetLiveInsights("Login required for live analysis.");
        return;
      }
      resetLiveInsights(`Live analysis unavailable (${response.status}).`);
      return;
    }
    const data = await response.json();
    if (seq !== liveAnalysisSeq) {
      return;
    }
    renderLiveInsights(data);
  } catch (error) {
    if (error?.name === "AbortError") {
      return;
    }
    resetLiveInsights("Live analysis unavailable.");
  }
}

function renderItemAnalyses(items) {
  const container = document.getElementById("itemAnalyses");
  container.innerHTML = "";
  if (!items || !items.length) {
    container.textContent = "No item-level analysis available.";
    return;
  }
  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "card";

    const requirement = document.createElement("p");
    requirement.textContent = `Requirement: ${item.requirement}`;

    const badge = document.createElement("span");
    badge.className = `status-badge status-${item.status}`;
    badge.textContent = item.status;

    const badgeWrap = document.createElement("p");
    badgeWrap.appendChild(badge);

    const msg = document.createElement("p");
    msg.textContent = item.message;

    const qs = document.createElement("p");
    qs.textContent = `Questions: ${(item.questions || []).join(" | ") || "None"}`;

    card.appendChild(requirement);
    card.appendChild(badgeWrap);
    card.appendChild(msg);
    card.appendChild(qs);
    container.appendChild(card);
  });
}

function renderAnalysis(data) {
  resultPanel.classList.remove("hidden");
  document.getElementById("status").textContent = data.status || "unknown";
  document.getElementById("message").textContent = data.message || "";
  document.getElementById("summary").textContent = data.llm_summary || "";
  listInto("domains", data.domains || []);
  listInto("extractedRequirements", data.extracted_requirements || []);
  listInto("questions", data.questions || []);
  listInto("openQuestions", data.open_questions || []);
  listInto("resolvedQuestions", data.resolved_questions || []);
  renderItemAnalyses(data.item_analyses || []);

  const capability = data.capability_insights || {};
  document.getElementById("complexityScore").textContent = String(capability.complexity_score ?? 0);
  document.getElementById("decisionReadinessScore").textContent = String(
    capability.decision_readiness_score ?? 0,
  );
  listInto("topConcepts", capability.top_concepts || []);
  listInto("investigationActions", capability.investigation_actions || []);
  listInto("serviceImprovements", capability.service_improvements || []);
  listInto("businessOpportunities", capability.business_opportunities || []);
  listInto("stakeholderComms", capability.stakeholder_communications || []);
  listInto("visualRecommendations", capability.visualization_recommendations || []);
}

function renderMeetingHistory(detail) {
  meetingHistory.innerHTML = "";
  const blocks = [];

  blocks.push([
    "Summary",
    [
      `Title: ${detail.title}`,
      `Meeting ID: ${detail.id}`,
      `Created: ${new Date(detail.created_at).toLocaleString()}`,
      `Updated: ${new Date(detail.updated_at).toLocaleString()}`,
      `Domains: ${(detail.domains || []).join(", ") || "None"}`,
    ],
  ]);

  blocks.push([
    "Open Questions",
    (detail.open_questions || []).length
      ? detail.open_questions.map((q, i) => `${i + 1}. ${q}`)
      : ["None"],
  ]);

  blocks.push([
    "Resolved Questions",
    (detail.resolved_questions || []).length
      ? detail.resolved_questions.map((q, i) => `${i + 1}. ${q}`)
      : ["None"],
  ]);

  const recentMinutes = (detail.minutes || [])
    .slice(-3)
    .reverse()
    .map((m) => {
      const label = m.filename ? `${m.source} (${m.filename})` : m.source;
      return `[${new Date(m.created_at).toLocaleString()}] ${label}`;
    });
  blocks.push(["Recent Minutes", recentMinutes.length ? recentMinutes : ["None"]]);

  const recentAnalyses = (detail.analysis_history || [])
    .slice(-5)
    .reverse()
    .map((a) => `[${new Date(a.created_at).toLocaleString()}] ${a.analysis?.status || "unknown"}`);
  blocks.push(["Recent Analyses", recentAnalyses.length ? recentAnalyses : ["None"]]);

  blocks.forEach(([title, lines]) => {
    const wrapper = document.createElement("div");
    wrapper.className = "history-block";
    const heading = document.createElement("h3");
    heading.textContent = title;
    const body = document.createElement("pre");
    body.textContent = lines.join("\n");
    wrapper.appendChild(heading);
    wrapper.appendChild(body);
    meetingHistory.appendChild(wrapper);
  });
}

function initials(name) {
  if (!name) {
    return "U";
  }
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

function updateSessionUI() {
  const loggedIn = Boolean(authToken && currentUsername);
  openLoginBtn.classList.toggle("hidden", loggedIn);
  switchAccountBtn.classList.toggle("hidden", !loggedIn);
  profileBox.classList.toggle("hidden", !loggedIn);
  profileName.textContent = loggedIn ? currentUsername : "";
  profileAvatar.textContent = loggedIn ? initials(currentUsername) : "U";
}

function selectedMeetingId() {
  return meetingSelect.value || "";
}

async function fetchJson(path, options = {}) {
  const response = await fetch(`${getBaseUrl()}${path}`, options);
  if (!response.ok) {
    let detail = "";
    try {
      const errBody = await response.json();
      detail = errBody.detail || JSON.stringify(errBody);
    } catch (_) {
      detail = response.statusText;
    }
    if (response.status === 401) {
      logout(false);
      openLoginModal();
      throw new Error("401 Unauthorized. Please login again.");
    }
    throw new Error(`${response.status} ${detail}`);
  }
  return response.json();
}

function openLoginModal() {
  setLoginError("");
  loginModal.classList.remove("hidden");
}

function closeLoginModal() {
  loginModal.classList.add("hidden");
}

async function register() {
  const username = usernameInput.value.trim().toLowerCase();
  const password = passwordInput.value.trim();
  if (username.length < 3) {
    throw new Error("Username must be at least 3 characters.");
  }
  if (password.length < 6) {
    throw new Error("Password must be at least 6 characters.");
  }
  const availability = await fetchJson(
    `/auth/availability?username=${encodeURIComponent(username)}`,
    { method: "GET" },
  );
  if (!availability.available) {
    throw new Error("Username already exists. Try a different username.");
  }
  const data = await fetchJson("/auth/register", {
    method: "POST",
    headers: authHeaders(true),
    body: JSON.stringify({ username, password }),
  });
  authToken = data.access_token;
  currentUsername = data.username;
  localStorage.setItem("shield_token", authToken);
  localStorage.setItem("shield_user", currentUsername);
  updateSessionUI();
}

async function login() {
  const username = usernameInput.value.trim().toLowerCase();
  const password = passwordInput.value.trim();
  if (username.length < 3) {
    throw new Error("Enter a valid username.");
  }
  if (!password) {
    throw new Error("Enter password.");
  }
  const data = await fetchJson("/auth/login", {
    method: "POST",
    headers: authHeaders(true),
    body: JSON.stringify({ username, password }),
  });
  authToken = data.access_token;
  currentUsername = data.username;
  localStorage.setItem("shield_token", authToken);
  localStorage.setItem("shield_user", currentUsername);
  updateSessionUI();
}

async function serverLogout() {
  try {
    await fetch(`${getBaseUrl()}/auth/logout`, {
      method: "POST",
      headers: authHeaders(false),
    });
  } catch (_) {
    // Ignore network errors during logout cleanup.
  }
}

function logout(triggerServer = true) {
  if (triggerServer && authToken) {
    serverLogout();
  }
  authToken = "";
  currentUsername = "";
  localStorage.removeItem("shield_token");
  localStorage.removeItem("shield_user");
  meetings = [];
  meetingSelect.innerHTML = "";
  meetingHistory.innerHTML = "<p>No meeting selected.</p>";
  resetLiveInsights();
  setLoginError("");
  updateSessionUI();
}

async function loadMeetings() {
  if (!authToken) {
    meetings = [];
    meetingSelect.innerHTML = "";
    return;
  }
  meetings = await fetchJson("/meetings", {
    method: "GET",
    headers: authHeaders(false),
  });
  meetingSelect.innerHTML = "";
  meetings.forEach((meeting) => {
    const option = document.createElement("option");
    option.value = meeting.id;
    option.textContent = `${meeting.title} (${new Date(meeting.updated_at).toLocaleString()})`;
    meetingSelect.appendChild(option);
  });
  if (meetings.length) {
    await loadMeetingDetail(meetings[0].id);
  } else {
    meetingHistory.innerHTML = "<p>No meeting records yet.</p>";
  }
}

async function createMeeting() {
  const title = meetingTitle.value.trim();
  if (!title) {
    throw new Error("Enter meeting title.");
  }
  await fetchJson("/meetings", {
    method: "POST",
    headers: authHeaders(true),
    body: JSON.stringify({ title }),
  });
  meetingTitle.value = "";
  await loadMeetings();
}

async function loadMeetingDetail(meetingId) {
  if (!meetingId) {
    meetingHistory.innerHTML = "<p>No meeting selected.</p>";
    return;
  }
  const detail = await fetchJson(`/meetings/${meetingId}`, {
    method: "GET",
    headers: authHeaders(false),
  });
  renderMeetingHistory(detail);
}

async function uploadPdf() {
  const meetingId = selectedMeetingId();
  if (!meetingId) {
    throw new Error("Select meeting first.");
  }
  const file = minutesPdf.files?.[0];
  if (!file) {
    return;
  }
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${getBaseUrl()}/meetings/${meetingId}/minutes/pdf`, {
    method: "POST",
    headers: authHeaders(false),
    body: formData,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Upload failed: ${response.status}`);
  }
  minutesPdf.value = "";
  await loadMeetingDetail(meetingId);
}

async function downloadTranscript() {
  const meetingId = selectedMeetingId();
  if (!meetingId) {
    throw new Error("Select meeting first.");
  }
  const response = await fetch(`${getBaseUrl()}/meetings/${meetingId}/transcript`, {
    method: "GET",
    headers: authHeaders(false),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Download failed: ${response.status}`);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `meeting-${meetingId}.txt`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

async function analyzeStandalone() {
  const text = requirementText.value.trim();
  if (!text) {
    throw new Error("Enter requirement text.");
  }
  const data = await fetchJson("/analyze", {
    method: "POST",
    headers: authHeaders(true),
    body: JSON.stringify({ text }),
  });
  renderAnalysis(data);
}

function renderSegments() {
  speakerSegmentsList.innerHTML = "";
  if (!currentSegments.length) {
    const li = document.createElement("li");
    li.textContent = "No speaker segments captured.";
    speakerSegmentsList.appendChild(li);
    return;
  }
  currentSegments.forEach((segment) => {
    const li = document.createElement("li");
    li.textContent = `${segment.speaker}: ${segment.text}`;
    speakerSegmentsList.appendChild(li);
  });
}

function renderAudioTranscriptPreview(interimText = "") {
  const historyText = audioTranscriptLines.join("\n");
  const composed = [historyText, interimText.trim()].filter(Boolean).join("\n");
  transcriptPreview.textContent = composed || "No transcript yet.";
}

function upsertSpeakerOption(name) {
  const trimmed = (name || "").trim();
  if (!trimmed) {
    return;
  }
  const exists = [...speakerSelect.options].some((option) => option.value === trimmed);
  if (!exists) {
    const option = document.createElement("option");
    option.value = trimmed;
    option.textContent = trimmed;
    speakerSelect.appendChild(option);
  }
  speakerSelect.value = trimmed;
}

function addSpeaker() {
  const name = speakerName.value.trim();
  if (!name) {
    throw new Error("Enter speaker name.");
  }
  upsertSpeakerOption(name);
  speakerName.value = "";
}

function cosineSimilarity(a, b) {
  if (!a || !b || a.length !== b.length) {
    return -1;
  }
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i += 1) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  if (!normA || !normB) {
    return -1;
  }
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

function euclideanDistance(a, b) {
  if (!a || !b || a.length !== b.length) {
    return 1;
  }
  let sum = 0;
  for (let i = 0; i < a.length; i += 1) {
    const d = a[i] - b[i];
    sum += d * d;
  }
  return Math.sqrt(sum);
}

function averageSignature(samples) {
  if (!samples || !samples.length) {
    return null;
  }
  const len = samples[0].length;
  const avg = new Array(len).fill(0);
  for (const sample of samples) {
    for (let i = 0; i < len; i += 1) {
      avg[i] += sample[i];
    }
  }
  for (let i = 0; i < len; i += 1) {
    avg[i] /= samples.length;
  }
  return avg;
}

function startVoiceSampling(stream) {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) {
    return;
  }
  voiceCapture.context = new AudioContextClass();
  voiceCapture.source = voiceCapture.context.createMediaStreamSource(stream);
  voiceCapture.analyser = voiceCapture.context.createAnalyser();
  voiceCapture.analyser.fftSize = 1024;
  voiceCapture.source.connect(voiceCapture.analyser);
  voiceCapture.samples = [];
  voiceCapture.recentSamples = [];
  voiceCapture.lastSignature = null;
  if (voiceCapture.context.state === "suspended") {
    voiceCapture.context.resume().catch(() => {});
  }

  const freqData = new Uint8Array(voiceCapture.analyser.frequencyBinCount);
  voiceCapture.timer = setInterval(() => {
    if (!voiceCapture.analyser) {
      return;
    }
    voiceCapture.analyser.getByteFrequencyData(freqData);
    let total = 0;
    let weighted = 0;
    let low = 0;
    let mid = 0;
    let high = 0;
    for (let i = 1; i < freqData.length; i += 1) {
      const mag = freqData[i];
      total += mag;
      weighted += i * mag;
      if (i < freqData.length / 6) {
        low += mag;
      } else if (i < freqData.length / 3) {
        mid += mag;
      } else {
        high += mag;
      }
    }
    if (!total) {
      return;
    }

    const centroidNorm = weighted / (total * freqData.length);
    let cumulative = 0;
    let rolloffIndex = 0;
    const threshold = total * 0.85;
    for (let i = 0; i < freqData.length; i += 1) {
      cumulative += freqData[i];
      if (cumulative >= threshold) {
        rolloffIndex = i;
        break;
      }
    }
    const rolloffNorm = rolloffIndex / freqData.length;
    const signature = [
      centroidNorm,
      rolloffNorm,
      low / total,
      mid / total,
      high / total,
    ];
    voiceCapture.samples.push(signature);
    voiceCapture.recentSamples.push(signature);
    if (voiceCapture.recentSamples.length > 12) {
      voiceCapture.recentSamples.shift();
    }
    voiceCapture.lastSignature = signature;
  }, 120);
}

async function beginAudioCapture() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    voiceCapture.stream = stream;
    startVoiceSampling(stream);
  } catch (_) {
    // Best effort only for signature extraction.
  }
}

async function endAudioCapture() {
  if (voiceCapture.timer) {
    clearInterval(voiceCapture.timer);
    voiceCapture.timer = null;
  }
  if (voiceCapture.stream) {
    voiceCapture.stream.getTracks().forEach((track) => track.stop());
    voiceCapture.stream = null;
  }
  if (voiceCapture.context) {
    await voiceCapture.context.close().catch(() => {});
  }
  voiceCapture.context = null;
  voiceCapture.analyser = null;
  voiceCapture.source = null;

  if (!voiceCapture.samples.length) {
    return null;
  }
  return averageSignature(voiceCapture.samples);
}

function currentSignatureSnapshot() {
  return averageSignature(voiceCapture.recentSamples) || voiceCapture.lastSignature;
}

function assignAutoSpeaker(signatureVector) {
  if (!Array.isArray(signatureVector)) {
    const fallback = `Speaker ${speakerProfiles.length + 1}`;
    upsertSpeakerOption(fallback);
    detectedSpeaker.textContent = fallback;
    return fallback;
  }

  if (!speakerProfiles.length) {
    const label = "Speaker 1";
    speakerProfiles.push({ label, signature: signatureVector, count: 1 });
    upsertSpeakerOption(label);
    detectedSpeaker.textContent = `${label} (new)`;
    return label;
  }

  let best = speakerProfiles[0];
  let bestScore = cosineSimilarity(signatureVector, best.signature);
  let bestDistance = euclideanDistance(signatureVector, best.signature);
  for (const profile of speakerProfiles) {
    const score = cosineSimilarity(signatureVector, profile.signature);
    const dist = euclideanDistance(signatureVector, profile.signature);
    if (score > bestScore || (Math.abs(score - bestScore) < 0.01 && dist < bestDistance)) {
      bestScore = score;
      bestDistance = dist;
      best = profile;
    }
  }

  const sameSpeaker =
    (bestScore >= 0.97 && bestDistance <= 0.11) ||
    (bestScore >= 0.94 && bestDistance <= 0.075) ||
    (bestScore >= 0.9 && bestDistance <= 0.05);

  if (!sameSpeaker) {
    const label = `Speaker ${speakerProfiles.length + 1}`;
    speakerProfiles.push({ label, signature: signatureVector, count: 1 });
    upsertSpeakerOption(label);
    detectedSpeaker.textContent = `${label} (new)`;
    return label;
  }

  const updatedCount = best.count + 1;
  const merged = [];
  for (let i = 0; i < best.signature.length; i += 1) {
    merged.push((best.signature[i] * best.count + signatureVector[i]) / updatedCount);
  }
  best.signature = merged;
  best.count = updatedCount;
  upsertSpeakerOption(best.label);
  detectedSpeaker.textContent = `${best.label} (confidence ${(bestScore * 100).toFixed(0)}%, d=${bestDistance.toFixed(3)})`;
  return best.label;
}

function resolveSpeakerLabel(signature) {
  if (autoSpeakerToggle.checked) {
    return assignAutoSpeaker(signature);
  }
  const manual = speakerSelect.value || speakerName.value.trim();
  if (!manual) {
    detectedSpeaker.textContent = "Speaker";
    return "Speaker";
  }
  upsertSpeakerOption(manual);
  detectedSpeaker.textContent = manual;
  return manual;
}

async function analyzeMeeting() {
  const meetingId = selectedMeetingId();
  if (!meetingId) {
    throw new Error("Select meeting first.");
  }
  const typedText = requirementText.value.trim();
  const audioText = currentSegments.map((segment) => `${segment.speaker}: ${segment.text}`).join("\n").trim();
  let text = typedText;
  if (audioAsPrimary.checked) {
    text = audioText || typedText;
  } else {
    text = [typedText, audioText].filter(Boolean).join("\n");
  }
  if (!text && !currentSegments.length) {
    throw new Error("No meeting content found. Record audio or type notes.");
  }
  const payload = {
    text,
    speaker_segments: currentSegments,
  };
  const data = await fetchJson(`/meetings/${meetingId}/analyze`, {
    method: "POST",
    headers: authHeaders(true),
    body: JSON.stringify(payload),
  });
  renderAnalysis(data);
  await loadMeetingDetail(meetingId);
}

function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    audioStatus.textContent = "Not supported in this browser.";
    audioStartBtn.disabled = true;
    audioStopBtn.disabled = true;
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.continuous = true;
  recognition.interimResults = true;

  recognition.onstart = async () => {
    audioStatus.textContent = "Listening...";
    audioStartBtn.disabled = true;
    audioStopBtn.disabled = false;
    await beginAudioCapture();
  };

  recognition.onresult = (event) => {
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const result = event.results[i];
      if (result.isFinal) {
        const utterance = (result[0].transcript || "").trim();
        if (utterance) {
          const signature = currentSignatureSnapshot();
          const speaker = resolveSpeakerLabel(signature);
          currentSegments.push({ speaker, text: utterance });
          audioTranscriptLines.push(`${speaker}: ${utterance}`);
          renderSegments();
          if (!audioAsPrimary.checked) {
            const existing = requirementText.value.trim();
            requirementText.value = existing
              ? `${existing}\n${speaker}: ${utterance}`
              : `${speaker}: ${utterance}`;
          }
          renderLiveRequirements();
          scheduleLiveAnalysis();
        }
      } else {
        interim += result[0].transcript;
      }
    }
    finalTranscript = interim;
    renderAudioTranscriptPreview(interim);
  };

  recognition.onerror = (event) => {
    audioStatus.textContent = `Error: ${event.error}`;
  };

  recognition.onend = async () => {
    audioStatus.textContent = "Stopped";
    audioStartBtn.disabled = false;
    audioStopBtn.disabled = true;

    await endAudioCapture();
    finalTranscript = "";
    renderAudioTranscriptPreview();
  };
}

getStartedBtn.addEventListener("click", () => {
  landingView.classList.add("hidden");
  appView.classList.remove("hidden");
});

openLoginBtn.addEventListener("click", () => {
  setError("");
  openLoginModal();
});

switchAccountBtn.addEventListener("click", () => {
  setError("");
  usernameInput.value = "";
  passwordInput.value = "";
  openLoginModal();
});

closeLoginBtn.addEventListener("click", () => {
  closeLoginModal();
});

loginModal.addEventListener("click", (event) => {
  if (event.target === loginModal) {
    closeLoginModal();
  }
});

registerBtn.addEventListener("click", async () => {
  setError("");
  setLoginError("");
  try {
    await register();
    await loadMeetings();
    closeLoginModal();
  } catch (error) {
    setLoginError(error.message);
  }
});

loginBtn.addEventListener("click", async () => {
  setError("");
  setLoginError("");
  try {
    await login();
    await loadMeetings();
    closeLoginModal();
  } catch (error) {
    setLoginError(error.message);
  }
});

logoutBtn.addEventListener("click", () => {
  logout(true);
});

createMeetingBtn.addEventListener("click", async () => {
  setError("");
  try {
    await createMeeting();
  } catch (error) {
    setError(error.message);
  }
});

refreshMeetingsBtn.addEventListener("click", async () => {
  setError("");
  try {
    await loadMeetings();
  } catch (error) {
    setError(error.message);
  }
});

meetingSelect.addEventListener("change", async () => {
  setError("");
  try {
    await loadMeetingDetail(selectedMeetingId());
  } catch (error) {
    setError(error.message);
  }
});

uploadPdfBtn.addEventListener("click", async () => {
  setError("");
  try {
    await uploadPdf();
  } catch (error) {
    setError(error.message);
  }
});

downloadTranscriptBtn.addEventListener("click", async () => {
  setError("");
  try {
    await downloadTranscript();
  } catch (error) {
    setError(error.message);
  }
});

analyzeBtn.addEventListener("click", async () => {
  setError("");
  try {
    await analyzeStandalone();
  } catch (error) {
    setError(error.message);
  }
});

analyzeMeetingBtn.addEventListener("click", async () => {
  setError("");
  try {
    await analyzeMeeting();
  } catch (error) {
    setError(error.message);
  }
});

addSpeakerBtn.addEventListener("click", () => {
  setError("");
  try {
    addSpeaker();
  } catch (error) {
    setError(error.message);
  }
});

audioStartBtn.addEventListener("click", () => {
  setError("");
  if (!recognition) {
    return;
  }
  if (!autoSpeakerToggle.checked && !speakerSelect.value && !speakerName.value.trim()) {
    setError("Provide a speaker name or enable auto speaker detection.");
    return;
  }
  finalTranscript = "";
  detectedSpeaker.textContent = "Detecting...";
  renderAudioTranscriptPreview();
  recognition.start();
});

audioStopBtn.addEventListener("click", () => {
  if (recognition) {
    recognition.stop();
  }
});

requirementText.addEventListener("input", () => {
  if (liveRequirementTimer) {
    clearTimeout(liveRequirementTimer);
  }
  liveRequirementTimer = setTimeout(() => {
    renderLiveRequirements();
    scheduleLiveAnalysis();
  }, 120);
});

audioAsPrimary.addEventListener("change", () => {
  renderLiveRequirements();
  scheduleLiveAnalysis();
});

function bootstrap() {
  updateSessionUI();
  upsertSpeakerOption("Speaker 1");
  initSpeechRecognition();
  renderSegments();
  renderLiveRequirements();
  resetLiveInsights();
  detectedSpeaker.textContent = "None";
  renderAudioTranscriptPreview();
  scheduleLiveAnalysis();

  if (authToken) {
    loadMeetings().catch((error) => setError(error.message));
  }
}

bootstrap();
