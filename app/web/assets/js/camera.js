/**
 * camera.js: Camera capture module for the ADK Bidi-streaming demo app.
 *
 * CameraManager encapsulates all getUserMedia / canvas / modal logic and
 * calls provided callbacks for captured images and errors.
 */

export class CameraManager {
  #cameraPreview;
  #cameraModal;
  #cameraStream = null;
  #onCapture;
  #onError;

  /**
   * @param {{
   *   cameraButton: HTMLElement,
   *   cameraModal: HTMLDialogElement,
   *   cameraPreview: HTMLVideoElement,
   *   closeCameraModal: HTMLElement,
   *   cancelCamera: HTMLElement,
   *   captureImageBtn: HTMLElement,
   *   onCapture: (base64data: string, imageDataUrl: string, dimensions: string) => void,
   *   onError: (message: string, error: Error) => void,
   * }} options
   */
  constructor({
    cameraButton,
    cameraModal,
    cameraPreview,
    closeCameraModal,
    cancelCamera,
    captureImageBtn,
    onCapture,
    onError,
  }) {
    this.#cameraPreview = cameraPreview;
    this.#cameraModal = cameraModal;
    this.#onCapture = onCapture;
    this.#onError = onError;

    // Stop camera stream whenever the dialog is closed (by JS or backdrop click)
    cameraModal.addEventListener("close", () => {
      if (this.#cameraStream) {
        this.#cameraStream.getTracks().forEach((track) => track.stop());
        this.#cameraStream = null;
      }
      cameraPreview.srcObject = null;
    });

    // Button event listeners
    cameraButton.addEventListener("click", () => this.openPreview());
    closeCameraModal.addEventListener("click", () => this.closePreview());
    cancelCamera.addEventListener("click", () => this.closePreview());
    captureImageBtn.addEventListener("click", () =>
      this.captureFromPreview(),
    );
  }

  /** Request getUserMedia and open the camera modal. */
  async openPreview() {
    try {
      // Request access to the user's webcam
      this.#cameraStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 768 },
          height: { ideal: 768 },
          facingMode: "user",
        },
      });

      // Set the stream to the video element
      this.#cameraPreview.srcObject = this.#cameraStream;

      // Show the modal (DaisyUI dialog API)
      this.#cameraModal.showModal();
    } catch (error) {
      console.error("Error accessing camera:", error);
      this.#onError(`Failed to access camera: ${error.message}`, error);
    }
  }

  /** Close the camera modal — the "close" event handler stops the stream. */
  closePreview() {
    // Hide the modal — the 'close' event handler will stop the camera stream
    this.#cameraModal.close();
  }

  /** Capture a JPEG frame from the live preview and invoke onCapture. */
  captureFromPreview() {
    if (!this.#cameraStream) {
      // Pass null error so the orchestrator knows not to log a console entry
      this.#onError("No camera stream available", null);
      return;
    }

    try {
      // Create canvas to capture the frame
      const canvas = document.createElement("canvas");
      canvas.width = this.#cameraPreview.videoWidth;
      canvas.height = this.#cameraPreview.videoHeight;
      const context = canvas.getContext("2d");

      // Draw current video frame to canvas
      context.drawImage(
        this.#cameraPreview,
        0,
        0,
        canvas.width,
        canvas.height,
      );

      // Convert canvas to data URL for display
      const imageDataUrl = canvas.toDataURL("image/jpeg", 0.85);
      const dimensions = `${canvas.width}x${canvas.height}`;

      // Convert canvas to blob for sending to server
      canvas.toBlob(
        (blob) => {
          // Convert blob to base64 for sending to server
          const reader = new FileReader();
          reader.onloadend = () => {
            const base64data = reader.result.split(",")[1]; // Remove data:image/jpeg;base64, prefix
            this.#onCapture(base64data, imageDataUrl, dimensions, blob.size);
          };
          reader.readAsDataURL(blob);
        },
        "image/jpeg",
        0.85,
      );

      // Close the camera modal
      this.closePreview();
    } catch (error) {
      console.error("Error capturing image:", error);
      this.#onError(`Failed to capture image: ${error.message}`, error);
    }
  }
}
