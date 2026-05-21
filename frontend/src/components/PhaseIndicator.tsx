interface PhaseIndicatorProps {
  currentPhase: number;
  totalPhases?: number;
}

const PHASE_LABELS = [
  'Background',
  'Project #1',
  'Project #2',
  'Factual',
  'Behavioral',
];

export default function PhaseIndicator({ currentPhase, totalPhases = 5 }: PhaseIndicatorProps) {
  return (
    <div className="w-full px-4 py-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
          Interview Progress
        </span>
        <span className="text-xs font-medium text-indigo-400">
          Phase {currentPhase} of {totalPhases}
        </span>
      </div>

      <div className="flex items-center gap-1">
        {Array.from({ length: totalPhases }, (_, i) => {
          const phase = i + 1;
          const isActive = phase === currentPhase;
          const isCompleted = phase < currentPhase;

          return (
            <div key={phase} className="flex-1 flex flex-col items-center gap-1.5">
              {/* Bar segment */}
              <div
                className={`w-full h-2 rounded-full transition-all duration-500 ${
                  isCompleted
                    ? 'bg-indigo-500'
                    : isActive
                      ? 'bg-indigo-400 shadow-sm shadow-indigo-400/50'
                      : 'bg-gray-700'
                }`}
              />
              {/* Label */}
              <span
                className={`text-[10px] font-medium transition-colors duration-300 ${
                  isActive
                    ? 'text-indigo-300'
                    : isCompleted
                      ? 'text-gray-400'
                      : 'text-gray-600'
                }`}
              >
                {PHASE_LABELS[i] ?? `Phase ${phase}`}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
