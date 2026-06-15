# EDA TCO Calculator: Reference Document

A vendor-neutral analytical tool that calculates when it is economically rational to spend money on AI-accelerated cloud compute to close a chip design block faster, versus closing it on a normal human-driven schedule.

This document is the canonical reference for what the calculator does, what every input means, and how every output is computed. Use it as the source of truth when explaining the project to others, debugging unexpected outputs, or writing about the model.

---

## The core question

When is it economically rational to spend money on AI-accelerated cloud compute to close a chip design block faster, instead of letting a human engineering team close it on a normal schedule?

The tool's job is not to assert a universal answer. It computes the break-even point given the user's assumptions about value, cost, and licensing structure, so the user can see whether the AI path is rational for their specific situation.

---

## Two licensing modes

The calculator supports two licensing structures because EDA pricing varies significantly between contracts.

**ELA / Sunk mode (default).** Models customers on traditional Enterprise License Agreements. Per-block decisions don't have marginal licensing costs because the ELA is paid as a flat annual cost regardless of how many blocks the team works on. `ai_licensing_cost = 0`.

**Token-based mode.** Models customers on consumption-based or token-metered pricing. AI features consume tokens at a multiplier above baseline. Cost scales with usage. `ai_licensing_cost = (accelerated_weeks × team_size × token_cost_per_eng_week × ai_token_multiplier) − (baseline_weeks × team_size × token_cost_per_eng_week)`.

Negative ai_licensing values are valid and indicate that schedule compression more than offsets the AI multiplier. This is shown as an explicit line item in the cost breakdown.

---

## All input variables

### Design inputs

| Variable | Default | Meaning |
|----------|---------|---------|
| `node` | "3nm" | Process node dropdown: 5nm, 3nm, or 2nm. Sets a soft default for `base_node_weeks`. |
| `base_node_weeks` | 12 | The baseline schedule for closing one block at the selected node, in weeks. Set by node dropdown (9 for 5nm, 12 for 3nm, 16 for 2nm) but user can override via slider. |

### Team inputs

| Variable | Default | Meaning |
|----------|---------|---------|
| `team_size` | 5 | Number of physical design engineers assigned to this block. |
| `fully_burdened_annual` | $300,000 | All-in annual cost per engineer including salary, benefits, equipment, and overhead. Base PD salary is roughly $124-143K; the fully-burdened multiplier is 1.3-1.4×. |

### Compute inputs

| Variable | Default | Meaning |
|----------|---------|---------|
| `automatable_fraction` | 0.40 | Fraction of the baseline schedule that AI tools can compress. Default reflects the conservative view that ~40% of the flow is exploratory/iterative work AI can parallelize; the rest is human judgment. |
| `acceleration_factor` | 4.0 | How much faster the automatable portion runs under AI acceleration. |
| `parallel_gpus` | 64 | Number of GPUs the AI flow runs concurrently. |
| `compute_hours` | 500 | Total GPU-hours of compute the AI flow consumes (cumulative across all parallel runs). |
| `cloud_rate_per_gpu_hr` | $3.00 | Dollar cost per GPU per hour. Range $2-12 spans neocloud ($2-3) to hyperscaler ($7-12) pricing. |

### Licensing inputs

| Variable | Default | Meaning |
|----------|---------|---------|
| `licensing_mode` | "ela_or_sunk" | Either "ela_or_sunk" or "token". Selected via radio button in the UI. |
| `token_cost_per_eng_week` | $5,000 | Token mode only. Baseline token consumption cost per engineer-week. Generic placeholder; real values are company-specific. |
| `ai_token_multiplier` | 4.0 | Token mode only. AI features consume more tokens than traditional flows. Default 4.0 sits in the middle of the EDA Primer's cited 3-5× range. |

### Schedule value input

| Variable | Default | Meaning |
|----------|---------|---------|
| `value_per_week` | $250,000 | The dollar value of pulling in your tapeout by one week. The master input that implicitly encodes company type. Startups: $50-100K. Mid-market: $250-500K. Hyperscalers: $1M+. |

### PPA inputs

| Variable | Default | Meaning |
|----------|---------|---------|
| `deployed_units` | 100,000 | How many chips containing this block will ultimately be deployed. |
| `power_per_unit_w` | 300 | Average power dissipation per chip in watts. |
| `leakage_reduction_pct` | 0.08 | Fraction of leakage power the AI tool reduces. Default 8% is conservative versus public claims of 5-25%. |
| `hours_per_year` | 8,760 | Hours the chip runs per year. 8,760 means continuous operation. |
| `electricity_cost_per_kwh` | $0.10 | Power cost per kWh. Typical US industrial rate. |

