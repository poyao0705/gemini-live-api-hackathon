/**
 * chat-ui.js: Chat bubble DOM management for the ADK Bidi-streaming demo app.
 *
 * ChatUI creates and updates message bubbles in the messages container and
 * processes incoming ADK events into DOM updates.
 *
 * Named exports:
 *   cleanCJKSpaces(text)  — removes inter-character spaces inside CJK runs
 *   base64ToArray(base64) — decodes a base64/base64url string to an ArrayBuffer
 *   ChatUI                — main class
 */

/**
 * Remove spaces between consecutive CJK characters while preserving spaces
 * around Latin text.
 * @param {string} text
 * @returns {string}
 */
export function cleanCJKSpaces(text) {
  // CJK Unicode ranges: Hiragana, Katakana, Kanji, CJK Unified Ideographs, Fullwidth forms
  const cjkPattern =
    /[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf\uff00-\uffef]/;

  // Remove spaces between two CJK characters
  return text.replace(/(\S)\s+(?=\S)/g, (match, char1) => {
    // Get the character after the space(s)
    const nextCharMatch = text.match(new RegExp(char1 + "\\s+(.)", "g"));
    if (nextCharMatch && nextCharMatch.length > 0) {
      const char2 = nextCharMatch[0].slice(-1);
      // If both characters are CJK, remove the space
      if (cjkPattern.test(char1) && cjkPattern.test(char2)) {
        return char1;
      }
    }
    return match;
  });
}

/**
 * Decode a base64 or base64url string to an ArrayBuffer.
 * Returns null if the input is malformed.
 * @param {string} base64
 * @returns {ArrayBuffer|null}
 */
