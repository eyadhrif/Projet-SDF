"""RUL-02 — Modèle LSTM pour l'estimation du RUL (Salma).

- Entrées : 12 capteurs retenus (PDM-01), normalisés min-max sur l'entraînement
- Fenêtres glissantes de 30 cycles -> RUL au dernier cycle de la fenêtre
- Cible linéaire par morceaux plafonnée à 125 cycles (phase saine sans dégradation visible)
- LSTM 2 couches (64 unités) + dropout, Adam, arrêt précoce sur 15 moteurs de validation
"""
import numpy as np
import torch
import torch.nn as nn

SEQ = 30
RUL_CAP = 125
torch.manual_seed(0)
np.random.seed(0)


class LSTMRegressor(nn.Module):
    def __init__(self, n_feat, hidden=64, layers=2, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(n_feat, hidden, layers, batch_first=True, dropout=dropout)
        self.head = nn.Sequential(nn.Linear(hidden, 32), nn.ReLU(), nn.Dropout(dropout), nn.Linear(32, 1))

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.head(out[:, -1]).squeeze(-1)


class LSTMRUL:
    def __init__(self, sensors):
        self.sensors = sensors

    # ---------------- préparation
    def _norm(self, df):
        return ((df[self.sensors] - self.lo) / (self.hi - self.lo + 1e-9)).values.astype(np.float32)

    def _windows(self, X, y=None):
        """Toutes les fenêtres d'un moteur (complétées au début si série courte)."""
        if len(X) < SEQ:
            X = np.vstack([np.repeat(X[:1], SEQ - len(X), 0), X])
            if y is not None:
                y = np.concatenate([np.repeat(y[:1], SEQ - len(y)), y])
        idx = np.arange(SEQ)[None, :] + np.arange(len(X) - SEQ + 1)[:, None]
        return X[idx], (None if y is None else y[SEQ - 1:])

    def _build(self, df, units):
        Xs, ys = [], []
        for u in units:
            g = df[df.unit == u]
            X, y = self._windows(self._norm(g), np.minimum(g.RUL.values, RUL_CAP).astype(np.float32))
            Xs.append(X), ys.append(y)
        return torch.tensor(np.concatenate(Xs)), torch.tensor(np.concatenate(ys))

    # ---------------- apprentissage
    def fit(self, train, epochs=60, patience=8, batch=256, lr=1e-3, log=print):
        self.lo, self.hi = train[self.sensors].min(), train[self.sensors].max()
        units = train.unit.unique()
        rng = np.random.default_rng(0)
        val_u = rng.choice(units, 15, replace=False)
        tr_u = np.setdiff1d(units, val_u)
        Xtr, ytr = self._build(train, tr_u)
        Xva, yva = self._build(train, val_u)

        self.model = LSTMRegressor(len(self.sensors))
        opt = torch.optim.Adam(self.model.parameters(), lr=lr)
        sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=3)
        loss_fn = nn.MSELoss()
        best, best_state, wait, self.history = 1e9, None, 0, []
        for ep in range(epochs):
            self.model.train()
            perm = torch.randperm(len(Xtr))
            tot = 0.0
            for i in range(0, len(perm), batch):
                b = perm[i:i + batch]
                opt.zero_grad()
                loss = loss_fn(self.model(Xtr[b]), ytr[b])
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                opt.step()
                tot += loss.item() * len(b)
            self.model.eval()
            with torch.no_grad():
                vl = loss_fn(self.model(Xva), yva).item()
            sched.step(vl)
            tr_rmse, va_rmse = (tot / len(Xtr)) ** .5, vl ** .5
            self.history.append({"epoch": ep + 1, "train_rmse": round(tr_rmse, 3), "val_rmse": round(va_rmse, 3)})
            log(f"  époque {ep+1:02d}  RMSE train {tr_rmse:6.2f}  val {va_rmse:6.2f}")
            if vl < best - 1e-3:
                best, wait = vl, 0
                best_state = {k: v.clone() for k, v in self.model.state_dict().items()}
            else:
                wait += 1
                if wait >= patience:
                    log(f"  arrêt précoce à l'époque {ep+1}")
                    break
        self.model.load_state_dict(best_state)
        self.best_val_rmse = best ** .5
        return self

    # ---------------- prédiction
    def predict_unit(self, g):
        """RUL prédit à chaque cycle d'un moteur (à partir de la 1re fenêtre complète)."""
        X, _ = self._windows(self._norm(g))
        self.model.eval()
        with torch.no_grad():
            p = self.model(torch.tensor(X)).numpy()
        cycles = g.cycle.values[-len(p):]
        return cycles, np.clip(p, 0, None)

    def save(self, path):
        torch.save({"state": self.model.state_dict(), "sensors": self.sensors,
                    "lo": self.lo.to_dict(), "hi": self.hi.to_dict(),
                    "history": getattr(self, "history", []),
                    "best_val_rmse": getattr(self, "best_val_rmse", None)}, path)

    @classmethod
    def load(cls, path):
        """Recharge un modèle sauvegardé (poids, normalisation, historique d'apprentissage).

        Les prédictions sont identiques à celles du modèle d'origine : c'est la référence
        des résultats publiés, car le réentraînement varie d'une machine à l'autre (D4).
        """
        import pandas as pd
        ck = torch.load(path, weights_only=False)
        m = cls(ck["sensors"])
        m.lo, m.hi = pd.Series(ck["lo"]), pd.Series(ck["hi"])
        m.model = LSTMRegressor(len(ck["sensors"]))
        m.model.load_state_dict(ck["state"])
        m.model.eval()
        m.history = ck.get("history", [])
        m.best_val_rmse = ck.get("best_val_rmse")
        return m
