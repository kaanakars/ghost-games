"""Did referees favour the home side because of the crowd?"""

import plotly.graph_objects as go
import streamlit as st

from common import (
    AWAY,
    EMPTY,
    FANS,
    HOME,
    INK,
    LEAGUES,
    MUTED,
    footer,
    kpis,
    league_picker,
    load,
    setup,
    show,
    slope,
    style,
)

setup("Referees")
st.title("Referees")
league = league_picker()
name = LEAGUES[league]
means = load("group_means").query("league == @league").set_index("crowd_status")
fans, empty = means.loc["fans"], means.loc["empty"]

st.write(
    "With fans, away teams got more yellow cards than home teams. Without fans, that gap "
    "disappeared. Did the home players change, or did the referee?"
)

c1, c2 = st.columns(2)
with c1:
    fig = slope(
        {"Home": fans["home_yellows"], "Away": fans["away_yellows"]},
        {"Home": empty["home_yellows"], "Away": empty["away_yellows"]},
        {"Home": HOME, "Away": AWAY},
        fmt="{:.2f}",
    )
    show(style(fig, "Away teams lost their extra cards", f"{name}: yellow cards per match"))
with c2:
    fig = slope(
        {"Home": fans["home_fouls"], "Away": fans["away_fouls"]},
        {"Home": empty["home_fouls"], "Away": empty["away_fouls"]},
        {"Home": HOME, "Away": AWAY},
        fmt="{:.1f}",
    )
    show(style(fig, "Fouls barely moved", f"{name}: fouls per match"))

kpis(
    [
        (
            "Extra away yellows per 100 fouls, with fans",
            f"{fans['booking_gap'] * 100:+.1f}",
            "away booking rate minus home",
            FANS,
        ),
        (
            "Without fans",
            f"{empty['booking_gap'] * 100:+.1f}",
            "the referee's lean almost disappeared",
            EMPTY,
        ),
        (
            "Home fouls per match",
            f"{fans['home_fouls']:.1f} → {empty['home_fouls']:.1f}",
            "home teams didn't calm down",
            HOME,
        ),
    ]
)
st.caption(
    "Limit: the data has no foul severity, so harder away fouls could explain part of the gap."
)

st.markdown("#### Did any referee stand out?")
if league not in ("ALL", "E0"):
    st.info("Only the Premier League files name the referee. Pick Premier League or All leagues.")
else:
    refs = load("referees").sort_values("change")
    overall = refs["shrunk_change"].iloc[0]
    fig = go.Figure()
    fig.add_vrect(
        x0=overall - 0.02, x1=overall + 0.02, fillcolor="rgba(42,120,214,0.25)", line_width=0
    )
    fig.add_annotation(
        x=overall,
        y=1.02,
        yref="paper",
        text=f"all referees: {overall:+.2f}",
        showarrow=False,
        font={"color": FANS},
    )
    fig.add_bar(
        y=refs["referee"],
        x=2 * 1.96 * refs["se"],
        base=refs["change"] - 1.96 * refs["se"],
        orientation="h",
        marker_color="rgba(176,74,156,0.15)",
        width=0.55,
        hoverinfo="skip",
    )
    fig.add_scatter(
        x=refs["change"],
        y=refs["referee"],
        mode="markers",
        marker={"color": AWAY, "size": 11, "line": {"color": "white", "width": 1.5}},
        customdata=refs[["matches_fans", "matches_empty", "se"]],
        hovertemplate="%{y}: %{x:+.2f} cards<br>%{customdata[0]} fan matches, "
        "%{customdata[1]} empty<extra></extra>",
    )
    fig.add_vline(x=0, line_color=MUTED, line_width=1)
    fig.update_xaxes(title="Change in the away-minus-home card gap, empty minus fans")
    fig.update_yaxes(tickfont={"color": INK})
    show(
        style(
            fig,
            "No referee stands out: all changed by about the same amount",
            "Premier League referees with 30+ fan and 10+ empty matches. Bars are 95% CIs.",
            height=40 + 26 * len(refs) + 80,
        )
    )
    st.caption(
        "Every interval overlaps the overall change. After empirical-Bayes shrinkage, the "
        "estimated real spread between referees is zero."
    )
footer()
