"""Piezas comunes del protocolo (sin lectura de archivos): clases, Pipeline, pliegues y metricas.

Este modulo NO lee datos. Lo importan tanto la etapa de desarrollo (que solo ve datos hasta dic-2025)
como la de prueba, de modo que ambas usan exactamente el mismo diseno experimental.
"""
import json
import warnings

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import BaggingRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, LinearRegression, Ridge
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import warnings
warnings.filterwarnings("ignore")

SEED = 0
ESPS = ["CA", "Cattle", "Poultry", "Swine"]
ONEHOT = [f"esp_{e}" for e in ESPS]
CONT_M = ["ipc_yoy", "ipc_yoy_CA", "pib", "pib_agro", "smmlv", "var_leche", "var_res", "var_cerdo", "var_huevo", "var_pollo"]
TASKS = {
    "mercado": dict(y="y_mercado", cont=CONT_M, ini="2021-12-01", emb=6, holdout=12, sizes=[6, 12, 18, 24, 30, 36]),
    "compite": dict(y="y_compite", cont=CONT_M, ini="2021-12-01", emb=6, holdout=12, sizes=[6, 12, 18, 24, 30, 36]),
    "lab": dict(y="y_lab", cont=CONT_M + ["y_compite"], ini="2023-12-01", emb=3, holdout=6, sizes=[4, 8, 12, 16]),
    "lab_ym": dict(y="y_lab", cont=CONT_M + ["y_mercado"], ini="2023-12-01", emb=3, holdout=6, sizes=[4, 8, 12, 16]),
}
TRAIN_END, TEST_INI, TEST_END = "2025-12-01", "2026-01-01", "2026-06-01"
BLOCK = 6
# complejidad para la regla de parsimonia (menor es mas simple)
COMPLEJIDAD = {"ols_esp": 0, "ridge_esp": 0, "enet_esp": 0, "ols": 1, "ridge": 1, "enet": 1, "knn": 2, "bagging": 3, "rf": 3, "gbm": 4}
NOMBRES = {"ols_esp": "Regresión lineal por especie", "ridge_esp": "Ridge por especie", "enet_esp": "Elastic Net por especie",
           "ols": "Regresión lineal", "ridge": "Ridge común", "enet": "Elastic Net común", "knn": "K vecinos más cercanos",
           "bagging": "Bagging de árboles", "rf": "Random Forest", "gbm": "Gradient Boosting"}


def clase(y):
    return np.digitize(np.asarray(y, dtype=float), [0.08, 0.15])  # 0 regular, 1 estable, 2 optimista


def costo(real, pred):
    d = np.asarray(pred) - np.asarray(real)
    return np.where(d > 0, 2.0 * d, -1.0 * d)


def mes_idx(f):
    f = pd.to_datetime(f)
    return (f.dt.year * 12 + f.dt.month).to_numpy()



class PerEspecie(BaseEstimator, RegressorMixin):
    """Un modelo lineal por especie (base: ols, ridge o enet); la especie se lee de las 4 ultimas columnas (one-hot)."""

    def __init__(self, base="ridge", alpha=1.0, l1_ratio=0.5):
        self.base = base
        self.alpha = alpha
        self.l1_ratio = l1_ratio

    def _nuevo(self):
        if self.base == "ridge":
            return Ridge(alpha=self.alpha)
        if self.base == "enet":
            return ElasticNet(alpha=self.alpha, l1_ratio=self.l1_ratio, max_iter=50000)
        return LinearRegression()

    def fit(self, X, y, sample_weight=None):
        X, y = np.asarray(X), np.asarray(y, dtype=float)
        w = None if sample_weight is None else np.asarray(sample_weight)
        sp = X[:, -4:].argmax(1)
        self.models_ = {k: self._nuevo().fit(X[sp == k][:, :-4], y[sp == k], sample_weight=None if w is None else w[sp == k])
                        for k in np.unique(sp)}
        self.mean_ = np.average(y, weights=w)
        return self

    def predict(self, X):
        X = np.asarray(X)
        sp = X[:, -4:].argmax(1)
        p = np.full(len(X), self.mean_)
        for k, m in self.models_.items():
            p[sp == k] = m.predict(X[sp == k][:, :-4])
        return p


class Balanceado(BaseEstimator, RegressorMixin):
    """Pondera cada muestra por la frecuencia inversa de su clase de escenario. Los pesos se
    calculan dentro de fit, es decir solo con el entrenamiento del pliegue."""

    def __init__(self, est=None, balance=False):
        self.est = est
        self.balance = balance

    def fit(self, X, y):
        self.est_ = clone(self.est)
        y = np.asarray(y, dtype=float)
        if self.balance:
            c = clase(y)
            n = np.bincount(c, minlength=3).astype(float)
            self.est_.fit(X, y, sample_weight=len(y) / (3.0 * n[c]))
        else:
            self.est_.fit(X, y)
        return self

    def predict(self, X):
        return self.est_.predict(X)


