import { useEffect, useRef } from 'react'

/** Ops feed — the multi-agent "band" chatter. Autoscrolls to the newest line. */
export default function BandFeed({ band = [] }) {
  const bodyRef = useRef(null)

  useEffect(() => {
    const el = bodyRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [band.length])

  return (
    <section className="card live-rail-card live-feed">
      <h3 className="live-card-title">ops feed · band</h3>
      <div className="live-feed-body" ref={bodyRef}>
        {band.map((b, i) => (
          <div className="live-feed-line" key={i}>
            <span className="live-feed-actor">{b.actor}</span> {b.text}
          </div>
        ))}
      </div>
    </section>
  )
}
