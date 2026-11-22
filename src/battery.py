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


def solve_custom(p, mw=10.0, mwh=20.0, rte=0.88, deg=1000.0, cycles=2, fee=0.0, soc_min_frac=0.10):
    """General battery plan for the demo app and sensitivity tests.

    Maximise  sum_t p_t*d_t - (p_t + fee)*c_t - (deg + fee)*d_t   over one day of 96 blocks
    subject to  s_t = s_{t-1} + eta*c_t - d_t/eta         (state of charge, eta = sqrt(rte))
                s_min <= s_t <= mwh,  s_0 = s_96 = s_min   (start and end empty)
                0 <= c_t, d_t <= mw/4                       (power limit per 15 minutes)
                sum_t d_t/eta <= cycles*(mwh - s_min)       (wear limit: equivalent full cycles)
    Returns charge and discharge in grid MWh per block, and the state of charge path.
    """
    n = len(p); eta = np.sqrt(rte); smin = soc_min_frac * mwh; pmax = mw / 4
    A = lil_matrix((n, 3 * n)); b = np.zeros(n)
    for t in range(n):
        A[t, 2 * n + t] = 1; A[t, t] = -eta; A[t, n + t] = 1 / eta
        if t > 0: A[t, 2 * n + t - 1] = -1
        else: b[t] = smin
    Aub = lil_matrix((1, 3 * n)); Aub[0, n:2 * n] = 1 / eta
    cost = np.r_[np.asarray(p) + fee, -(np.asarray(p) - deg - fee), np.zeros(n)]
    bnds = [(0, pmax)] * (2 * n) + [(smin, mwh)] * (n - 1) + [(smin, smin)]
    r = linprog(cost, A_ub=Aub.tocsr(), b_ub=[cycles * (mwh - smin)], A_eq=A.tocsr(), b_eq=b, bounds=bnds, method="highs")
    return r.x[:n], r.x[n:2 * n], r.x[2 * n:]


def settle_custom(c, d, p, deg=1000.0, fee=0.0):
    return float(p @ d - p @ c - deg * d.sum() - fee * (c.sum() + d.sum()))
