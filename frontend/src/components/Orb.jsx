import './orb.css'

/**
 * The orb — the ONLY big element in the app (design law 5).
 * mode: 'idle' | 'recording' | 'processing'
 * size: px diameter of the disc (rings extend beyond)
 */
export default function Orb({ mode = 'idle', size = 96, onPressStart, onPressEnd, label }) {
  return (
    <div className={`orb-wrap orb-${mode}`}>
      <div
        className="orb"
        style={{ width: size, height: size }}
        onMouseDown={onPressStart}
        onMouseUp={onPressEnd}
        onMouseLeave={mode === 'recording' ? onPressEnd : undefined}
        onTouchStart={onPressStart}
        onTouchEnd={onPressEnd}
        role="button"
        aria-label="hold to talk"
      >
        <span className="orb-ring r1" />
        <span className="orb-ring r2" />
        <span className="orb-disc">
          <svg className="orb-mic" viewBox="0 0 24 24" width={size * 0.3} height={size * 0.3} fill="none"
            stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <rect x="9" y="2.5" width="6" height="11" rx="3" />
            <path d="M5 11a7 7 0 0 0 14 0" />
            <line x1="12" y1="18" x2="12" y2="21.5" />
          </svg>
        </span>
      </div>
      {label && (
        <div className="orb-label">
          <span className="orb-eq"><i /><i /><i /><i /></span>
          <span className="orb-label-text">{label}</span>
        </div>
      )}
    </div>
  )
}
