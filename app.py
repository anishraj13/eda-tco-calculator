"""
app.py — Streamlit UI for the EDA TCO / Schedule Accelerator.
Imports all math from engine.py. No calculations performed here.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from engine import (
    baseline_schedule,
    engineer_cost_per_week,
    licensing_cost,
    baseline_cost,
    accelerated_schedule,
    accelerated_cost,
    acceleration_value,
    net_benefit,
    breakeven_compute,
    ppa_lifecycle_saving,
    sensitivity_grid,
    compute_sweep,
)
from styles import (
    inject_css,
    metric_card,
    section_header,
    sidebar_section,
    PLOTLY_TEMPLATE,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="EDA TCO Calculator",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NODE_PRESETS: dict[str, float] = {"5nm": 9.0, "3nm": 12.0, "2nm": 16.0}

VALUE_PER_WEEK_RANGE = [50_000, 100_000, 250_000, 500_000, 1_000_000, 2_000_000]
CLOUD_RATE_RANGE = [2, 3, 5, 8, 12]

LICENSING_MODE_MAP = {"ELA / Sunk": "ela_or_sunk", "Token-based": "token"}


def _money(v: float) -> str:
    """Format a dollar amount with thousands separators, sign before the symbol."""
    return f"-${abs(v):,.0f}" if v < 0 else f"${v:,.0f}"

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "node" not in st.session_state:
    st.session_state["node"] = "3nm"
if "base_node_weeks" not in st.session_state:
    st.session_state["base_node_weeks"] = NODE_PRESETS["3nm"]


def on_node_change() -> None:
    st.session_state["base_node_weeks"] = NODE_PRESETS[st.session_state["node"]]


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## EDA TCO Calculator")
    st.markdown("---")

    # Design
    st.markdown(sidebar_section("Design"), unsafe_allow_html=True)
    node = st.selectbox(
        "Process node",
        options=list(NODE_PRESETS.keys()),
        key="node",
        on_change=on_node_change,
    )
    base_node_weeks = st.slider(
        "Baseline schedule (weeks)",
        min_value=4.0,
        max_value=52.0,
        step=0.5,
        key="base_node_weeks",
        help="Weeks to close the block on a traditional flow. Node preset provides a soft default.",
    )

    st.markdown("---")

    # Team
    st.markdown(sidebar_section("Team"), unsafe_allow_html=True)
    team_size = st.slider("Team size (engineers)", min_value=1, max_value=30, value=5)
    fully_burdened_annual = st.number_input(
        "Fully burdened cost per engineer ($/yr)",
        min_value=50_000,
        max_value=1_000_000,
        value=300_000,
        step=10_000,
        format="%d",
    )

    st.markdown("---")

    # Compute
    st.markdown(sidebar_section("Compute"), unsafe_allow_html=True)
    parallel_gpus = st.slider("Parallel GPUs", min_value=1, max_value=512, value=64)
    compute_hours = st.slider(
        "Compute hours (GPU-hrs of accelerated exploration)",
        min_value=10.0,
        max_value=5_000.0,
        value=500.0,
        step=10.0,
    )
    cloud_rate_per_gpu_hr = st.slider(
        "Cloud rate ($/GPU-hr)",
        min_value=0.5,
        max_value=20.0,
        value=3.0,
        step=0.5,
    )

    st.markdown("---")

    # Licensing
    st.markdown(sidebar_section("Licensing"), unsafe_allow_html=True)
    _licensing_label = st.radio(
        "Licensing mode",
        options=["ELA / Sunk", "Token-based"],
        index=0,
        key="licensing_mode_label",
    )
    licensing_mode = LICENSING_MODE_MAP[_licensing_label]

    if licensing_mode == "ela_or_sunk":
        st.caption(
            "Traditional EDA Enterprise License Agreements treat licensing as a "
            "flat annual cost. Per-block decisions don't have marginal licensing "
            "costs under this model. Switch to Token-based mode if your company "
            "uses capacity-based or token-metered pricing."
        )
        token_cost_per_eng_week = 0.0
        ai_token_multiplier = 1.0
    else:
        token_cost_per_eng_week = st.number_input(
            "Token cost ($/engineer-week)",
            min_value=0,
            max_value=50_000,
            value=5_000,
            step=500,
            format="%d",
        )
        ai_token_multiplier = st.slider(
            "AI token multiplier (×)",
            min_value=1.0,
            max_value=5.0,
            value=4.0,
            step=0.1,
        )

    st.markdown("---")

    # Schedule value
    st.markdown(sidebar_section("Schedule Value"), unsafe_allow_html=True)
    automatable_fraction = st.slider(
        "Automatable fraction of work",
        min_value=0.0,
        max_value=0.7,
        value=0.40,
        step=0.01,
        format="%.2f",
    )
    acceleration_factor = st.slider(
        "Acceleration factor (×)",
        min_value=2.0,
        max_value=10.0,
        value=4.0,
        step=0.5,
    )
    value_per_week = st.number_input(
        "Value of one week saved ($/week)",
        min_value=0,
        max_value=5_000_000,
        value=250_000,
        step=10_000,
        format="%d",
    )

    st.markdown("---")

    # PPA Upside
    st.markdown(sidebar_section("PPA Upside"), unsafe_allow_html=True)
    deployed_units = st.number_input(
        "Deployed units",
        min_value=1_000,
        max_value=10_000_000,
        value=100_000,
        step=1_000,
        format="%d",
    )
    power_per_unit_w = st.slider(
        "Power per unit (W)",
        min_value=1.0,
        max_value=1_000.0,
        value=300.0,
        step=10.0,
    )
    leakage_reduction_pct = st.slider(
        "Leakage reduction (%)",
        min_value=0.0,
        max_value=20.0,
        value=8.0,
        step=0.5,
        format="%.1f%%",
    )
    hours_per_year = st.number_input(
        "Operating hours per year",
        min_value=1_000.0,
        max_value=8_760.0,
        value=8_760.0,
        step=100.0,
    )
    electricity_cost_per_kwh = st.slider(
        "Electricity cost ($/kWh)",
        min_value=0.01,
        max_value=0.50,
        value=0.10,
        step=0.01,
        format="$%.2f",
    )

# ---------------------------------------------------------------------------
# Calculations
# ---------------------------------------------------------------------------

_baseline_weeks = baseline_schedule(base_node_weeks)
_eng_cost_wk = engineer_cost_per_week(fully_burdened_annual, team_size)
_bc = baseline_cost(_baseline_weeks, _eng_cost_wk)
_sched = accelerated_schedule(_baseline_weeks, automatable_fraction, acceleration_factor)
_ai_licensing = licensing_cost(
    licensing_mode,
    _sched["accelerated_weeks"],
    _baseline_weeks,
    team_size,
    token_cost_per_eng_week,
    ai_token_multiplier,
)
_ac = accelerated_cost(
    _sched["accelerated_weeks"],
    _eng_cost_wk,
    _ai_licensing,
    parallel_gpus,
    compute_hours,
    cloud_rate_per_gpu_hr,
)
_av = acceleration_value(_sched["weeks_saved"], value_per_week)
_nb = net_benefit(_bc["total"], _ac["total"], _av)
_be = breakeven_compute(_bc["total"], _ac["labor"], _ac["ai_licensing"], _av)
_ppa = ppa_lifecycle_saving(
    deployed_units,
    power_per_unit_w,
    leakage_reduction_pct / 100.0,  # slider is 0–20, engine expects 0.0–0.20
    hours_per_year,
    electricity_cost_per_kwh,
)
_sweep_df = compute_sweep(_be, _bc["total"], _ac["labor"], _ac["ai_licensing"], _av)
_grid_df = sensitivity_grid(
    VALUE_PER_WEEK_RANGE,
    CLOUD_RATE_RANGE,
    base_node_weeks,
    team_size,
    fully_burdened_annual,
    automatable_fraction,
    acceleration_factor,
    parallel_gpus,
    compute_hours,
    licensing_mode,
    token_cost_per_eng_week,
    ai_token_multiplier,
)

_rational = _ac["compute"] <= _be
_verdict_class = "verdict-rational" if _rational else "verdict-irrational"
_verdict_word = "RATIONAL" if _rational else "NOT RATIONAL"

# ---------------------------------------------------------------------------
# Row 1 — Headline verdict
# ---------------------------------------------------------------------------

st.markdown(
    f"""
    <div class="verdict-card">
      <div class="verdict-label">Break-even analysis</div>
      <div class="verdict-headline">
        Rational to spend up to ${_be:,.0f} on compute to save {_sched['weeks_saved']:.1f} weeks
      </div>
      <div class="verdict-subline">
        Your modeled compute spend: ${_ac['compute']:,.0f} &mdash;
        <span class="{_verdict_class}">VERDICT: {_verdict_word}</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Row 2 — Charts (two columns)
