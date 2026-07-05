"""Admin page for users, matches, predictions, and point recalculation."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

import pandas as pd
import streamlit as st

from auth import hash_password, login_user, require_admin
from storage import (
    create_user,
    delete_match,
    delete_user,
    get_matches,
    get_prediction,
    get_predictions,
    get_users,
    recalculate_all_points,
    save_prediction,
    update_user,
    upsert_match,
)


st.set_page_config(page_title="Admin", page_icon="⚙️", layout="wide")
admin_user = require_admin()

st.title("Admin")

tab_matches, tab_users, tab_predictions = st.tabs(["Partidos", "Usuarios", "Predicciones y puntos"])

with tab_matches:
    matches = get_matches()
    match_options = {"Crear partido nuevo": None}
    match_options.update({f"{match['id']} - {match['home_team']} vs {match['away_team']}": match["id"] for match in matches})

    selected_label = st.selectbox("Partido", list(match_options.keys()))
    selected_id = match_options[selected_label]
    selected_match = next((match for match in matches if match["id"] == selected_id), None)

    default_dt = datetime.now(timezone.utc) + timedelta(hours=2)
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
            "Cargar marcador",
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

        existing_pred = get_prediction(admin_user["id"], selected_id) if selected_id else None
        can_predict = status != "FINISHED"
        st.subheader("Tu prediccion")
        pred_col_home, pred_col_away = st.columns(2)
        with pred_col_home:
            pred_home = st.number_input(
                "Pronostico local",
                min_value=0,
                step=1,
                value=int(existing_pred["pred_home"]) if existing_pred else 0,
                disabled=not can_predict,
                key="admin_pred_home",
            )
        with pred_col_away:
            pred_away = st.number_input(
                "Pronostico visitante",
                min_value=0,
                step=1,
                value=int(existing_pred["pred_away"]) if existing_pred else 0,
                disabled=not can_predict,
                key="admin_pred_away",
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
            if can_predict:
                save_prediction(
                    user_id=admin_user["id"],
                    match_id=saved["id"],
                    pred_home=int(pred_home),
                    pred_away=int(pred_away),
                )
            st.success("Partido guardado y puntos recalculados.")
            st.rerun()

    if selected_match:
        with st.expander("Eliminar partido", expanded=False):
            st.warning("Eliminar un partido tambien elimina sus predicciones asociadas.")
            confirm_delete = st.checkbox(
                f"Confirmo que quiero eliminar {selected_match['home_team']} vs {selected_match['away_team']}",
                key=f"confirm_delete_{selected_match['id']}",
            )
            if st.button("Eliminar partido", disabled=not confirm_delete, type="primary"):
                try:
                    delete_match(selected_match["id"])
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    st.success("Partido eliminado.")
                    st.rerun()

    st.subheader("Partidos cargados")
    if matches:
        st.dataframe(matches, use_container_width=True)
    else:
        st.info("No hay partidos cargados todavia.")

with tab_users:
    users = get_users()

    st.subheader("Crear usuario")
    with st.form("create_user_form"):
        new_username = st.text_input("Usuario nuevo")
        new_password = st.text_input("Contrasena", type="password")
        new_is_admin = st.checkbox("Administrador")
        create_submitted = st.form_submit_button("Crear usuario")

    if create_submitted:
        if not new_username.strip() or not new_password:
            st.error("Completa usuario y contrasena.")
        elif len(new_password) < 6:
            st.error("La contrasena debe tener al menos 6 caracteres.")
        else:
            try:
                create_user(new_username, hash_password(new_password), is_admin=new_is_admin)
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success("Usuario creado.")
                st.rerun()

    st.subheader("Modificar usuarios")
    if not users:
        st.info("No hay usuarios registrados.")
    for user in users:
        with st.expander(f"{user['username']} {'(admin)' if user.get('is_admin') else ''}", expanded=False):
            with st.form(f"user_form_{user['id']}"):
                username = st.text_input("Usuario", value=user["username"], key=f"username_{user['id']}")
                password = st.text_input("Nueva contrasena", type="password", key=f"password_{user['id']}")
                is_admin = st.checkbox("Administrador", value=bool(user.get("is_admin")), key=f"is_admin_{user['id']}")
                save_user = st.form_submit_button("Guardar cambios")

            if save_user:
                if password and len(password) < 6:
                    st.error("La contrasena debe tener al menos 6 caracteres.")
                else:
                    try:
                        updated = update_user(
                            user_id=user["id"],
                            username=username,
                            password_hash=hash_password(password) if password else None,
                            is_admin=is_admin,
                        )
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        if int(user["id"]) == int(admin_user["id"]):
                            login_user(updated)
                        st.success("Usuario actualizado.")
                        st.rerun()

            confirm_delete_user = st.checkbox(
                "Confirmo que quiero eliminar este usuario y sus predicciones",
                key=f"delete_user_confirm_{user['id']}",
            )
            if st.button("Eliminar usuario", disabled=not confirm_delete_user, key=f"delete_user_{user['id']}"):
                try:
                    delete_user(user["id"])
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    st.success("Usuario eliminado.")
                    st.rerun()

with tab_predictions:
    if st.button("Recalcular todos los puntos"):
        result = recalculate_all_points()
        st.success(
            f"Predicciones revisadas: {result['updated']}. "
            f"Sin marcador final: {result['without_score']}."
        )

    users_by_id = {user["id"]: user for user in get_users()}
    matches_by_id = {match["id"]: match for match in get_matches()}
    rows = []
    for prediction in get_predictions():
        match = matches_by_id.get(prediction["match_id"])
        user = users_by_id.get(prediction["user_id"])
        if not match or not user:
            continue
        actual = "-"
        if match.get("home_score") is not None and match.get("away_score") is not None:
            actual = f"{match['home_score']} - {match['away_score']}"
        rows.append(
            {
                "Partido": f"{match['home_team']} vs {match['away_team']}",
                "Fecha UTC": match.get("utc_date", ""),
                "Estado": match.get("status", ""),
                "Usuario": user["username"],
                "Eleccion": f"{prediction['pred_home']} - {prediction['pred_away']}",
                "Marcador": actual,
                "Puntos": prediction.get("points"),
            }
        )

    st.subheader("Historial de predicciones")
    if rows:
        df = pd.DataFrame(rows).sort_values(["Fecha UTC", "Partido", "Usuario"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Todavia no hay predicciones guardadas.")
