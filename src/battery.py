"""Battery dispatch model shared by the notebooks (same physics as src/dispatch_lp.py).

10 MW / 20 MWh, 88% round trip (sqrt split), state of charge 2-20 MWh, starts and ends each day at 2 MWh.
Variables are grid-side MWh per 15-minute block; wear is charged per MWh sold, as in the M2 Data Note.
"""
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

T, PMAX, EMIN, EMAX = 96, 2.5, 2.0, 20.0
EC = ED = np.sqrt(0.88)


def _build():
    A = lil_matrix((T, 3 * T)); b = np.zeros(T)
    for t in range(T):
        A[t, 2 * T + t] = 1; A[t, t] = -EC; A[t, T + t] = 1 / ED
        if t > 0: A[t, 2 * T + t - 1] = -1
        else: b[t] = EMIN
    Aub = lil_matrix((1, 3 * T)); Aub[0, T:2 * T] = 1 / ED
    return A.tocsr(), b, Aub.tocsr()


_A, _B, _AUB = _build()
_BNDS = [(0, PMAX)] * (2 * T) + [(EMIN, EMAX)] * (T - 1) + [(EMIN, EMIN)]


def solve(p, deg=1000.0, cycles=1):
    """Optimal charge c and discharge d (grid MWh per block) for price vector p (96,)."""
    cost = np.r_[p, -(p - deg), np.zeros(T)]
    r = linprog(cost, A_ub=_AUB, b_ub=[18 * cycles], A_eq=_A, b_eq=_B, bounds=_BNDS, method="highs")
    return r.x[:T], r.x[T:2 * T]


def settle(c, d, p, deg=1000.0):
    """Daily trading profit at actual prices p."""
    return float(p @ d - p @ c - deg * d.sum())


def fixed_rule(p, deg=1000.0):
    """Canvas rule made feasible: store 18 MWh over 11:00-15:00, release it over 18:00-22:00."""
    c = np.zeros(T); d = np.zeros(T); c[44:60] = 18 / EC / 16; d[72:88] = 18 * ED / 16
    return settle(c, d, p, deg)
