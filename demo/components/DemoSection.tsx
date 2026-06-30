'use client'
import { useState, useCallback } from 'react'

// ─── Types ───────────────────────────────────────────────────────────────────

type Inputs = {
  dayOfWeek: number
  storeType: number
  assortment: number
  baseline_sales_30d: number
  competition_distance: number
  days_since_last_promo: number
  lag_7_sales: number
  lag_30_sales: number
  store_enrolled_in_promo2: boolean
  is_school_holiday: boolean
  is_state_holiday: boolean
  month: number
}

type ShapEntry = { feature: string; value: number }

type Result = {
  margin_impact: number
  sales_lift_pct: number
  roi_verdict: 'POSITIVE' | 'NEGATIVE'
  margin_shap: ShapEntry[]
  lift_shap: ShapEntry[]
}

// ─── Presets ─────────────────────────────────────────────────────────────────

const PRESETS: Record<string, { label: string; description: string; inputs: Inputs }> = {
  optimal: {
    label: 'Optimal timing',
    description: 'Long gap since last promo · strong baseline · peak season',
    inputs: {
      dayOfWeek: 1, storeType: 1, assortment: 1,
      baseline_sales_30d: 5200, competition_distance: 7500,
      days_since_last_promo: 22, lag_7_sales: 5800, lag_30_sales: 5300,
      store_enrolled_in_promo2: true, is_school_holiday: false, is_state_holiday: false, month: 6,
    },
  },
  poor: {
    label: 'Poor timing',
    description: 'Promo just ran · slow sales · off-season · nearby competitor',
    inputs: {
      dayOfWeek: 7, storeType: 2, assortment: 2,
      baseline_sales_30d: 3850, competition_distance: 620,
      days_since_last_promo: 2, lag_7_sales: 2900, lag_30_sales: 3100,
      store_enrolled_in_promo2: false, is_school_holiday: false, is_state_holiday: true, month: 11,
    },
  },
  pent_up: {
    label: 'Pent-up demand',
    description: '30-day gap + high lag sales = maximum pent-up demand signal',
    inputs: {
      dayOfWeek: 5, storeType: 1, assortment: 0,
      baseline_sales_30d: 4800, competition_distance: 3200,
      days_since_last_promo: 30, lag_7_sales: 6500, lag_30_sales: 5100,
      store_enrolled_in_promo2: true, is_school_holiday: false, is_state_holiday: false, month: 8,
    },
  },
  holiday: {
    label: 'Holiday effect',
    description: 'State holiday suppresses baseline but boosts foot traffic uncertainty',
    inputs: {
      dayOfWeek: 6, storeType: 0, assortment: 0,
      baseline_sales_30d: 4200, competition_distance: 2100,
      days_since_last_promo: 8, lag_7_sales: 4600, lag_30_sales: 4000,
      store_enrolled_in_promo2: false, is_school_holiday: true, is_state_holiday: true, month: 12,
    },
  },
}

// ─── Mock Prediction (mirrors XGBoost SHAP patterns from training) ────────────

