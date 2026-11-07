"""RUL-01 — Modèle de dégradation : projection du HI jusqu'au seuil de défaillance (Eya).

Modèle : HI(t) = w0 + w1·τ + w2·τ² + ε,  τ = t/100,  ε ~ N(0, σ²)
- Apprentissage « flotte » : un ajustement MCO par moteur d'entraînement -> loi a priori
  gaussienne des coefficients  w ~ N(m0, S0)  (moyenne et covariance de la flotte)
- Seuil de défaillance : valeur moyenne du HI ajusté au cycle de défaillance
- Pour un moteur en service : mise à jour bayésienne (a posteriori conjugué) avec ses
  propres mesures, puis tirage de 1000 trajectoires -> 1er passage sous le seuil
  -> distribution du RUL (médiane + intervalle 10–90 %), seuil tiré dans N(seuil, σ_seuil²)
Approche équivalente à l'« exponentialDegradationModel » de la PdM Toolbox MATLAB,
avec une base polynomiale.
"""
import numpy as np

HORIZON = 400
N_SAMPLES = 1000
DEG = 2


def _phi(t):
    tau = np.asarray(t, float) / 100.0
    return np.vander(tau, DEG + 1, increasing=True)


class DegradationRUL:
    def fit(self, units):
        """units : liste de tableaux (cycles, hi_brut) pour les moteurs d'entraînement."""
        W, res, thr = [], [], []
        for t, h in units:
            P = _phi(t)
            w, *_ = np.linalg.lstsq(P, h, rcond=None)
            W.append(w)
            res.append(h - P @ w)
            thr.append(float((_phi([t[-1]]) @ w)[0]))
        W = np.array(W)
        self.m0 = W.mean(0)
        self.S0 = np.cov(W.T) + 1e-6 * np.eye(DEG + 1)
        self.S0inv = np.linalg.inv(self.S0)
        self.sigma2 = float(np.var(np.concatenate(res)))
        self.threshold = float(np.mean(thr))
        self.threshold_std = float(np.std(thr))
        self.W_train = W
        return self

    def posterior(self, t, h):
        P = _phi(t)
        Sinv = self.S0inv + P.T @ P / self.sigma2
        S = np.linalg.inv(Sinv)
        m = S @ (self.S0inv @ self.m0 + P.T @ h / self.sigma2)
        return m, S

    def predict(self, t, h, rng=None):
        """RUL au dernier cycle observé : médiane, P10, P90, et courbe projetée moyenne."""
        rng = rng or np.random.default_rng(0)
        t_now = float(t[-1])
        m, S = self.posterior(t, h)
        Ws = rng.multivariate_normal(m, S, size=N_SAMPLES)
        grid = np.arange(t_now, t_now + HORIZON + 1)
        curves = Ws @ _phi(grid).T                      # (N, len(grid))
        # incertitude sur le seuil de défaillance (dispersion observée sur la flotte)
        thr = rng.normal(self.threshold, self.threshold_std, size=(N_SAMPLES, 1))
        below = curves <= thr
        first = np.where(below.any(1), below.argmax(1), HORIZON)
        rul = first.astype(float)
        return {
            "rul": float(np.median(rul)), "p10": float(np.percentile(rul, 10)),
            "p90": float(np.percentile(rul, 90)), "m": m,
        }

    def mean_curve(self, m, t0, t1, step=2):
        g = np.arange(t0, t1 + 1, step)
        return g, _phi(g) @ m
