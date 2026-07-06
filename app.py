"""Freelance Pipeline CRM — suivi prospects, relances J+3/J+7, objectif mensuel."""
import os
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.demo_data import generate_prospects, STATUTS, PROBAS, SOURCES, OFFRES, VALEURS

C_PRIMARY  = "#00C896"
C_GOLD     = "#F5C842"
C_DANGER   = "#E85D5D"
C_WARNING  = "#F5A623"
C_SURF     = "#14141C"
C_SURF2    = "#1E1E2E"
C_TEXT     = "#F0F0F5"
C_MUTED    = "#6B7280"
C_BORDER   = "#2A2A3E"

STATUT_COLORS = {
    "Nouveau": C_MUTED, "Contacte": "#5B8DEF", "Call planifie": C_GOLD,
    "Proposition envoyee": C_WARNING, "Negociation": "#B57BFF",
    "Gagne": C_PRIMARY, "Perdu": C_DANGER,
}

CHART_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=C_TEXT, family="Inter, sans-serif"),
    margin=dict(l=20, r=20, t=40, b=20),
)

OBJECTIF_MENSUEL = 6000
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "prospects.csv")
DATE_COLS = ["date_creation", "dernier_contact", "prochaine_relance"]

st.set_page_config(page_title="Freelance Pipeline CRM", page_icon="🎯",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0A0A0F; color: #F0F0F5; }
.stApp { background-color: #0A0A0F; }
section[data-testid="stSidebar"] { background-color: #14141C; border-right: 1px solid #2A2A3E; }
div[data-testid="stMetricValue"] { color: #00C896; font-size: 1.8rem; font-weight: 700; }
.stButton button { background-color: #00C896; color: #0A0A0F; border: none; border-radius: 8px; font-weight: 600; }
.stTabs [aria-selected="true"] { background-color: #1E1E2E; color: #F0F0F5; }
</style>
""", unsafe_allow_html=True)


def load_prospects() -> pd.DataFrame:
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        for c in DATE_COLS:
            df[c] = pd.to_datetime(df[c]).dt.date
        df["notes"] = df["notes"].fillna("")
        return df
    df = generate_prospects()
    df.to_csv(CSV_PATH, index=False)
    return df


def save_prospects(df: pd.DataFrame) -> None:
    df.to_csv(CSV_PATH, index=False)


if "prospects" not in st.session_state:
    st.session_state.prospects = load_prospects()

df = st.session_state.prospects
today = date.today()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='text-align:center;padding:20px 0 8px;'>"
        "<div style='font-size:2rem;'>🎯</div>"
        f"<div style='color:{C_PRIMARY};font-size:1.1rem;font-weight:700;'>Pipeline CRM</div>"
        f"<div style='color:{C_MUTED};font-size:0.72rem;'>Objectif : 6 000 €/mois</div>"
        "</div>", unsafe_allow_html=True)
    st.markdown(f"<hr style='border-color:{C_BORDER};'>", unsafe_allow_html=True)

    page = st.radio("Navigation", ["Dashboard", "Relances du jour", "Prospects",
                                   "Recherche entreprise", "Ajouter un prospect"],
                    label_visibility="collapsed")

    st.markdown(f"<hr style='border-color:{C_BORDER};'>", unsafe_allow_html=True)

    actifs = df[~df["statut"].isin(["Gagne", "Perdu"])]
    pondere = int((actifs["valeur_eur"] * actifs["statut"].map(PROBAS)).sum())
    gagne_mois = int(df[(df["statut"] == "Gagne") &
                        (pd.to_datetime(df["dernier_contact"]).dt.month == today.month)]["valeur_eur"].sum())
    pct = min(100, int(gagne_mois / OBJECTIF_MENSUEL * 100))
    bar_color = C_PRIMARY if pct >= 100 else C_WARNING if pct >= 50 else C_DANGER
    st.markdown(
        f"<div style='background:{C_SURF2};border:1px solid {C_BORDER};border-radius:10px;padding:14px;'>"
        f"<div style='color:{C_MUTED};font-size:0.7rem;text-transform:uppercase;'>Signe ce mois</div>"
        f"<div style='color:{bar_color};font-size:1.6rem;font-weight:800;'>{gagne_mois} € <span style='font-size:0.85rem;color:{C_MUTED};'>/ {OBJECTIF_MENSUEL} €</span></div>"
        f"<div style='background:{C_SURF};border-radius:4px;height:6px;margin-top:6px;'>"
        f"<div style='background:{bar_color};width:{pct}%;height:6px;border-radius:4px;'></div></div>"
        f"<div style='color:{C_MUTED};font-size:0.72rem;margin-top:8px;'>Pipeline pondere : <strong style='color:{C_GOLD};'>{pondere} €</strong></div>"
        f"</div>", unsafe_allow_html=True)

# ── Dashboard ─────────────────────────────────────────────────────────────────
if page == "Dashboard":
    st.markdown(f"<h2 style='color:{C_TEXT};'>Dashboard pipeline</h2>", unsafe_allow_html=True)

    en_retard = actifs[actifs["prochaine_relance"] < today]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Prospects actifs", len(actifs))
    c2.metric("Pipeline pondere", f"{pondere} €")
    c3.metric("Signe ce mois", f"{gagne_mois} €")
    c4.metric("Relances en retard", len(en_retard),
              delta=f"-{len(en_retard)}" if len(en_retard) else "OK", delta_color="inverse")

    col1, col2 = st.columns(2)

    with col1:
        # Funnel par statut
        funnel = [(s, len(df[df["statut"] == s]), int(df[df["statut"] == s]["valeur_eur"].sum()))
                  for s in STATUTS if s != "Perdu"]
        fig = go.Figure(go.Funnel(
            y=[f[0] for f in funnel], x=[f[1] for f in funnel],
            text=[f"{f[2]} €" for f in funnel], textinfo="value+text",
            marker=dict(color=[STATUT_COLORS[f[0]] for f in funnel]),
        ))
        fig.update_layout(title="Funnel de conversion", height=380, **CHART_DEFAULTS)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Valeur par source
        src = actifs.groupby("source")["valeur_eur"].sum().sort_values()
        fig = go.Figure(go.Bar(x=src.values, y=src.index, orientation="h",
                               marker_color=C_PRIMARY))
        fig.update_layout(title="Valeur du pipeline par source (€)", height=380, **CHART_DEFAULTS)
        st.plotly_chart(fig, use_container_width=True)

    # Repartition par offre
    off = df[df["statut"] != "Perdu"].groupby("offre")["valeur_eur"].sum()
    fig = go.Figure(go.Pie(labels=off.index, values=off.values, hole=0.55,
                           marker=dict(colors=[C_PRIMARY, C_GOLD, "#5B8DEF"])))
    fig.update_layout(title="Repartition de la valeur par offre", height=320, **CHART_DEFAULTS)
    st.plotly_chart(fig, use_container_width=True)

# ── Relances du jour ──────────────────────────────────────────────────────────
elif page == "Relances du jour":
    st.markdown(f"<h2 style='color:{C_TEXT};'>Relances du jour</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{C_MUTED};'>Regle : J+3 apres proposition/call, J+7 apres premier contact.</p>",
                unsafe_allow_html=True)

    dues = actifs[actifs["prochaine_relance"] <= today].sort_values("prochaine_relance")
    if dues.empty:
        st.success("Aucune relance due aujourd'hui. Prospection ou production !")
    for idx, r in dues.iterrows():
        retard = (today - r["prochaine_relance"]).days
        color = C_DANGER if retard > 2 else C_WARNING
        cols = st.columns([5, 1])
        with cols[0]:
            st.markdown(
                f"<div style='background:{C_SURF};border-left:4px solid {color};"
                f"border-radius:0 10px 10px 0;padding:14px 18px;margin:6px 0;'>"
                f"<strong style='color:{C_TEXT};'>{r['organisation']}</strong> — {r['contact']} "
                f"<span style='background:{STATUT_COLORS[r['statut']]}22;color:{STATUT_COLORS[r['statut']]};"
                f"padding:2px 10px;border-radius:12px;font-size:0.75rem;'>{r['statut']}</span><br>"
                f"<span style='color:{C_MUTED};font-size:0.85rem;'>{r['offre']} · {r['valeur_eur']} € · "
                f"relance prevue le {r['prochaine_relance']} ({retard} j de retard)</span></div>",
                unsafe_allow_html=True)
        with cols[1]:
            if st.button("Fait ✓", key=f"rel_{idx}"):
                df.at[idx, "dernier_contact"] = today
                delai = 3 if r["statut"] in ("Proposition envoyee", "Negociation", "Call planifie") else 7
                df.at[idx, "prochaine_relance"] = today + timedelta(days=delai)
                save_prospects(df)
                st.rerun()

# ── Prospects (edition) ───────────────────────────────────────────────────────
elif page == "Prospects":
    st.markdown(f"<h2 style='color:{C_TEXT};'>Tous les prospects</h2>", unsafe_allow_html=True)
    edited = st.data_editor(
        df, use_container_width=True, num_rows="dynamic", hide_index=True,
        column_config={
            "statut": st.column_config.SelectboxColumn("statut", options=STATUTS),
            "source": st.column_config.SelectboxColumn("source", options=SOURCES),
            "offre": st.column_config.SelectboxColumn("offre", options=OFFRES),
            "valeur_eur": st.column_config.NumberColumn("valeur (€)", min_value=0, step=100),
        })
    if st.button("Enregistrer les modifications"):
        st.session_state.prospects = edited
        save_prospects(edited)
        st.success("Pipeline enregistre.")
    st.download_button("Exporter CSV", df.to_csv(index=False).encode("utf-8"),
                       "pipeline.csv", "text/csv")

# ── Recherche entreprise ──────────────────────────────────────────────────────
elif page == "Recherche entreprise":
    import research

    def _add_to_pipeline(org, secteur, offre):
        new = {"organisation": org, "secteur": secteur, "contact": "",
               "source": "Recherche annuaire", "offre": offre,
               "valeur_eur": VALEURS.get(offre, 0), "statut": "Nouveau",
               "date_creation": today, "dernier_contact": today,
               "prochaine_relance": today + timedelta(days=7), "notes": ""}
        st.session_state.prospects = pd.concat(
            [st.session_state.prospects, pd.DataFrame([new])], ignore_index=True)
        save_prospects(st.session_state.prospects)

    research.render(_add_to_pipeline)

# ── Ajouter ───────────────────────────────────────────────────────────────────
else:
    st.markdown(f"<h2 style='color:{C_TEXT};'>Ajouter un prospect</h2>", unsafe_allow_html=True)
    with st.form("add"):
        c1, c2 = st.columns(2)
        org = c1.text_input("Organisation *")
        contact = c2.text_input("Contact")
        c3, c4, c5 = st.columns(3)
        source = c3.selectbox("Source", SOURCES)
        offre = c4.selectbox("Offre visee", OFFRES)
        secteur = c5.selectbox("Secteur", ["Sante", "Secteur public", "Industrie", "Services", "Autre"])
        valeur = st.number_input("Valeur estimee (€)", value=VALEURS[OFFRES[0]], step=100)
        notes = st.text_area("Notes", height=80)
        if st.form_submit_button("Ajouter au pipeline") and org:
            new = {"organisation": org, "secteur": secteur, "contact": contact,
                   "source": source, "offre": offre, "valeur_eur": valeur,
                   "statut": "Nouveau", "date_creation": today,
                   "dernier_contact": today, "prochaine_relance": today + timedelta(days=7),
                   "notes": notes}
            st.session_state.prospects = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
            save_prospects(st.session_state.prospects)
            st.success(f"{org} ajoute — relance auto le {today + timedelta(days=7)}.")
