"""Admin page for manual match management and point recalculation."""

from __future__ import annotations

from datetime import datetime, time, timezone

import streamlit as st

from auth import require_admin
from scoring import calculate_points
from storage import get_matches, get_predictions, update_prediction_points, upsert_match


st.set_page_config(page_title="Admin", page_icon="⚙️", layout="wide")
require_admin()

st.title("Admin")

matches = get_matches()
match_options = {"Crear partido nuevo": None}
match_options.update({f"{match['id']} - {match['home_team']} vs {match['away_team']}": match["id"] for match in matches})

selected_label = st.selectbox("Partido", list(match_options.keys()))
selected_id = match_options[selected_label]
selected_match = next((match for match in matches if match["id"] == selected_id), None)

default_dt = datetime.now(timezone.utc)
if selected_match:
    default_dt = datetime.fromisoformat(selected_match["utc_date"])
    if default_dt.tzinfo is None:
        default_dt = default_dt.replace(tzinfo=timezone.utc)

with st.form("match_form"):
    home_team = st.text_input("Equipo local", value=selected_match["home_team"] if selected_match else "")
    away_team = st.text_input("Equipo visitante", value=selected_match["away_team"] if selected_match else "")
    date_value = st.date_input("Fecha de inicio", value=default_dt.date())
    time_value = st.time_input("Hora UTC de inicio", value=time(default_dt.hour, default_dt.minute))
    status = st.selectbox(
        "Estado",
        ["SCHEDULED", "LIVE", "FINISHED"],
        index=["SCHEDULED", "LIVE", "FINISHED"].index(selected_match["status"]) if selected_match else 0,
    )
    has_score = st.checkbox(
        "Cargar marcador final",
        value=bool(selected_match and selected_match.get("home_score") is not None and selected_match.get("away_score") is not None),
    )

    col_home, col_away = st.columns(2)
    with col_home:
        home_score = st.number_input(
            "Goles local",
            min_value=0,
            step=1,
            value=int(selected_match["home_score"]) if selected_match and selected_match.get("home_score") is not None else 0,
            disabled=not has_score,
        )
    with col_away:
        away_score = st.number_input(
            "Goles visitante",
            min_value=0,
            step=1,
            value=int(selected_match["away_score"]) if selected_match and selected_match.get("away_score") is not None else 0,
            disabled=not has_score,
        )

    submitted = st.form_submit_button("Guardar partido")

if submitted:
    if not home_team.strip() or not away_team.strip():
        st.error("Completa los nombres de ambos equipos.")
    else:
        kickoff = datetime.combine(date_value, time_value, tzinfo=timezone.utc)
        saved = upsert_match(
            match_id=selected_id,
            external_id=selected_match.get("external_id") if selected_match else None,
            home_team=home_team,
            away_team=away_team,
            utc_date=kickoff.isoformat(),
            status=status,
            home_score=int(home_score) if has_score else None,
            away_score=int(away_score) if has_score else None,
        )
        st.success(f"Partido guardado: {saved['home_team']} vs {saved['away_team']}.")
        st.rerun()

st.divider()

if st.button("Recalcular puntos pendientes"):
    matches_by_id = {match["id"]: match for match in get_matches()}
    updated = 0
    skipped = 0

    for prediction in get_predictions():
        if prediction.get("points") is not None:
            skipped += 1
            continue

        match = matches_by_id.get(prediction["match_id"])
        if not match or match.get("home_score") is None or match.get("away_score") is None:
            skipped += 1
            continue

        points = calculate_points(
            int(prediction["pred_home"]),
            int(prediction["pred_away"]),
            int(match["home_score"]),
            int(match["away_score"]),
        )
        update_prediction_points(prediction["id"], points)
        updated += 1

    st.success(f"Puntos recalculados para {updated} predicciones. Omitidas: {skipped}.")

st.subheader("Partidos cargados")
if matches:
    st.dataframe(matches, use_container_width=True)
else:
    st.info("No hay partidos cargados todavía.")
