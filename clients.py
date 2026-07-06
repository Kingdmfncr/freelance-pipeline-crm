"""Clients & Projets — les prospects Gagne deviennent des clients avec un suivi
de mission (taches/echeances). Gestion de projet legere, pas de Gantt complexe."""
from datetime import date

import pandas as pd
import streamlit as st

C_PRIMARY = "#00C896"
C_GOLD    = "#F5C842"
C_DANGER  = "#E85D5D"
C_WARNING = "#F5A623"
C_SURF    = "#14141C"
C_TEXT    = "#F0F0F5"
C_MUTED   = "#6B7280"
C_BORDER  = "#2A2A3E"

STATUT_COLORS = {"A faire": C_MUTED, "En cours": C_WARNING, "Termine": C_PRIMARY}


def render(prospects_df: pd.DataFrame, projets_df: pd.DataFrame, save_projets):
    st.markdown(f"<h2 style='color:{C_TEXT};'>Clients & Projets</h2>", unsafe_allow_html=True)

    clients = prospects_df[prospects_df["statut"] == "Gagne"]
    if clients.empty:
        st.info("Aucun client actif pour le moment — les prospects passent ici une fois au statut 'Gagne'.")
        return

    today = date.today()
    for _, c in clients.iterrows():
        taches = projets_df[projets_df["prospect_id"] == c["id"]]
        total = len(taches)
        faites = len(taches[taches["statut"] == "Termine"])
        pct = int(faites / total * 100) if total else 0
        en_retard = taches[(taches["statut"] != "Termine") & (pd.to_datetime(taches["echeance"]).dt.date < today)]

        with st.expander(f"{c['organisation']} — {c['offre']} ({pct}% complete)"):
            st.markdown(
                f"<div style='background:{C_SURF};border-radius:10px;height:6px;margin-bottom:14px;'>"
                f"<div style='background:{C_PRIMARY};width:{pct}%;height:6px;border-radius:6px;'></div></div>",
                unsafe_allow_html=True)

            if len(en_retard):
                st.markdown(
                    f"<p style='color:{C_DANGER};font-size:0.85rem;'>⚠ {len(en_retard)} tache(s) en retard</p>",
                    unsafe_allow_html=True)

            for idx, t in taches.sort_values("echeance").iterrows():
                sc = STATUT_COLORS.get(t["statut"], C_MUTED)
                cols = st.columns([4, 1.5, 1.5])
                cols[0].markdown(f"<span style='color:{C_TEXT};'>{t['tache']}</span>", unsafe_allow_html=True)
                cols[1].markdown(
                    f"<span style='color:{C_MUTED};font-size:0.82rem;'>echeance {t['echeance']}</span>",
                    unsafe_allow_html=True)
                nouveau = cols[2].selectbox("statut", ["A faire", "En cours", "Termine"],
                                           index=["A faire", "En cours", "Termine"].index(t["statut"]),
                                           key=f"tache_{idx}", label_visibility="collapsed")
                if nouveau != t["statut"]:
                    projets_df.at[idx, "statut"] = nouveau
                    save_projets(projets_df)
                    st.rerun()

    st.markdown(f"<hr style='border-color:{C_BORDER};'>", unsafe_allow_html=True)
    st.download_button("Exporter le suivi projets (CSV)", projets_df.to_csv(index=False).encode("utf-8"),
                       "projets.csv", "text/csv")
