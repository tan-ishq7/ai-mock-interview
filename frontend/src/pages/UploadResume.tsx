import { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadResume, startInterview } from '../services/api';

export default function UploadResume() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [candidateId, setCandidateId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback((selectedFile: File) => {
    if (selectedFile.type !== 'application/pdf') {
      setError('Please upload a PDF file.');
      return;
    }
    setError(null);
    setFile(selectedFile);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) handleFile(droppedFile);
    },
    [handleFile],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleUpload = useCallback(async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);
    try {
      const result = await uploadResume(file);
      setCandidateId(result.candidate_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  }, [file]);

  const handleStartInterview = useCallback(async () => {
    if (!candidateId) return;
    try {
      const result = await startInterview(candidateId);
      // Store the initial greeting for the Interview page to read
      sessionStorage.setItem(
        `interview_${result.session_id}`,
        JSON.stringify({ message: result.message, phase: result.phase }),
      );
      navigate(`/interview/${result.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start interview');
    }
  }, [candidateId, navigate]);

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center p-6">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold text-white mb-3 tracking-tight">
          AI Interview Platform
        </h1>
        <p className="text-gray-400 text-lg max-w-md">
          Upload your resume to begin your AI-powered technical interview
        </p>
      </div>

      {/* Upload Card */}
      <div className="w-full max-w-lg">
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => !file && fileInputRef.current?.click()}
          className={`relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 ${
            isDragging
              ? 'border-indigo-400 bg-indigo-500/10 scale-[1.02]'
              : file
                ? 'border-emerald-500/50 bg-emerald-500/5'
                : 'border-gray-700 bg-gray-900/50 hover:border-gray-500 hover:bg-gray-900'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => {
              const selected = e.target.files?.[0];
              if (selected) handleFile(selected);
            }}
          />

          {file ? (
            <div className="space-y-3">
              <div className="w-16 h-16 mx-auto rounded-xl bg-emerald-500/10 flex items-center justify-center">
                <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-white font-medium text-lg">{file.name}</p>
              <p className="text-gray-500 text-sm">
                {(file.size / 1024).toFixed(1)} KB
              </p>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setFile(null);
                  setCandidateId(null);
                }}
                className="text-sm text-gray-400 hover:text-white underline underline-offset-2 transition-colors"
              >
                Choose a different file
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="w-16 h-16 mx-auto rounded-xl bg-gray-800 flex items-center justify-center">
                <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
              </div>
              <div>
                <p className="text-white font-medium text-lg">
                  Drop your resume here
                </p>
                <p className="text-gray-500 text-sm mt-1">
                  or click to browse (PDF only)
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-6 flex flex-col gap-3">
          {file && !candidateId && (
            <button
              onClick={handleUpload}
              disabled={isUploading}
              className="w-full py-3.5 px-6 rounded-xl font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-indigo-600/20 hover:shadow-indigo-500/30"
            >
              {isUploading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Uploading...
                </span>
              ) : (
                'Upload Resume'
              )}
            </button>
          )}

          {candidateId && (
            <button
              onClick={handleStartInterview}
              className="w-full py-3.5 px-6 rounded-xl font-semibold text-white bg-emerald-600 hover:bg-emerald-500 transition-all duration-200 shadow-lg shadow-emerald-600/20 hover:shadow-emerald-500/30"
            >
              Start Interview
            </button>
          )}
        </div>
      </div>

      {/* Footer */}
      <p className="mt-12 text-gray-600 text-xs">
        Your resume data is processed securely and used only for this interview session.
      </p>
    </div>
  );
}