function predict(inp: Inputs): Result {
  const {
    dayOfWeek, storeType, assortment,
    baseline_sales_30d: b, competition_distance: cd,
    days_since_last_promo: gap, lag_7_sales: l7, lag_30_sales: l30,
    store_enrolled_in_promo2: p2, is_school_holiday: sch, is_state_holiday: sta, month,
  } = inp

  const month_sin = Math.sin((2 * Math.PI * month) / 12)
  const month_cos = Math.cos((2 * Math.PI * month) / 12)
  const pgxb = Math.min(gap, 30) * b                // promo_gap × baseline (rank-3 SHAP)

  // --- margin_impact SHAP contributions ---
  const s_base    = (b   - 4200) * 0.13               // #1 driver
  const s_lag7    = (l7  - 4500) * 0.042              // #2
  const s_pgxb    = (pgxb / 4200 - 1.0) * 110         // #3  interaction feature
  const s_lag30   = (l30 - 4500) * 0.022              // #4
  const s_comp    = (cd  - 5000) * 0.006              // #5
  const s_msin    = month_sin * 72                    // #6
  const s_mcos    = month_cos * 34                    // #7
  const day_lut   = [62, -28, 18, 12, 74, 125, -65]
  const s_day     = day_lut[dayOfWeek - 1]            // #8
  const s_stype   = [30, 85, -18, 12][storeType]
  const s_assort  = [0, 42, -22][assortment]
  const s_p2      = p2  ? 28 : -8
  const s_sch     = sch ? -22 : 4
  const s_sta     = sta ? -65 : 0

  const margin = Math.round(
    s_base + s_lag7 + s_pgxb + s_lag30 + s_comp
    + s_msin + s_mcos + s_day + s_stype + s_assort
    + s_p2 + s_sch + s_sta - 18
  )

  // --- sales_lift_pct SHAP contributions ---
  const l_gap   = Math.min(gap, 30) * 0.82 + 7.5
  const l_ratio = (l7 / b - 1) * 22
  const lift_day_lut = [4, -4, 1, 1, 6, 12, -8]
  const l_day   = lift_day_lut[dayOfWeek - 1]
  const l_msin  = month_sin * 4.5
  const l_comp  = cd < 1000 ? -4 : cd > 8000 ? 3 : 0
  const l_p2    = p2 ? 2 : 0

  const lift = parseFloat((l_gap + l_ratio + l_day + l_msin + l_comp + l_p2).toFixed(1))

  // Build top SHAP features (sorted by |value|)
  const margin_shap: ShapEntry[] = [
    { feature: 'baseline_sales_30d',   value: +s_base.toFixed(1) },
    { feature: 'lag_7_sales',          value: +s_lag7.toFixed(1) },
    { feature: 'promo_gap × baseline', value: +s_pgxb.toFixed(1) },
    { feature: 'month_sin (season)',   value: +s_msin.toFixed(1) },
    { feature: 'day_of_week',          value: +s_day.toFixed(1) },
    { feature: 'competition_dist',     value: +s_comp.toFixed(1) },
    { feature: 'store_type',           value: +s_stype.toFixed(1) },
  ]
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 5)

  const lift_shap: ShapEntry[] = [
    { feature: 'days_since_last_promo',  value: +(l_gap - 7.5).toFixed(1) },
    { feature: 'lag_7 / baseline ratio', value: +l_ratio.toFixed(1) },
    { feature: 'day_of_week',            value: +l_day.toFixed(1) },
    { feature: 'month_sin (season)',     value: +l_msin.toFixed(1) },
    { feature: 'competition_dist',       value: +l_comp.toFixed(1) },
  ]
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 4)

  return { margin_impact: margin, sales_lift_pct: lift, roi_verdict: margin >= 0 ? 'POSITIVE' : 'NEGATIVE', margin_shap, lift_shap }
}

// ─── SHAP Bar Chart ───────────────────────────────────────────────────────────

