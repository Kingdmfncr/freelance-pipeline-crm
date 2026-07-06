"""Donnees demo du pipeline freelance. Aucune donnee reelle."""
import random
from datetime import date, timedelta

import pandas as pd

random.seed(42)

SOURCES = ["LinkedIn inbound", "LinkedIn outbound", "Reseau CHU", "Reseau Ministeres",
           "Malt", "BOAMP / marche public", "Recommandation", "Sovereign Career",
           "Recherche annuaire"]

STATUTS = ["Nouveau", "Contacte", "Call planifie", "Proposition envoyee",
           "Negociation", "Gagne", "Perdu"]

# Probabilite de signature par statut (pipeline pondere)
PROBAS = {"Nouveau": 0.05, "Contacte": 0.10, "Call planifie": 0.25,
          "Proposition envoyee": 0.45, "Negociation": 0.70, "Gagne": 1.0, "Perdu": 0.0}

OFFRES = ["Audit Data Flash", "Sprint Outil 30 jours", "PMO Data mensuel"]
VALEURS = {"Audit Data Flash": 1490, "Sprint Outil 30 jours": 4900, "PMO Data mensuel": 5970}

_ORGS = [
    ("CH Intercommunal Elbeuf", "Sante"), ("Clinique Les Aubes", "Sante"),
    ("Conseil Departemental 76", "Secteur public"), ("Mairie de Sotteville", "Secteur public"),
    ("Metropole Rouen Normandie", "Secteur public"), ("EHPAD Les Jardins", "Sante"),
    ("PME AgroNord", "Industrie"), ("Cabinet RH Talents&Co", "Services"),
    ("ARS Normandie", "Sante"), ("GHT Rouen Coeur de Seine", "Sante"),
    ("Syndicat Mixte Eau 27", "Secteur public"), ("Startup MedFlow", "Sante"),
    ("Federation BTP 76", "Services"), ("Laboratoire BioSeine", "Sante"),
]

_CONTACTS = ["A. Durand", "M. Lefevre", "C. Bernard", "S. Moreau", "J. Petit",
             "L. Roux", "N. Fournier", "E. Girard", "P. Lambert", "V. Mercier",
             "T. Bonnet", "H. Faure", "K. Blanc", "R. Guerin"]


def generate_prospects(n: int = 14) -> pd.DataFrame:
    today = date.today()
    rows = []
    for i in range(n):
        org, secteur = _ORGS[i]
        statut = random.choices(STATUTS, weights=[3, 3, 2, 2, 1, 1, 2])[0]
        offre = random.choice(OFFRES)
        created = today - timedelta(days=random.randint(3, 60))
        last_contact = created + timedelta(days=random.randint(0, 10))
        # Relance J+3 (statuts chauds) ou J+7 (statuts froids)
        delai = 3 if statut in ("Proposition envoyee", "Negociation", "Call planifie") else 7
        relance = last_contact + timedelta(days=delai)
        rows.append({
            "id": i + 1,
            "organisation": org,
            "secteur": secteur,
            "contact": _CONTACTS[i],
            "source": random.choice(SOURCES),
            "offre": offre,
            "valeur_eur": VALEURS[offre],
            "statut": statut,
            "date_creation": created,
            "dernier_contact": last_contact,
            "prochaine_relance": relance,
            "notes": "",
        })
    return pd.DataFrame(rows)


CANAUX = ["Email", "LinkedIn", "Telephone", "Visio", "En personne"]

TACHES_TYPES = {
    "Audit Data Flash": ["Cartographie des flux", "Diagnostic gisements", "Rapport + roadmap", "Restitution"],
    "Sprint Outil 30 jours": ["Cadrage besoin", "Connexion donnees", "Dev outil (demo J+7)",
                              "Formation utilisateurs", "Support post-livraison"],
    "PMO Data mensuel": ["Revue KPIs du mois", "Maintenance outils", "Nouveaux indicateurs", "Reporting direction"],
}


def generate_messages(prospects_df: pd.DataFrame, n_per: int = 3) -> pd.DataFrame:
    rows = []
    msg_id = 1
    for _, p in prospects_df.iterrows():
        n = random.randint(1, n_per)
        d = p["date_creation"]
        for k in range(n):
            d = d + timedelta(days=random.randint(1, 6))
            if d > date.today():
                break
            rows.append({
                "id": msg_id, "prospect_id": p["id"], "organisation": p["organisation"],
                "date": d, "canal": random.choice(CANAUX),
                "resume": random.choice([
                    "Premier contact, presentation de l'offre",
                    "Envoi de la proposition commerciale",
                    "Relance suite a silence",
                    "Point d'avancement projet",
                    "Question technique sur perimetre",
                    "Confirmation de rendez-vous",
                ]),
            })
            msg_id += 1
    return pd.DataFrame(rows)


PROJETS_COLS = ["id", "prospect_id", "organisation", "offre", "tache", "echeance", "statut"]


def generate_projets(prospects_df: pd.DataFrame) -> pd.DataFrame:
    gagnes = prospects_df[prospects_df["statut"] == "Gagne"]
    rows = []
    proj_id = 1
    for _, p in gagnes.iterrows():
        taches = TACHES_TYPES.get(p["offre"], ["Cadrage", "Realisation", "Livraison"])
        debut = p["dernier_contact"]
        for j, t in enumerate(taches):
            statut = random.choices(["A faire", "En cours", "Termine"], weights=[1, 1, 2])[0]
            rows.append({
                "id": proj_id, "prospect_id": p["id"], "organisation": p["organisation"],
                "offre": p["offre"], "tache": t,
                "echeance": debut + timedelta(days=(j + 1) * 6),
                "statut": statut,
            })
            proj_id += 1
    return pd.DataFrame(rows, columns=PROJETS_COLS)
