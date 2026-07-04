"""JSON-backed data access layer for Polla Familiar.

All Streamlit pages must use this module instead of reading or writing the JSON
file directly. A future PostgreSQL/SQLAlchemy implementation should preserve
these function signatures as the app-facing contract.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "polla_data.json"

DEFAULT_DATA: dict[str, list[dict[str, Any]]] = {
    "users": [],
    "matches": [],
    "predictions": [],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_data_file() -> None:
    """Create the JSON store with the expected shape when it does not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        _write_data(deepcopy(DEFAULT_DATA))


def _read_data() -> dict[str, list[dict[str, Any]]]:
    """Read and normalize the full JSON document from disk."""
    _ensure_data_file()
    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    for key, default_value in DEFAULT_DATA.items():
        data.setdefault(key, deepcopy(default_value))
    return data


def _write_data(data: dict[str, list[dict[str, Any]]]) -> None:
    """Write the full JSON document to disk using a readable format."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def _next_id(records: list[dict[str, Any]]) -> int:
    """Return the next integer id for a list of records."""
    return max((int(record["id"]) for record in records), default=0) + 1


def get_users() -> list[dict[str, Any]]:
    """Return all registered users."""
    return deepcopy(_read_data()["users"])


def get_user(user_id: int) -> dict[str, Any] | None:
    """Return a user by id, or None when it does not exist."""
    for user in _read_data()["users"]:
        if int(user["id"]) == int(user_id):
            return deepcopy(user)
    return None


def get_user_by_username(username: str) -> dict[str, Any] | None:
    """Return a user by username using case-insensitive comparison."""
    normalized = username.strip().lower()
    for user in _read_data()["users"]:
        if user["username"].lower() == normalized:
            return deepcopy(user)
    return None


def get_user_by_email(email: str) -> dict[str, Any] | None:
    """Return a user by email using case-insensitive comparison."""
    normalized = email.strip().lower()
    for user in _read_data()["users"]:
        if user["email"].lower() == normalized:
            return deepcopy(user)
    return None


def create_user(username: str, email: str, password_hash: str, is_admin: bool = False) -> dict[str, Any]:
    """Create and return a user, raising ValueError for duplicate username/email."""
    data = _read_data()
    normalized_username = username.strip()
    normalized_email = email.strip().lower()

    if any(user["username"].lower() == normalized_username.lower() for user in data["users"]):
        raise ValueError("El usuario ya existe.")
    if any(user["email"].lower() == normalized_email for user in data["users"]):
        raise ValueError("El correo ya está registrado.")

    user = {
        "id": _next_id(data["users"]),
        "username": normalized_username,
        "email": normalized_email,
        "password_hash": password_hash,
        "is_admin": bool(is_admin),
        "created_at": _now_iso(),
    }
    data["users"].append(user)
    _write_data(data)
    return deepcopy(user)


def get_matches() -> list[dict[str, Any]]:
    """Return all matches ordered by kickoff date."""
    matches = deepcopy(_read_data()["matches"])
    return sorted(matches, key=lambda match: match.get("utc_date", ""))


def get_match(match_id: int) -> dict[str, Any] | None:
    """Return a match by id, or None when it does not exist."""
    for match in _read_data()["matches"]:
        if int(match["id"]) == int(match_id):
            return deepcopy(match)
    return None


def upsert_match(
    *,
    match_id: int | None = None,
    external_id: str | None = None,
    home_team: str,
    away_team: str,
    utc_date: str,
    status: str,
    home_score: int | None = None,
    away_score: int | None = None,
) -> dict[str, Any]:
    """Create or update a match and return the saved record."""
    data = _read_data()
    payload = {
        "external_id": external_id or "",
        "home_team": home_team.strip(),
        "away_team": away_team.strip(),
        "utc_date": utc_date,
        "status": status,
        "home_score": home_score,
        "away_score": away_score,
    }

    if match_id is None:
        match = {"id": _next_id(data["matches"]), **payload}
        data["matches"].append(match)
    else:
        match = None
        for index, existing in enumerate(data["matches"]):
            if int(existing["id"]) == int(match_id):
                match = {**existing, **payload, "id": int(match_id)}
                data["matches"][index] = match
                break
        if match is None:
            raise ValueError("El partido no existe.")

    _write_data(data)
    return deepcopy(match)


def get_predictions() -> list[dict[str, Any]]:
    """Return all predictions."""
    return deepcopy(_read_data()["predictions"])


def get_prediction(user_id: int, match_id: int) -> dict[str, Any] | None:
    """Return one prediction by user and match, or None when absent."""
    for prediction in _read_data()["predictions"]:
        if int(prediction["user_id"]) == int(user_id) and int(prediction["match_id"]) == int(match_id):
            return deepcopy(prediction)
    return None


def save_prediction(
    *,
    user_id: int,
    match_id: int,
    pred_home: int,
    pred_away: int,
    points: int | None = None,
) -> dict[str, Any]:
    """Create or update a prediction and return the saved record."""
    data = _read_data()
    payload = {
        "user_id": int(user_id),
        "match_id": int(match_id),
        "pred_home": int(pred_home),
        "pred_away": int(pred_away),
        "points": points,
    }

    prediction = None
    for index, existing in enumerate(data["predictions"]):
        if int(existing["user_id"]) == int(user_id) and int(existing["match_id"]) == int(match_id):
            prediction = {**existing, **payload}
            data["predictions"][index] = prediction
            break

    if prediction is None:
        prediction = {"id": _next_id(data["predictions"]), **payload}
        data["predictions"].append(prediction)

    _write_data(data)
    return deepcopy(prediction)


def update_prediction_points(prediction_id: int, points: int | None) -> dict[str, Any]:
    """Update the points assigned to a prediction and return the saved record."""
    data = _read_data()
    for index, prediction in enumerate(data["predictions"]):
        if int(prediction["id"]) == int(prediction_id):
            updated = {**prediction, "points": points}
            data["predictions"][index] = updated
            _write_data(data)
            return deepcopy(updated)
    raise ValueError("La predicción no existe.")


def get_leaderboard() -> list[dict[str, Any]]:
    """Return users with total points, sorted from highest to lowest score."""
    data = _read_data()
    totals = {int(user["id"]): 0 for user in data["users"]}
    for prediction in data["predictions"]:
        totals[int(prediction["user_id"])] = totals.get(int(prediction["user_id"]), 0) + int(prediction.get("points") or 0)

    rows = [
        {
            "user_id": int(user["id"]),
            "username": user["username"],
            "points": totals.get(int(user["id"]), 0),
        }
        for user in data["users"]
    ]
    return sorted(rows, key=lambda row: (-row["points"], row["username"].lower()))


def seed_admin_if_empty(username: str, email: str, password_hash: str) -> dict[str, Any] | None:
    """Create an initial admin when the user table is empty; otherwise return None."""
    data = _read_data()
    if data["users"]:
        return None

    user = {
        "id": 1,
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "is_admin": True,
        "created_at": _now_iso(),
    }
    data["users"].append(user)
    _write_data(data)
    return deepcopy(user)
