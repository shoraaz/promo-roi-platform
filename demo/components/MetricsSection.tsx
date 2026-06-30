const phases = [
  { phase: 'Phase 1–6', label: 'Baseline XGBoost', sales_r2: '0.433', margin_r2: '0.632', notes: 'Core features, no HPO' },
  { phase: 'Phase 7',   label: 'Interaction features', sales_r2: '0.440', margin_r2: '0.640', notes: 'promo_gap × baseline + competition × store_type' },
  { phase: 'Phase 8',   label: 'Optuna tuning',  sales_r2: '0.498', margin_r2: '0.700', notes: '50-trial Bayesian HPO per target' },
  { phase: 'Phase 9',   label: '+ Seasonality',  sales_r2: '0.544', margin_r2: '0.711', notes: 'month_sin/cos — SHAP rank 6-7' },
]

const shapFeatures = [
  { rank: 1,  name: 'baseline_sales_30d',     note: 'Store volume drives absolute impact' },
  { rank: 2,  name: 'lag_7_sales',            note: 'Recent momentum predicts promo uptake' },
  { rank: 3,  name: 'promo_gap × baseline',   note: 'Pent-up demand × store size (engineered)' },
  { rank: 4,  name: 'lag_30_sales',           note: 'Medium-term trend signal' },
  { rank: 5,  name: 'competition_distance',   note: 'Market pressure moderates lift' },
  { rank: '6–7', name: 'month_sin / month_cos', note: 'Cyclical seasonality encoding' },
]

export default function MetricsSection() {
  return (
    <section className="px-6 py-24 max-w-6xl mx-auto">
      <div className="mb-14">
        <p className="register mb-3">§01 — RESULTS</p>
        <h2 className="text-2xl md:text-3xl font-medium mb-3">Model performance</h2>
        <p style={{ color: 'var(--ink-dim)' }}>9 training phases · Optuna-tuned · validated on 45K held-out promo events</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* R² progression table */}
        <div className="row p-6">
          <h3 className="text-sm font-medium mb-1">R² progression by phase</h3>
          <p className="text-xs mb-5" style={{ color: 'var(--ink-faint)' }}>Higher = model explains more variance in the held-out set</p>
          <div className="space-y-0">
            {phases.map((p, i) => (
              <div key={p.phase} className={`py-3 ${i !== 0 ? 'hairline' : ''} ${i === phases.length - 1 ? 'pl-3' : ''}`}
                style={i === phases.length - 1 ? { borderLeft: '2px solid var(--amber)' } : undefined}>
                <div className="flex items-center justify-between mb-1.5">
                  <div>
                    <span className="font-mono text-xs" style={{ color: 'var(--ink-faint)' }}>{p.phase}</span>
                    <span className="text-sm font-medium ml-2">{p.label}</span>
                  </div>
                  {i === phases.length - 1 && (
                    <span className="font-mono text-[10px] tracking-wider" style={{ color: 'var(--amber)' }}>FINAL</span>
                  )}
                </div>
                <div className="font-mono flex gap-5 text-xs" style={{ color: 'var(--ink-dim)' }}>
                  <span>SALES R² <span className="sig-positive">{p.sales_r2}</span></span>
                  <span>MARGIN R² <span className="sig-positive">{p.margin_r2}</span></span>
                </div>
                <div className="text-xs mt-1" style={{ color: 'var(--ink-faint)' }}>{p.notes}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Final metrics + SHAP rankings */}
        <div className="space-y-6">
          <div className="row p-6">
            <h3 className="text-sm font-medium mb-4">Final model — Phase 9</h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Sales lift RMSE',  value: '19.85%', delta: '−10.3% vs baseline' },
                { label: 'Margin RMSE',      value: '240.99', delta: '−11.3% vs baseline' },
                { label: 'Sales lift R²',    value: '0.544',  delta: '+0.111 improvement' },
                { label: 'Margin R²',        value: '0.711',  delta: '+0.079 improvement' },
              ].map((m) => (
                <div key={m.label} className="p-3" style={{ background: 'var(--row)' }}>
                  <div className="font-mono text-lg font-medium">{m.value}</div>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--ink-dim)' }}>{m.label}</div>
                  <div className="font-mono text-xs sig-positive mt-1">{m.delta}</div>
                </div>
              ))}
            </div>
          </div>

          {/* SHAP feature importance */}
          <div className="row p-6">
            <h3 className="text-sm font-medium mb-1">Top SHAP features</h3>
            <p className="text-xs mb-4" style={{ color: 'var(--ink-faint)' }}>Ranked by mean absolute SHAP value on validation set</p>
            <div className="space-y-2.5">
              {shapFeatures.map((f) => (
                <div key={f.rank} className="flex items-start gap-3">
                  <span className="font-mono text-xs w-5 shrink-0 mt-0.5" style={{ color: 'var(--ink-faint)' }}>{f.rank}</span>
                  <div>
                    <span className="font-mono text-xs" style={{ color: 'var(--amber)' }}>{f.name}</span>
                    <span className="text-xs" style={{ color: 'var(--ink-faint)' }}> · {f.note}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Data split / drift info */}
      <div className="mt-6 grid md:grid-cols-3 gap-3">
        {[
          { label: 'Training set',   value: '331,875 rows', sub: 'Jan 2013 – Mar 2015' },
          { label: 'Validation set',  value: '45,000 rows',  sub: 'Apr – Jul 2015 (held-out)' },
          { label: 'Drift check',     value: 'PSI ≤ 0.039',  sub: 'All 13 features < 0.10 threshold' },
        ].map((d) => (
          <div key={d.label} className="row p-4">
            <div className="font-mono text-[10px] tracking-wider mb-2" style={{ color: 'var(--ink-faint)' }}>{d.label.toUpperCase()}</div>
            <div className="text-sm font-medium">{d.value}</div>
            <div className="text-xs mt-0.5" style={{ color: 'var(--ink-faint)' }}>{d.sub}</div>
          </div>
        ))}
      </div>
    </section>
  )
}
