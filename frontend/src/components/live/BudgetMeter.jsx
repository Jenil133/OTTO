/** Time-budget meter — used vs cap seconds for the current run. */
export default function BudgetMeter({ budget = { used_s: 0, cap_s: 90 } }) {
  const pct = budget.cap_s ? Math.min(100, (budget.used_s / budget.cap_s) * 100) : 0
  return (
    <section className="card live-rail-card">
      <h3 className="live-card-title">budget</h3>
      <div className="live-budget-nums">
        <span className="live-budget-used">{budget.used_s}s</span>
        <span className="live-budget-cap">/ {budget.cap_s}s</span>
      </div>
      <div className="bar">
        <i style={{ width: `${pct}%` }} />
      </div>
    </section>
  )
}
