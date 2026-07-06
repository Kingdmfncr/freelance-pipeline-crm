"""Recherche entreprise — annuaire officiel (API gratuite recherche-entreprises.api.gouv.fr),
suggestion d'offre selon profil, contacts a cibler, et branchement Sovereign Career."""
from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st

C_PRIMARY = "#00C896"
C_GOLD    = "#F5C842"
C_DANGER  = "#E85D5D"
C_WARNING = "#F5A623"
C_SURF    = "#14141C"
C_SURF2   = "#1E1E2E"
C_TEXT    = "#F0F0F5"
C_MUTED   = "#6B7280"
C_BORDER  = "#2A2A3E"

API_URL = "https://recherche-entreprises.api.gouv.fr/search"

# Tranches effectif INSEE -> libelle
EFFECTIFS = {
    "00": "0 salarie", "01": "1-2", "02": "3-5", "03": "6-9", "11": "10-19",
    "12": "20-49", "21": "50-99", "22": "100-199", "31": "200-249",
    "32": "250-499", "41": "500-999", "42": "1000-1999", "51": "2000-4999",
    "52": "5000-9999", "53": "10000+",
}

# Sections NAF pertinentes -> (secteur lisible, ciblage)
SECTEURS = {
    "86": "Sante", "87": "Medico-social", "88": "Action sociale",
    "84": "Administration publique", "85": "Enseignement",
}


def _secteur(naf: str) -> str:
    if not naf:
        return "Autre"
    return SECTEURS.get(naf[:2], "Prive / Autre")


def _reco(secteur: str, tranche: str) -> dict:
    """Suggestion d'offre + contacts + canal selon secteur et taille."""
    grande = tranche in ("31", "32", "41", "42", "51", "52", "53")
    moyenne = tranche in ("21", "22")

    if secteur in ("Sante", "Medico-social"):
        return {
            "offre": "Sprint Outil 30 jours" if moyenne or grande else "Audit Data Flash",
            "argument": "Suivi qualite / evenements indesirables — demontrer avec Quality Suite UPRAS",
            "contacts": ["Responsable qualite / gestionnaire des risques", "DSI", "Directeur des soins"],
            "canal": "Email professionnel (secteur reglemente) puis LinkedIn",
            "demo": "https://quality-suite-upras.streamlit.app",
        }
    if secteur in ("Administration publique", "Action sociale", "Enseignement"):
        return {
            "offre": "Audit Data Flash" if not grande else "PMO Data mensuel",
            "argument": "Gouvernance des donnees, fiabilisation des reportings reglementaires",
            "contacts": ["DGS / SG", "Directeur de la transformation", "Chef de projet data"],
            "canal": "Email officiel (marches publics : voir BOAMP) — LinkedIn en second",
            "demo": "https://change-onboarding-tracker.streamlit.app",
        }
    return {
        "offre": "Sprint Outil 30 jours" if moyenne or grande else "Audit Data Flash",
        "argument": "Automatiser les reportings Excel manuels, tableaux de bord direction",
        "contacts": ["DG / DAF", "DRH", "Responsable operations"],
        "canal": "LinkedIn d'abord (reactivite PME), email en relance",
        "demo": "https://freelance-pipeline-crm.streamlit.app",
    }


@st.cache_data(ttl=3600, show_spinner=False)
def _search(query: str) -> list:
    r = requests.get(API_URL, params={"q": query, "per_page": 6}, timeout=10)
    r.raise_for_status()
    return r.json().get("results", [])


