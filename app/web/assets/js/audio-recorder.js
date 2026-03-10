/**
 * Audio Recorder Worklet
 */

let micStream;

async function createAudioRecorderWorklet(stream, audioRecorderHandler) {
  const audioRecorderContext = new AudioContext({ sampleRate: 16000 });
  console.log("AudioContext sample rate:", audioRecorderContext.sampleRate);

  const workletURL = new URL("./pcm-recorder-processor.js", import.meta.url);
  await audioRecorderContext.audioWorklet.addModule(workletURL);

  const source = audioRecorderContext.createMediaStreamSource(stream);
  const audioRecorderNode = new AudioWorkletNode(
    audioRecorderContext,
    "pcm-recorder-processor",
  );

  source.connect(audioRecorderNode);
  audioRecorderNode.port.onmessage = (event) => {
    const pcmData = convertFloat32ToPCM(event.data);
    audioRecorderHandler(pcmData);
  };

  return [audioRecorderNode, audioRecorderContext, stream];
}

export async function startAudioRecorderWorklet(audioRecorderHandler) {
  micStream = await navigator.mediaDevices.getUserMedia({
    audio: { channelCount: 1 },
  });
  return createAudioRecorderWorklet(micStream, audioRecorderHandler);
}

export async function startStreamAudioRecorderWorklet(
  mediaStream,
  audioRecorderHandler,
) {
  return createAudioRecorderWorklet(mediaStream, audioRecorderHandler);
}

/**
 * Stop the microphone.
 */
export function stopMicrophone(micStream) {
  micStream.getTracks().forEach((track) => track.stop());
  console.log("stopMicrophone(): Microphone stopped.");
}

// Convert Float32 samples to 16-bit PCM.
function convertFloat32ToPCM(inputData) {
  // Create an Int16Array of the same length.
  const pcm16 = new Int16Array(inputData.length);
  for (let i = 0; i < inputData.length; i++) {
    // Multiply by 0x7fff (32767) to scale the float value to 16-bit PCM range.
    pcm16[i] = inputData[i] * 0x7fff;
  }
  // Return the underlying ArrayBuffer.
  return pcm16.buffer;
}
