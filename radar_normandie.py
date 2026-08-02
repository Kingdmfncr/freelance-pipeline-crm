"""Radar Normandie — vitalite du secteur sante/medico-social par departement.
Bascule sur l'annuaire officiel Sirene (API gratuite recherche-entreprises.api.gouv.fr,
sans cle, deja utilisee dans research.py). Aucun chiffre invente : chaque valeur
affichee vient d'un appel live a l'API au moment du rendu (cache 1h)."""
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

C_PRIMARY = "#00C896"
C_GOLD    = "#F5C842"
C_SURF    = "#FFFFFF"
C_SURF2   = "#EDEDF2"
C_TEXT    = "#1D1D1F"
C_MUTED   = "#6E6E73"
C_BORDER  = "#E8E8ED"

CHART_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=C_TEXT, family="Inter, sans-serif"),
    margin=dict(l=20, r=20, t=40, b=20),
)

API_URL = "https://recherche-entreprises.api.gouv.fr/search"

DEPARTEMENTS = {"14": "Calvados", "27": "Eure", "50": "Manche", "61": "Orne", "76": "Seine-Maritime"}

# Divisions NAF 86 (sante humaine) + 87 (hebergement medico-social) + 88 (action sociale)
NAF_SANTE_MEDICOSOCIAL = [
    "86.10Z", "86.21Z", "86.22A", "86.22B", "86.22C", "86.23Z",
    "86.90A", "86.90B", "86.90C", "86.90D", "86.90E", "86.90F",
    "87.10A", "87.10B", "87.10C", "87.20A", "87.20B", "87.30A", "87.30B",
    "87.90A", "87.90B",
    "88.10A", "88.10B", "88.10C", "88.91A", "88.91B", "88.99A", "88.99B",
]
# EHPAD : echantillon de suivi (26 a 71 etabl. actifs / departement en Normandie,
# assez petit pour etre entierement page en direct sans cle ni cache lourd).
NAF_EHPAD = "87.10A"


@st.cache_data(ttl=3600, show_spinner=False)
def _count(departement: str, naf_codes: str, etat: str = "A") -> int:
    r = requests.get(API_URL, params={
        "departement": departement, "activite_principale": naf_codes,
        "etat_administratif": etat, "per_page": 1,
    }, timeout=10)
    r.raise_for_status()
    return r.json().get("total_results", 0)


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_all(departement: str, naf_code: str, etat: str = "A") -> list:
    """Pagine l'annuaire pour un NAF cible sur un departement (jeu restreint, <100 resultats)."""
    results, page = [], 1
    while True:
        r = requests.get(API_URL, params={
            "departement": departement, "activite_principale": naf_code,
            "etat_administratif": etat, "per_page": 25, "page": page,
        }, timeout=10)
        r.raise_for_status()
        data = r.json()
        results.extend(data.get("results", []))
        if page >= data.get("total_pages", 1):
            break
        page += 1
    return results


