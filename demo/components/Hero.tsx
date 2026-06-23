'use client'
export default function Hero() {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden">
      {/* Ambient glow orbs */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] rounded-full"
        style={{ background: 'radial-gradient(ellipse, rgba(99,102,241,0.08) 0%, transparent 70%)' }} />
      <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] rounded-full"
        style={{ background: 'radial-gradient(ellipse, rgba(168,85,247,0.05) 0%, transparent 70%)' }} />

      {/* Subtle dot grid */}
      <div className="absolute inset-0 opacity-[0.03]"
        style={{ backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)', backgroundSize: '32px 32px' }} />

      <div className="relative z-10 text-center max-w-4xl mx-auto">
        {/* Eyebrow badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full mb-8"
          style={{ border: '1px solid rgba(129,140,248,0.25)', background: 'rgba(99,102,241,0.08)' }}>
          <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse-slow" />
          <span className="text-indigo-400 text-xs font-semibold tracking-widest uppercase">
            GCP Production ML System
          </span>
        </div>

        {/* Title */}
        <h1 className="text-6xl md:text-8xl font-extrabold tracking-tight text-white mb-6 leading-none">
          Promo{' '}
          <span className="gradient-text">ROI</span>
          <br />
          Platform
        </h1>

        {/* Subtitle */}
        <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-12 leading-relaxed">
          Predicts whether retail promotions will be <em className="text-gray-300 not-italic font-medium">profitable</em> before
          you run them — dual XGBoost models with SHAP explainability, trained on 376K promo events.
        </p>

        {/* Stats row */}
        <div className="flex flex-wrap justify-center gap-3 mb-12">
          {[
            { value: '376K',   label: 'Promo events' },
            { value: '2',      label: 'XGBoost models' },
            { value: 'R² 0.71',label: 'Margin model' },
            { value: '−11.3%', label: 'RMSE vs baseline' },
            { value: 'PSI <0.04', label: 'No feature drift' },
          ].map((s) => (
            <div key={s.label} className="card px-5 py-3 text-center min-w-[100px]">
              <div className="text-xl font-bold text-white">{s.value}</div>
              <div className="text-xs text-gray-500 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>

        {/* CTAs */}
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <a
            href="#demo"
            className="px-7 py-3.5 rounded-xl font-semibold text-white transition-all duration-200"
            style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
            onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.85')}
            onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
          >
            Try the Demo →
          </a>
          <a
            href="https://github.com/shoraaz/promo-roi-platform"
            target="_blank"
            rel="noopener noreferrer"
            className="px-7 py-3.5 rounded-xl font-semibold text-gray-300 hover:text-white transition-all duration-200"
            style={{ border: '1px solid rgba(255,255,255,0.10)' }}
          >
            GitHub ↗
          </a>
        </div>
      </div>

      {/* Scroll cue */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-gray-700">
        <span className="text-[10px] tracking-[0.2em] uppercase">Scroll</span>
        <div className="w-px h-10 bg-gradient-to-b from-gray-700 to-transparent" />
      </div>
    </section>
  )
}
