"""Landing page for Polla Familiar: login and self-registration."""

from __future__ import annotations

import streamlit as st

from auth import get_current_user, hash_password, login_user, logout_user, verify_password
from storage import create_user, get_user_by_username, get_users, seed_admin_if_empty, update_user


st.set_page_config(page_title="Polla Familiar", page_icon="⚽", layout="centered")

if not get_users():
    seed_admin_if_empty("adminp0lla", hash_password("p0lla2026"))

st.title("Polla Familiar")
st.caption("Predice marcadores, suma puntos y mira cómo va la familia.")

current_user = get_current_user()
if current_user:
    st.success(f"Sesión activa: {current_user['username']}")

    with st.expander("Cambiar contraseña", expanded=False):
        with st.form("password_form"):
            new_password = st.text_input("Nueva contraseña", type="password")
            confirm_password = st.text_input("Confirmar nueva contraseña", type="password")
            profile_submitted = st.form_submit_button("Guardar contraseña")

        if profile_submitted:
            if not new_password:
                st.error("Ingresa una contraseña.")
            elif new_password != confirm_password:
                st.error("Las contraseñas no coinciden.")
            elif len(new_password) < 6:
                st.error("La contraseña debe tener al menos 6 caracteres.")
            else:
                updated = update_user(
                    user_id=current_user["id"],
                    password_hash=hash_password(new_password),
                )
                login_user(updated)
                st.success("Contraseña actualizada.")
                st.rerun()

    if st.button("Cerrar sesión"):
        logout_user()
        st.rerun()
    st.stop()

tab_login, tab_register = st.tabs(["Ingresar", "Registrarme"])

with tab_login:
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")

    if submitted:
        if not username.strip() or not password:
            st.error("Ingresa usuario y contraseña.")
        else:
            user = get_user_by_username(username)
            if user is None or not verify_password(password, user["password_hash"]):
                st.error("Usuario o contraseña incorrectos.")
            else:
                login_user(user)
                st.success("Ingreso correcto.")
                st.rerun()

with tab_register:
    with st.form("register_form"):
        new_username = st.text_input("Usuario", key="register_username")
        password = st.text_input("Contraseña", type="password", key="register_password")
        confirm_password = st.text_input("Confirmar contraseña", type="password")
        submitted = st.form_submit_button("Crear cuenta")

    if submitted:
        if not new_username.strip() or not password:
            st.error("Completa usuario y contraseña.")
        elif password != confirm_password:
            st.error("Las contraseñas no coinciden.")
        elif len(password) < 6:
            st.error("La contraseña debe tener al menos 6 caracteres.")
        else:
            try:
                user = create_user(
                    username=new_username,
                    password_hash=hash_password(password),
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                login_user(user)
                st.success("Cuenta creada. Ya estás dentro.")
                st.rerun()