---

## All formulas

### Engineer cost per week (derived)
engineer_cost_per_week = (fully_burdened_annual / 52) × team_size

Default: ($300,000 / 52) × 5 = $28,846.15

### Baseline path
baseline_weeks = base_node_weeks

baseline_labor = baseline_weeks × engineer_cost_per_week

baseline_total = baseline_labor

Baseline licensing is not modeled. Either it's sunk under an ELA or it's the reference point against which token cost is incremental. Either way, baseline_total = baseline_labor.

Default: baseline_total = 12 × $28,846.15 = $346,154

### Accelerated schedule (derived)
automatable_weeks = baseline_weeks × automatable_fraction

non_automatable_weeks = baseline_weeks × (1 − automatable_fraction)

accelerated_automatable_weeks = automatable_weeks / acceleration_factor

accelerated_weeks = non_automatable_weeks + accelerated_automatable_weeks

weeks_saved = baseline_weeks − accelerated_weeks

Default: automatable_weeks = 4.8, non_automatable_weeks = 7.2, accelerated_automatable_weeks = 1.2, accelerated_weeks = 8.4, weeks_saved = 3.6

### Compute cost (derived)
compute_cost = parallel_gpus × compute_hours × cloud_rate_per_gpu_hr

Default: 64 × 500 × $3.00 = $96,000

### Licensing cost (derived, mode-dependent)

ELA / Sunk mode:
ai_licensing_cost = 0

Token mode:
ai_token_cost = accelerated_weeks × team_size × token_cost_per_eng_week × ai_token_multiplier

baseline_token_cost = baseline_weeks × team_size × token_cost_per_eng_week

ai_licensing_cost = ai_token_cost − baseline_token_cost

Token mode default: 8.4 × 5 × $5,000 × 4.0 − 12 × 5 × $5,000 = $840,000 − $300,000 = $540,000

### Accelerated path (derived)
accel_labor = accelerated_weeks × engineer_cost_per_week

accel_total = accel_labor + compute_cost + ai_licensing_cost

ELA mode default: accel_labor = $242,308. accel_total = $242,308 + $96,000 + $0 = $338,308
Token mode default: accel_total = $242,308 + $96,000 + $540,000 = $878,308

### Acceleration value (derived)
acceleration_value = weeks_saved × value_per_week

Default: 3.6 × $250,000 = $900,000

### Net benefit (derived)
net_benefit = baseline_total − accel_total + acceleration_value

The overall economic verdict. Positive means the AI path is better; negative means it isn't.

ELA mode default: $346,154 − $338,308 + $900,000 = $907,846
Token mode default: $346,154 − $878,308 + $900,000 = $367,846

### Break-even compute (derived, the headline output)

Derivation: set net_benefit = 0 and solve for compute_cost.
0 = baseline_total − (accel_labor + compute_cost + ai_licensing_cost) + acceleration_value

breakeven_compute = baseline_total − accel_labor − ai_licensing_cost + acceleration_value

The maximum compute spend that still leaves the AI path at least as good as baseline.

ELA mode default: $346,154 − $242,308 − $0 + $900,000 = $1,003,846
Token mode default: $346,154 − $242,308 − $540,000 + $900,000 = $463,846

### PPA upside (derived, separate from break-even)
annual_power_saving = (deployed_units × power_per_unit_w × leakage_reduction_pct × hours_per_year × electricity_cost_per_kwh) / 1000

lifecycle_ppa_saving = annual_power_saving × 3

Default: annual = $21,024,000. Three-year lifecycle = $63,072,000.

Presented as a separate bonus figure, not folded into the break-even calculation.

---

## Sanity-check reference numbers (default configuration)

| Metric | ELA / Sunk | Token-based (4×) |
|--------|------------|------------------|
| baseline_total | $346,154 | $346,154 |
| accel_labor | $242,308 | $242,308 |
| compute_cost | $96,000 | $96,000 |
| ai_licensing | $0 | $540,000 |
| accel_total | $338,308 | $878,308 |
| acceleration_value | $900,000 | $900,000 |
| net_benefit | $907,846 | $367,846 |
| breakeven_compute | $1,003,846 | $463,846 |
| Verdict | RATIONAL | RATIONAL |

In both modes the AI path is rational at $96K compute spend. Token mode has roughly half the headroom before AI stops being rational.

---

## Sensitivity grid

A 6×5 grid of net_benefit values, calculated by holding all inputs at default except sweeping:

- Rows: `value_per_week` ∈ [$50K, $100K, $250K, $500K, $1M, $2M]
- Columns: `cloud_rate_per_gpu_hr` ∈ [$2, $3, $5, $8, $12]

Each cell shows net_benefit for that combination. Cells where net_benefit > 0 are colored green (AI is rational), cells where net_benefit < 0 are colored red (baseline is rational).

The grid respects the selected licensing mode. ELA mode shows mostly green. Token mode shows more red at lower value_per_week rows.

---

## What's intentionally not modeled

These simplifications are defensible for v1 and explicitly called out in the disclaimer.

**Yield and reliability differences.** Both paths are assumed to produce equivalent designs. In reality AI-optimized designs may have different PVT corner behavior.

**Schedule variance.** Both schedules are deterministic. Real schedules have variance from team illness, spec changes, tool bugs, etc.

**Switching costs.** The model assumes the AI flow is already qualified and engineers are trained. First-time adoption has transition costs that amortize.

**Capacity contention.** Compute is assumed available at the listed price. In a real shortage (which currently exists in 2026), top-tier compute is allocated by relationship and contract.

**The exact mapping from baseline_weeks to node.** The 9/12/16 weeks for 5nm/3nm/2nm is a planning envelope grounded in advanced-node complexity scaling, not a hard rule. Users can override.

---

## Decisions and tradeoffs

This section documents the substantive modeling choices made during the design of this calculator. Every choice below was a real decision with alternatives that were considered and rejected. They are the human-judgment layer of the project.

### Why the calculator models a per-block decision rather than a full project

Early versions of the model considered framing this as a full chip-program decision, comparing the total cost of two engineering approaches across an entire project. That framing was rejected for two reasons. First, the inputs scale wildly across program types and the model would have needed many more configuration knobs to be defensible. Second, real decisions about AI tool adoption happen at the block level. A team picks one block to pilot AI acceleration on, sees the result, and rolls forward. The per-block frame matches how the industry actually adopts new tooling.

### Why the licensing model has two modes and not one

The initial spec used a single licensing model that treated EDA licensing as time-based per-engineer-per-week. That was incoherent because real EDA vendors price through Enterprise License Agreements where marginal license cost is zero for per-block decisions, or through token-based pricing where cost scales with usage. These are fundamentally different economic structures and produce different break-even answers. Forcing them into one formula meant the model would be wrong for everyone.

The two-mode design is more honest. ELA-mode customers see zero marginal licensing cost (which is accurate to how their contracts work). Token-mode customers see incremental cost scaling with AI feature usage (which is accurate to consumption-based contracts). The user picks the mode that matches their company's actual pricing structure.

### Why renewal uplift was dropped from the ELA model

An earlier version of the ELA mode attempted to amortize the SemiAnalysis EDA Primer's cited 20% renewal uplift on AI-enhanced ELAs as a per-block marginal cost. This was wrong. Renewal uplift is a contract-cycle event tied to whether the company enables AI features at all, not a per-block marginal cost. Even if the user does not accelerate this specific block, if the company has decided to enable AI features in the ELA, the uplift hits anyway. It is already locked in by company-level licensing decisions and is sunk relative to the per-block decision.

The corrected ELA mode treats licensing as fully sunk. This is the economically honest position and produces cleaner break-even math.

### Why automatable_fraction defaults to 0.40 rather than higher

This input is the credibility anchor of the entire model. Vendor marketing claims often imply that AI tools compress the entire design schedule by large multiples (4x, 10x, 40x). Those numbers reflect best-case scenarios on specific automatable stages, not whole-flow compression. Real chip design schedules are gated on human work that does not parallelize: floorplanning judgment, fixing real DRC and timing violations, signoff sign-off meetings, customer reviews.

The 40% default reflects the conservative view that roughly half the flow is exploratory or iterative work an AI tool can parallelize, and the other half is human-gated and does not move. A user who wants to model an aggressive scenario can slide it up to 70%. A user who wants to model a conservative scenario can slide it down to 20%. The slider itself is the disclosure that whole-flow compression numbers are not credible.

### Why size_factor and clock_factor were removed

The first iteration of the spec included two multiplicative scalars to make baseline schedule responsive to gate count and target clock frequency. Both were cosmetic. Neither had enough physical grounding to be defensible, and both required the user to enter values they would not know precisely. Worse, they created a false impression of precision in a model whose actual uncertainty is far larger.

The simpler design is to let the user set baseline_weeks directly, with the node dropdown providing a soft default. This is more honest about what the model actually knows and removes inputs that could not be defended in a review conversation.

### Why compute_hours is a direct user input rather than derived from iteration counts