# ---------------------------------------------------------------------------

col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.markdown(section_header("Net benefit vs. compute spend"), unsafe_allow_html=True)

    fig_sweep = go.Figure()

    # Shade above/below zero
    _above = _sweep_df[_sweep_df["net_benefit"] >= 0]
    _below = _sweep_df[_sweep_df["net_benefit"] < 0]

    if not _above.empty:
        fig_sweep.add_trace(go.Scatter(
            x=_above["compute_cost"],
            y=_above["net_benefit"],
            mode="lines",
            line=dict(color="#1a6b1a", width=2),
            name="Net benefit (positive)",
            hovertemplate="Compute spend: $%{x:,.0f}<br>Net benefit: $%{y:,.0f}<extra></extra>",
        ))
    if not _below.empty:
        fig_sweep.add_trace(go.Scatter(
            x=_below["compute_cost"],
            y=_below["net_benefit"],
            mode="lines",
            line=dict(color="#b81c1c", width=2),
            name="Net benefit (negative)",
            hovertemplate="Compute spend: $%{x:,.0f}<br>Net benefit: $%{y:,.0f}<extra></extra>",
        ))

    # Break-even marker
    fig_sweep.add_vline(
        x=_be,
        line_dash="dash",
        line_color="#555555",
        line_width=1,
        annotation_text=f"Break-even ${_be:,.0f}",
        annotation_font=dict(family="IBM Plex Mono, monospace", size=10),
        annotation_position="top right",
    )

    # Current spend marker
    _spend_color = "#1a6b1a" if _rational else "#b81c1c"
    fig_sweep.add_vline(
        x=_ac["compute"],
        line_dash="dot",
        line_color=_spend_color,
        line_width=1.5,
        annotation_text=f"Your spend ${_ac['compute']:,.0f}",
        annotation_font=dict(family="IBM Plex Mono, monospace", size=10, color=_spend_color),
        annotation_position="top left",
    )

    fig_sweep.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis_title="Compute spend ($)",
        yaxis_title="Net benefit ($)",
        xaxis_tickformat="$,.0f",
        yaxis_tickformat="$,.0f",
        showlegend=False,
        height=340,
        margin=dict(l=70, r=20, t=30, b=50),
    )
    st.plotly_chart(fig_sweep, width="stretch")
    st.caption(
        "Sweep varies total compute spend as a scalar. GPU count, compute hours, "
        "and cloud rate are held constant at their sidebar values."
    )

