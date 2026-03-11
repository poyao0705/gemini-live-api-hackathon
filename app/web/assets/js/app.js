/**
 * app.js: Thin orchestrator for the ADK Bidi-streaming demo app.
 *
 * Imports focused ES modules and wires them together.
 * No business logic lives here — it all lives in the modules.
 */

import { GeminiWSClient } from "./ws-client.js";
import { EventConsole } from "./event-console.js";
import { ChatUI, cleanCJKSpaces } from "./chat-ui.js";
import { CameraManager } from "./camera.js";
import { startAudioPlayerWorklet } from "./audio-player.js";
import { startAudioRecorderWorklet } from "./audio-recorder.js";

// ─── State ────────────────────────────────────────────────────────────────────

const userId = "demo-user";
const sessionId = "demo-session-" + Math.random().toString(36).substring(7);
let is_audio = false;

// ─── DOM references ───────────────────────────────────────────────────────────

const messageForm = document.getElementById("messageForm");
const messageInput = document.getElementById("message");
const messagesDiv = document.getElementById("messages");
const statusIndicator = document.getElementById("statusIndicator");
const statusText = document.getElementById("statusText");
const enableProactivityCheckbox = document.getElementById("enableProactivity");
const enableAffectiveDialogCheckbox = document.getElementById(
  "enableAffectiveDialog",
);

// ─── Audio worklet state ──────────────────────────────────────────────────────

let audioPlayerNode;
let audioPlayerContext;
let audioRecorderNode;
let audioRecorderContext;
let micStream;

// ─── WebSocket URL builder ────────────────────────────────────────────────────

function getWebSocketUrl() {
  const baseUrl =
    "ws://" + window.location.host + "/ws/" + userId + "/" + sessionId;
  const params = new URLSearchParams();

  if (enableProactivityCheckbox && enableProactivityCheckbox.checked) {
    params.append("proactivity", "true");
  }
  if (enableAffectiveDialogCheckbox && enableAffectiveDialogCheckbox.checked) {
    params.append("affective_dialog", "true");
  }

  const queryString = params.toString();
  return queryString ? baseUrl + "?" + queryString : baseUrl;
}

// ─── Connection status UI helper ──────────────────────────────────────────────

function updateConnectionStatus(connected) {
  if (connected) {
    statusIndicator.classList.remove("disconnected");
    statusText.textContent = "Connected";
  } else {
    statusIndicator.classList.add("disconnected");
    statusText.textContent = "Disconnected";
  }
}

// ─── Module instantiation ─────────────────────────────────────────────────────

const wsClient = new GeminiWSClient(getWebSocketUrl, { reconnectMs: 5000 });

const eventConsole = new EventConsole({
  consoleContent: document.getElementById("consoleContent"),
  showAudioEventsCheckbox: document.getElementById("showAudioEvents"),
  clearButton: document.getElementById("clearConsole"),
});

const chatUI = new ChatUI({ messagesDiv, cleanCJKSpaces });

const cameraManager = new CameraManager({
  cameraButton: document.getElementById("cameraButton"),
  cameraModal: document.getElementById("cameraModal"),
  cameraPreview: document.getElementById("cameraPreview"),
  closeCameraModal: document.getElementById("closeCameraModal"),
  cancelCamera: document.getElementById("cancelCamera"),
  captureImageBtn: document.getElementById("captureImage"),

  onCapture: (base64data, imageDataUrl, dimensions, blobSize) => {
    // Display image bubble immediately
    const imageBubble = chatUI.createImageBubble(imageDataUrl, true);
    messagesDiv.appendChild(imageBubble);
    chatUI.scrollToBottom();

    // Send to server
    wsClient.sendImage(base64data, "image/jpeg");
    console.log("[CLIENT TO AGENT] Sent image");

    // Log to console panel
    eventConsole.addEntry(
      "outgoing",
      `Image captured: ${blobSize} bytes (JPEG)`,
      {
        size: blobSize,
        type: "image/jpeg",
        dimensions,
      },
      "📷",
      "user",
    );
  },

  onError: (message, error) => {
    chatUI.addSystemMessage(message);
    if (error) {
      const label = message.startsWith("Failed to access camera")
        ? "Camera access failed"
        : "Image capture failed";
      eventConsole.addEntry(
        "error",
        label,
        { error: error.message, name: error.name },
        "⚠️",
        "system",
      );
    }
  },
});

// ─── WebSocket event wiring ───────────────────────────────────────────────────

