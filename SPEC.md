Project: Generative EDA TCO and Schedule Accelerator (vendor-neutral, open-source)
We are building an independent, open-source TCO calculator that answers one question: when is it economically rational to spend money on AI-accelerated cloud compute to close a chip design block faster, versus closing it on a normal human-driven schedule? The tool is vendor-neutral and uses only generic public industry benchmarks. It must not reference any proprietary or company-internal data.
Stack: Python 3.11+, Streamlit for UI, NumPy and Pandas for logic, Plotly for charts. Local virtual environment. No database, no external API calls, no secrets.
Architecture: Build in three files.

engine.py — a standalone, pure-function calculation module with no Streamlit dependency. All math lives here. Must be unit-testable.
app.py — the Streamlit UI that imports from engine.py, renders the sidebar inputs and the main-panel outputs.
test_engine.py — basic unit tests for the engine functions.

Start with engine.py. Implement these pure functions:
inputs (all passed explicitly, no globals):
  node: str in {"5nm","3nm","2nm"}
  base_node_weeks: float          # default 12.0 for 3nm
  size_factor: float              # scales with gate count, default 1.0
  clock_factor: float             # scales with target freq, default 1.0
  team_size: int                  # default 5
  fully_burdened_annual: float    # default 300_000
  automatable_fraction: float     # 0..0.7, default 0.40
  acceleration_factor: float      # 2..10, default 4.0
  parallel_gpus: int              # default 64
  compute_hours: float            # GPU-hours of accelerated exploration, default 500
  cloud_rate_per_gpu_hr: float    # default 3.0
  licensing_mode: str              # "ela_or_sunk" | "token", default "ela_or_sunk"
  token_cost_per_eng_week: float   # token-mode only, generic placeholder, default 5000
  ai_token_multiplier: float       # token-mode only, 1.0..5.0, default 4.0
  value_per_week: float           # default 250_000
  # PPA block
  deployed_units: int             # default 100_000
  power_per_unit_w: float         # default 300
  leakage_reduction_pct: float    # 0..0.20, default 0.08
  hours_per_year: float           # default 8760
  electricity_cost_per_kwh: float # default 0.10

functions:
  baseline_schedule(base_node_weeks, size_factor, clock_factor) -> baseline_weeks
  engineer_cost_per_week(fully_burdened_annual, team_size) -> float
  baseline_cost(baseline_weeks, eng_cost_wk) -> dict{labor, total}
  accelerated_schedule(baseline_weeks, automatable_fraction, acceleration_factor) -> dict{accelerated_weeks, weeks_saved}
  licensing_cost(licensing_mode, accelerated_weeks, baseline_weeks, team_size, token_cost_per_eng_week=0, ai_token_multiplier=1.0) -> float
  accelerated_cost(accelerated_weeks, eng_cost_wk, ai_licensing, parallel_gpus, compute_hours, cloud_rate_per_gpu_hr) -> dict{labor, compute, ai_licensing, total}
  acceleration_value(weeks_saved, value_per_week) -> float
  net_benefit(baseline_total, accel_total, accel_value) -> float
  breakeven_compute(baseline_total, accel_labor, accel_ai_licensing, accel_value) -> float
  ppa_lifecycle_saving(deployed_units, power_per_unit_w, leakage_reduction_pct, hours_per_year, electricity_cost_per_kwh, years=3) -> dict{annual, lifecycle}
  sensitivity_grid(value_per_week_range, cloud_rate_range, **fixed_inputs) -> pandas.DataFrame  # net_benefit across the grid
Formulas:
baseline_weeks = base_node_weeks * size_factor * clock_factor
eng_cost_wk    = (fully_burdened_annual / 52) * team_size
baseline_labor = baseline_weeks * eng_cost_wk
baseline_total = baseline_labor
  # Licensing is modeled as an incremental cost via licensing_cost() — not split
  # between paths here. See accel_ai_licensing below.

automatable_weeks = baseline_weeks * automatable_fraction
non_auto_weeks    = baseline_weeks * (1 - automatable_fraction)
accel_auto_weeks  = automatable_weeks / acceleration_factor
accelerated_weeks = non_auto_weeks + accel_auto_weeks
weeks_saved       = baseline_weeks - accelerated_weeks

accel_labor   = accelerated_weeks * eng_cost_wk
compute_cost  = parallel_gpus * compute_hours * cloud_rate_per_gpu_hr
accel_ai_licensing = licensing_cost(licensing_mode, accelerated_weeks, baseline_weeks,
                                    team_size, token_cost_per_eng_week, ai_token_multiplier)
accel_total        = accel_labor + compute_cost + accel_ai_licensing

accel_value   = weeks_saved * value_per_week
net_benefit   = baseline_total - accel_total + accel_value
breakeven_compute = (baseline_total - accel_labor - accel_ai_licensing) + accel_value

annual_power_saving = deployed_units * power_per_unit_w * leakage_reduction_pct * hours_per_year * electricity_cost_per_kwh / 1000.0
lifecycle_ppa_saving = annual_power_saving * years
Node presets (defaults the dropdown applies): 5nm base_node_weeks 9, 3nm 12, 2nm 16. These scale only the baseline schedule; they are generic planning envelopes, not vendor data.
After engine.py and its tests pass, build app.py:

Left sidebar: all inputs as sliders/dropdowns/number inputs with the defaults above. Group them under headers: Design, Team, Compute, Licensing, Schedule Value, PPA Upside.
## The outputs (main panel layout)

The layout is a research dashboard, two columns where appropriate, generous whitespace.

**Row 1: Headline verdict (full width)**
Large metric card. Two lines:
- Line 1: "Rational to spend up to ${breakeven_compute:,.0f} on compute to save {weeks_saved:.1f} weeks"
- Line 2: "Your modeled compute spend: ${compute_cost:,.0f} — VERDICT: rational / not rational"
The verdict text is colored green or red. Use streamlit-extras `colored_header` or a custom HTML container.

**Row 2: Two columns**
- Left column: Plotly chart of net_benefit vs compute spend, with the break-even point marked and the current modeled spend marked. Hover shows exact dollars.
- Right column: Schedule comparison. Baseline weeks vs accelerated weeks, horizontal bar chart.

**Row 3: PPA upside panel (full width)**
Separate visually from rows 1-2 with a thin divider. Two metric cards side by side:
- Annual power saving (dollars)
- 3-year lifecycle saving (dollars)
Clearly labeled "Bonus PPA upside — separate from schedule economics."

**Row 4: Sensitivity table (full width)**
Pandas DataFrame styled with conditional formatting. Green cells where net_benefit > 0, red where < 0. Rows are value_per_week, columns are cloud_rate.

**Row 5: Disclaimer (full width, small text)**
"Illustrative model using generic public benchmarks. Not affiliated with any EDA vendor."
Plotly chart 1: net_benefit vs compute spend (sweep compute from 0 to 2x breakeven), mark break-even point and current modeled spend.
Plotly chart 2: bar chart, baseline_weeks vs accelerated_weeks.
A separate PPA panel showing annual and 3-year lifecycle power savings as bonus upside, clearly labeled as separate from the schedule break-even.
A sensitivity table (Pandas styled dataframe) of net_benefit across value_per_week (rows) by cloud_rate (columns).

Constraints: keep all monetary outputs formatted with thousands separators. No browser localStorage. Pure in-memory. Add a short disclaimer line at the bottom: "Illustrative model using generic public benchmarks. Not affiliated with any EDA vendor."
Begin by writing engine.py and test_engine.py, show me the test output, then we build app.py.
