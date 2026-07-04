"""Landing page for Polla Familiar: login and self-registration."""

from __future__ import annotations

import streamlit as st

from auth import get_current_user, hash_password, login_user, logout_user, verify_password
from storage import create_user, get_user_by_username, get_users, seed_admin_if_empty


st.set_page_config(page_title="Polla Familiar", page_icon="⚽", layout="centered")

if not get_users():
    seed_admin_if_empty("admin", "admin@polla.local", hash_password("admin123"))

st.title("Polla Familiar")
st.caption("Predice marcadores, suma puntos y mira cómo va la familia.")

current_user = get_current_user()
if current_user:
    st.success(f"Sesión activa: {current_user['username']}")
    if current_user.get("is_admin"):
        st.info("Usuario administrador. Puedes cargar partidos desde la página Admin.")
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
        email = st.text_input("Correo")
        password = st.text_input("Contraseña", type="password", key="register_password")
        confirm_password = st.text_input("Confirmar contraseña", type="password")
        submitted = st.form_submit_button("Crear cuenta")

    if submitted:
        if not new_username.strip() or not email.strip() or not password:
            st.error("Completa usuario, correo y contraseña.")
        elif password != confirm_password:
            st.error("Las contraseñas no coinciden.")
        elif len(password) < 6:
            st.error("La contraseña debe tener al menos 6 caracteres.")
        else:
            try:
                user = create_user(
                    username=new_username,
                    email=email,
                    password_hash=hash_password(password),
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                login_user(user)
                st.success("Cuenta creada. Ya estás dentro.")
                st.rerun()

st.divider()
st.caption("Primer acceso admin: usuario `admin`, contraseña `admin123`. Cámbialo o reemplázalo cuando agregues tu capa de base de datos.")
