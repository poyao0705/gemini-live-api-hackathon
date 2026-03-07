import { startAudioPlayerWorklet } from "./audio-player.js?v=20260308";
import { startStreamAudioRecorderWorklet } from "./audio-recorder.js?v=20260308";

const DEFAULT_USER_ID = "local-tester";
const DEFAULT_SOURCE = "none";
const AUTO_RECONNECT_DELAY_MS = 3000;
const urlParams = new URLSearchParams(window.location.search);
const isDebugMode = urlParams.get("debug") === "1";

const agentFeedEl = document.getElementById("agentFeed");
const wsUrlInput = document.getElementById("wsUrl");
const userIdInput = document.getElementById("userId");
const sessionIdInput = document.getElementById("sessionId");
const inputSourceSelect = document.getElementById("inputSource");
const autoReconnectCheckbox = document.getElementById("autoReconnect");
const autoEnableAudioCheckbox = document.getElementById("autoEnableAudio");
const connectButton = document.getElementById("connectButton");
const disconnectButton = document.getElementById("disconnectButton");
const startInputButton = document.getElementById("startInputButton");
const stopInputButton = document.getElementById("stopInputButton");
const enableAudioButton = document.getElementById("enableAudioButton");
const resetFeedButton = document.getElementById("resetFeedButton");
const textForm = document.getElementById("textForm");
const textPromptInput = document.getElementById("textPrompt");
const sendTextButton = document.getElementById("sendTextButton");
const connectionStateEl = document.getElementById("connectionState");
const inputStateEl = document.getElementById("inputState");
const audioOutputStateEl = document.getElementById("audioOutputState");
const sessionStateEl = document.getElementById("sessionState");
const lastEventStateEl = document.getElementById("lastEventState");
const debugOnlyElements = document.querySelectorAll(".debug-only");

let agentSocket = null;
let agentReconnectTimer = null;
let audioPlayerNode = null;
let audioPlayerContext = null;
let audioRecorderNode = null;
let audioRecorderContext = null;
let inputStream = null;
let currentAgentEvent = null;
let currentAgentText = "";
let currentTurnUsesTranscription = false;
let currentSessionId = createSessionId();
let autoSyncWebSocketUrl = true;
let manualDisconnect = false;

function createSessionId() {
  return `local-${Math.random().toString(36).slice(2, 10)}`;
}

function setStatus(element, value) {
  if (element) {
    element.textContent = value;
  }
}

function updateConnectionState(value) {
  setStatus(connectionStateEl, value);
}

function updateInputState(value) {
  setStatus(inputStateEl, value);
}

function updateAudioOutputState(value) {
  setStatus(audioOutputStateEl, value);
}

function updateSessionState() {
  const userId = userIdInput.value.trim() || DEFAULT_USER_ID;
  const sessionId = sessionIdInput.value.trim() || currentSessionId;
  setStatus(sessionStateEl, `${userId} / ${sessionId}`);
}

function updateLastEvent(value) {
  setStatus(lastEventStateEl, value);
}

function appendEvent(title, text, meta = "") {
  const event = document.createElement("div");
  event.className = "event";

  const titleEl = document.createElement("p");
  const strongEl = document.createElement("strong");
  strongEl.textContent = title;
  titleEl.appendChild(strongEl);

  const textEl = document.createElement("p");
  textEl.textContent = text;

  const metaEl = document.createElement("p");
  metaEl.className = "meta";
  metaEl.textContent = meta || new Date().toLocaleTimeString();

  event.appendChild(titleEl);
  event.appendChild(textEl);
  event.appendChild(metaEl);
  agentFeedEl.prepend(event);
  return event;
}

function setDebugVisibility() {
  for (const element of debugOnlyElements) {
    element.hidden = !isDebugMode;
  }
}

function updateEvent(event, text, meta = "") {
  const paragraphs = event.querySelectorAll("p");
  if (paragraphs[1]) {
    paragraphs[1].textContent = text;
  }
  if (paragraphs[2] && meta) {
    paragraphs[2].textContent = meta;
  }
}

