"""Leaderboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from auth import require_login
from storage import get_leaderboard


st.set_page_config(page_title="Tabla de posiciones", page_icon="🏆", layout="wide")
require_login()

st.title("Tabla de posiciones")

leaderboard = get_leaderboard()
if not leaderboard:
    st.info("Aún no hay usuarios registrados.")
    st.stop()

df = pd.DataFrame(leaderboard)
df.index = range(1, len(df) + 1)

st.dataframe(
    df.rename(columns={"username": "Usuario", "points": "Puntos"})[["Usuario", "Puntos"]],
    use_container_width=True,
)

chart_df = df.set_index("username")[["points"]].rename(columns={"points": "Puntos"})
st.bar_chart(chart_df)
