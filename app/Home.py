"""Front page: the result in plain English, for coaches and non-technical readers."""

import plotly.graph_objects as go
import streamlit as st

from common import (
    AWAY,
    EMPTY,
    FANS,
    HOME,
    LEAGUES,
    NEUTRAL,
    footer,
    kpis,
    league_picker,
    load,
    setup,
    show,
    slope,
    style,
    summary,
)

setup("Home")
st.title("Ghost Games")
st.markdown(
    "#### What empty stadiums revealed about home advantage\n"
    "In 2020 and 2021, COVID forced Europe's top leagues to play without fans. Same teams, "
    "same referees, same rules, no crowd. Comparing those matches with normal ones shows how "
    "much of home advantage the crowd really creates. Pick a league to see its own numbers."
)
league = league_picker()
name = LEAGUES[league]

shares = load("share_lost").query("league == @league and treatment == 'closed_doors'")
shares = shares.set_index("outcome")
means = load("group_means").query("league == @league").set_index("crowd_status")
fans, empty = means.loc["fans"], means.loc["empty"]


def share_text(value: float) -> str:
    return "all of it" if value >= 0.995 else f"{value:.0%}"


goals, cards = shares.loc["goal_diff", "share_lost"], shares.loc["card_gap", "share_lost"]
lost_text = "all" if goals >= 0.995 else f"{goals:.0%}"
where = "Across all five leagues" if league == "ALL" else f"In {name}"
kpis(
    [
        ("Home advantage lost", share_text(goals), "of the goal edge, without fans", EMPTY),
        (
            "Home win rate",
            f"{fans['home_win']:.0%} → {empty['home_win']:.0%}",
            "with fans → empty stadium",
            FANS,
        ),
        (
            "Referee card edge lost",
            share_text(cards),
            "away teams stopped getting extra cards",
            HOME,
        ),
    ]
)

# where the home edge went: the part the crowd took away vs the part that stayed
h, e = shares.loc["goal_diff", "home_adv"], shares.loc["goal_diff", "effect"]
kept, lost = max(h + e, 0), min(-e, h)
fig = go.Figure()
fig.add_bar(
    y=["Home edge"],
    x=[kept],
    orientation="h",
    marker_color=FANS,
    name="Stayed without fans",
    text=f"Stayed: {kept:.2f}",
    textposition="inside",
    insidetextanchor="middle",
    textfont={"color": "white", "size": 15},
    hovertemplate="Stayed without fans: %{x:.2f} goals<extra></extra>",
)
fig.add_bar(
    y=["Home edge"],
    x=[lost],
    orientation="h",
    marker_color=EMPTY,
    name="Left with the fans",
    text=f"Left with the fans: {lost:.2f}",
    textposition="inside",
    insidetextanchor="middle",
    textfont={"color": "white", "size": 15},
    hovertemplate="Left with the fans: %{x:.2f} goals<extra></extra>",
)
fig.update_layout(barmode="stack", bargap=0.25, showlegend=False)
fig.update_xaxes(title="Home edge in goals per match (after controlling for team strength)")
fig.update_yaxes(visible=False)
title = (
    f"The crowd was worth {lost:.2f} of the {h:.2f}-goal home edge"
    if h + e > 0
    else f"In {name}, the whole {h:.2f}-goal home edge left with the fans"
)
show(style(fig, title, f"{name}: average home edge in goals per match", height=270))

st.markdown("#### In plain words")
st.markdown(
    f"""
- **The crowd is worth a lot.** {where}, {lost_text} of the home goal edge disappeared without
  fans. Whatever stayed comes from travel, a familiar pitch and routine.
- **The lost wins went to the away team, not to draws.** Home teams won {fans["home_win"]:.0%}
  of matches with fans and {empty["home_win"]:.0%} without. Away wins went from
  {fans["away_win"]:.0%} to {empty["away_win"]:.0%}.
- **Referees stopped favouring the home side.** Away teams got
  {fans["away_yellows"] - fans["home_yellows"]:+.2f} yellow cards per match compared with home
  teams when fans were in, and {empty["away_yellows"] - empty["home_yellows"]:+.2f} without them.
- **For a coach:** a home crowd is worth about a quarter of a goal per match, partly through the
  referee. A hostile away crowd is worth preparing players for, and a quiet stadium is a chance.
"""
)

outcomes = {"Home win": "home_win", "Draw": "draw", "Away win": "away_win"}
fig = slope(
    {k: fans[v] for k, v in outcomes.items()},
    {k: empty[v] for k, v in outcomes.items()},
    {"Home win": HOME, "Draw": NEUTRAL, "Away win": AWAY},
)
show(
    style(
        fig,
        f"Without fans, home wins fell from {fans['home_win']:.0%} to {empty['home_win']:.0%}, "
        "and away wins took them",
        f"{name}: share of matches, {int(fans['n_matches']):,} with fans and "
        f"{int(empty['n_matches']):,} empty",
        height=420,
    )
)

with st.expander("How was this measured?"):
    st.write(
        f"{summary()['n_matches']:,} matches from the top five European leagues. Empty matches "
        "were identified from real attendance figures. A regression compares fans and empty "
        "matches while controlling for how strong each team was that season, so the result "
        "isn't just 'stronger teams happened to play at home'. The other pages show the "
        "uncertainty around each number."
    )
footer()
