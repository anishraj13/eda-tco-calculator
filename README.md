# EDA TCO Calculator

A vendor-neutral analytical tool that calculates when it is economically rational to spend money on AI-accelerated cloud compute to close a chip design block faster than a traditional human-driven flow.

**Live app:** _link added after deployment_

## What it does

Models the economics of AI-augmented physical design flows across two licensing structures (ELA and token-based) and surfaces the break-even compute budget for any given assumption about the value of schedule acceleration.

The tool's headline output is a single sentence: to pull your tapeout in by N weeks, it is rational to spend up to $X on accelerated compute, given your assumptions about labor cost, licensing structure, and the value of schedule acceleration.

## Disclaimer

Illustrative model using generic public benchmarks. Not affiliated with any EDA vendor.

## Running locally

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Architecture

- `engine.py` — pure-function math module
- `app.py` — Streamlit UI
- `styles.py` — custom CSS and Plotly template
- `test_engine.py` — 57 unit tests covering all formulas
- `SPEC.md` — original implementation spec
- `REFERENCE.md` — full documentation of inputs, formulas, defaults, and their sources

See `REFERENCE.md` for the complete model documentation.
