"""Prediction entry page."""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from auth import require_login
from storage import get_matches, get_prediction, save_prediction


st.set_page_config(page_title="Predicciones", page_icon="📝", layout="wide")
user = require_login()

st.title("Predicciones")

matches = [match for match in get_matches() if match.get("status") != "FINISHED"]
if not matches:
    st.info("Todavía no hay partidos abiertos para predecir.")
    st.stop()

now = datetime.now(timezone.utc)

for match in matches:
    kickoff = datetime.fromisoformat(match["utc_date"])
    if kickoff.tzinfo is None:
        kickoff = kickoff.replace(tzinfo=timezone.utc)

    prediction = get_prediction(user["id"], match["id"])
    locked = now >= kickoff

    with st.container(border=True):
        st.subheader(f"{match['home_team']} vs {match['away_team']}")
        st.caption(f"Inicio UTC: {kickoff.strftime('%Y-%m-%d %H:%M')} | Estado: {match['status']}")

        col_home, col_away, col_action = st.columns([1, 1, 1])
        with col_home:
            pred_home = st.number_input(
                "Goles local",
                min_value=0,
                step=1,
                value=int(prediction["pred_home"]) if prediction else 0,
                disabled=locked,
                key=f"home_{match['id']}",
            )
        with col_away:
            pred_away = st.number_input(
                "Goles visitante",
                min_value=0,
                step=1,
                value=int(prediction["pred_away"]) if prediction else 0,
                disabled=locked,
                key=f"away_{match['id']}",
            )
        with col_action:
            st.write("")
            st.write("")
            if locked:
                st.warning("Edición bloqueada: el partido ya empezó.")
            elif st.button("Guardar", key=f"save_{match['id']}"):
                save_prediction(
                    user_id=user["id"],
                    match_id=match["id"],
                    pred_home=int(pred_home),
                    pred_away=int(pred_away),
                )
                st.success("Predicción guardada.")
                st.rerun()

        if prediction:
            st.caption(f"Tu predicción actual: {prediction['pred_home']} - {prediction['pred_away']}")
