interface ChatBubbleProps {
  role: 'interviewer' | 'candidate';
  content: string;
  isHint?: boolean;
}

export default function ChatBubble({ role, content, isHint = false }: ChatBubbleProps) {
  const isInterviewer = role === 'interviewer';

  return (
    <div className={`flex ${isInterviewer ? 'justify-start' : 'justify-end'} mb-4`}>
      <div className={`flex items-start gap-3 max-w-[75%] ${isInterviewer ? 'flex-row' : 'flex-row-reverse'}`}>
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold ${
            isInterviewer
              ? 'bg-indigo-600 text-white'
              : 'bg-emerald-600 text-white'
          }`}
        >
          {isInterviewer ? 'AI' : 'You'}
        </div>

        {/* Bubble */}
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
            isHint
              ? 'bg-amber-500/10 border border-amber-500/30 text-amber-200 italic'
              : isInterviewer
                ? 'bg-gray-800 text-gray-100 border border-gray-700'
                : 'bg-indigo-600 text-white'
          }`}
        >
          {isHint && (
            <span className="text-xs font-medium text-amber-400 block mb-1">Hint</span>
          )}
          <p className="whitespace-pre-wrap">{content}</p>
        </div>
      </div>
    </div>
  );
}
