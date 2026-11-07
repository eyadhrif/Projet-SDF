"""SET-02 — Chargement du jeu NASA C-MAPSS FD001 (Salma).

FD001 : 100 moteurs d'entraînement suivis jusqu'à la défaillance (run-to-failure),
100 moteurs de test tronqués avant la défaillance + vrai RUL au dernier cycle.
Une condition opératoire, un mode de défaillance (dégradation HPC).
"""
from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

COLS = ["unit", "cycle", "set1", "set2", "set3"] + [f"s{i}" for i in range(1, 22)]
SENSORS = [f"s{i}" for i in range(1, 22)]

# Description physique des capteurs (Saxena et al., 2008)
SENSOR_INFO = {
    "s1": "T2 — Température entrée fan (°R)", "s2": "T24 — Température sortie LPC (°R)",
    "s3": "T30 — Température sortie HPC (°R)", "s4": "T50 — Température sortie LPT (°R)",
    "s5": "P2 — Pression entrée fan (psia)", "s6": "P15 — Pression bypass (psia)",
    "s7": "P30 — Pression sortie HPC (psia)", "s8": "Nf — Vitesse physique fan (rpm)",
    "s9": "Nc — Vitesse physique core (rpm)", "s10": "epr — Rapport de pression moteur",
    "s11": "Ps30 — Pression statique sortie HPC (psia)", "s12": "phi — Débit carburant / Ps30",
    "s13": "NRf — Vitesse corrigée fan (rpm)", "s14": "NRc — Vitesse corrigée core (rpm)",
    "s15": "BPR — Taux de dilution", "s16": "farB — Rapport carburant/air brûleur",
    "s17": "htBleed — Enthalpie de prélèvement", "s18": "Nf_dmd — Vitesse fan demandée",
    "s19": "PCNfR_dmd — Vitesse fan corrigée demandée", "s20": "W31 — Débit air refroidissement HPT",
    "s21": "W32 — Débit air refroidissement LPT",
}


def _read(name: str) -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / name, sep=r"\s+", header=None)
    df = df.iloc[:, : len(COLS)]
    df.columns = COLS
    return df


def load_fd001():
    """Retourne (train, test, rul_test) avec la colonne RUL calculée."""
    train = _read("train_FD001.txt")
    test = _read("test_FD001.txt")
    rul = pd.read_csv(DATA_DIR / "RUL_FD001.txt", header=None, names=["RUL"])
    rul["unit"] = np.arange(1, len(rul) + 1)

    # RUL d'entraînement : cycles restants jusqu'à la défaillance
    max_c = train.groupby("unit")["cycle"].transform("max")
    train["RUL"] = max_c - train["cycle"]

    # RUL de test : vrai RUL final + cycles restants dans la série tronquée
    last = test.groupby("unit")["cycle"].transform("max")
    test = test.merge(rul, on="unit", how="left", suffixes=("", "_end"))
    test["RUL"] = test["RUL"] + (last - test["cycle"])
    return train, test, rul


def lifetime_table(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    """Table de durées de vie pour l'analyse de fiabilité.

    - Moteurs d'entraînement : défaillance observée (statut = 1)
    - Moteurs de test : encore en service au dernier cycle -> censure à droite (statut = 0)
    """
    tr = train.groupby("unit")["cycle"].max().reset_index()
    tr["status"] = 1
    tr["source"] = "train"
    te = test.groupby("unit")["cycle"].max().reset_index()
    te["status"] = 0
    te["source"] = "test"
    out = pd.concat([tr, te], ignore_index=True).rename(columns={"cycle": "time"})
    return out