with col_right:
    st.markdown(section_header("Schedule comparison"), unsafe_allow_html=True)

    fig_sched = go.Figure()
    fig_sched.add_trace(go.Bar(
        y=["Accelerated", "Baseline"],
        x=[_sched["accelerated_weeks"], _baseline_weeks],
        orientation="h",
        marker_color=["#1a6b1a", "#aaaaaa"],
        text=[
            f"{_sched['accelerated_weeks']:.1f} wks",
            f"{_baseline_weeks:.1f} wks",
        ],
        textposition="outside",
        textfont=dict(family="IBM Plex Mono, monospace", size=11),
        hovertemplate="%{y}: %{x:.1f} weeks<extra></extra>",
    ))
    fig_sched.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis_title="Weeks",
        yaxis_title="",
        height=340,
        margin=dict(l=20, r=60, t=30, b=50),
        xaxis=dict(range=[0, _baseline_weeks * 1.25]),
        showlegend=False,
    )
    st.plotly_chart(fig_sched, width="stretch")

    # Cost breakdown side-by-side
    st.markdown(section_header("Cost breakdown"), unsafe_allow_html=True)
    cb_left, cb_right = st.columns(2)
    with cb_left:
        st.markdown(
            metric_card("Baseline total", f"${_bc['total']:,.0f}",
                        f"Labor ${_bc['labor']:,.0f}"),
            unsafe_allow_html=True,
        )
    with cb_right:
        st.markdown(
            metric_card("Accelerated total", f"${_ac['total']:,.0f}",
                        f"Labor ${_ac['labor']:,.0f} · Compute ${_ac['compute']:,.0f} · "
                        f"AI licensing {_money(_ac['ai_licensing'])}"),
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Row 3 — PPA upside
# ---------------------------------------------------------------------------

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown(section_header("Bonus PPA upside — separate from schedule economics"), unsafe_allow_html=True)

ppa_col1, ppa_col2, ppa_col3 = st.columns(3)
with ppa_col1:
    st.markdown(
        metric_card("Annual power saving", f"${_ppa['annual']:,.0f}",
                    f"{leakage_reduction_pct:.1f}% leakage reduction × {deployed_units:,} units"),
        unsafe_allow_html=True,
    )
with ppa_col2:
    st.markdown(
        metric_card("3-year lifecycle saving", f"${_ppa['lifecycle']:,.0f}",
                    "Based on annual saving × 3 years"),
        unsafe_allow_html=True,
    )
with ppa_col3:
    st.markdown(
        metric_card("Schedule value captured", f"${_av:,.0f}",
                    f"{_sched['weeks_saved']:.1f} weeks × ${value_per_week:,.0f}/week"),
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Row 4 — Sensitivity table
# ---------------------------------------------------------------------------

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown(section_header("Sensitivity: net benefit ($) — rows = value per week saved, columns = cloud rate ($/GPU-hr)"), unsafe_allow_html=True)


def _fmt(v: float) -> str:
    return f"${v:,.0f}"


def _color_cell(v: float) -> str:
    if v > 0:
        intensity = min(int(80 * v / 2_000_000), 80)
        return f"background-color: rgba(26, 107, 26, {0.08 + intensity/400:.2f}); color: #0d3d0d;"
    else:
        intensity = min(int(80 * abs(v) / 2_000_000), 80)
        return f"background-color: rgba(184, 28, 28, {0.08 + intensity/400:.2f}); color: #5c0000;"


_display_grid = _grid_df.copy()
_display_grid.index = [f"${v:,.0f}" for v in _display_grid.index]
_display_grid.columns = [f"${r}/hr" for r in _display_grid.columns]
_display_grid.index.name = "Value / week saved"
_display_grid.columns.name = "Cloud rate ($/GPU-hr)"

styled = (
    _display_grid.style
    .format(_fmt)
    .map(_color_cell)
    .set_table_styles([
        {"selector": "th", "props": [
            ("font-family", "IBM Plex Sans, sans-serif"),
            ("font-size", "11px"),
            ("font-weight", "600"),
            ("color", "#555555"),
            ("text-transform", "uppercase"),
            ("letter-spacing", "0.06em"),
            ("background-color", "#f5f5f5"),
            ("border-bottom", "2px solid #cccccc"),
        ]},
        {"selector": "td", "props": [
            ("font-family", "IBM Plex Mono, monospace"),
            ("font-size", "12px"),
            ("text-align", "right"),
            ("padding", "6px 12px"),
            ("border-bottom", "1px solid #eeeeee"),
        ]},
        {"selector": "tr:hover", "props": [
            ("filter", "brightness(0.97)"),
        ]},
    ])
)

st.dataframe(styled, width="stretch")

# ---------------------------------------------------------------------------
# Row 5 — Disclaimer
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="disclaimer">'
    'Illustrative model using generic public benchmarks. Not affiliated with any EDA vendor. '
    'Licensing modeled as either ELA / sunk (no marginal cost) or token-based (incremental AI '
    'token consumption). ELA / sunk treats EDA licensing as a flat annual cost where per-block '
    "decisions don't have marginal licensing costs."
    '</div>',
    unsafe_allow_html=True,
)
