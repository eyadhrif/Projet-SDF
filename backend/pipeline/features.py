"""PDM-01 — Feature engineering et construction de l'indicateur de santé (Salma).

1. Suppression des capteurs constants (variance quasi nulle sur FD001)
2. Scores de tendance et de monotonie (Coble & Hines) -> sélection des capteurs pronostiques
3. Features temporelles par fenêtre glissante : moyenne, écart-type (RMS centré), pente, kurtosis
4. Indicateur de santé HI ∈ [0,1] par fusion linéaire des capteurs retenus
   (régression vers une cible 1 = neuf -> 0 = défaillant, Wang 2008)
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from .data import SENSORS, SENSOR_INFO

WINDOW = 10
TREND_THRESHOLD = 0.5  # |corrélation avec le temps| minimale pour retenir un capteur


def drop_constant(train: pd.DataFrame, min_unique=10):
    """Capteurs (quasi) constants : moins de 10 valeurs distinctes sur tout le jeu."""
    return [s for s in SENSORS if train[s].nunique() >= min_unique]


def monotonicity(train: pd.DataFrame, sensors):
    """Mon = |#(dx>0) − #(dx<0)| / (n−1), moyenné sur les moteurs (série lissée)."""
    out = {}
    for s in sensors:
        vals = []
        for _, g in train.groupby("unit"):
            x = g[s].rolling(WINDOW, min_periods=1).mean().values
            d = np.diff(x)
            vals.append(abs((d > 0).sum() - (d < 0).sum()) / max(len(d), 1))
        out[s] = float(np.mean(vals))
    return out


def trendability(train: pd.DataFrame, sensors):
    """Corrélation moyenne capteur / temps (signe -> sens de la dérive)."""
    return {s: float(train.groupby("unit").apply(
        lambda g: np.corrcoef(g["cycle"], g[s])[0, 1], include_groups=False).mean()) for s in sensors}


def sensor_ranking(train: pd.DataFrame):
    kept = drop_constant(train)
    mono = monotonicity(train, kept)
    trend = trendability(train, kept)
    rank = sorted(
        [{"sensor": s, "label": SENSOR_INFO[s], "mono": round(mono[s], 4),
          "trend": round(trend[s], 4), "selected": abs(trend[s]) >= TREND_THRESHOLD} for s in kept],
        key=lambda d: -abs(d["trend"]))
    selected = [d["sensor"] for d in rank if d["selected"]]
    dropped = [s for s in SENSORS if s not in kept]
    return rank, selected, dropped


def window_features(df: pd.DataFrame, sensors):
    """Features temporelles par moteur sur une fenêtre glissante."""
    parts = []
    for _, g in df.groupby("unit", sort=False):
        r = g[sensors].rolling(WINDOW, min_periods=1)
        f = pd.DataFrame(index=g.index)
        mean, std = r.mean(), r.std().fillna(0)
        for s in sensors:
            f[f"{s}_mean"] = mean[s]
            f[f"{s}_std"] = std[s]
        # pente locale (moindres carrés sur la fenêtre)
        idx = np.arange(WINDOW) - (WINDOW - 1) / 2
        for s in sensors:
            f[f"{s}_slope"] = g[s].rolling(WINDOW, min_periods=WINDOW).apply(
                lambda v: np.dot(idx, v - v.mean()) / np.dot(idx, idx), raw=True).fillna(0)
        parts.append(f)
    return pd.concat(parts).loc[df.index]


class HealthIndicator:
    """HI = fusion linéaire des capteurs normalisés, cible 1 (début de vie) -> 0 (fin de vie)."""

    def __init__(self, sensors, healthy_frac=0.1, failed_frac=0.1):
        self.sensors = sensors
        self.hf, self.ff = healthy_frac, failed_frac

    def fit(self, train: pd.DataFrame):
        self.scaler = StandardScaler().fit(train[self.sensors])
        life = train.groupby("unit")["cycle"].transform("max")
        frac = train["cycle"] / life
        mask_h, mask_f = frac <= self.hf, frac >= 1 - self.ff
        X = self.scaler.transform(train.loc[mask_h | mask_f, self.sensors])
        y = np.where(mask_h[mask_h | mask_f], 1.0, 0.0)
        self.reg = LinearRegression().fit(X, y)
        return self

    def raw(self, df):
        return self.reg.predict(self.scaler.transform(df[self.sensors]))

    def transform(self, df, smooth=WINDOW):
        hi = pd.Series(self.raw(df), index=df.index)
        return hi.groupby(df["unit"]).transform(
            lambda s: s.rolling(smooth, min_periods=1).mean())

    def weights(self):
        return [{"sensor": s, "w": round(float(w), 4)} for s, w in zip(self.sensors, self.reg.coef_)]
