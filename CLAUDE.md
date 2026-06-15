l, open-source Streamlit tool that calculates when it is economically rational to spend money on AI-accelerated cloud compute to close a chip design block faster than a traditional human-driven flow.

**Read SPEC.md first.** It contains the full project specification, formulas, default values, and architecture. Treat SPEC.md as the source of truth. If anything in this CLAUDE.md conflicts with SPEC.md, ask before proceeding.

## Build order
1. `engine.py` — pure math, no Streamlit dependency
2. `test_engine.py` — unit tests for every function in engine.py
3. `app.py` — Streamlit UI that imports from engine.py

Do not start app.py until engine.py and its tests are passing.

## Tech stack
- Python 3.11+
- Streamlit, NumPy, Pandas, Plotly
- Local virtual environment (already set up at `./venv`)
- No external API calls, no database, no secrets, no localStorage

## Coding conventions
- Pure functions in engine.py. No globals, no side effects, no I/O.
- Type hints on every public function.
- Docstrings include the formula being implemented and a citation to SPEC.md.
- Monetary values formatted with thousands separators when displayed.
- All inputs to engine functions passed explicitly. Default values live in app.py, not engine.py.

## Agency boundaries (important)
The math and modeling choices are the intellectual content of this project. Before implementing any formula or default value not already specified in SPEC.md, propose it and wait for my sign-off. This includes:
- Any change to a formula in SPEC.md
- Any new default value
- Any new input or output beyond what SPEC.md lists
- Any change to `size_factor` or `clock_factor` scaling logic

Full agency is fine for: file scaffolding, imports, type hints, docstring drafts, Streamlit layout, Plotly styling, test boilerplate, error handling, formatting.

## Visual design standards

The tool must look like a research-grade analytical dashboard, not a consumer app or SaaS landing page. The reference aesthetic is SemiAnalysis charts and Bloomberg Terminal data density.

Principles:
- Analytical density over decoration. Big numbers, clear labels, no icons or emojis.
- One headline metric at the top: the break-even verdict in large type.
- Conditional color: green when the AI path is rational, red when not. No other "fun" colors.
- Typography: use IBM Plex Sans (sans-serif) and IBM Plex Mono (for numbers). Load from Google Fonts.
- Layout: two-column main panel where appropriate. Avoid pure vertical scroll.
- Charts: use a shared Plotly template defined once and reused. White background, thin grid lines, IBM Plex font, muted palette.
- Whitespace: generous padding around metric cards. Avoid cramped layouts.

Do not add: icons, emojis, gradients, animations, marketing copy, hero images, decorative dividers, or anything that signals "consumer app."

Required files:
- `.streamlit/config.toml` with the theme
- `styles.py` with the CSS injection helper and Plotly template

 Do not
- Reference any EDA vendor name in code, comments, or UI text. The model is vendor-neutral.
- Hard-code any number sourced from a private or proprietary document.
- Add browser storage (localStorage, sessionStorage). Streamlit session state only.
- Add authentication, telemetry, or external network calls.
- Add files outside the project root without asking.

## Disclaimer in UI
The Streamlit app must include this exact line at the bottom of the main panel: "Illustrative model using generic public benchmarks. Not affiliated with any EDA vendor."

## When in doubt
Ask. This project is small enough that one round-trip is cheaper than undoing wrong work.

