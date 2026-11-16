"""Save the results the web app shows as small CSVs.

The app reads only these files, so it never needs the raw data or FBref.
Run after any change to the analysis: ghost-games-export
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ghost_games.market import market_check
from ghost_games.model import fit_home_advantage, home_advantage_over_time
from ghost_games.pipeline import build_matches
from ghost_games.referees import booking_rate_gap, referee_table

OUTCOMES = ["goal_diff", "goal_diff_capped", "points_diff", "card_gap"]
LEAGUES = ["E0", "D1", "SP1", "I1", "F1"]


def league_subsets(matches: pd.DataFrame):
    """("ALL", every match), then one subset per league."""
    yield "ALL", matches
    for league in LEAGUES:
        yield league, matches[matches["league"] == league]


def share_lost_table(matches: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for league, subset in league_subsets(matches):
        # crowd size only for all leagues: per league, too few part-filled matches
        treatments = ["closed_doors", "crowd_level"] if league == "ALL" else ["closed_doors"]
        for treatment in treatments:
            for outcome in OUTCOMES:
                fit = fit_home_advantage(subset, outcome, treatment=treatment)
                low, high = fit.share_ci
                rows.append(
                    {
                        "league": league,
                        "treatment": treatment,
                        "outcome": outcome,
                        "home_adv": fit.home_adv,
                        "effect": fit.effect,
                        "share_lost": fit.share_of_advantage_lost,
                        "ci_low": low,
                        "ci_high": high,
                        "n_matches": fit.n_matches,
                    }
                )
    return pd.DataFrame(rows)


def by_league_table(matches: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for league in LEAGUES:
        for outcome in ["goal_diff", "points_diff", "card_gap"]:
            fit = fit_home_advantage(matches[matches["league"] == league], outcome)
            rows.append(
                {
                    "league": league,
                    "outcome": outcome,
                    "fans": fit.home_adv,
                    "empty": fit.home_adv + fit.effect,
                    "effect_ci_low": fit.ci[0],
                    "effect_ci_high": fit.ci[1],
                }
            )
    return pd.DataFrame(rows)


def over_time_table(matches: pd.DataFrame) -> pd.DataFrame:
    frames = [
        home_advantage_over_time(subset, outcome, freq="QS").assign(outcome=outcome, league=league)
        for league, subset in league_subsets(matches)
        for outcome in ["goal_diff", "points_diff", "card_gap"]
    ]
    return pd.concat(frames, ignore_index=True)


def group_means(matches: pd.DataFrame) -> pd.DataFrame:
    """Win/draw/loss rates, cards, fouls and booking gap per match, fans vs empty."""
    cols = ["home_win", "draw", "away_win", "home_yellows", "away_yellows"]
    cols += ["home_fouls", "away_fouls", "goal_diff"]
    rows = []
    for league, subset in league_subsets(matches):
        for status in ["fans", "empty"]:
            group = subset[subset["crowd_status"] == status]
            row = group[cols].mean().to_dict()
            row.update(
                league=league,
                crowd_status=status,
                n_matches=len(group),
                booking_gap=booking_rate_gap(group),
            )
            rows.append(row)
    return pd.DataFrame(rows)


def market_table(matches: pd.DataFrame) -> pd.DataFrame:
    frames = [
        market_check(subset).reset_index().assign(league=league)
        for league, subset in league_subsets(matches)
    ]
    return pd.concat(frames, ignore_index=True)


def export_app_data(project_dir: str | Path = ".", out_dir: str | Path = "app/data") -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    matches = build_matches(project_dir)

    share_lost_table(matches).to_csv(out / "share_lost.csv", index=False)
    by_league_table(matches).to_csv(out / "by_league.csv", index=False)
    over_time_table(matches).to_csv(out / "over_time.csv", index=False)
    group_means(matches).to_csv(out / "group_means.csv", index=False)
    referee_table(matches).to_csv(out / "referees.csv")
    market_table(matches).to_csv(out / "market.csv", index=False)

    summary = {
        "n_matches": len(matches),
        "seasons": f"{matches['season'].min()} to {matches['season'].max()}",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2))


def main() -> None:
    export_app_data()
    print("Saved app data to app/data")


if __name__ == "__main__":
    main()
