"""Data loading, league picker and chart style shared by every page."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"
REPO = "https://github.com/kaanakars/ghost-games"

FANS = "#2a78d6"  # blue
EMPTY = "#eb6834"  # orange
# home vs away: a separate colour pair from fans vs empty
HOME = "#1d7a4c"  # green
AWAY = "#b04a9c"  # magenta
NEUTRAL = "#8f8d87"  # draws
INK = "#16352a"
MUTED = "#5b6b63"
GRID = "#e6e9e4"
FONT = "Archivo, system-ui, sans-serif"

LEAGUES = {
    "ALL": "All leagues",
    "E0": "Premier League",
    "D1": "Bundesliga",
    "SP1": "La Liga",
    "I1": "Serie A",
    "F1": "Ligue 1",
}
# flags, not league logos (trademarks)
FLAGS = {
    "ALL": "🌍",
    "E0": "🏴\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f",
    "D1": "🇩🇪",
    "SP1": "🇪🇸",
    "I1": "🇮🇹",
    "F1": "🇫🇷",
}
OUTCOMES = {
    "goal_diff": "Goal difference",
    "goal_diff_capped": "Goal difference (capped at ±3)",
    "points_diff": "Points difference",
    "card_gap": "Yellow card gap",
}
UNITS = {
    "goal_diff": "goals per match",
    "points_diff": "points per match",
    "card_gap": "yellow cards per match",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&display=swap');
html, body, [class*="css"], .stMarkdown, .stCaption {
  font-family: 'Archivo', system-ui, sans-serif; }
h1, h2, h3 { font-family: 'Archivo', sans-serif !important; font-variation-settings: "wdth" 112;
  color: #16352a !important; letter-spacing: -0.01em; }
h1 { font-weight: 800 !important; }
.block-container { padding-top: 2.2rem; max-width: 1150px; }
.kpis { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin: 8px 0 18px; }
.kpi { background: #ffffff; border: 1px solid #e6e9e4; border-left: 5px solid var(--accent);
  border-radius: 10px; padding: 16px 18px; }
.kpi .label { color: #5b6b63; font-size: 0.9rem; }
.kpi .value { color: #16352a; font-size: 2.3rem; font-weight: 800; line-height: 1.15;
  font-variation-settings: "wdth" 115; }
.kpi .note { color: #5b6b63; font-size: 0.85rem; }
.chart-head { background: #ffffff; border: 1px solid #e6e9e4; border-bottom: 0;
  border-radius: 10px 10px 0 0; padding: 14px 16px 2px; margin-bottom: -16px; }
.chart-title { font-weight: 700; font-size: 1.1rem; color: #16352a; }
.chart-sub { color: #5b6b63; font-size: 0.88rem; margin-top: 2px; }
@media (max-width: 700px) { .kpis { grid-template-columns: 1fr; } }
</style>
"""


def setup(title: str) -> None:
    """Page config and styles. Must be the first Streamlit call on every page."""
    st.set_page_config(page_title=f"{title} · Ghost Games", page_icon="⚽", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


def league_picker() -> str:
    """League choice that stays the same when switching pages.

    Streamlit clears a widget's state when its page closes, so the choice is
    copied into a separate session key and used as the next page's default.
    """
    saved = st.session_state.get("league", "ALL")
    choice = st.segmented_control(
        "League",
        options=list(LEAGUES),
        format_func=lambda code: f"{FLAGS[code]} {LEAGUES[code]}",
        default=saved,
        key="league_widget",
    )
    league = choice or saved  # clicking the selected option again returns None
    st.session_state["league"] = league
    return league


@st.cache_data
def load(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / f"{name}.csv")


@st.cache_data
def summary() -> dict:
    return json.loads((DATA / "summary.json").read_text())


def kpis(cards: list[tuple[str, str, str, str]]) -> None:
    """Metric cards: (label, value, note, accent colour)."""
    html = "".join(
        f'<div class="kpi" style="--accent:{accent}"><div class="label">{label}</div>'
        f'<div class="value">{value}</div><div class="note">{note}</div></div>'
        for label, value, note, accent in cards
    )
    st.markdown(f'<div class="kpis">{html}</div>', unsafe_allow_html=True)


def style(fig: go.Figure, title: str, subtitle: str = "", height: int = 400) -> go.Figure:
    """House style. The title states the finding, the subtitle says what is plotted.

    Titles are kept in the figure's meta and written as page text by show(),
    so readers can select and copy them (text inside a chart can't be).
    """
    fig.update_layout(
        meta={"title": title, "subtitle": subtitle},
        height=height,
        font={"family": FONT, "color": INK, "size": 13},
        margin={"l": 10, "r": 20, "t": 40, "b": 10},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.0, "x": 1, "xanchor": "right"},
        hoverlabel={"bgcolor": "#ffffff", "bordercolor": GRID, "font": {"family": FONT}},
        showlegend=fig.layout.showlegend if fig.layout.showlegend is not None else False,
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=GRID, zeroline=False, tickfont={"color": MUTED})
    fig.update_yaxes(gridcolor=GRID, linecolor=GRID, zeroline=False, tickfont={"color": MUTED})
    return fig


def show(fig: go.Figure) -> None:
    meta = fig.layout.meta or {}
    if meta.get("title"):
        sub = f'<div class="chart-sub">{meta["subtitle"]}</div>' if meta.get("subtitle") else ""
        st.markdown(
            f'<div class="chart-head"><div class="chart-title">{meta["title"]}</div>{sub}</div>',
            unsafe_allow_html=True,
        )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def slope(
    left: dict[str, float],
    right: dict[str, float],
    colours: dict[str, str],
    fmt: str = "{:.0%}",
    labels: tuple[str, str] = ("With fans", "Empty stadium"),
) -> go.Figure:
    """Slope chart: one line per series from fans (left) to empty (right), labelled at both ends."""
    fig = go.Figure()
    # labels of two close end points would overlap: push the higher one up, the lower one down
    span = max([*left.values(), *right.values()]) - min([*left.values(), *right.values()])
    nudge = {}
    for side, values in (("left", left), ("right", right)):
        ordered = sorted(values, key=values.get)
        for low, high in zip(ordered, ordered[1:], strict=False):
            if values[high] - values[low] < 0.08 * span:
                nudge[(side, high)], nudge[(side, low)] = "top", "bottom"
    for name, colour in colours.items():
        a, b = left[name], right[name]
        fig.add_scatter(
            x=list(labels),
            y=[a, b],
            mode="lines+markers+text",
            line={"color": colour, "width": 4},
            marker={"size": 14, "color": colour, "line": {"color": "white", "width": 2}},
            text=[f"{name}  {fmt.format(a)}", f"{fmt.format(b)}  {name}"],
            textposition=[
                f"{nudge.get(('left', name), 'middle')} left",
                f"{nudge.get(('right', name), 'middle')} right",
            ],
            textfont={"color": colour, "size": 14},
            hovertemplate=f"{name}<br>%{{x}}: %{{y:.3f}}<extra></extra>",
            cliponaxis=False,
        )
    fig.update_xaxes(range=[-0.9, 1.9], showgrid=False, tickfont={"size": 14, "color": INK})
    fig.update_yaxes(visible=False)
    return fig


def footer() -> None:
    st.divider()
    st.caption(
        f"Data: football-data.co.uk results and FBref attendance, {summary()['seasons']}. "
        f"Code, tests and methods on [GitHub]({REPO}). Built by Kaan Akar."
    )
