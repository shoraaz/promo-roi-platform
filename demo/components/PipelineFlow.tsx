const nodes = [
  {
    idx: '01',
    name: 'BigQuery',
    sub: 'Feature engineering',
    detail: '376K promo events · rolling baselines · lag features · SQL',
  },
  {
    idx: '02',
    name: 'Vertex AI',
    sub: 'Training + Optuna',
    detail: 'Bayesian HPO · 50 trials/model · XGBoost dual-target',
  },
  {
    idx: '03',
    name: 'GCS',
    sub: 'Model artifacts',
    detail: 'Versioned .pkl + SHAP explainer · experiment tracking',
  },
  {
    idx: '04',
    name: 'GKE + FastAPI',
    sub: 'Live serving',
    detail: 'REST endpoint · SHAP per request · <100ms · Pydantic',
  },
  {
    idx: '05',
    name: 'Grafana',
    sub: 'Observability',
    detail: 'Prometheus metrics · drift alerts · p95 latency',
  },
]

function Connector() {
  return (
    <div className="hidden md:flex items-center justify-center w-8 shrink-0">
      <svg width="32" height="2" viewBox="0 0 32 2">
        <line
          x1="0" y1="1" x2="32" y2="1"
          stroke="var(--line-bright)"
          strokeWidth="1"
          className="arrow-animated"
          strokeDasharray="4 5"
        />
      </svg>
    </div>
  )
}

export default function PipelineFlow() {
  return (
    <section className="px-6 py-24 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-14">
        <p className="register mb-3">§02 — ARCHITECTURE</p>
        <h2 className="text-2xl md:text-3xl font-medium mb-3">End-to-end pipeline</h2>
        <p className="max-w-xl" style={{ color: 'var(--ink-dim)' }}>
          From raw sales data in BigQuery to live predictions with SHAP explainability — all on GCP.
        </p>
      </div>

      {/* Pipeline row */}
      <div className="flex flex-col md:flex-row items-stretch justify-center gap-3 md:gap-0">
        {nodes.map((node, i) => (
          <div key={node.name} className="flex flex-col md:flex-row items-center w-full md:w-auto">
            {/* Node row */}
            <div className="row w-full md:w-44 p-4 flex-shrink-0">
              <div className="font-mono text-xs mb-3" style={{ color: 'var(--ink-faint)' }}>{node.idx}</div>
              <div className="text-sm font-medium mb-0.5">{node.name}</div>
              <div className="font-mono text-xs mb-2" style={{ color: 'var(--amber)' }}>{node.sub}</div>
              <div className="text-xs leading-relaxed" style={{ color: 'var(--ink-faint)' }}>{node.detail}</div>
            </div>
            {i < nodes.length - 1 && <Connector />}
          </div>
        ))}
      </div>

      {/* CI/CD note */}
      <div className="mt-8 row px-6 py-3 flex items-center gap-3 text-sm" style={{ color: 'var(--ink-dim)' }}>
        <span className="font-mono text-xs" style={{ color: 'var(--ink-faint)' }}>CI/CD</span>
        <span style={{ color: 'var(--line-bright)' }}>·</span>
        <span>
          <span style={{ color: 'var(--ink)' }}>Cloud Build</span> — git push triggers automated
          retrain, model promotion, and rolling GKE deployment.
        </span>
      </div>
    </section>
  )
}
