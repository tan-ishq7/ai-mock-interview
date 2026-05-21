import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { sendMessage, transcribeAudio, synthesizeSpeech, evaluateSession } from '../services/api';
import ChatBubble from '../components/ChatBubble';
import AudioRecorder from '../components/AudioRecorder';
import PhaseIndicator from '../components/PhaseIndicator';

interface Message {
  role: 'interviewer' | 'candidate';
  content: string;
  isHint?: boolean;
}

export default function Interview() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentPhase, setCurrentPhase] = useState(1);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // The initial greeting is already returned by startInterview.
  // Read it from sessionStorage (set by UploadResume page).
  useEffect(() => {
    const stored = sessionStorage.getItem(`interview_${sessionId}`);
    if (stored) {
      const data = JSON.parse(stored);
      setMessages([{ role: 'interviewer', content: data.message }]);
      if (data.phase) setCurrentPhase(data.phase);
      sessionStorage.removeItem(`interview_${sessionId}`);
    }
  }, [sessionId]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || !sessionId || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'candidate', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await sendMessage(sessionId, userMessage);

      // Add interviewer response (may be a hint)
      setMessages((prev) => [
        ...prev,
        {
          role: 'interviewer',
          content: response.message,
          isHint: response.is_hint || false,
        },
      ]);

      if (response.phase) setCurrentPhase(response.phase);

      // Handle anxiety break
      if (response.anxiety_break) {
        // The message already contains the comfort text
      }

      // Handle interview completion
      if (response.interview_complete) {
        // Trigger evaluation, then redirect to report
        try {
          await evaluateSession(sessionId);
        } catch {
          // Evaluation may already exist
        }
        setTimeout(() => navigate(`/report/${sessionId}`), 2000);
      }

      // Auto-play speech
      try {
        const audioBlob = await synthesizeSpeech(response.message);
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play().catch(() => {});
      } catch {
        // Speech synthesis is optional
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'interviewer', content: 'Sorry, there was an error. Please try again.' },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [input, sessionId, isLoading, navigate]);

  const handleAudioComplete = useCallback(
    async (blob: Blob) => {
      if (!sessionId) return;
      setIsLoading(true);
      try {
        const transcription = await transcribeAudio(blob);
        const text = transcription.text;
        const anxietyDetected = transcription.anxiety_detected || false;
        setMessages((prev) => [...prev, { role: 'candidate', content: text }]);

        const response = await sendMessage(sessionId, text, anxietyDetected);
        setMessages((prev) => [
          ...prev,
          {
            role: 'interviewer',
            content: response.message,
            isHint: response.is_hint || false,
          },
        ]);
        if (response.phase) setCurrentPhase(response.phase);
        if (response.interview_complete) {
          try { await evaluateSession(sessionId); } catch {}
          setTimeout(() => navigate(`/report/${sessionId}`), 2000);
        }

        // Auto-play speech
        try {
          const audioBlob = await synthesizeSpeech(response.message);
          const audioUrl = URL.createObjectURL(audioBlob);
          new Audio(audioUrl).play().catch(() => {});
        } catch {}
      } catch {
        setMessages((prev) => [
          ...prev,
          { role: 'interviewer', content: 'Sorry, I could not process your audio. Please try typing instead.' },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, navigate],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      {/* Top Bar */}
      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between px-4 py-3">
            <h1 className="text-lg font-semibold text-white tracking-tight">
              Technical Interview
            </h1>
            <span className="text-xs text-gray-500 font-mono">
              {sessionId?.slice(0, 8)}
            </span>
          </div>
          <PhaseIndicator currentPhase={currentPhase} />
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-1">
          {messages.map((msg, i) => (
            <ChatBubble
              key={i}
              role={msg.role}
              content={msg.content}
              isHint={msg.isHint}
            />
          ))}

          {isLoading && (
            <div className="flex justify-start mb-4">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-full bg-indigo-600 flex items-center justify-center text-sm font-semibold text-white">
                  AI
                </div>
                <div className="px-4 py-3 rounded-2xl bg-gray-800 border border-gray-700">
                  <div className="flex gap-1.5">
                    <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0ms]" />
                    <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:150ms]" />
                    <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Bar */}
      <footer className="border-t border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky bottom-0">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-end gap-3">
            <AudioRecorder onRecordingComplete={handleAudioComplete} disabled={isLoading} />
            <div className="flex-1 relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your response..."
                rows={1}
                disabled={isLoading}
                className="w-full resize-none rounded-xl bg-gray-900 border border-gray-700 px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50 transition-all"
              />
            </div>
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="flex items-center justify-center w-12 h-12 rounded-xl bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-indigo-600/20"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
              </svg>
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
