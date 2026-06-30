'use client'
export default function Hero() {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden">
      {/* Faint dot grid, kept minimal */}
      <div className="absolute inset-0 opacity-[0.025]"
        style={{ backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)', backgroundSize: '36px 36px' }} />

      <div className="relative z-10 text-center max-w-3xl mx-auto">
        {/* Ticker strip — system status read like a terminal line, not a pill badge */}
        <div className="font-mono ticker-in flex items-center justify-center gap-3 mb-10 text-[11px] tracking-wider"
          style={{ color: 'var(--ink-faint)' }}>
          <span className="inline-block w-1.5 h-1.5" style={{ background: 'var(--amber)' }} />
          <span>GCP · VERTEX AI · GKE AUTOPILOT</span>
          <span style={{ color: 'var(--line-bright)' }}>/</span>
          <span style={{ color: 'var(--ink-dim)' }}>376,012 EVENTS INDEXED</span>
        </div>

        {/* Title */}
        <h1 className="text-6xl md:text-7xl font-medium tracking-tight mb-7 leading-none">
          Margin<span className="accent-text font-mono font-medium">Lens</span>
        </h1>

        {/* Subtitle */}
        <p className="text-base md:text-lg max-w-xl mx-auto mb-12 leading-relaxed" style={{ color: 'var(--ink-dim)' }}>
          Predicts whether a retail promotion will be profitable before you run it —
          dual XGBoost models, SHAP-explained, trained on 376K promo events.
        </p>

        {/* Signature number — one stat given real weight, instead of five equal pills */}
        <div className="mb-12 ticker-in" style={{ animationDelay: '0.1s' }}>
          <div className="font-mono text-5xl md:text-6xl font-medium mb-2">
            <span className="sig-positive">−11.3%</span>
          </div>
          <div className="font-mono text-xs tracking-wider" style={{ color: 'var(--ink-faint)' }}>
            MARGIN RMSE, VS. BASELINE
          </div>
          <div className="font-mono flex items-center justify-center gap-5 mt-5 text-xs flex-wrap" style={{ color: 'var(--ink-dim)' }}>
            <span>SALES R² <span style={{ color: 'var(--ink)' }}>0.544</span></span>
            <span style={{ color: 'var(--line-bright)' }}>·</span>
            <span>MARGIN R² <span style={{ color: 'var(--ink)' }}>0.711</span></span>
            <span style={{ color: 'var(--line-bright)' }}>·</span>
            <span>DRIFT PSI <span style={{ color: 'var(--ink)' }}>&lt;0.04</span></span>
          </div>
        </div>

        {/* CTAs */}
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <a
            href="#demo"
            className="font-mono px-6 py-3 text-sm tracking-wide transition-colors duration-150"
            style={{ background: 'var(--amber)', color: '#1A1306' }}
          >
            Try the demo →
          </a>
          <a
            href="https://github.com/shoraaz/MarginLens"
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono px-6 py-3 text-sm tracking-wide transition-colors duration-150"
            style={{ border: '1px solid var(--line-bright)', color: 'var(--ink-dim)' }}
          >
            View source ↗
          </a>
        </div>
      </div>

      {/* Scroll cue */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 font-mono text-[10px] tracking-[0.2em]" style={{ color: 'var(--ink-faint)' }}>
        <span>SCROLL</span>
        <div className="w-px h-8" style={{ background: 'linear-gradient(to bottom, var(--ink-faint), transparent)' }} />
      </div>
    </section>
  )
}
