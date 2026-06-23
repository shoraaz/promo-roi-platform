const phases = [
  { phase: 'Phase 1–6', label: 'Baseline XGBoost', sales_r2: '0.433', margin_r2: '0.632', notes: 'Core features, no HPO' },
  { phase: 'Phase 7',   label: 'Interaction Features', sales_r2: '0.440', margin_r2: '0.640', notes: 'promo_gap × baseline + competition × store_type' },
  { phase: 'Phase 8',   label: 'Optuna Tuning',  sales_r2: '0.498', margin_r2: '0.700', notes: '50-trial Bayesian HPO per target' },
  { phase: 'Phase 9',   label: '+ Seasonality',  sales_r2: '0.544', margin_r2: '0.711', notes: 'month_sin/cos — SHAP rank 6-7' },
]

const shapFeatures = [
  { rank: 1,  name: 'baseline_sales_30d',     target: 'both',   note: 'Store volume drives absolute impact' },
  { rank: 2,  name: 'lag_7_sales',            target: 'both',   note: 'Recent momentum predicts promo uptake' },
  { rank: 3,  name: 'promo_gap × baseline',   target: 'margin', note: 'Pent-up demand × store size (engineered)' },
  { rank: 4,  name: 'lag_30_sales',           target: 'both',   note: 'Medium-term trend signal' },
  { rank: 5,  name: 'competition_distance',   target: 'both',   note: 'Market pressure moderates lift' },
  { rank: '6–7', name: 'month_sin / month_cos', target: 'both', note: 'Cyclical seasonality encoding' },
]

export default function MetricsSection() {
  return (
    <section className="px-6 py-24 max-w-6xl mx-auto">
      <div className="text-center mb-16">
        <p className="text-xs text-indigo-400 font-semibold tracking-widest uppercase mb-3">Results</p>
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Model Performance</h2>
        <p className="text-gray-400">9 training phases · Optuna-tuned · validated on 45K held-out promo events</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        {/* R² progression table */}
        <div className="card p-6">
          <h3 className="text-base font-semibold text-white mb-1">R² Progression by Phase</h3>
          <p className="text-xs text-gray-500 mb-5">Higher = model explains more variance in the held-out set</p>
          <div className="space-y-3">
            {phases.map((p, i) => (
              <div key={p.phase} className={`rounded-lg p-3 ${i === phases.length - 1 ? 'border border-indigo-500/30 bg-indigo-500/5' : ''}`}>
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="text-xs text-gray-500">{p.phase} · </span>
                    <span className="text-sm font-medium text-gray-200">{p.label}</span>
                  </div>
                  {i === phases.length - 1 && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 font-semibold">Final</span>
                  )}
                </div>
                <div className="flex gap-6 text-xs text-gray-400">
                  <span>Sales R² <span className="font-mono text-green-400 font-bold">{p.sales_r2}</span></span>
                  <span>Margin R² <span className="font-mono text-green-400 font-bold">{p.margin_r2}</span></span>
                </div>
                <div className="text-xs text-gray-600 mt-1">{p.notes}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Final metrics + SHAP rankings */}
        <div className="space-y-6">
          {/* Final model numbers */}
          <div className="card p-6">
            <h3 className="text-base font-semibold text-white mb-4">Final Model — Phase 9</h3>
            <div className="grid grid-cols-2 gap-4">
              {[
                { label: 'Sales Lift RMSE',  value: '19.85%', delta: '−10.3% vs baseline' },
                { label: 'Margin RMSE',      value: '240.99', delta: '−11.3% vs baseline' },
                { label: 'Sales Lift R²',    value: '0.544',  delta: '+0.111 improvement' },
                { label: 'Margin R²',        value: '0.711',  delta: '+0.079 improvement' },
              ].map((m) => (
                <div key={m.label} className="rounded-lg p-3" style={{ background: 'rgba(255,255,255,0.03)' }}>
                  <div className="text-lg font-bold text-white">{m.value}</div>
                  <div className="text-xs text-gray-400 mt-0.5">{m.label}</div>
                  <div className="text-xs text-green-500/70 mt-1">{m.delta}</div>
                </div>
              ))}
            </div>
          </div>

          {/* SHAP feature importance */}
          <div className="card p-6">
            <h3 className="text-base font-semibold text-white mb-1">Top SHAP Features</h3>
            <p className="text-xs text-gray-500 mb-4">Ranked by mean absolute SHAP value on validation set</p>
            <div className="space-y-2">
              {shapFeatures.map((f) => (
                <div key={f.rank} className="flex items-start gap-3">
                  <span className="text-xs font-mono text-gray-600 w-4 shrink-0 mt-0.5">#{f.rank}</span>
                  <div>
                    <span className="text-xs font-mono text-indigo-300">{f.name}</span>
                    <span className="text-xs text-gray-600"> · {f.note}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Data split / drift info */}
      <div className="mt-8 grid md:grid-cols-3 gap-4">
        {[
          { icon: '🗂️', label: 'Training set',   value: '331,875 rows', sub: 'Jan 2013 – Mar 2015' },
          { icon: '🔍', label: 'Validation set',  value: '45,000 rows',  sub: 'Apr – Jul 2015 (held-out)' },
          { icon: '✅', label: 'Drift check',     value: 'PSI ≤ 0.039',  sub: 'All 13 features < 0.10 threshold' },
        ].map((d) => (
          <div key={d.label} className="card p-4 flex items-center gap-4">
            <span className="text-2xl">{d.icon}</span>
            <div>
              <div className="text-sm font-bold text-white">{d.value}</div>
              <div className="text-xs text-gray-400">{d.label}</div>
              <div className="text-xs text-gray-600">{d.sub}</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
