"""Donnees demo du pipeline freelance. Aucune donnee reelle."""
import random
from datetime import date, timedelta

import pandas as pd

random.seed(42)

SOURCES = ["LinkedIn inbound", "LinkedIn outbound", "Reseau CHU", "Reseau Ministeres",
           "Malt", "BOAMP / marche public", "Recommandation", "Sovereign Career"]

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
