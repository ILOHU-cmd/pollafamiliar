"""Prediction history page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from auth import require_login
from storage import get_matches, get_predictions, get_users


st.set_page_config(page_title="Historial", page_icon="📋", layout="wide")
require_login()

st.title("Historial de predicciones")

users_by_id = {user["id"]: user for user in get_users()}
matches_by_id = {match["id"]: match for match in get_matches()}
rows = []

for prediction in get_predictions():
    match = matches_by_id.get(prediction["match_id"])
    user = users_by_id.get(prediction["user_id"])
    if not match or not user:
        continue

    actual_score = "-"
    if match.get("home_score") is not None and match.get("away_score") is not None:
        actual_score = f"{match['home_score']} - {match['away_score']}"

    rows.append(
        {
            "Partido": f"{match['home_team']} vs {match['away_team']}",
            "Fecha UTC": match.get("utc_date", ""),
            "Estado": match.get("status", ""),
            "Usuario": user["username"],
            "Eleccion": f"{prediction['pred_home']} - {prediction['pred_away']}",
            "Marcador": actual_score,
            "Puntos": prediction.get("points"),
        }
    )

if not rows:
    st.info("Todavia no hay predicciones guardadas.")
    st.stop()

df = pd.DataFrame(rows).sort_values(["Fecha UTC", "Partido", "Usuario"])
st.dataframe(df, use_container_width=True, hide_index=True)