def render(add_to_pipeline):
    st.markdown(f"<h2 style='color:{C_TEXT};'>Radar Normandie — Sante & medico-social</h2>",
                unsafe_allow_html=True)
    st.markdown(
        f"<p style='color:{C_MUTED};'>Donnees live, annuaire officiel des entreprises (Sirene / API gratuite "
        f"recherche-entreprises.api.gouv.fr). Aucun chiffre invente : chaque valeur est interrogee en direct "
        f"(cache 1h).</p>", unsafe_allow_html=True)

    try:
        with st.spinner("Interrogation de l'annuaire officiel..."):
            poids = {dep: _count(dep, ",".join(NAF_SANTE_MEDICOSOCIAL)) for dep in DEPARTEMENTS}
            ehpad_lists = {dep: _fetch_all(dep, NAF_EHPAD) for dep in DEPARTEMENTS}
    except requests.RequestException as e:
        st.error(f"API annuaire indisponible : {e}")
        return

    today = date.today()
    seuil_12m = today - timedelta(days=365)

    lignes = []
    for dep, nom in DEPARTEMENTS.items():
        etabs = ehpad_lists[dep]
        total_ehpad = len(etabs)
        recents = [e for e in etabs if e.get("date_creation")
                   and pd.to_datetime(e["date_creation"]).date() >= seuil_12m]
        taux = (len(recents) / total_ehpad * 100) if total_ehpad else 0
        lignes.append({
            "departement": f"{dep} — {nom}", "poids_sante": poids[dep],
            "ehpad_actifs": total_ehpad, "ehpad_recents_12m": len(recents),
            "taux_renouvellement": round(taux, 1),
        })
    radar_df = pd.DataFrame(lignes)

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Bar(x=radar_df["departement"], y=radar_df["poids_sante"], marker_color=C_PRIMARY))
        fig.update_layout(title="Poids du secteur sante/medico-social (etabl. actifs)",
                           height=360, **CHART_DEFAULTS)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = go.Figure(go.Bar(x=radar_df["departement"], y=radar_df["taux_renouvellement"], marker_color=C_GOLD))
        fig.update_layout(title="Taux de renouvellement EHPAD (% ouverts depuis 12 mois)",
                           height=360, **CHART_DEFAULTS)
        st.plotly_chart(fig, use_container_width=True)

    # Anomalie / angle de prospection
    top = radar_df.loc[radar_df["taux_renouvellement"].idxmax()]
    moyenne = radar_df["taux_renouvellement"].mean()
    if top["taux_renouvellement"] > 0:
        dep_nom = top["departement"].split(" — ")[1]
        st.markdown(
            f"<div style='background:{C_SURF2};border-left:4px solid {C_GOLD};border-radius:0 10px 10px 0;"
            f"padding:14px 18px;margin:14px 0;'>"
            f"<strong style='color:{C_TEXT};'>Anomalie detectee :</strong> "
            f"<span style='color:{C_MUTED};'>{top['departement']} affiche un taux de renouvellement EHPAD de "
            f"{top['taux_renouvellement']}% (moyenne Normandie : {moyenne:.1f}%) — "
            f"{top['ehpad_recents_12m']} structure(s) ouverte(s) sur les 12 derniers mois.<br>"
            f"Angle d'approche : « J'ai analyse les ouvertures d'EHPAD en {dep_nom}, "
            f"voici ce que ca signifie pour votre suivi qualite. »</span></div>",
            unsafe_allow_html=True)

    st.dataframe(radar_df, use_container_width=True, hide_index=True)

    # Drill-down par departement
    st.markdown(f"<hr style='border-color:{C_BORDER};'>", unsafe_allow_html=True)
    dep_choice = st.selectbox("Explorer un departement", list(DEPARTEMENTS.keys()),
                              format_func=lambda d: f"{d} — {DEPARTEMENTS[d]}")
    etabs = sorted(ehpad_lists[dep_choice], key=lambda e: e.get("date_creation") or "", reverse=True)
    if not etabs:
        st.info("Aucun EHPAD actif trouve pour ce departement.")
    for i, e in enumerate(etabs[:15]):
        nom = (e.get("nom_complet") or "?").title()
        ville = (e.get("siege") or {}).get("libelle_commune", "n.c.")
        creation = e.get("date_creation", "n.c.")
        recent = creation != "n.c." and pd.to_datetime(creation).date() >= seuil_12m
        badge = (f"<span style='background:{C_GOLD}22;color:{C_GOLD};padding:2px 10px;border-radius:12px;"
                 f"font-size:0.72rem;font-weight:700;'>Ouvert &lt; 12 mois</span>") if recent else ""
        cols = st.columns([5, 1])
        with cols[0]:
            st.markdown(
                f"<div style='background:{C_SURF};border:1px solid {C_BORDER};border-radius:10px;"
                f"padding:12px 16px;margin:6px 0;'>"
                f"<strong style='color:{C_TEXT};'>{nom}</strong> — {ville} {badge}<br>"
                f"<span style='color:{C_MUTED};font-size:0.82rem;'>SIREN {e.get('siren', '?')} · "
                f"ouvert le {creation}</span></div>", unsafe_allow_html=True)
        with cols[1]:
            if st.button("➕ Pipeline", key=f"radar_add_{dep_choice}_{i}"):
                add_to_pipeline(nom, "Sante", "Audit Data Flash")
                st.success(f"{nom} ajoute au pipeline — relance J+7 programmee.")
