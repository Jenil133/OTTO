/** "otto knows" — preference pills learned mid-run, each deletable. */
export default function OttoKnows({ knows = [], dispatch }) {
  return (
    <section className="card live-rail-card">
      <h3 className="live-card-title">otto knows</h3>
      {knows.length === 0 ? (
        <div className="live-empty-note">nothing yet</div>
      ) : (
        <div className="live-knows">
          {knows.map((text) => (
            <span className="pill accent live-know" key={text}>
              {text}
              <button
                className="live-know-x"
                aria-label={`forget ${text}`}
                onClick={() => dispatch({ type: 'ui/delete_know', text })}
              >
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth="2.5" strokeLinecap="round">
                  <line x1="6" y1="6" x2="18" y2="18" />
                  <line x1="18" y1="6" x2="6" y2="18" />
                </svg>
              </button>
            </span>
          ))}
        </div>
      )}
    </section>
  )
}
