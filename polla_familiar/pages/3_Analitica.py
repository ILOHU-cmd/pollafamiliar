"""Simple analytics page for prediction accuracy."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from auth import require_login
from scoring import calculate_points, match_outcome
from storage import get_matches, get_predictions, get_users


st.set_page_config(page_title="Analítica", page_icon="📊", layout="wide")
require_login()

st.title("Analítica")

users = {user["id"]: user for user in get_users()}
matches = {match["id"]: match for match in get_matches()}
rows = []

for prediction in get_predictions():
    match = matches.get(prediction["match_id"])
    user = users.get(prediction["user_id"])
    if not match or not user or match.get("home_score") is None or match.get("away_score") is None:
        continue

    actual_home = int(match["home_score"])
    actual_away = int(match["away_score"])
    pred_home = int(prediction["pred_home"])
    pred_away = int(prediction["pred_away"])
    points = calculate_points(pred_home, pred_away, actual_home, actual_away)

    rows.append(
        {
            "Usuario": user["username"],
            "Marcador exacto": points == 3,
            "Resultado acertado": match_outcome(pred_home, pred_away) == match_outcome(actual_home, actual_away),
        }
    )

if not rows:
    st.info("No hay predicciones con partidos finalizados para analizar todavía.")
    st.stop()

df = pd.DataFrame(rows)
summary = (
    df.groupby("Usuario", as_index=False)
    .agg(
        Predicciones=("Usuario", "count"),
        Exactos=("Marcador exacto", "mean"),
        Resultado=("Resultado acertado", "mean"),
    )
)
summary["% marcadores exactos"] = (summary["Exactos"] * 100).round(1)
summary["% aciertos de resultado"] = (summary["Resultado"] * 100).round(1)

st.dataframe(
    summary[["Usuario", "Predicciones", "% marcadores exactos", "% aciertos de resultado"]],
    use_container_width=True,
)
