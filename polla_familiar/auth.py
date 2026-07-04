"""Authentication helpers for password hashing and Streamlit session state."""

from __future__ import annotations

from typing import Any

import streamlit as st
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash for a plaintext password."""
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return True when a plaintext password matches a stored bcrypt hash."""
    return pwd_context.verify(password, password_hash)


def login_user(user: dict[str, Any]) -> None:
    """Persist the logged-in user in Streamlit session state."""
    st.session_state["user"] = user
    st.session_state["user_id"] = user["id"]


def logout_user() -> None:
    """Clear the active Streamlit login session."""
    st.session_state.pop("user", None)
    st.session_state.pop("user_id", None)


def get_current_user() -> dict[str, Any] | None:
    """Return the user stored in Streamlit session state, if any."""
    return st.session_state.get("user")


def require_login() -> dict[str, Any] | None:
    """Render a friendly warning and stop the page when there is no login."""
    user = get_current_user()
    if user is None:
        st.warning("Inicia sesión desde la página principal para continuar.")
        st.stop()
    return user


def require_admin() -> dict[str, Any] | None:
    """Render a friendly warning and stop the page when the user is not admin."""
    user = require_login()
    if not user or not user.get("is_admin"):
        st.error("Esta página solo está disponible para administradores.")
        st.stop()
    return user
