"""How much of the home edge was lost, and when."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from common import (
    EMPTY,
    FANS,
    INK,
    LEAGUES,
    MUTED,
    OUTCOMES,
    UNITS,
    footer,
    league_picker,
    load,
    setup,
    show,
    style,
)

setup("Goals and points")
st.title("Goals and points")
league = league_picker()
name = LEAGUES[league]

treatment = "closed_doors"
if league == "ALL":
    choice = st.radio(
        "Compare",
        ["Fans vs empty", "Crowd size (includes part-filled stadiums)"],
        horizontal=True,
    )
    treatment = "closed_doors" if choice.startswith("Fans") else "crowd_level"

table = load("share_lost").query("league == @league and treatment == @treatment").iloc[::-1]
counts = load("group_means").query("league == @league").set_index("crowd_status")["n_matches"]
n_note = f"{int(counts['empty']):,} empty-stadium matches vs {int(counts['fans']):,} with fans"
labels = [OUTCOMES[o] for o in table["outcome"]]

fig = go.Figure()
# CI as a thick, light bar behind the estimate
fig.add_bar(
    y=labels,
    x=table["ci_high"] - table["ci_low"],
    base=table["ci_low"],
    orientation="h",
    marker_color="rgba(235,104,52,0.18)",
    width=0.45,
    hoverinfo="skip",
)
fig.add_scatter(
    x=table["share_lost"],
    y=labels,
    mode="markers+text",
    marker={"size": 18, "color": EMPTY, "line": {"color": "white", "width": 2}},
    text=[f"{v:.0%}" for v in table["share_lost"]],
    textposition="top center",
    textfont={"size": 14, "color": INK},
    customdata=table[["ci_low", "ci_high"]],
    hovertemplate="%{y}<br>%{x:.0%} lost (95% CI %{customdata[0]:.0%} to %{customdata[1]:.0%})"
    "<extra></extra>",
)
fig.add_vline(x=1, line_dash="dash", line_color=MUTED, annotation_text="all of it")
fig.update_xaxes(tickformat=".0%", range=[min(-0.1, table["ci_low"].min() - 0.05), 1.6])
fig.update_layout(bargap=0.5)
show(
    style(
        fig,
        "Every measure agrees: most of the home edge left with the fans",
        f"{name}: share of home advantage lost. Shaded bars are 95% confidence intervals, "
        f"from {n_note}; one league alone has fewer matches, so its bars are wider.",
        height=380,
    )
)

st.markdown("#### Home advantage over time")
outcome = (
    st.segmented_control(
        "Measure",
        ["goal_diff", "points_diff", "card_gap"],
        format_func=lambda o: OUTCOMES[o],
        default="goal_diff",
        key="time_measure",
    )
    or "goal_diff"
)
series = load("over_time").query("league == @league and outcome == @outcome").copy()
series["date"] = series["date"].astype("datetime64[ns]")

fig = go.Figure()
# shade each run of quarters where most matches were empty
empty = (series["share_empty"] > 0.5).to_numpy()
runs = np.flatnonzero(np.diff(np.r_[0, empty.astype(int), 0]))
for start, end in zip(runs[::2], runs[1::2], strict=True):
    fig.add_vrect(
        x0=series["date"].iloc[start] - np.timedelta64(45, "D"),
        x1=series["date"].iloc[end - 1] + np.timedelta64(45, "D"),
        fillcolor="rgba(235,104,52,0.12)",
        line_width=0,
        layer="below",
    )
if len(runs):
    fig.add_annotation(
        x=series["date"].iloc[runs[0]],
        y=1,
        yref="paper",
        text="Stadiums empty",
        showarrow=False,
        xanchor="left",
        font={"color": EMPTY, "size": 13},
    )
fig.add_scatter(
    x=list(series["date"]) + list(series["date"][::-1]),
    y=list(series["ci_high"]) + list(series["ci_low"][::-1]),
    fill="toself",
    fillcolor="rgba(42,120,214,0.12)",
    line={"width": 0},
    hoverinfo="skip",
)
fig.add_scatter(
    x=series["date"],
    y=series["mean"],
    mode="lines+markers",
    line={"color": FANS, "width": 3, "shape": "spline", "smoothing": 0.6},
    marker={"size": 7, "color": [EMPTY if e else FANS for e in empty]},
    customdata=series[["ci_low", "ci_high", "count"]],
    hovertemplate="%{x|%b %Y}<br>%{y:.2f} (CI %{customdata[0]:.2f} to %{customdata[1]:.2f})"
    "<br>%{customdata[2]} matches<extra></extra>",
)
before = series.loc[series["date"] < "2020-03-01", "mean"].mean()
fig.add_hline(
    y=before,
    line_dash="dot",
    line_color=MUTED,
    annotation_text="average before COVID",
    annotation_position="top left",
)
fig.add_hline(y=0, line_color=MUTED, line_width=1)
fig.update_xaxes(rangeslider={"visible": True, "thickness": 0.06})
fig.update_yaxes(title=f"Home edge, {UNITS[outcome]}")
show(
    style(
        fig,
        "The edge dropped when the fans left, and came back with them",
        f"{name}: average per quarter with 95% CI. Drag the slider to zoom.",
        height=460,
    )
)
footer()
