/**
 * event-console.js: Debug console panel for the ADK Bidi-streaming demo app.
 *
 * EventConsole renders incoming/outgoing ADK events in an expandable panel
 * and summarizes structured ADK events for display.
 */

export class EventConsole {
  #consoleContent;
  #showAudioEventsCheckbox;

  /**
   * @param {{ consoleContent: HTMLElement, showAudioEventsCheckbox: HTMLInputElement, clearButton: HTMLElement }} elements
   */
  constructor({ consoleContent, showAudioEventsCheckbox, clearButton }) {
    this.#consoleContent = consoleContent;
    this.#showAudioEventsCheckbox = showAudioEventsCheckbox;
    clearButton.addEventListener("click", () => this.clear());
  }

  // ─── Formatting ──────────────────────────────────────────────────────────────

  /** @returns {string} HH:MM:SS.mmm */
  #formatTimestamp() {
    const now = new Date();
    return now.toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      fractionalSecondDigits: 3,
    });
  }

  // ─── Public API ──────────────────────────────────────────────────────────────

  /**
   * Append a console entry row.
   * @param {"incoming"|"outgoing"|"error"} type
   * @param {string} content  Short summary text shown in the header
   * @param {object|null} data  Optional JSON detail (collapsed by default)
   * @param {string|null} emoji
   * @param {string|null} author
   * @param {boolean} isAudio  When true, entry is hidden if the audio-events checkbox is unchecked
   */
  addEntry(
    type,
    content,
    data = null,
    emoji = null,
    author = null,
    isAudio = false,
  ) {
    // Skip audio events if checkbox is unchecked
    if (isAudio && !this.#showAudioEventsCheckbox.checked) {
      return;
    }

    const entry = document.createElement("div");
    entry.className = `console-entry ${type} rounded-box border border-white/10 shadow-sm`;

    const header = document.createElement("div");
    header.className = "console-entry-header";

    const leftSection = document.createElement("div");
    leftSection.className = "console-entry-left";

    // Add emoji icon if provided
    if (emoji) {
      const emojiIcon = document.createElement("span");
      emojiIcon.className = "console-entry-emoji";
      emojiIcon.textContent = emoji;
      leftSection.appendChild(emojiIcon);
    }

    // Add expand/collapse icon
    const expandIcon = document.createElement("span");
    expandIcon.className = "console-expand-icon";
    expandIcon.textContent = data ? "▶" : "";

    const typeLabel = document.createElement("span");
    typeLabel.className = "console-entry-type";
    typeLabel.textContent =
      type === "outgoing"
        ? "↑ Upstream"
        : type === "incoming"
          ? "↓ Downstream"
          : "⚠ Error";

    leftSection.appendChild(expandIcon);
    leftSection.appendChild(typeLabel);

    // Add author badge if provided
    if (author) {
      const authorBadge = document.createElement("span");
      authorBadge.className = "console-entry-author";
      authorBadge.textContent = author;
      authorBadge.setAttribute("data-author", author);
      leftSection.appendChild(authorBadge);
    }

    const timestamp = document.createElement("span");
    timestamp.className = "console-entry-timestamp";
    timestamp.textContent = this.#formatTimestamp();

    header.appendChild(leftSection);
    header.appendChild(timestamp);

    const contentDiv = document.createElement("div");
    contentDiv.className = "console-entry-content";
    contentDiv.textContent = content;

    entry.appendChild(header);
    entry.appendChild(contentDiv);

    // JSON details (hidden by default)
    if (data) {
      const jsonDiv = document.createElement("div");
      jsonDiv.className = "console-entry-json collapsed";
      const pre = document.createElement("pre");
      pre.textContent = JSON.stringify(data, null, 2);
      jsonDiv.appendChild(pre);
      entry.appendChild(jsonDiv);

      // Make entry clickable if it has data
      entry.classList.add("expandable");

      // Toggle expand/collapse on click
      entry.addEventListener("click", () => {
        const isExpanded = !jsonDiv.classList.contains("collapsed");

        if (isExpanded) {
          // Collapse
          jsonDiv.classList.add("collapsed");
          expandIcon.textContent = "▶";
          entry.classList.remove("expanded");
        } else {
          // Expand
          jsonDiv.classList.remove("collapsed");
          expandIcon.textContent = "▼";
          entry.classList.add("expanded");
        }
      });
    }

    this.#consoleContent.appendChild(entry);
    this.#consoleContent.scrollTop = this.#consoleContent.scrollHeight;
  }

  /** Clear all console entries. */
  clear() {
    this.#consoleContent.innerHTML = "";
  }

  /**
   * Deep-clone an ADK event and replace large base64 audio payloads with a
   * human-readable byte-size summary.
   * @param {object} event
   * @returns {object}
   */
  sanitizeEventForDisplay(event) {
    // Deep clone the event object
    const sanitized = structuredClone(event);

    // Check for audio data in content.parts
    if (sanitized.content && sanitized.content.parts) {
      sanitized.content.parts = sanitized.content.parts.map((part) => {
        if (part.inlineData && part.inlineData.data) {
          // Calculate byte size (base64 string length / 4 * 3, roughly)
          const byteSize = Math.floor(part.inlineData.data.length * 0.75);
          return {
            ...part,
            inlineData: {
              ...part.inlineData,
              data: `(${byteSize.toLocaleString()} bytes)`,
            },
          };
        }
        return part;
      });
    }

    return sanitized;
  }

  /**
   * Derive a human-readable summary + metadata from a structured ADK event.
   * @param {object} adkEvent
   * @returns {{ summary: string, emoji: string, author: string, isAudio: boolean }}
   */
  summarizeADKEvent(adkEvent) {
    let summary = "Event";
    let emoji = "📨";
    const author = adkEvent.author || "system";
    let isAudio = false;

    if (adkEvent.turnComplete) {
      summary = "Turn Complete";
      emoji = "✅";
    } else if (adkEvent.interrupted) {
      summary = "Interrupted";
      emoji = "⏸️";
    } else if (adkEvent.inputTranscription) {
      const text = adkEvent.inputTranscription.text || "";
      const truncated =
        text.length > 60 ? text.substring(0, 60) + "..." : text;
      summary = `Input Transcription: "${truncated}"`;
      emoji = "📝";
    } else if (adkEvent.outputTranscription) {
      const text = adkEvent.outputTranscription.text || "";
      const truncated =
        text.length > 60 ? text.substring(0, 60) + "..." : text;
      summary = `Output Transcription: "${truncated}"`;
      emoji = "📝";
    } else if (adkEvent.usageMetadata) {
      const usage = adkEvent.usageMetadata;
      const promptTokens = usage.promptTokenCount || 0;
      const responseTokens = usage.candidatesTokenCount || 0;
      const totalTokens = usage.totalTokenCount || 0;
      summary = `Token Usage: ${totalTokens.toLocaleString()} total (${promptTokens.toLocaleString()} prompt + ${responseTokens.toLocaleString()} response)`;
      emoji = "📊";
    } else if (adkEvent.content && adkEvent.content.parts) {
      const hasText = adkEvent.content.parts.some((p) => p.text);
      const hasAudio = adkEvent.content.parts.some((p) => p.inlineData);
      const hasExecutableCode = adkEvent.content.parts.some(
        (p) => p.executableCode,
      );
      const hasCodeExecutionResult = adkEvent.content.parts.some(
        (p) => p.codeExecutionResult,
      );

      if (hasExecutableCode) {
        const codePart = adkEvent.content.parts.find((p) => p.executableCode);
        if (codePart && codePart.executableCode) {
          const code = codePart.executableCode.code || "";
          const language = codePart.executableCode.language || "unknown";
          const truncated =
            code.length > 60
              ? code.substring(0, 60).replace(/\n/g, " ") + "..."
              : code.replace(/\n/g, " ");
          summary = `Executable Code (${language}): ${truncated}`;
          emoji = "💻";
        }
      }

      if (hasCodeExecutionResult) {
        const resultPart = adkEvent.content.parts.find(
          (p) => p.codeExecutionResult,
        );
        if (resultPart && resultPart.codeExecutionResult) {
          const outcome =
            resultPart.codeExecutionResult.outcome || "UNKNOWN";
          const output = resultPart.codeExecutionResult.output || "";
          const truncatedOutput =
            output.length > 60
              ? output.substring(0, 60).replace(/\n/g, " ") + "..."
              : output.replace(/\n/g, " ");
          summary = `Code Execution Result (${outcome}): ${truncatedOutput}`;
          emoji = outcome === "OUTCOME_OK" ? "✅" : "❌";
        }
      }

      if (hasText) {
        const textPart = adkEvent.content.parts.find((p) => p.text);
        if (textPart && textPart.text) {
          const text = textPart.text;
          const truncated =
            text.length > 80 ? text.substring(0, 80) + "..." : text;
          summary = `Text: "${truncated}"`;
          emoji = "💭";
        } else {
          summary = "Text Response";
          emoji = "💭";
        }
      }

      if (hasAudio) {
        const audioPart = adkEvent.content.parts.find((p) => p.inlineData);
        if (audioPart && audioPart.inlineData) {
          const mimeType = audioPart.inlineData.mimeType || "unknown";
          const dataLength = audioPart.inlineData.data
            ? audioPart.inlineData.data.length
            : 0;
          const byteSize = Math.floor(dataLength * 0.75);
          summary = `Audio Response: ${mimeType} (${byteSize.toLocaleString()} bytes)`;
          emoji = "🔊";
        } else {
          summary = "Audio Response";
          emoji = "🔊";
        }
        isAudio = true;
      }
    }

    return { summary, emoji, author, isAudio };
  }
}
