"""Messagerie — journal des communications par prospect/client. Pas d'envoi reel,
journal de suivi (canal, resume, prochaine action)."""
from datetime import date

import pandas as pd
import streamlit as st

from data.demo_data import CANAUX

C_PRIMARY = "#00C896"
C_GOLD    = "#F5C842"
C_SURF    = "#FFFFFF"
C_TEXT    = "#1D1D1F"
C_MUTED   = "#6E6E73"
C_BORDER  = "#E8E8ED"

CANAL_ICONS = {"Email": "✉️", "LinkedIn": "💼", "Telephone": "📞", "Visio": "🎥", "En personne": "🤝"}


def render(prospects_df: pd.DataFrame, messages_df: pd.DataFrame, save_messages):
    st.markdown(f"<h2 style='color:{C_TEXT};'>Messagerie — journal des echanges</h2>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='color:{C_MUTED};'>Un fil de suivi par organisation : ce qui a ete dit, sur quel canal, "
        f"et quand. Pas d'envoi automatique — un journal fiable pour ne jamais relancer a l'aveugle.</p>",
        unsafe_allow_html=True)

    orgs = sorted(prospects_df["organisation"].unique())
    choix = st.selectbox("Organisation", orgs)
    pid = int(prospects_df[prospects_df["organisation"] == choix]["id"].iloc[0])

    with st.form("new_msg", clear_on_submit=True):
        c1, c2 = st.columns([1, 3])
        canal = c1.selectbox("Canal", CANAUX)
        resume = c2.text_input("Resume de l'echange")
        if st.form_submit_button("Ajouter au journal") and resume:
            new_id = int(messages_df["id"].max()) + 1 if len(messages_df) else 1
            new = {"id": new_id, "prospect_id": pid, "organisation": choix,
                   "date": date.today(), "canal": canal, "resume": resume}
            updated = pd.concat([messages_df, pd.DataFrame([new])], ignore_index=True)
            save_messages(updated)
            st.rerun()

    st.markdown(f"<hr style='border-color:{C_BORDER};'>", unsafe_allow_html=True)

    fil = messages_df[messages_df["prospect_id"] == pid].sort_values("date", ascending=False)
    if fil.empty:
        st.info("Aucun echange enregistre pour cette organisation.")
    for _, m in fil.iterrows():
        icon = CANAL_ICONS.get(m["canal"], "•")
        st.markdown(
            f"<div style='background:{C_SURF};border-left:3px solid {C_PRIMARY};border-radius:0 10px 10px 0;"
            f"padding:12px 16px;margin:6px 0;'>"
            f"<span style='color:{C_MUTED};font-size:0.78rem;'>{m['date']} · {icon} {m['canal']}</span><br>"
            f"<span style='color:{C_TEXT};'>{m['resume']}</span></div>",
            unsafe_allow_html=True)