def render(add_to_pipeline):
    st.markdown(f"<h2 style='color:{C_TEXT};'>Recherche entreprise</h2>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='color:{C_MUTED};'>Annuaire officiel des entreprises francaises (API publique gratuite). "
        f"Tape un nom, un SIREN ou une ville + activite.</p>", unsafe_allow_html=True)

    query = st.text_input("Recherche", placeholder="ex : clinique Rouen, CH Elbeuf, 130025265…")
    if not query or len(query) < 3:
        st.info("Saisis au moins 3 caracteres pour lancer la recherche.")
        return

    try:
        results = _search(query)
    except requests.RequestException as e:
        st.error(f"API annuaire indisponible : {e}")
        return

    if not results:
        st.warning("Aucun resultat. Essaie avec le SIREN ou un nom plus court.")
        return

    for i, r in enumerate(results):
        nom = r.get("nom_complet", "?").title()
        siege = r.get("siege", {}) or {}
        naf = r.get("activite_principale", "") or ""
        secteur = _secteur(naf)
        tranche = r.get("tranche_effectif_salarie") or siege.get("tranche_effectif_salarie") or ""
        effectif = EFFECTIFS.get(tranche, "n.c.")
        ville = siege.get("libelle_commune", "n.c.")
        dirigeants = [
            f"{d.get('prenoms','')} {d.get('nom','')}".strip().title()
            for d in (r.get("dirigeants") or []) if d.get("nom")
        ][:3]
        reco = _reco(secteur, tranche)

        with st.container():
            st.markdown(
                f"<div style='background:{C_SURF};border:1px solid {C_BORDER};border-radius:12px;"
                f"padding:18px;margin:10px 0;'>"
                f"<div style='display:flex;justify-content:space-between;flex-wrap:wrap;'>"
                f"<div><strong style='color:{C_TEXT};font-size:1.05rem;'>{nom}</strong><br>"
                f"<span style='color:{C_MUTED};font-size:0.82rem;'>SIREN {r.get('siren','?')} · {ville} · "
                f"{effectif} salaries · NAF {naf}</span></div>"
                f"<span style='background:{C_PRIMARY}22;color:{C_PRIMARY};padding:3px 12px;height:fit-content;"
                f"border-radius:12px;font-size:0.75rem;font-weight:700;'>{secteur}</span></div>"
                f"<hr style='border-color:{C_BORDER};margin:10px 0;'>"
                f"<div style='color:{C_TEXT};font-size:0.88rem;line-height:1.9;'>"
                f"<strong style='color:{C_GOLD};'>Offre suggeree :</strong> {reco['offre']}<br>"
                f"<strong style='color:{C_GOLD};'>Angle d'attaque :</strong> {reco['argument']}<br>"
                f"<strong style='color:{C_GOLD};'>Contacts a viser :</strong> {', '.join(reco['contacts'])}"
                + (f"<br><strong style='color:{C_GOLD};'>Dirigeants declares :</strong> {', '.join(dirigeants)}" if dirigeants else "")
                + f"<br><strong style='color:{C_GOLD};'>Canal :</strong> {reco['canal']}<br>"
                f"<strong style='color:{C_GOLD};'>Demo a partager :</strong> "
                f"<a href='{reco['demo']}' style='color:{C_PRIMARY};'>{reco['demo']}</a>"
                f"</div></div>",
                unsafe_allow_html=True)

            cols = st.columns([1, 1, 3])
            if cols[0].button("➕ Ajouter au pipeline", key=f"add_{i}"):
                add_to_pipeline(nom, secteur, reco["offre"])
                st.success(f"{nom} ajoute au pipeline — relance J+7 programmee.")
            cols[1].link_button("🔎 LinkedIn",
                                f"https://www.linkedin.com/search/results/companies/?keywords={nom.replace(' ', '%20')}")

    # ── Branchement Sovereign Career ──────────────────────────────────────────
    st.markdown(f"<hr style='border-color:{C_BORDER};'>", unsafe_allow_html=True)
    with st.expander("🔗 Enrichissement Sovereign Career (Radar Sante Entreprise)"):
        sov_url = st.secrets.get("SOVEREIGN_API_URL", "")
        if sov_url:
            st.success(f"Connecte a Sovereign Career : {sov_url}")
        else:
            st.markdown(
                f"<p style='color:{C_MUTED};font-size:0.85rem;'>"
                f"Non connecte. Pour activer l'enrichissement (sante financiere, signaux de recrutement, "
                f"marche cache) : ajouter <code>SOVEREIGN_API_URL</code> et <code>SOVEREIGN_API_KEY</code> "
                f"dans les secrets Streamlit. Endpoint attendu : "
                f"<code>GET /api/company-radar?siren=…</code> — voir SPEC_LANDING_FREELANCE.md §integration.</p>",
                unsafe_allow_html=True)