EST = {
    "ols_esp": lambda: PerEspecie(base="ols"),
    "ridge_esp": lambda: PerEspecie(base="ridge"),
    "enet_esp": lambda: PerEspecie(base="enet"),
    "ols": lambda: LinearRegression(),
    "ridge": lambda: Ridge(),
    "enet": lambda: ElasticNet(max_iter=50000),
    "knn": lambda: KNeighborsRegressor(),
    "bagging": lambda: BaggingRegressor(estimator=DecisionTreeRegressor(random_state=SEED), n_estimators=200, random_state=SEED, n_jobs=1),
    "rf": lambda: RandomForestRegressor(n_estimators=300, random_state=SEED, n_jobs=1),
    "gbm": lambda: GradientBoostingRegressor(subsample=0.8, random_state=SEED),
}
ALPHAS = [0.1, 1, 10, 100, 1000, 10000]
GRID = {
    "ols_esp": {},
    "ridge_esp": {"alpha": ALPHAS},
    "enet_esp": {"alpha": [0.001, 0.01, 0.1, 1], "l1_ratio": [0.1, 0.5, 0.9, 1.0]},
    "ols": {},
    "ridge": {"alpha": ALPHAS},
    "enet": {"alpha": [0.001, 0.01, 0.1, 1], "l1_ratio": [0.1, 0.5, 0.9, 1.0]},
    "knn": {"n_neighbors": [3, 5, 8, 12, 20, 30], "weights": ["uniform", "distance"], "p": [1, 2]},
    "bagging": {"estimator__max_depth": [2, 3, 5, None], "estimator__min_samples_leaf": [3, 8], "max_samples": [0.5, 0.8, 1.0]},
    "rf": {"max_depth": [2, 3, 5, 8], "min_samples_leaf": [3, 8], "max_features": [0.5, 1.0]},
    "gbm": {"n_estimators": [50, 100, 200, 400], "learning_rate": [0.03, 0.1], "max_depth": [1, 2, 3], "min_samples_leaf": [3, 8]},
}
SIN_PESOS = {"knn"}  # KNeighborsRegressor no admite sample_weight: la ponderacion por clase no aplica


def r2(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    return float(1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def pipeline(kind, task, balance=False, **params):
    cont = TASKS[task]["cont"]
    pre = ColumnTransformer([("num", StandardScaler(), cont), ("esp", "passthrough", ONEHOT)])
    p = Pipeline([("pre", pre), ("model", Balanceado(EST[kind](), balance))])
    p.set_params(**{f"model__est__{k}": v for k, v in params.items()})
    return p


def columnas(task):
    return TASKS[task]["cont"] + ONEHOT


def splits(meses, emb, block=BLOCK):
    """K-fold por bloques de `block` meses con purga de `emb` meses a cada lado."""
    um = np.unique(meses)
    out = []
    for b in np.array_split(um, int(np.ceil(len(um) / block))):
        te = np.where(np.isin(meses, b))[0]
        tr = np.where((meses < b.min() - emb) | (meses > b.max() + emb))[0]
        if len(tr) >= 24:
            out.append((tr, te))
    return out


def met(y, p):
    e = np.asarray(p) - np.asarray(y)
    return {"MAE_pp": float(np.abs(e).mean() * 100), "RMSE_pp": float(np.sqrt((e ** 2).mean()) * 100),
            "sesgo_pp": float(e.mean() * 100)}


def met_clase(y, p, m=0.0):
    cy, cp = clase(y), clase(np.asarray(p) - m)
    cm = confusion_matrix(cy, cp, labels=[0, 1, 2])
    rec = cm.diagonal() / np.maximum(cm.sum(1), 1)
    return {"acierto": float((cy == cp).mean()), "F1_macro": float(f1_score(cy, cp, average="macro", labels=[0, 1, 2], zero_division=0)),
            "recall_regular": float(rec[0]) if cm[0].sum() else None, "recall_estable": float(rec[1]) if cm[1].sum() else None,
            "recall_optimista": float(rec[2]) if cm[2].sum() else None,
            "costo_medio": float(costo(cy, cp).mean()), "matriz": cm.tolist()}


def oof(pipe, d, task, cv):
    y = d[TASKS[task]["y"]].to_numpy()
    X = d[columnas(task)]
    p = np.full(len(d), np.nan)
    fold = np.full(len(d), -1)
    for i, (tr, te) in enumerate(cv):
        m = clone(pipe).fit(X.iloc[tr], y[tr])
        p[te] = m.predict(X.iloc[te])
        fold[te] = i
    return p, fold


def mae_pliegues(y, p, fold, mask=None):
    out = []
    for i in sorted(set(fold[fold >= 0])):
        s = (fold == i) if mask is None else (fold == i) & mask
        if s.sum():
            out.append(float(np.abs(p[s] - y[s]).mean() * 100))
    return out


