const BASE_URL = '/api';

export async function uploadResume(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${BASE_URL}/resume/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed: ${response.statusText}`);
  }

  return response.json();
}

export async function startInterview(candidateId: string) {
  const response = await fetch(`${BASE_URL}/interview/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ candidate_id: candidateId }),
  });

  if (!response.ok) {
    throw new Error(`Failed to start interview: ${response.statusText}`);
  }

  return response.json();
}

export async function sendMessage(
  sessionId: string,
  text: string,
  anxietyDetected = false,
) {
  const response = await fetch(`${BASE_URL}/interview/${sessionId}/respond`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, anxiety_detected_voice: anxietyDetected }),
  });

  if (!response.ok) {
    throw new Error(`Failed to send message: ${response.statusText}`);
  }

  return response.json();
}

export async function transcribeAudio(audioBlob: Blob) {
  const formData = new FormData();
  formData.append('file', audioBlob, 'recording.webm');

  const response = await fetch(`${BASE_URL}/voice/transcribe`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Transcription failed: ${response.statusText}`);
  }

  return response.json();
}

export async function synthesizeSpeech(text: string): Promise<Blob> {
  const response = await fetch(`${BASE_URL}/voice/synthesize-raw`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(`Speech synthesis failed: ${response.statusText}`);
  }

  return response.blob();
}

export async function evaluateSession(sessionId: string) {
  const response = await fetch(`${BASE_URL}/evaluation/${sessionId}/evaluate`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Evaluation failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getReport(sessionId: string) {
  const response = await fetch(`${BASE_URL}/evaluation/${sessionId}/report`);

  if (!response.ok) {
    throw new Error(`Failed to get report: ${response.statusText}`);
  }

  return response.json();
}