export function base64ToArray(base64) {
  try {
    // Convert base64url to standard base64
    // Replace URL-safe characters: - with +, _ with /
    let standardBase64 = base64.replace(/-/g, "+").replace(/_/g, "/");

    // Add padding if needed
    while (standardBase64.length % 4) {
      standardBase64 += "=";
    }

    const binaryString = window.atob(standardBase64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  } catch (err) {
    console.error("base64ToArray: failed to decode audio data", err);
    return null;
  }
}

export class ChatUI {
  #messagesDiv;
  #cleanCJKSpaces;

  // Turn state
  #currentMessageId = null;
  #currentBubbleElement = null;
  #currentInputTranscriptionId = null;
  #currentInputTranscriptionElement = null;
  #currentOutputTranscriptionId = null;
  #currentOutputTranscriptionElement = null;
  #inputTranscriptionFinished = false;

  /**
   * @param {{ messagesDiv: HTMLElement, cleanCJKSpaces: (text: string) => string }} options
   */
  constructor({ messagesDiv, cleanCJKSpaces }) {
    this.#messagesDiv = messagesDiv;
    this.#cleanCJKSpaces = cleanCJKSpaces;
  }

  // ─── Public DOM helpers ──────────────────────────────────────────────────────

  /**
   * Create a text message bubble element.
   * @param {string} text
   * @param {boolean} isUser
   * @param {boolean} isPartial  When true, appends a typing indicator
   * @returns {HTMLElement}
   */
  createBubble(text, isUser, isPartial = false) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${isUser ? "user" : "agent"} w-full`;

    const bubbleDiv = document.createElement("div");
    bubbleDiv.className = "bubble border border-base-300/60 shadow-sm";

    const textP = document.createElement("p");
    textP.className = "bubble-text";
    textP.textContent = text;

    // Add typing indicator for partial messages
    if (isPartial && !isUser) {
      const typingSpan = document.createElement("span");
      typingSpan.className = "typing-indicator";
      textP.appendChild(typingSpan);
    }

    bubbleDiv.appendChild(textP);
    messageDiv.appendChild(bubbleDiv);

    return messageDiv;
  }

  /**
   * Create an image message bubble element.
   * @param {string} imageDataUrl
   * @param {boolean} isUser
   * @returns {HTMLElement}
   */
  createImageBubble(imageDataUrl, isUser) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${isUser ? "user" : "agent"} w-full`;

    const bubbleDiv = document.createElement("div");
    bubbleDiv.className =
      "bubble image-bubble border border-base-300/60 shadow-sm";

    const img = document.createElement("img");
    img.src = imageDataUrl;
    img.className = "bubble-image";
    img.alt = "Captured image";

    bubbleDiv.appendChild(img);
    messageDiv.appendChild(bubbleDiv);

    return messageDiv;
  }

  /**
   * Update the text content of an existing bubble element.
   * @param {HTMLElement} element
   * @param {string} text
   * @param {boolean} isPartial
   */
  updateBubble(element, text, isPartial = false) {
    const textElement = element.querySelector(".bubble-text");

    // Remove existing typing indicator
    const existingIndicator = textElement.querySelector(".typing-indicator");
    if (existingIndicator) {
      existingIndicator.remove();
    }

    textElement.textContent = text;

    // Add typing indicator for partial messages
    if (isPartial) {
      const typingSpan = document.createElement("span");
      typingSpan.className = "typing-indicator";
      textElement.appendChild(typingSpan);
    }
  }

  /**
   * Append a system message badge to the messages container.
   * @param {string} text
   */
  addSystemMessage(text) {
    const messageDiv = document.createElement("div");
    messageDiv.className =
      "system-message badge badge-ghost badge-lg mx-auto";
    messageDiv.textContent = text;
    this.#messagesDiv.appendChild(messageDiv);
    this.scrollToBottom();
  }

  /** Scroll the messages container to the bottom. */
  scrollToBottom() {
    this.#messagesDiv.scrollTop = this.#messagesDiv.scrollHeight;
  }

  // ─── ADK event handler ───────────────────────────────────────────────────────

  /**
   * Process an incoming ADK event and update the chat UI accordingly.
   * @param {object} adkEvent
   * @param {AudioWorkletNode|null} audioPlayerNode
   */
  handleADKEvent(adkEvent, audioPlayerNode) {
    // Handle turn complete event
    if (adkEvent.turnComplete === true) {
      // Remove typing indicator from current message
      if (this.#currentBubbleElement) {
        const textElement =
          this.#currentBubbleElement.querySelector(".bubble-text");
        const typingIndicator = textElement.querySelector(".typing-indicator");
        if (typingIndicator) {
          typingIndicator.remove();
        }
      }
      // Remove typing indicator from current output transcription
      if (this.#currentOutputTranscriptionElement) {
        const textElement =
          this.#currentOutputTranscriptionElement.querySelector(".bubble-text");
        const typingIndicator = textElement.querySelector(".typing-indicator");
        if (typingIndicator) {
          typingIndicator.remove();
        }
      }
      this.#currentMessageId = null;
      this.#currentBubbleElement = null;
      this.#currentOutputTranscriptionId = null;
      this.#currentOutputTranscriptionElement = null;
      this.#inputTranscriptionFinished = false; // Reset for next turn
      return;
    }

    // Handle interrupted event
    if (adkEvent.interrupted === true) {
      // Stop audio playback if it's playing
      if (audioPlayerNode) {
        audioPlayerNode.port.postMessage({ command: "endOfAudio" });
      }

      // Keep the partial message but mark it as interrupted
      if (this.#currentBubbleElement) {
        const textElement =
          this.#currentBubbleElement.querySelector(".bubble-text");

        // Remove typing indicator
        const typingIndicator = textElement.querySelector(".typing-indicator");
        if (typingIndicator) {
          typingIndicator.remove();
        }

        // Add interrupted marker
        this.#currentBubbleElement.classList.add("interrupted");
      }

      // Keep the partial output transcription but mark it as interrupted
      if (this.#currentOutputTranscriptionElement) {
        const textElement =
          this.#currentOutputTranscriptionElement.querySelector(".bubble-text");

        // Remove typing indicator
        const typingIndicator = textElement.querySelector(".typing-indicator");
        if (typingIndicator) {
          typingIndicator.remove();
        }

        // Add interrupted marker
        this.#currentOutputTranscriptionElement.classList.add("interrupted");
      }

      // Reset state so new content creates a new bubble
      this.#currentMessageId = null;
      this.#currentBubbleElement = null;
      this.#currentOutputTranscriptionId = null;
      this.#currentOutputTranscriptionElement = null;
      this.#inputTranscriptionFinished = false; // Reset for next turn
      return;
    }

    // Handle input transcription (user's spoken words)
    if (adkEvent.inputTranscription && adkEvent.inputTranscription.text) {
      const transcriptionText = adkEvent.inputTranscription.text;
      const isFinished = adkEvent.inputTranscription.finished;

      if (transcriptionText) {
        // Ignore late-arriving transcriptions after we've finished for this turn
        if (this.#inputTranscriptionFinished) {
          return;
        }

        if (this.#currentInputTranscriptionId == null) {
          // Create new transcription bubble
          this.#currentInputTranscriptionId = Math.random()
            .toString(36)
            .substring(7);
          // Clean spaces between CJK characters
          const cleanedText = this.#cleanCJKSpaces(transcriptionText);
          this.#currentInputTranscriptionElement = this.createBubble(
            cleanedText,
            true,
            !isFinished,
          );
          this.#currentInputTranscriptionElement.id =
            this.#currentInputTranscriptionId;

          // Add a special class to indicate it's a transcription
          this.#currentInputTranscriptionElement.classList.add("transcription");

          this.#messagesDiv.appendChild(this.#currentInputTranscriptionElement);
        } else {
          // Update existing transcription bubble only if model hasn't started responding
          // This prevents late partial transcriptions from overwriting complete ones
          if (
            this.#currentOutputTranscriptionId == null &&
            this.#currentMessageId == null
          ) {
            if (isFinished) {
              // Final transcription contains the complete text, replace entirely
              const cleanedText = this.#cleanCJKSpaces(transcriptionText);
              this.updateBubble(
                this.#currentInputTranscriptionElement,
                cleanedText,
                false,
              );
            } else {
              // Partial transcription - append to existing text
              const existingText =
                this.#currentInputTranscriptionElement.querySelector(
                  ".bubble-text",
                ).textContent;
              // Remove typing indicator if present
              const cleanText = existingText.replace(/\.\.\.$/, "");
              // Clean spaces between CJK characters before updating
              const accumulatedText = this.#cleanCJKSpaces(
                cleanText + transcriptionText,
              );
              this.updateBubble(
                this.#currentInputTranscriptionElement,
                accumulatedText,
                true,
              );
            }
          }
        }

        // If transcription is finished, reset the state and mark as complete
        if (isFinished) {
          this.#currentInputTranscriptionId = null;
          this.#currentInputTranscriptionElement = null;
          this.#inputTranscriptionFinished = true; // Prevent duplicate bubbles from late events
        }

        this.scrollToBottom();
      }
    }

    // Handle output transcription (model's spoken words)
    if (adkEvent.outputTranscription && adkEvent.outputTranscription.text) {
      const transcriptionText = adkEvent.outputTranscription.text;
      const isFinished = adkEvent.outputTranscription.finished;

      if (transcriptionText) {
        // Finalize any active input transcription when server starts responding
        if (
          this.#currentInputTranscriptionId != null &&
          this.#currentOutputTranscriptionId == null
        ) {
          // This is the first output transcription - finalize input transcription
          const textElement =
            this.#currentInputTranscriptionElement.querySelector(".bubble-text");
          const typingIndicator =
            textElement.querySelector(".typing-indicator");
          if (typingIndicator) {
            typingIndicator.remove();
          }
          // Reset input transcription state so next user input creates new balloon
          this.#currentInputTranscriptionId = null;
          this.#currentInputTranscriptionElement = null;
          this.#inputTranscriptionFinished = true; // Prevent duplicate bubbles from late events
        }

        if (this.#currentOutputTranscriptionId == null) {
          // Create new transcription bubble for agent
          this.#currentOutputTranscriptionId = Math.random()
            .toString(36)
            .substring(7);
          this.#currentOutputTranscriptionElement = this.createBubble(
            transcriptionText,
            false,
            !isFinished,
          );
          this.#currentOutputTranscriptionElement.id =
            this.#currentOutputTranscriptionId;

          // Add a special class to indicate it's a transcription
          this.#currentOutputTranscriptionElement.classList.add("transcription");

          this.#messagesDiv.appendChild(this.#currentOutputTranscriptionElement);
        } else {
          // Update existing transcription bubble
          if (isFinished) {
            // Final transcription contains the complete text, replace entirely
            this.updateBubble(
              this.#currentOutputTranscriptionElement,
              transcriptionText,
              false,
            );
          } else {
            // Partial transcription - append to existing text
            const existingText =
              this.#currentOutputTranscriptionElement.querySelector(
                ".bubble-text",
              ).textContent;
            // Remove typing indicator if present
            const cleanText = existingText.replace(/\.\.\.$/, "");
            this.updateBubble(
              this.#currentOutputTranscriptionElement,
              cleanText + transcriptionText,
              true,
            );
          }
        }

        // If transcription is finished, reset the state
        if (isFinished) {
          this.#currentOutputTranscriptionId = null;
          this.#currentOutputTranscriptionElement = null;
        }

        this.scrollToBottom();
      }
    }

    // Handle content events (text or audio)
    if (adkEvent.content && adkEvent.content.parts) {
      const parts = adkEvent.content.parts;

      // Finalize any active input transcription when server starts responding with content
      if (
        this.#currentInputTranscriptionId != null &&
        this.#currentMessageId == null &&
        this.#currentOutputTranscriptionId == null
      ) {
        // This is the first content event - finalize input transcription
        const textElement =
          this.#currentInputTranscriptionElement.querySelector(".bubble-text");
        const typingIndicator = textElement.querySelector(".typing-indicator");
        if (typingIndicator) {
          typingIndicator.remove();
        }
        // Reset input transcription state so next user input creates new balloon
        this.#currentInputTranscriptionId = null;
        this.#currentInputTranscriptionElement = null;
        this.#inputTranscriptionFinished = true; // Prevent duplicate bubbles from late events
      }

      for (const part of parts) {
        // Handle inline data (audio)
        if (part.inlineData) {
          const mimeType = part.inlineData.mimeType;
          const data = part.inlineData.data;

          if (mimeType && mimeType.startsWith("audio/pcm") && audioPlayerNode) {
            const pcmBuffer = base64ToArray(data);
            if (pcmBuffer) {
              audioPlayerNode.port.postMessage(pcmBuffer);
            }
          }
        }

        // Handle text
        if (part.text) {
          // Add a new message bubble for a new turn
          if (this.#currentMessageId == null) {
            this.#currentMessageId = Math.random().toString(36).substring(7);
            this.#currentBubbleElement = this.createBubble(
              part.text,
              false,
              true,
            );
            this.#currentBubbleElement.id = this.#currentMessageId;
            this.#messagesDiv.appendChild(this.#currentBubbleElement);
          } else {
            // Update the existing message bubble with accumulated text
            const existingText =
              this.#currentBubbleElement.querySelector(
                ".bubble-text",
              ).textContent;
            // Remove the "..." if present
            const cleanText = existingText.replace(/\.\.\.$/, "");
            this.updateBubble(
              this.#currentBubbleElement,
              cleanText + part.text,
              true,
            );
          }

          // Scroll down to the bottom of the messagesDiv
          this.scrollToBottom();
        }
      }
    }
  }
}
