"""API minimaliste en lecture seule pour une integration future (ex: KAMI ou tout
autre systeme). Service independant du Streamlit — ne pas fusionner les deux stacks.
Lance en local avec : uvicorn api:app --port 8000
"""
import os

import pandas as pd
from fastapi import FastAPI, HTTPException

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

app = FastAPI(title="Freelance CRM API", version="0.1.0",
             description="Lecture seule — prospects, clients, projets. "
                         "Aucune authentification pour l'instant : a proteger avant tout usage externe.")


def _load(name: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        raise HTTPException(404, f"{name} introuvable — lancer l'app Streamlit au moins une fois.")
    return pd.read_csv(path).fillna("")


@app.get("/prospects")
def list_prospects():
    return _load("prospects.csv").to_dict(orient="records")


@app.get("/clients")
def list_clients():
    df = _load("prospects.csv")
    return df[df["statut"] == "Gagne"].to_dict(orient="records")


@app.get("/clients/{organisation}/projets")
def client_projets(organisation: str):
    projets = _load("projets.csv") if os.path.exists(os.path.join(DATA_DIR, "projets.csv")) else pd.DataFrame()
    if projets.empty:
        return []
    return projets[projets["organisation"].str.lower() == organisation.lower()].to_dict(orient="records")
