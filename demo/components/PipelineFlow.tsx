const nodes = [
  {
    icon: '🗄️',
    name: 'BigQuery',
    sub: 'Feature Engineering',
    detail: '376K promo events · rolling baselines · lag features · SQL',
    color: '#3b82f6',
    bg: 'rgba(59,130,246,0.08)',
    border: 'rgba(59,130,246,0.25)',
  },
  {
    icon: '🧠',
    name: 'Vertex AI',
    sub: 'Training + Optuna',
    detail: 'Bayesian HPO · 50 trials/model · XGBoost dual-target',
    color: '#8b5cf6',
    bg: 'rgba(139,92,246,0.08)',
    border: 'rgba(139,92,246,0.25)',
  },
  {
    icon: '📦',
    name: 'GCS',
    sub: 'Model Artifacts',
    detail: 'Versioned .pkl + SHAP explainer · experiment tracking',
    color: '#f97316',
    bg: 'rgba(249,115,22,0.08)',
    border: 'rgba(249,115,22,0.25)',
  },
  {
    icon: '⚡',
    name: 'GKE + FastAPI',
    sub: 'Live Serving',
    detail: 'REST endpoint · SHAP per request · <100ms · Pydantic',
    color: '#22c55e',
    bg: 'rgba(34,197,94,0.08)',
    border: 'rgba(34,197,94,0.25)',
  },
  {
    icon: '📊',
    name: 'Grafana',
    sub: 'Observability',
    detail: 'Prometheus metrics · drift alerts · p95 latency',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.08)',
    border: 'rgba(245,158,11,0.25)',
  },
]

function Arrow({ color }: { color: string }) {
  return (
    <div className="hidden md:flex items-center justify-center w-10 shrink-0">
      <svg width="40" height="20" viewBox="0 0 40 20">
        <defs>
          <linearGradient id={`grad-${color}`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0.8" />
          </linearGradient>
        </defs>
        <line
          x1="0" y1="10" x2="30" y2="10"
          stroke={`url(#grad-${color})`}
          strokeWidth="1.5"
          className="arrow-animated"
          strokeDasharray="6 6"
        />
        <polyline
          points="25,5 33,10 25,15"
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeOpacity="0.7"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  )
}

export default function PipelineFlow() {
  return (
    <section className="px-6 py-24 max-w-7xl mx-auto">
      {/* Header */}
      <div className="text-center mb-16">
        <p className="text-xs text-indigo-400 font-semibold tracking-widest uppercase mb-3">Architecture</p>
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">End-to-End ML Pipeline</h2>
        <p className="text-gray-400 max-w-xl mx-auto">
          From raw sales data in BigQuery to live predictions with SHAP explainability — all on GCP.
        </p>
      </div>

      {/* Pipeline row */}
      <div className="flex flex-col md:flex-row items-start md:items-stretch justify-center gap-2 md:gap-0">
        {nodes.map((node, i) => (
          <div key={node.name} className="flex flex-col md:flex-row items-center w-full md:w-auto">
            {/* Node card */}
            <div
              className="w-full md:w-44 p-4 rounded-xl flex-shrink-0 transition-all duration-300 hover:-translate-y-1 cursor-default group"
              style={{ background: node.bg, border: `1px solid ${node.border}` }}
            >
              <div className="text-2xl mb-2">{node.icon}</div>
              <div className="text-sm font-bold text-white mb-0.5">{node.name}</div>
              <div className="text-xs font-medium mb-2" style={{ color: node.color }}>{node.sub}</div>
              <div className="text-xs text-gray-500 leading-relaxed">{node.detail}</div>
            </div>
            {/* Arrow between nodes */}
            {i < nodes.length - 1 && <Arrow color={nodes[i + 1].color} />}
          </div>
        ))}
      </div>

      {/* CI/CD note */}
      <div className="mt-10 flex justify-center">
        <div className="card px-6 py-3 flex items-center gap-3 text-sm text-gray-400">
          <span className="text-lg">🔁</span>
          <span>
            <span className="text-gray-200 font-medium">Cloud Build CI/CD</span> — git push triggers automated
            retrain, model promotion, and rolling GKE deployment
          </span>
        </div>
      </div>
    </section>
  )
}
