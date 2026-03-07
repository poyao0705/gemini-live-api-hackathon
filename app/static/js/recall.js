import { startAudioPlayerWorklet } from "./audio-player.js";
import { startStreamAudioRecorderWorklet } from "./audio-recorder.js";

const sessionId = `recall-${Math.random().toString(36).slice(2, 10)}`;
const userId = "recall-bot";
const agentFeedEl = document.getElementById("agentFeed");

let agentSocket = null;
let agentReconnectTimer = null;
let transcriptSocket = null;
let audioPlayerNode = null;
let audioPlayerContext = null;
let audioRecorderNode = null;
let audioRecorderContext = null;
let meetingStream = null;
let currentAgentEvent = null;
let currentAgentText = "";
let currentTurnUsesTranscription = false;
let currentUserEvent = null;
let currentUserText = "";
let currentUserFinished = false;

function appendEvent(title, text, meta = "") {
  const event = document.createElement("div");
  event.className = "event";

  const titleEl = document.createElement("p");
  titleEl.innerHTML = `<strong>${title}</strong>`;

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

function getAgentWebSocketUrl() {
  const queryValue = getAgentWsFromQuery();
  if (queryValue) {
    return queryValue.includes("{session_id}")
      ? queryValue.replaceAll("{session_id}", sessionId)
      : queryValue;
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/${userId}/${sessionId}`;
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
    return;
  }

  [audioPlayerNode, audioPlayerContext] = await startAudioPlayerWorklet();
  if (audioPlayerContext?.state === "suspended") {
    await audioPlayerContext.resume();
  }
}

function resetCurrentAgentEvent() {
  currentAgentEvent = null;
  currentAgentText = "";
  currentTurnUsesTranscription = false;
}

function resetCurrentUserEvent() {
  currentUserEvent = null;
  currentUserText = "";
  currentUserFinished = false;
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

function ensureCurrentUserEvent(initialText = "") {
  if (!currentUserEvent) {
    currentUserEvent = appendEvent("You", initialText || "...", "transcribing");
  }
  return currentUserEvent;
}

function renderAgentText(text, isFinal = false, source = "text") {
  const event = ensureCurrentAgentEvent(text);
  updateEvent(event, text, isFinal ? `final ${source}` : `partial ${source}`);
  if (isFinal) {
    resetCurrentAgentEvent();
  }
}

function renderUserText(text, isFinal = false) {
  if (currentUserFinished) {
    return;
  }
  const event = ensureCurrentUserEvent(text);
  updateEvent(event, text, isFinal ? "final transcription" : "partial transcription");
  if (isFinal) {
    currentUserFinished = true;
  }
}

function handleAgentEvent(message) {
  const adkEvent = JSON.parse(message.data);

  if (adkEvent.turnComplete) {
    resetCurrentAgentEvent();
    resetCurrentUserEvent();
    return;
  }

  if (adkEvent.interrupted) {
    resetCurrentAgentEvent();
    resetCurrentUserEvent();
    appendEvent("System", "Agent output interrupted");
    return;
  }

  if (adkEvent.inputTranscription?.text) {
    const isFinished = Boolean(adkEvent.inputTranscription.finished);
    currentUserText = isFinished
      ? adkEvent.inputTranscription.text
      : `${currentUserText}${adkEvent.inputTranscription.text}`;
    renderUserText(currentUserText, isFinished);
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

    if (part.text && !currentTurnUsesTranscription) {
      currentAgentText = `${currentAgentText}${part.text}`;
      renderAgentText(currentAgentText, false, "content");
    }
  }
}

function sendAudioChunk(pcmData) {
  if (!agentSocket || agentSocket.readyState !== WebSocket.OPEN) {
    return;
  }

  agentSocket.send(pcmData);
}

async function startMeetingAudio() {
  if (audioRecorderNode) {
    return;
  }

  meetingStream = await navigator.mediaDevices.getUserMedia({
    audio: { channelCount: 1 },
  });

  [audioRecorderNode, audioRecorderContext] =
    await startStreamAudioRecorderWorklet(meetingStream, sendAudioChunk);

  if (audioRecorderContext?.state === "suspended") {
    await audioRecorderContext.resume();
  }

  appendEvent("System", "Meeting audio connected", "streaming to Gemini Live");
}

function connectAgentSocket() {
  const wsUrl = getAgentWebSocketUrl();
  if (!isValidWebSocketUrl(wsUrl)) {
    appendEvent("System", "Invalid Gemini Live websocket URL", wsUrl);
    return;
  }

  if (agentReconnectTimer) {
    clearTimeout(agentReconnectTimer);
    agentReconnectTimer = null;
  }

  if (agentSocket && agentSocket.readyState === WebSocket.OPEN) {
    return;
  }

  agentSocket = new WebSocket(wsUrl);
  appendEvent("System", "Connecting to Gemini Live", wsUrl);

  agentSocket.onopen = async () => {
    appendEvent("System", "Gemini Live connected", sessionId);
    try {
      await initAudioOutput();
      await startMeetingAudio();
    } catch (error) {
      appendEvent("System", "Voice pipeline failed to start", String(error));
    }
  };

  agentSocket.onmessage = handleAgentEvent;

  agentSocket.onerror = () => {
    appendEvent("System", "Gemini Live websocket error");
  };

  agentSocket.onclose = () => {
    resetCurrentAgentEvent();
    appendEvent("System", "Gemini Live disconnected", "retrying in 3 seconds");
    agentSocket = null;
    agentReconnectTimer = setTimeout(() => {
      connectAgentSocket();
    }, 3000);
  };
}

connectAgentSocket();

function getTranscriptWsFromQuery() {
  const params = new URLSearchParams(window.location.search);
  const value = params.get("transcript_ws");
  return value ? value.trim() : "";
}

function connectTranscriptSocket() {
  const wsUrl = getTranscriptWsFromQuery();
  if (!wsUrl || !isValidWebSocketUrl(wsUrl)) {
    return;
  }

  transcriptSocket = new WebSocket(wsUrl);
  appendEvent("System", "Connecting to Recall transcript feed", wsUrl);

  transcriptSocket.onopen = () => {
    appendEvent("System", "Recall transcript feed connected");
  };

  transcriptSocket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      const speaker =
        typeof data.speaker?.name === "string"
          ? data.speaker.name
          : typeof data.speaker === "string"
            ? data.speaker
            : "Speaker";
      const words = Array.isArray(data.words)
        ? data.words.map((w) => (typeof w === "string" ? w : w.text ?? "")).join(" ")
        : data.text ?? String(event.data);
      if (words) {
        appendEvent(`[Transcript] ${speaker}`, words);
      }
    } catch (err) {
      console.warn("Failed to parse transcript message:", err);
      appendEvent("[Transcript]", String(event.data));
    }
  };

  transcriptSocket.onerror = () => {
    appendEvent("System", "Recall transcript feed error");
  };

  transcriptSocket.onclose = () => {
    appendEvent("System", "Recall transcript feed disconnected");
    transcriptSocket = null;
  };
}

connectTranscriptSocket();