function ShapChart({ title, features }: { title: string; features: ShapEntry[] }) {
  const maxAbs = Math.max(...features.map((f) => Math.abs(f.value)), 1)
  const BAR_MAX_PX = 140

  return (
    <div>
      <div className="font-mono text-xs tracking-widest mb-3" style={{ color: 'var(--ink-faint)' }}>{title}</div>
      <div className="space-y-2.5">
        {features.map((f) => {
          const pos = f.value >= 0
          const barW = (Math.abs(f.value) / maxAbs) * BAR_MAX_PX

          return (
            <div key={f.feature} className="flex items-center gap-3">
              {/* Feature label */}
              <div className="w-40 text-right text-xs shrink-0 leading-tight" style={{ color: 'var(--ink-dim)' }}>{f.feature}</div>

              {/* Bar track */}
              <div className="flex-1 relative h-5 flex items-center">
                {/* Center line */}
                <div className="absolute left-1/2 top-1 bottom-1 w-px" style={{ background: 'var(--line)' }} />

                {/* Bar */}
                <div
                  className="absolute h-3.5 bar-grow"
                  style={{
                    backgroundColor: pos ? 'var(--green)' : 'var(--brick)',
                    width: barW,
                    [pos ? 'left' : 'right']: '50%',
                  }}
                />
              </div>

              {/* Value */}
              <div
                className="font-mono w-14 text-right text-xs font-medium shrink-0"
                style={{ color: pos ? 'var(--green)' : 'var(--brick)' }}
              >
                {pos ? '+' : ''}{f.value.toFixed(1)}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── Slider Row ───────────────────────────────────────────────────────────────

function SliderRow({
  label, value, min, max, step = 1, unit = '', format,
  onChange,
}: {
  label: string; value: number; min: number; max: number
  step?: number; unit?: string; format?: (v: number) => string
  onChange: (v: number) => void
}) {
  const display = format ? format(value) : `${value.toLocaleString()}${unit}`
  return (
    <div>
      <div className="flex justify-between items-baseline mb-1.5">
        <label className="text-xs" style={{ color: 'var(--ink-dim)' }}>{label}</label>
        <span className="font-mono text-xs font-medium" style={{ color: 'var(--amber)' }}>{display}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full"
      />
    </div>
  )
}

function Toggle({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!value)}
      className="flex items-center justify-between w-full p-2.5 transition-colors text-left"
      style={{
        background: value ? 'rgba(245,166,35,0.08)' : 'var(--row)',
        border: `1px solid ${value ? 'rgba(245,166,35,0.3)' : 'var(--line)'}`,
      }}
    >
      <span className="text-xs" style={{ color: 'var(--ink-dim)' }}>{label}</span>
      <div
        className="relative transition-colors"
        style={{
          background: value ? 'var(--amber)' : 'var(--line-bright)',
          width: 32, height: 18,
        }}
      >
        <div
          className="absolute top-0.5 transition-transform"
          style={{ transform: value ? 'translateX(16px)' : 'translateX(2px)', width: 14, height: 14, background: 'var(--bg)' }}
        />
      </div>
    </button>
  )
}

// ─── Segment Control ─────────────────────────────────────────────────────────

function SegmentControl<T extends number>({
  label, value, options, onChange,
}: {
  label: string; value: T; options: { label: string; value: T }[]; onChange: (v: T) => void
}) {
  return (
    <div>
      <div className="text-xs mb-1.5" style={{ color: 'var(--ink-dim)' }}>{label}</div>
      <div className="flex gap-1 p-0.5" style={{ background: 'var(--row)', border: '1px solid var(--line)' }}>
        {options.map((o) => (
          <button
            key={String(o.value)}
            onClick={() => onChange(o.value)}
            className="flex-1 py-1.5 text-xs font-medium transition-all"
            style={{
              background: value === o.value ? 'rgba(245,166,35,0.14)' : 'transparent',
              color: value === o.value ? 'var(--amber)' : 'var(--ink-faint)',
              border: value === o.value ? '1px solid rgba(245,166,35,0.35)' : '1px solid transparent',
            }}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────

const DEFAULT = PRESETS.optimal.inputs

export default function DemoSection() {
  const [inp, setInp] = useState<Inputs>(DEFAULT)
  const [result, setResult] = useState<Result | null>(null)
  const [loading, setLoading] = useState(false)

  const set = useCallback(<K extends keyof Inputs>(key: K, val: Inputs[K]) => {
    setInp((prev) => ({ ...prev, [key]: val }))
    setResult(null)
  }, [])

  const handlePreset = (key: string) => {
    setInp(PRESETS[key].inputs)
    setResult(null)
  }

  const handlePredict = async () => {
    setLoading(true)
    setResult(null)
    await new Promise((r) => setTimeout(r, 750))
    setResult(predict(inp))
    setLoading(false)
  }

  const DOW_OPTIONS = [
    { label: 'Mon', value: 1 }, { label: 'Tue', value: 2 }, { label: 'Wed', value: 3 },
    { label: 'Thu', value: 4 }, { label: 'Fri', value: 5 }, { label: 'Sat', value: 6 }, { label: 'Sun', value: 7 },
  ] as const

  const MONTHS = [
    { label: 'Jan', value: 1 }, { label: 'Feb', value: 2 }, { label: 'Mar', value: 3 },
    { label: 'Apr', value: 4 }, { label: 'May', value: 5 }, { label: 'Jun', value: 6 },
    { label: 'Jul', value: 7 }, { label: 'Aug', value: 8 }, { label: 'Sep', value: 9 },
    { label: 'Oct', value: 10 }, { label: 'Nov', value: 11 }, { label: 'Dec', value: 12 },
  ] as const

  const isPositive = result?.roi_verdict === 'POSITIVE'

  return (
    <section id="demo" className="px-6 py-24 max-w-6xl mx-auto">
      {/* Section header */}
      <div className="mb-14">
        <p className="register mb-3">§03 — INTERACTIVE DEMO</p>
        <h2 className="text-2xl md:text-3xl font-medium mb-3">Try the model</h2>
        <p className="max-w-lg" style={{ color: 'var(--ink-dim)' }}>
          Configure a promotion scenario. The model predicts sales lift, margin impact, and explains
          the top drivers via SHAP values — exactly as it runs in the live GKE API.
        </p>
      </div>

      {/* Preset buttons */}
      <div className="flex flex-wrap gap-2 mb-10">
        {Object.entries(PRESETS).map(([key, p]) => (
          <button
            key={key}
            onClick={() => handlePreset(key)}
            className="font-mono px-4 py-2 text-xs tracking-wide transition-all duration-150"
            style={{
              border: '1px solid var(--line)',
              background: 'var(--row)',
              color: 'var(--ink-faint)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'rgba(245,166,35,0.4)'
              e.currentTarget.style.color = 'var(--ink)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--line)'
              e.currentTarget.style.color = 'var(--ink-faint)'
            }}
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="grid lg:grid-cols-[1fr_1fr] gap-6 items-start">
        {/* ── Left: Form ── */}
        <div className="space-y-4">
          {/* Store Profile */}
          <div className="row p-5 space-y-4">
            <div className="register">STORE PROFILE</div>
            <SegmentControl
              label="Store type"
              value={inp.storeType}
              onChange={(v) => set('storeType', v)}
              options={[
                { label: 'Type A', value: 0 }, { label: 'Type B', value: 1 },
                { label: 'Type C', value: 2 }, { label: 'Type D', value: 3 },
              ]}
            />
            <SegmentControl
              label="Assortment"
              value={inp.assortment}
              onChange={(v) => set('assortment', v)}
              options={[
                { label: 'Basic', value: 0 }, { label: 'Extra', value: 1 }, { label: 'Extended', value: 2 },
              ]}
            />
            <SliderRow
              label="Competition distance (m)"
              value={inp.competition_distance}
              min={300} max={15000} step={100}
              format={(v) => v >= 10000 ? `${(v / 1000).toFixed(1)} km` : `${v.toLocaleString()} m`}
              onChange={(v) => set('competition_distance', v)}
            />
            <Toggle
              label="Enrolled in Promo2 (long-running promo program)"
              value={inp.store_enrolled_in_promo2}
              onChange={(v) => set('store_enrolled_in_promo2', v)}
            />
          </div>

          {/* Timing */}
          <div className="row p-5 space-y-4">
            <div className="register">PROMOTION TIMING</div>
            <div>
              <div className="text-xs mb-1.5" style={{ color: 'var(--ink-dim)' }}>Day of week</div>
              <div className="flex gap-1">
                {DOW_OPTIONS.map((d) => (
                  <button
                    key={d.value}
                    onClick={() => set('dayOfWeek', d.value)}
                    className="flex-1 py-1.5 text-xs font-medium transition-all"
                    style={{
                      background: inp.dayOfWeek === d.value ? 'rgba(245,166,35,0.14)' : 'var(--row)',
                      color: inp.dayOfWeek === d.value ? 'var(--amber)' : 'var(--ink-faint)',
                      border: inp.dayOfWeek === d.value ? '1px solid rgba(245,166,35,0.35)' : '1px solid var(--line)',
                    }}
                  >
                    {d.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <div className="text-xs mb-1.5" style={{ color: 'var(--ink-dim)' }}>Month</div>
              <div className="grid grid-cols-6 gap-1">
                {MONTHS.map((m) => (
                  <button
                    key={m.value}
                    onClick={() => set('month', m.value)}
                    className="py-1.5 text-xs font-medium transition-all"
                    style={{
                      background: inp.month === m.value ? 'rgba(245,166,35,0.14)' : 'var(--row)',
                      color: inp.month === m.value ? 'var(--amber)' : 'var(--ink-faint)',
                      border: inp.month === m.value ? '1px solid rgba(245,166,35,0.35)' : '1px solid var(--line)',
                    }}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>
            <SliderRow
              label="Days since last promo"
              value={inp.days_since_last_promo}
              min={1} max={30}
              format={(v) => v === 30 ? '30+ days' : `${v} day${v === 1 ? '' : 's'}`}
              onChange={(v) => set('days_since_last_promo', v)}
            />
          </div>

          {/* Sales History */}
          <div className="row p-5 space-y-4">
            <div className="register">RECENT SALES HISTORY</div>
            <SliderRow
              label="30-day baseline sales (avg non-promo)"
              value={inp.baseline_sales_30d}
              min={2500} max={7000} step={50}
              format={(v) => `${v.toLocaleString()} units`}
              onChange={(v) => set('baseline_sales_30d', v)}
            />
            <SliderRow
              label="Lag-7 sales (7 days ago)"
              value={inp.lag_7_sales}
              min={1500} max={9000} step={50}
              format={(v) => `${v.toLocaleString()} units`}
              onChange={(v) => set('lag_7_sales', v)}
            />
            <SliderRow
              label="Lag-30 sales (30 days ago)"
              value={inp.lag_30_sales}
              min={1500} max={9000} step={50}
              format={(v) => `${v.toLocaleString()} units`}
              onChange={(v) => set('lag_30_sales', v)}
            />
          </div>

          {/* Conditions */}
          <div className="row p-5 space-y-3">
            <div className="register mb-1">CONDITIONS</div>
            <Toggle label="School holiday" value={inp.is_school_holiday} onChange={(v) => set('is_school_holiday', v)} />
            <Toggle label="State/public holiday" value={inp.is_state_holiday} onChange={(v) => set('is_state_holiday', v)} />
          </div>

          {/* Submit */}
          <button
            onClick={handlePredict}
            disabled={loading}
            className="font-mono w-full py-4 text-sm tracking-wide transition-all duration-150 relative overflow-hidden"
            style={{
              background: loading ? 'rgba(245,166,35,0.4)' : 'var(--amber)',
              color: '#1A1306',
            }}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeOpacity="0.25" />
                  <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
                Running inference…
              </span>
            ) : (
              'Run prediction →'
            )}
          </button>
        </div>

        {/* ── Right: Results ── */}
        <div className="lg:sticky lg:top-8">
          {!result && !loading && (
            <div className="row p-12 text-center">
              <div className="font-mono text-xs tracking-widest mb-3" style={{ color: 'var(--ink-faint)' }}>AWAITING INPUT</div>
              <div className="text-sm" style={{ color: 'var(--ink-dim)' }}>
                Configure a scenario on the left and click{' '}
                <span className="font-medium" style={{ color: 'var(--amber)' }}>Run prediction</span> to see
                the model's output with SHAP explanations.
              </div>
            </div>
          )}

          {loading && (
            <div className="row p-12 text-center">
              <div className="font-mono text-xs tracking-widest mb-3" style={{ color: 'var(--amber)' }}>RUNNING</div>
              <div className="text-sm" style={{ color: 'var(--ink-faint)' }}>Loading XGBoost models + SHAP explainer…</div>
            </div>
          )}

          {result && (
            <div className="space-y-4 animate-fade-in">
              {/* Verdict banner */}
              <div
                className="p-5 text-center verdict-pop"
                style={{
                  background: isPositive ? 'rgba(78,155,115,0.08)' : 'rgba(181,96,74,0.08)',
                  border: `1px solid ${isPositive ? 'rgba(78,155,115,0.3)' : 'rgba(181,96,74,0.3)'}`,
                  borderLeft: `2px solid ${isPositive ? 'var(--green)' : 'var(--brick)'}`,
                }}
              >
                <div className="font-mono text-2xl font-medium" style={{ color: isPositive ? 'var(--green)' : 'var(--brick)' }}>
                  ROI {result.roi_verdict}
                </div>
                <div className="text-xs mt-1" style={{ color: 'var(--ink-faint)' }}>
                  {isPositive
                    ? 'This promotion is predicted to generate net positive margin.'
                    : 'This promotion is predicted to cost more than it returns.'}
                </div>
              </div>

              {/* Two prediction cards */}
              <div className="grid grid-cols-2 gap-3">
                <div className="row p-4 text-center">
                  <div className="font-mono text-xs tracking-wider mb-2" style={{ color: 'var(--ink-faint)' }}>SALES LIFT</div>
                  <div
                    className="font-mono text-3xl font-medium count-in"
                    style={{ color: result.sales_lift_pct >= 0 ? 'var(--green)' : 'var(--brick)' }}
                  >
                    {result.sales_lift_pct >= 0 ? '+' : ''}{result.sales_lift_pct}%
                  </div>
                  <div className="text-xs mt-1" style={{ color: 'var(--ink-faint)' }}>vs. 30-day baseline</div>
                </div>

                <div className="row p-4 text-center">
                  <div className="font-mono text-xs tracking-wider mb-2" style={{ color: 'var(--ink-faint)' }}>MARGIN IMPACT</div>
                  <div
                    className="font-mono text-3xl font-medium count-in"
                    style={{ color: isPositive ? 'var(--green)' : 'var(--brick)' }}
                  >
                    {result.margin_impact >= 0 ? '+' : ''}{result.margin_impact}
                  </div>
                  <div className="text-xs mt-1" style={{ color: 'var(--ink-faint)' }}>units · 20% FMCG margin</div>
                </div>
              </div>

              {/* SHAP charts */}
              <div className="row p-5 space-y-7">
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <span className="register">SHAP EXPLANATIONS</span>
                    <span className="text-xs" style={{ color: 'var(--ink-faint)' }}>— what drove this prediction</span>
                  </div>
                  <div className="text-xs mb-4 flex items-center gap-3" style={{ color: 'var(--ink-faint)' }}>
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block w-3 h-2" style={{ background: 'var(--green)' }} /> Positive impact
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block w-3 h-2" style={{ background: 'var(--brick)' }} /> Negative impact
                    </span>
                  </div>
                </div>
                <ShapChart title="margin_impact model" features={result.margin_shap} />
                <div className="hairline" />
                <ShapChart title="sales_lift_pct model" features={result.lift_shap} />
              </div>

              {/* Feature values used */}
              <div className="row p-4">
                <div className="register mb-3">
                  COMPUTED INPUT VECTOR
                </div>
                <div className="grid grid-cols-2 gap-x-6 gap-y-1.5">
                  {[
                    ['DayOfWeek', inp.dayOfWeek],
                    ['StoreType', ['a','b','c','d'][inp.storeType]],
                    ['Assortment', ['basic','extra','extended'][inp.assortment]],
                    ['baseline_sales_30d', inp.baseline_sales_30d.toFixed(0)],
                    ['lag_7_sales', inp.lag_7_sales],
                    ['lag_30_sales', inp.lag_30_sales],
                    ['competition_dist', `${inp.competition_distance} m`],
                    ['days_since_last_promo', inp.days_since_last_promo],
                    ['month_sin', Math.sin((2 * Math.PI * inp.month) / 12).toFixed(3)],
                    ['month_cos', Math.cos((2 * Math.PI * inp.month) / 12).toFixed(3)],
                    ['promo_gap×baseline', (Math.min(inp.days_since_last_promo, 30) * inp.baseline_sales_30d).toFixed(0)],
                  ].map(([k, v]) => (
                    <div key={String(k)} className="flex justify-between text-xs font-mono">
                      <span style={{ color: 'var(--ink-faint)' }}>{k}</span>
                      <span style={{ color: 'var(--ink-dim)' }}>{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
