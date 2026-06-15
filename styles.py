"""
styles.py — CSS injection and shared Plotly template for the EDA TCO dashboard.
"""

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ---------------------------------------------------------------------------
# Google Fonts + global CSS
# ---------------------------------------------------------------------------

_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">

<style>
  /* Base typography */
  html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
  }

  /* Monospace numbers */
  .metric-value, .mono {
    font-family: 'IBM Plex Mono', monospace;
  }

  /* Headline verdict card */
  .verdict-card {
    background: #ffffff;
    border: 1.5px solid #1a1a1a;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
  }

  .verdict-label {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #555555;
    margin-bottom: 0.4rem;
  }

  .verdict-headline {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.5rem;
    font-weight: 500;
    color: #1a1a1a;
    line-height: 1.3;
    margin-bottom: 0.5rem;
  }

  .verdict-subline {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.1rem;
    font-weight: 400;
    line-height: 1.3;
  }

  .verdict-rational   { color: #1a6b1a; }
  .verdict-irrational { color: #b81c1c; }

  /* Metric cards (PPA, cost breakdown) */
  .metric-card {
    background: #f5f5f5;
    border-left: 3px solid #1a1a1a;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
  }

  .metric-card-label {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #555555;
    margin-bottom: 0.25rem;
  }

  .metric-card-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.35rem;
    font-weight: 500;
    color: #1a1a1a;
  }

  .metric-card-sub {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.75rem;
    color: #777777;
    margin-top: 0.15rem;
  }

  /* Section divider */
  .section-divider {
    border: none;
    border-top: 1px solid #cccccc;
    margin: 1.5rem 0;
  }

  /* Section header */
  .section-header {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #555555;
    margin-bottom: 0.75rem;
  }

  /* Disclaimer */
  .disclaimer {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.7rem;
    color: #999999;
    margin-top: 2rem;
    padding-top: 0.75rem;
    border-top: 1px solid #eeeeee;
  }

  /* Sidebar section headers */
  .sidebar-section {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #777777;
    margin-top: 0.5rem;
    margin-bottom: -0.5rem;
  }

  /* Tighten up Streamlit's default padding */
  .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1100px;
  }

  /* Hide Streamlit branding but keep sidebar toggle visible */
  #MainMenu                        { visibility: hidden; }
  footer                           { visibility: hidden; }
  [data-testid="stToolbar"]        { visibility: hidden; }
  [data-testid="stExpandSidebarButton"] { visibility: visible; }
  [data-testid="stDecoration"]     { display: none; }
</style>
"""


def inject_css() -> None:
    """Inject Google Fonts and dashboard CSS into the Streamlit page."""
    st.markdown(_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Shared Plotly template
# ---------------------------------------------------------------------------

_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        font=dict(family="IBM Plex Sans, sans-serif", size=12, color="#1a1a1a"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        xaxis=dict(
            showgrid=True,
            gridcolor="#e8e8e8",
            gridwidth=1,
            linecolor="#cccccc",
            linewidth=1,
            tickfont=dict(family="IBM Plex Mono, monospace", size=11),
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#e8e8e8",
            gridwidth=1,
            linecolor="#cccccc",
            linewidth=1,
            tickfont=dict(family="IBM Plex Mono, monospace", size=11),
            zeroline=True,
            zerolinecolor="#aaaaaa",
            zerolinewidth=1,
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
            font=dict(family="IBM Plex Sans, sans-serif", size=11),
        ),
        margin=dict(l=60, r=30, t=40, b=50),
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor="#1a1a1a",
            font=dict(family="IBM Plex Mono, monospace", size=11),
        ),
        colorway=["#1a1a1a", "#555555", "#1a6b1a", "#b81c1c", "#2255aa"],
    )
)

pio.templates["eda_tco"] = _TEMPLATE
pio.templates.default = "eda_tco"

PLOTLY_TEMPLATE = "eda_tco"


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def metric_card(label: str, value: str, sub: str = "") -> str:
    sub_html = f'<div class="metric-card-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="metric-card">'
        f'<div class="metric-card-label">{label}</div>'
        f'<div class="metric-card-value">{value}</div>'
        f"{sub_html}"
        f"</div>"
    )


def section_header(text: str) -> str:
    return f'<div class="section-header">{text}</div>'


def sidebar_section(text: str) -> str:
    return f'<div class="sidebar-section">{text}</div>'
