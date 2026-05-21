import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getReport, evaluateSession } from '../services/api';

interface PhaseDetail {
  name: string;
  composite?: number;
  accuracy?: number;
  max_depth?: number;
  hints_given?: number;
  hints_recovered?: number;
  visionary?: number;
  grounded?: number;
  teamplayer?: number;
  correct?: number;
  total?: number;
}

interface ReportData {
  overall_score: number;
  phase_scores: Record<string, PhaseDetail>;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  report_text: string;
}

export default function Report() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    const fetchReport = async () => {
      try {
        // Try to get existing report first
        const data = await getReport(sessionId);
        setReport(data.report || data);
      } catch {
        // If no report yet, trigger evaluation
        try {
          const evalResult = await evaluateSession(sessionId);
          setReport(evalResult.report);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to load report');
        }
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [sessionId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <svg className="animate-spin h-10 w-10 text-indigo-500" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-gray-400 text-sm">Generating your evaluation report...</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-red-400">{error ?? 'Report not available'}</p>
          <button
            onClick={() => navigate('/')}
            className="text-indigo-400 hover:text-indigo-300 underline underline-offset-2 text-sm"
          >
            Return to home
          </button>
        </div>
      </div>
    );
  }

  const scorePercent = Math.round(report.overall_score);
  const scoreColor =
    scorePercent >= 80
      ? 'text-emerald-400'
      : scorePercent >= 60
        ? 'text-amber-400'
        : 'text-red-400';

  const scoreRingColor =
    scorePercent >= 80
      ? 'stroke-emerald-500'
      : scorePercent >= 60
        ? 'stroke-amber-500'
        : 'stroke-red-500';

  // Convert phase_scores object to array for rendering
  const phases = Object.entries(report.phase_scores || {}).map(([key, val]) => ({
    key,
    name: val.name,
    score: val.composite ?? val.accuracy ?? 0,
    details: val,
  }));

  return (
    <div className="min-h-screen bg-gray-950 py-10 px-4">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white tracking-tight">
            Interview Report
          </h1>
          <p className="text-gray-500 text-sm mt-2 font-mono">
            Session: {sessionId?.slice(0, 12)}
          </p>
        </div>

        {/* Overall Score */}
        <div className="flex justify-center">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 flex flex-col items-center gap-4 w-64">
            <div className="relative w-32 h-32">
              <svg className="w-32 h-32 -rotate-90" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="52" fill="none" stroke="currentColor" strokeWidth="8" className="text-gray-800" />
                <circle
                  cx="60"
                  cy="60"
                  r="52"
                  fill="none"
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={`${(scorePercent / 100) * 327} 327`}
                  className={scoreRingColor}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className={`text-3xl font-bold ${scoreColor}`}>
                  {scorePercent}
                </span>
              </div>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-400">Overall Score</p>
              <p className="text-xs text-gray-600 mt-1">
                {report.overall_score} / 100
              </p>
            </div>
          </div>
        </div>

        {/* Full Report Text */}
        {report.report_text && (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
            <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
              Detailed Report
            </h2>
            <div className="text-gray-400 text-sm leading-relaxed whitespace-pre-wrap">
              {report.report_text}
            </div>
          </div>
        )}

        {/* Phase Scores Grid */}
        <div>
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
            Phase Breakdown
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {phases.map((phase) => {
              const phasePercent = Math.round(phase.score);
              const barColor =
                phasePercent >= 80
                  ? 'bg-emerald-500'
                  : phasePercent >= 60
                    ? 'bg-amber-500'
                    : 'bg-red-500';

              return (
                <div
                  key={phase.key}
                  className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <h3 className="text-white font-medium text-sm">
                      {phase.name}
                    </h3>
                    <span className="text-xs text-gray-500">
                      {phasePercent}/100
                    </span>
                  </div>
                  <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${barColor}`}
                      style={{ width: `${phasePercent}%` }}
                    />
                  </div>
                  {/* Phase-specific details */}
                  <div className="text-gray-500 text-xs space-y-1">
                    {phase.details.max_depth !== undefined && (
                      <p>Depth reached: {phase.details.max_depth}/5</p>
                    )}
                    {phase.details.hints_given !== undefined && phase.details.hints_given > 0 && (
                      <p>Hints: {phase.details.hints_recovered}/{phase.details.hints_given} recovered</p>
                    )}
                    {phase.details.correct !== undefined && (
                      <p>Correct: {phase.details.correct}/{phase.details.total}</p>
                    )}
                    {phase.details.visionary !== undefined && (
                      <p>Visionary: {phase.details.visionary}/10 | Grounded: {phase.details.grounded}/10 | Team: {phase.details.teamplayer}/10</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Strengths & Weaknesses */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-emerald-400 uppercase tracking-wider mb-4">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              Strengths
            </h2>
            <ul className="space-y-2">
              {(report.strengths || []).map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                  <span className="text-emerald-500 mt-0.5 flex-shrink-0">+</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-amber-400 uppercase tracking-wider mb-4">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              Areas for Improvement
            </h2>
            <ul className="space-y-2">
              {(report.weaknesses || []).map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                  <span className="text-amber-500 mt-0.5 flex-shrink-0">-</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Recommendations */}
        {report.recommendations && report.recommendations.length > 0 && (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
            <h2 className="text-sm font-semibold text-indigo-400 uppercase tracking-wider mb-4">
              Recommendations
            </h2>
            <ul className="space-y-2">
              {report.recommendations.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                  <span className="text-indigo-400 mt-0.5 flex-shrink-0">{i + 1}.</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-center pt-4 pb-8">
          <button
            onClick={() => navigate('/')}
            className="px-6 py-3 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 transition-all duration-200 shadow-lg shadow-indigo-600/20"
          >
            Start New Interview
          </button>
        </div>
      </div>
    </div>
  );
}