A more sophisticated version of the model could derive compute_hours from iteration counts and per-iteration GPU hour estimates. That was considered and rejected. Per-iteration runtimes vary by orders of magnitude depending on workload, tool, and design complexity. Building that derivation into the model would create a false impression of precision and would require the user to enter values they would not know. Letting the user set GPU-hours directly is more honest because it puts the uncertainty in the user's hands rather than hiding it inside a formula.

### Why PPA savings is presented separately from the schedule break-even

The PPA upside (leakage reduction across deployed units over a 3-year lifecycle) and the schedule break-even live on different decision time horizons. Schedule break-even is about a decision happening now, on this block, with cash that will be spent this quarter. PPA savings is about future operational cost across deployed silicon over multiple years. Mixing them into a single net benefit number would be misleading because they have different risk profiles, different stakeholders, and different discount rates.

Presenting PPA as a separate bonus figure preserves the analytical separation. A user looking at the break-even number is making a near-term capital decision. A user looking at the PPA figure is making a strategic argument about operating economics.

### Why value_per_week is the master input

The single most important number in this model is the user's estimate of what one week of schedule acceleration is worth. It is the input that encodes company type implicitly. A scrappy fabless startup might value a week at $50K (incremental runway, slightly earlier revenue). A hyperscaler racing to deploy a custom AI accelerator instead of renting NVIDIA might value a week at $1M+ (avoided rental costs, earlier competitive deployment, faster capture of internal compute savings).

This design choice means the calculator does not assert an answer. It asks the user to declare what acceleration is worth to them, then computes the break-even given that assumption. The honesty is the selling point. A more opinionated tool would assert a value and lose credibility with users whose situation does not match the asserted assumption.

### What the model intentionally does not capture

Several real dynamics were considered and explicitly left out of v1 for honesty's sake.

The model does not capture yield or reliability differences between AI-optimized and traditional designs. In principle, AI-driven optimization could push designs closer to PVT corner edges, requiring respin risk to be priced in. Modeling this would require distributions and confidence intervals the v1 deliberately avoids.

The model does not capture schedule variance. Both paths are treated as deterministic schedules. Real schedules have variance from team illness, spec changes, tool bugs, and customer-driven requirement shifts. A more sophisticated v2 would model these as distributions.

The model does not capture switching costs. First-time adoption of an AI-driven flow involves training engineers, qualifying new tools with the foundry, and validating that signoff still passes. These costs are real but amortize across many blocks after the first. The model assumes the AI flow is already qualified.

The model does not capture capacity contention. Compute is assumed available at the listed market price. In the current AI infrastructure shortage, top-tier compute is allocated by relationship and contract, not by price alone. A hyperscaler that has committed to an NVIDIA capacity reservation pays a different effective rate than a fabless startup buying spot instances.

These omissions are documented in the disclaimer in the app and are flagged here so that any reviewer can see they were considered and explicitly scoped out, not overlooked.

---

## Architecture

Three core files:
- `engine.py`: pure-function math module. No Streamlit dependency. Unit-tested with 57 tests.
- `app.py`: Streamlit UI. Imports from engine.py and styles.py.
- `styles.py`: custom CSS injection and Plotly template for consistent visual styling.

Plus:
- `test_engine.py`: 57 unit tests covering all formulas across both licensing modes.
- `CLAUDE.md`: agent instructions for Claude Code.
- `SPEC.md`: original implementation specification.
- `REFERENCE.md`: this file.

---

## Default values' sources

All defaults are grounded in public benchmarks corroborated across multiple sources.

**Engineer cost ($300K fully-burdened annual):** Base PD salary $124-143K per Glassdoor, ZipRecruiter, Salary.com (Feb-Mar 2026). Fully-burdened multiplier 1.3-1.4× per Runway and EMARS. Default sits at mid-senior PD engineer at a major employer.

**Cloud rate ($3/GPU-hr):** Mid-market H100 pricing per Spheron, CloudZero, GetDeploying (May 2026). Range $2-12 spans neocloud to hyperscaler.

**Node-to-schedule mapping:** Grounded in SemiAnalysis EDA Primer Part 1, which notes 3nm designs carry 25,000+ design rules and 20-30 PVT corners.

**AI token multiplier (4.0):** Middle of the EDA Primer's cited 3-5× consumption increase for AI features.

**Leakage reduction (8%):** Conservative versus public claims. Cadence Cerebrus reports 5-20% PPA gains; Synopsys DSO.ai claims up to 25% lower power. Default 8% sits below the headlines because generalized results tend to be more conservative than best-case demos.