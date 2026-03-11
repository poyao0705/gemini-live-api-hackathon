/**
 * ws-client.js: WebSocket transport layer for the ADK Bidi-streaming demo app.
 *
 * GeminiWSClient extends EventTarget and dispatches:
 *   "connected"    — WebSocket opened (detail: { url })
 *   "disconnected" — WebSocket closed
 *   "error"        — WebSocket error (detail: ErrorEvent)
 *   "adkevent"     — parsed ADK JSON event (detail: adkEvent object)
 */

export class GeminiWSClient extends EventTarget {
  #ws = null;
  #buildUrl;
  #reconnectMs;

  /**
   * @param {() => string} buildUrl  Called fresh on each connect() to get the WS URL.
   * @param {{ reconnectMs?: number }} options
   */
  constructor(buildUrl, { reconnectMs = 5000 } = {}) {
    super();
    this.#buildUrl = buildUrl;
    this.#reconnectMs = reconnectMs;
  }

  /** Open the WebSocket connection. */
  connect() {
    const url = this.#buildUrl();
    this.#ws = new WebSocket(url);

    this.#ws.onopen = () => {
      this.dispatchEvent(new CustomEvent("connected", { detail: { url } }));
    };

    this.#ws.onclose = () => {
      this.dispatchEvent(new Event("disconnected"));
    };

    this.#ws.onerror = (e) => {
      this.dispatchEvent(new CustomEvent("error", { detail: e }));
    };

    this.#ws.onmessage = (event) => {
      let adkEvent;
      try {
        adkEvent = JSON.parse(event.data);
      } catch (err) {
        this.dispatchEvent(
          new CustomEvent("error", {
            detail: { type: "parse_error", message: "Invalid JSON in WebSocket message", cause: err },
          }),
        );
        return;
      }
      this.dispatchEvent(new CustomEvent("adkevent", { detail: adkEvent }));
    };
  }

  /**
   * Send a text message.
   * @param {string} text
   */
  sendText(text) {
    if (this.#ws?.readyState === WebSocket.OPEN) {
      this.#ws.send(JSON.stringify({ type: "text", text }));
    }
  }

  /**
   * Send raw PCM audio as a binary WebSocket frame.
   * @param {ArrayBuffer} pcmBuffer
   */
  sendAudio(pcmBuffer) {
    if (this.#ws?.readyState === WebSocket.OPEN) {
      this.#ws.send(pcmBuffer);
    }
  }

  /**
   * Send a base64-encoded image.
   * @param {string} base64
   * @param {string} mimeType
   */
  sendImage(base64, mimeType = "image/jpeg") {
    if (this.#ws?.readyState === WebSocket.OPEN) {
      this.#ws.send(JSON.stringify({ type: "image", data: base64, mimeType }));
    }
  }

  /** Close the connection without triggering auto-reconnect. */
  close() {
    this.#ws?.close();
  }

  /** @returns {boolean} */
  get isOpen() {
    return this.#ws?.readyState === WebSocket.OPEN;
  }
}