function getAgentWsFromQuery() {
  const params = new URLSearchParams(window.location.search);
  const value = params.get("wss");
  return value ? value.trim() : "";
}

function buildDefaultWebSocketUrl(userId, sessionId) {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/${userId}/${sessionId}`;
}

function syncWebSocketUrlFromIdentity() {
  if (!autoSyncWebSocketUrl) {
    return;
  }

  const userId = userIdInput.value.trim() || DEFAULT_USER_ID;
  const sessionId = sessionIdInput.value.trim() || currentSessionId;
  wsUrlInput.value = buildDefaultWebSocketUrl(userId, sessionId);
}

function getAgentWebSocketUrl() {
  const queryValue = getAgentWsFromQuery() || wsUrlInput.value.trim();
  const userId = userIdInput.value.trim() || DEFAULT_USER_ID;
  const sessionId = sessionIdInput.value.trim() || currentSessionId;

  if (queryValue) {
    return queryValue
      .replaceAll("{session_id}", sessionId)
      .replaceAll("{user_id}", userId);
  }

  return buildDefaultWebSocketUrl(userId, sessionId);
}

function isValidWebSocketUrl(url) {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "ws:" || parsed.protocol === "wss:";
  } catch {
    return false;
  }
}

function base64ToArray(base64) {
  let standardBase64 = base64.replace(/-/g, "+").replace(/_/g, "/");
  while (standardBase64.length % 4) {
    standardBase64 += "=";
  }

  const binaryString = window.atob(standardBase64);
  const bytes = new Uint8Array(binaryString.length);
  for (let index = 0; index < binaryString.length; index += 1) {
    bytes[index] = binaryString.charCodeAt(index);
  }
  return bytes.buffer;
}

async function initAudioOutput() {
  if (audioPlayerNode) {
    if (audioPlayerContext?.state === "suspended") {
      await audioPlayerContext.resume();
    }
    updateAudioOutputState("ready");
    return;
  }

  [audioPlayerNode, audioPlayerContext] = await startAudioPlayerWorklet();
  if (audioPlayerContext?.state === "suspended") {
    await audioPlayerContext.resume();
  }
  updateAudioOutputState("ready");
  appendEvent("System", "Audio output ready", "local playback enabled");
}

function resetCurrentAgentEvent() {
  currentAgentEvent = null;
  currentAgentText = "";
  currentTurnUsesTranscription = false;
}

function ensureCurrentAgentEvent(initialText = "") {
  if (!currentAgentEvent) {
    currentAgentEvent = appendEvent(
      "Gemini Live Agent",
      initialText || "Listening...",
      "streaming",
    );
  }
  return currentAgentEvent;
}

function renderAgentText(text, isFinal = false, source = "text") {
  const event = ensureCurrentAgentEvent(text);
  updateEvent(event, text, isFinal ? `final ${source}` : `partial ${source}`);
  if (isFinal) {
    resetCurrentAgentEvent();
  }
}

function handleAgentEvent(message) {
  const adkEvent = JSON.parse(message.data);
  updateLastEvent(
    adkEvent.turnComplete
      ? "turn complete"
      : adkEvent.outputTranscription?.text
        ? "output transcription"
        : adkEvent.inputTranscription?.text
          ? "input transcription"
          : adkEvent.content?.parts
            ? "content"
            : "event",
  );

  if (adkEvent.turnComplete) {
    resetCurrentAgentEvent();
    return;
  }

  if (adkEvent.interrupted) {
    resetCurrentAgentEvent();
    appendEvent("System", "Agent output interrupted");
    return;
  }

  if (adkEvent.outputTranscription?.text) {
    currentTurnUsesTranscription = true;
    currentAgentText = adkEvent.outputTranscription.finished
      ? adkEvent.outputTranscription.text
      : `${currentAgentText}${adkEvent.outputTranscription.text}`;
    renderAgentText(
      currentAgentText,
      Boolean(adkEvent.outputTranscription.finished),
      "transcription",
    );
  }

  if (!adkEvent.content?.parts) {
    return;
  }

  for (const part of adkEvent.content.parts) {
    if (part.inlineData?.mimeType?.startsWith("audio/pcm") && audioPlayerNode) {
      audioPlayerNode.port.postMessage(base64ToArray(part.inlineData.data));
    }

    if (
      part.inlineData?.mimeType?.startsWith("audio/pcm") &&
      !audioPlayerNode
    ) {
      updateAudioOutputState("not enabled");
    }

    if (part.text && !currentTurnUsesTranscription) {
      currentAgentText = `${currentAgentText}${part.text}`;
      renderAgentText(currentAgentText, false, "content");
    }
  }
}

function sendTextMessage(text) {
  if (!agentSocket || agentSocket.readyState !== WebSocket.OPEN) {
    appendEvent("System", "Cannot send text while disconnected");
    return;
  }

  const payload = JSON.stringify({ type: "text", text });
  agentSocket.send(payload);
  appendEvent("You", text, "text input");
}

function sendAudioChunk(pcmData) {
  if (!agentSocket || agentSocket.readyState !== WebSocket.OPEN) {
    return;
  }

  agentSocket.send(pcmData);
}

async function startSelectedInput() {
  const source = inputSourceSelect.value;

  if (source === DEFAULT_SOURCE) {
    updateInputState("none");
    appendEvent("System", "No live input source selected", "text-only mode");
    return;
  }

  if (!agentSocket || agentSocket.readyState !== WebSocket.OPEN) {
    appendEvent("System", "Connect before starting a live input source");
    return;
  }

  if (audioRecorderNode) {
    return;
  }

  inputStream = await navigator.mediaDevices.getUserMedia({
    audio: { channelCount: 1 },
  });

  [audioRecorderNode, audioRecorderContext] =
    await startStreamAudioRecorderWorklet(inputStream, sendAudioChunk);

  if (audioRecorderContext?.state === "suspended") {
    await audioRecorderContext.resume();
  }

  updateInputState(source);
  appendEvent(
    "System",
    `${source} input connected`,
    "streaming to Gemini Live",
  );
}

async function stopSelectedInput() {
  if (audioRecorderNode) {
    audioRecorderNode.port.onmessage = null;
    audioRecorderNode.disconnect();
    audioRecorderNode = null;
  }

  if (audioRecorderContext) {
    await audioRecorderContext.close();
    audioRecorderContext = null;
  }

  if (inputStream) {
    inputStream.getTracks().forEach((track) => track.stop());
    inputStream = null;
  }

  updateInputState(DEFAULT_SOURCE);
}

function updateControls() {
  if (!connectButton) {
    return;
  }

  const isConnected = agentSocket?.readyState === WebSocket.OPEN;
  const source = inputSourceSelect.value;
  connectButton.disabled = isConnected;
  disconnectButton.disabled = !agentSocket;
  sendTextButton.disabled = !isConnected;
  startInputButton.disabled = !isConnected || source === DEFAULT_SOURCE;
  stopInputButton.disabled = !audioRecorderNode;
}

function scheduleReconnect() {
  if (
    (autoReconnectCheckbox && !autoReconnectCheckbox.checked) ||
    manualDisconnect
  ) {
    return;
  }

  agentReconnectTimer = setTimeout(() => {
    connectAgentSocket();
  }, AUTO_RECONNECT_DELAY_MS);
}

async function disconnectAgentSocket() {
  manualDisconnect = true;

  if (agentReconnectTimer) {
    clearTimeout(agentReconnectTimer);
    agentReconnectTimer = null;
  }

  await stopSelectedInput();

  if (agentSocket) {
    const socketToClose = agentSocket;
    agentSocket = null;
    socketToClose.close(1000, "manual disconnect");
  }

  updateConnectionState("disconnected");
  updateLastEvent("manual disconnect");
  updateControls();
}

function connectAgentSocket() {
  const wsUrl = getAgentWebSocketUrl();
  if (!isValidWebSocketUrl(wsUrl)) {
    appendEvent("System", "Invalid Gemini Live websocket URL", wsUrl);
    updateConnectionState("invalid url");
    return;
  }

  if (agentReconnectTimer) {
    clearTimeout(agentReconnectTimer);
    agentReconnectTimer = null;
  }

  if (agentSocket && agentSocket.readyState === WebSocket.OPEN) {
    return;
  }

  manualDisconnect = false;
  currentSessionId = sessionIdInput.value.trim() || currentSessionId;
  agentSocket = new WebSocket(wsUrl);
  appendEvent("System", "Connecting to Gemini Live", wsUrl);
  updateConnectionState("connecting");
  updateSessionState();
  updateControls();

  agentSocket.onopen = async () => {
    appendEvent("System", "Gemini Live connected", currentSessionId);
    updateConnectionState("connected");
    updateLastEvent("socket open");
    updateControls();
    try {
      if (!autoEnableAudioCheckbox || autoEnableAudioCheckbox.checked) {
        await initAudioOutput();
      }

      if (!isDebugMode) {
        await startSelectedInput();
        updateControls();
      }
    } catch (error) {
      updateAudioOutputState("error");
      appendEvent("System", "Voice pipeline failed to start", String(error));
    }
  };

  agentSocket.onmessage = handleAgentEvent;

  agentSocket.onerror = () => {
    appendEvent("System", "Gemini Live websocket error");
    updateLastEvent("socket error");
  };

  agentSocket.onclose = async () => {
    resetCurrentAgentEvent();
    await stopSelectedInput();
    appendEvent(
      "System",
      "Gemini Live disconnected",
      manualDisconnect ? "manual disconnect" : "retrying soon",
    );
    agentSocket = null;
    updateConnectionState("disconnected");
    updateLastEvent("socket closed");
    updateControls();
    scheduleReconnect();
  };

  updateControls();
}

function initializeForm() {
  const queryUrl = getAgentWsFromQuery();
  userIdInput.value = DEFAULT_USER_ID;
  sessionIdInput.value = currentSessionId;
  inputSourceSelect.value = isDebugMode ? DEFAULT_SOURCE : "microphone";
  wsUrlInput.value =
    queryUrl || buildDefaultWebSocketUrl(DEFAULT_USER_ID, currentSessionId);
  autoSyncWebSocketUrl = !queryUrl;
  updateConnectionState("idle");
  updateInputState(inputSourceSelect.value);
  updateAudioOutputState("disabled");
  updateSessionState();
  updateLastEvent("ready");
  updateControls();
  appendEvent(
    "System",
    isDebugMode ? "Debug runtime ready" : "Conversational runtime ready",
    isDebugMode ? "connect when you want to start" : "connecting automatically",
  );
}

userIdInput.addEventListener("input", () => {
  updateSessionState();
  syncWebSocketUrlFromIdentity();
});

sessionIdInput.addEventListener("input", () => {
  currentSessionId = sessionIdInput.value.trim() || currentSessionId;
  updateSessionState();
  syncWebSocketUrlFromIdentity();
});

wsUrlInput.addEventListener("input", () => {
  autoSyncWebSocketUrl = false;
});

inputSourceSelect.addEventListener("change", () => {
  updateControls();
  updateInputState(inputSourceSelect.value);
});

connectButton.addEventListener("click", () => {
  connectAgentSocket();
});

disconnectButton.addEventListener("click", async () => {
  await disconnectAgentSocket();
});

startInputButton.addEventListener("click", async () => {
  try {
    await startSelectedInput();
  } catch (error) {
    updateInputState("error");
    appendEvent("System", "Input source failed to start", String(error));
  }
  updateControls();
});

stopInputButton.addEventListener("click", async () => {
  await stopSelectedInput();
  appendEvent("System", "Live input stopped");
  updateControls();
});

enableAudioButton.addEventListener("click", async () => {
  try {
    await initAudioOutput();
  } catch (error) {
    updateAudioOutputState("error");
    appendEvent("System", "Audio output failed to start", String(error));
  }
});

resetFeedButton.addEventListener("click", () => {
  agentFeedEl.innerHTML = "";
  appendEvent("System", "Feed cleared");
});

textForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = textPromptInput.value.trim();
  if (!text) {
    return;
  }

  sendTextMessage(text);
  textPromptInput.value = "";
});

setDebugVisibility();
initializeForm();

if (!isDebugMode) {
  connectAgentSocket();
}
