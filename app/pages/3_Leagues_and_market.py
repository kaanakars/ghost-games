"""League by league, and whether the betting market saw it."""

import plotly.graph_objects as go
import streamlit as st

from common import (
    EMPTY,
    FANS,
    FLAGS,
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

setup("Leagues and market")
st.title("Leagues and the betting market")
league = league_picker()
name = LEAGUES[league]

outcome = (
    st.segmented_control(
        "Measure",
        ["goal_diff", "points_diff", "card_gap"],
        format_func=lambda o: OUTCOMES[o],
        default="goal_diff",
        key="league_measure",
    )
    or "goal_diff"
)
table = load("by_league").query("outcome == @outcome").copy()
table["name"] = table["league"].map(lambda code: f"{FLAGS[code]} {LEAGUES[code]}")
table["drop"] = table["fans"] - table["empty"]
table = table.sort_values("drop")

fig = go.Figure()
for _, row in table.iterrows():
    # the chosen league stays bright, the others fade back
    alpha = 1.0 if league in ("ALL", row["league"]) else 0.25
    fig.add_annotation(
        x=row["empty"],
        y=row["name"],
        ax=row["fans"],
        ay=row["name"],
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.2,
        arrowwidth=3,
        arrowcolor=f"rgba(91,107,99,{0.55 * alpha})",
        standoff=10,
        startstandoff=10,
    )
    for col, colour, pos in [("fans", FANS, "middle right"), ("empty", EMPTY, "middle left")]:
        if row["fans"] < row["empty"]:
            pos = "middle left" if col == "fans" else "middle right"
        fig.add_scatter(
            x=[row[col]],
            y=[row["name"]],
            mode="markers+text",
            marker={
                "size": 16,
                "color": colour,
                "opacity": alpha,
                "line": {"color": "white", "width": 2},
            },
            text=[f"{row[col]:.2f}"],
            textposition=pos,
            textfont={"color": INK if alpha == 1 else MUTED, "size": 13},
            hovertemplate=f"{row['name']}<br>{'With fans' if col == 'fans' else 'Empty'}: "
            "%{x:.2f}<extra></extra>",
            cliponaxis=False,
        )
fig.add_vline(x=0, line_color=MUTED, line_width=1)
fig.update_xaxes(title=f"Home edge, {UNITS[outcome]}")
fig.update_yaxes(tickfont={"size": 14, "color": INK})
show(
    style(
        fig,
        "The home edge shrank in every league",
        "Blue = with fans, orange = empty, sorted by the size of the drop."
        + (" Serie A's goal drop is within its margin of error." if outcome == "goal_diff" else ""),
        height=380,
    )
)

st.markdown("#### Did the betting market see it?")
st.write(
    "Bet365 odds were turned into a home-win probability, with the bookmaker's margin "
    "removed, and compared with what actually happened."
)
market = load("market").query("league == @league").set_index("period")
market = market.loc[["fans", "empty: first weeks", "empty: later"]]
periods = ["With fans", "Empty: first 2 months", "Empty: later"]
fig = go.Figure()
fig.add_bar(
    x=periods,
    y=market["predicted"],
    name="Odds predicted",
    marker_color="#b9c6bf",
    text=[f"{v:.1%}" for v in market["predicted"]],
    textposition="outside",
)
fig.add_bar(
    x=periods,
    y=market["actual"],
    name="Actually happened",
    marker_color=INK,
    text=[f"{v:.1%}" for v in market["actual"]],
    textposition="outside",
    customdata=market[["gap", "ci_low", "ci_high", "matches"]] * [100, 100, 100, 1],
    hovertemplate="%{x}<br>Actual %{y:.1%}<br>Gap %{customdata[0]:+.1f} points "
    "(CI %{customdata[1]:+.1f} to %{customdata[2]:+.1f})<br>%{customdata[3]} matches"
    "<extra></extra>",
)
fig.update_layout(barmode="group", bargap=0.3, showlegend=True)
fig.update_yaxes(tickformat=".0%", range=[0, max(market[["predicted", "actual"]].max()) * 1.2])
show(
    style(
        fig,
        "The odds lowered home teams' chances, but not enough",
        f"{name}: home-win rate. Hover the bars for the gap and its 95% CI.",
        height=400,
    )
)
st.caption(
    "Across all leagues, empty-stadium home teams won about 3 points less often than priced "
    "(CI 0.9 to 5.2). Single leagues have fewer matches, so their intervals are wider. "
    "This is about how prices absorb news, not betting advice."
)
footer()
