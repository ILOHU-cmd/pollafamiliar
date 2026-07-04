"""Pure scoring helpers for Polla Familiar predictions."""

from __future__ import annotations


def match_outcome(home_score: int, away_score: int) -> str:
    """Return the outcome token for a score: 'home', 'away', or 'draw'."""
    if home_score > away_score:
        return "home"
    if away_score > home_score:
        return "away"
    return "draw"


def calculate_points(
    pred_home: int,
    pred_away: int,
    actual_home: int | None,
    actual_away: int | None,
) -> int | None:
    """Calculate prediction points, or None when the match has no final score."""
    if actual_home is None or actual_away is None:
        return None

    if pred_home == actual_home and pred_away == actual_away:
        return 3

    # Draws are scored exactly like picking a winner: same result, 2 points.
    if match_outcome(pred_home, pred_away) == match_outcome(actual_home, actual_away):
        return 2

    return 0