wsClient.addEventListener("connected", (e) => {
  const { url } = e.detail;
  console.log("WebSocket connection opened.");
  updateConnectionStatus(true);
  chatUI.addSystemMessage("Connected to ADK streaming server");

  eventConsole.addEntry(
    "incoming",
    "WebSocket Connected",
    { userId, sessionId, url },
    "🔌",
    "system",
  );

  // Enable the Send button
  document.getElementById("sendButton").disabled = false;

  // Bind form submit handler
  messageForm.onsubmit = function (e) {
    e.preventDefault();
    const message = messageInput.value.trim();
    if (message) {
      // Add user message bubble
      const userBubble = chatUI.createBubble(message, true, false);
      messagesDiv.appendChild(userBubble);
      chatUI.scrollToBottom();

      // Clear input
      messageInput.value = "";

      // Send to server
      wsClient.sendText(message);
      console.log("[CLIENT TO AGENT] " + message);

      // Log to console panel
      eventConsole.addEntry(
        "outgoing",
        "User Message: " + message,
        null,
        "💬",
        "user",
      );
    }
    return false;
  };
});

wsClient.addEventListener("disconnected", () => {
  console.log("WebSocket connection closed.");
  updateConnectionStatus(false);
  document.getElementById("sendButton").disabled = true;
  chatUI.addSystemMessage("Connection closed. Reconnecting in 5 seconds...");

  eventConsole.addEntry(
    "error",
    "WebSocket Disconnected",
    {
      status: "Connection closed",
      reconnecting: true,
      reconnectDelay: "5 seconds",
    },
    "🔌",
    "system",
  );

  setTimeout(() => {
    console.log("Reconnecting...");

    eventConsole.addEntry(
      "outgoing",
      "Reconnecting to ADK server...",
      { userId, sessionId },
      "🔄",
      "system",
    );

    wsClient.connect();
  }, 5000);
});

wsClient.addEventListener("error", (e) => {
  console.log("WebSocket error: ", e.detail);
  updateConnectionStatus(false);

  eventConsole.addEntry(
    "error",
    "WebSocket Error",
    {
      error: e.detail.type,
      message: "Connection error occurred",
    },
    "⚠️",
    "system",
  );
});

wsClient.addEventListener("adkevent", (e) => {
  const adkEvent = e.detail;
  console.log("[AGENT TO CLIENT] ", adkEvent);

  // Summarize event for console panel
  const { summary, emoji, author, isAudio } =
    eventConsole.summarizeADKEvent(adkEvent);
  const sanitized = eventConsole.sanitizeEventForDisplay(adkEvent);

  // If event has audio data, log it with the audio filter flag
  if (isAudio) {
    eventConsole.addEntry("incoming", summary, sanitized, emoji, author, true);
  }

  // Log non-audio-only events normally (audio-only events are already logged above)
  const isAudioOnlyEvent =
    adkEvent.content &&
    adkEvent.content.parts &&
    adkEvent.content.parts.some((p) => p.inlineData) &&
    !adkEvent.content.parts.some((p) => p.text);
  if (!isAudioOnlyEvent) {
    eventConsole.addEntry("incoming", summary, sanitized, emoji, author);
  }

  // Dispatch to chat UI for bubble rendering
  chatUI.handleADKEvent(adkEvent, audioPlayerNode);
});

// ─── RunConfig checkbox wiring ────────────────────────────────────────────────

function handleRunConfigChange() {
  if (wsClient.isOpen) {
    chatUI.addSystemMessage("Reconnecting with updated settings...");
    eventConsole.addEntry(
      "outgoing",
      "Reconnecting due to settings change",
      {
        proactivity: enableProactivityCheckbox.checked,
        affective_dialog: enableAffectiveDialogCheckbox.checked,
      },
      "🔄",
      "system",
    );
    wsClient.close();
    // disconnected event handler will schedule reconnect in 5 seconds
  }
}

enableProactivityCheckbox.addEventListener("change", handleRunConfigChange);
enableAffectiveDialogCheckbox.addEventListener("change", handleRunConfigChange);

// ─── Audio handling ───────────────────────────────────────────────────────────

function audioRecorderHandler(pcmData) {
  if (wsClient.isOpen && is_audio) {
    wsClient.sendAudio(pcmData);
    console.log(
      "[CLIENT TO AGENT] Sent audio chunk: %s bytes",
      pcmData.byteLength,
    );
  }
}

const startAudioButton = document.getElementById("startAudioButton");
startAudioButton.addEventListener("click", () => {
  startAudioButton.disabled = true;

  // Start audio output
  startAudioPlayerWorklet().then(([node, ctx]) => {
    audioPlayerNode = node;
    audioPlayerContext = ctx;
  });

  // Start audio input
  startAudioRecorderWorklet(audioRecorderHandler).then(
    ([node, ctx, stream]) => {
      audioRecorderNode = node;
      audioRecorderContext = ctx;
      micStream = stream;
    },
  );

  is_audio = true;
  chatUI.addSystemMessage(
    "Audio mode enabled - you can now speak to the agent",
  );

  eventConsole.addEntry(
    "outgoing",
    "Audio Mode Enabled",
    {
      status: "Audio worklets started",
      message: "Microphone active - audio input will be sent to agent",
    },
    "🎤",
    "system",
  );
});

// ─── Bootstrap ────────────────────────────────────────────────────────────────

wsClient.connect();
