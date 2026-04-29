# ============================================================
# SYSTEM-LEVEL SOLVER
# Iterative coupling between refrigeration cycle and heat exchangers
# ============================================================
"""
This module solves the operating point of the full system.
For a given heat-sink temperature it:
  1) guesses Tevap and Tcond,
  2) evaluates the thermodynamic cycle,
  3) updates Tevap and Tcond from heat exchanger LMTD equations,
  4) iterates until convergence.

Secondary-fluid handling is fully delegated to heat_exchanger.py
so this module contains no fluid-type logic of its own.
"""

from src import config as cfg
from src.utils import c_to_k, k_to_c
from src.thermodynamics import compressor_performance_from_map
from src.heat_exchanger import (
    solve_evap_temperature_from_hx,
    solve_cond_temperature_from_hx,
    cond_secondary_temps_at,        # new helper — handles air vs water
    _evap_secondary_temps_K,        # reads evap side from config
)


# ============================================================
# MAIN SOLVER
# ============================================================

def solve_operating_point(
    T_heatsink_C,
    KA_EVAP,
    KA_COND,
    ref=None,
    verbose=False,
):
    """
    Solve the full operating point for a given heat-sink temperature.

    Parameters
    ----------
    T_heatsink_C : float
        Condenser secondary-fluid *inlet* temperature [°C].
        For water-cooled condensers : water supply temperature.
        For air-cooled condensers   : ambient / inlet air temperature.
    KA_EVAP : float — evaporator conductance [W/K]
    KA_COND : float — condenser  conductance [W/K]
    ref     : str, optional — refrigerant (defaults to cfg.REF)
    verbose : bool — print iteration history if True

    Returns
    -------
    dict — converged operating point (see bottom of function)

    Notes
    -----
    The old parameter name was ``T_water_in_C``.  Any call site that
    used a keyword argument should rename it; positional calls are
    unaffected.
    """

    if ref is None:
        ref = cfg.REF

    # ---- evaporator secondary temperatures (fixed, from config) --------
    T_evap_sec_in_K, T_evap_sec_out_K = _evap_secondary_temps_K()

    # ---- condenser secondary temperatures for this heat-sink step ------
    T_cond_sec_in_K, T_cond_sec_out_K = cond_secondary_temps_at(T_heatsink_C)

    # ---- initial guesses -----------------------------------------------
    T_evap_K = c_to_k(5.0)
    T_cond_K = c_to_k(T_heatsink_C + 7.0)

    # ---- iteration loop ------------------------------------------------
    for it in range(cfg.MAX_ITER):

        cyc = compressor_performance_from_map(T_evap_K, T_cond_K, ref=ref)
        Qe  = cyc["Qe"]
        Qc  = cyc["Qc"]

        T_evap_new = solve_evap_temperature_from_hx(
            Qe,
            T_evap_sec_in_K,
            T_evap_sec_out_K,
            KA_EVAP,
        )

        T_cond_new = solve_cond_temperature_from_hx(
            Qc,
            T_cond_sec_in_K,
            T_cond_sec_out_K,
            KA_COND,
        )

        T_evap_next = (1 - cfg.RELAX) * T_evap_K + cfg.RELAX * T_evap_new
        T_cond_next = (1 - cfg.RELAX) * T_cond_K + cfg.RELAX * T_cond_new

        err = max(
            abs(T_evap_next - T_evap_K),
            abs(T_cond_next - T_cond_K),
        )

        T_evap_K = T_evap_next
        T_cond_K = T_cond_next

        if verbose:
            print(
                f"  Iter {it:02d}: "
                f"Tevap={k_to_c(T_evap_K):.3f} °C  "
                f"Tcond={k_to_c(T_cond_K):.3f} °C  "
                f"err={err:.6f}"
            )

        if err < cfg.TOL:
            break

    # ---- final evaluation at converged point ---------------------------
    real = compressor_performance_from_map(T_evap_K, T_cond_K, ref=ref)

    # ---- build result dict ---------------------------------------------
    # Keep both old key names (T_water_*) and new generic names so that
    # existing code in main.py / notebook still works without changes.
    T_cond_sec_in_C  = k_to_c(T_cond_sec_in_K)
    T_cond_sec_out_C = k_to_c(T_cond_sec_out_K)

    return {
        # Generic names (preferred going forward)
        "T_heatsink_in_C":  T_cond_sec_in_C,
        "T_heatsink_out_C": T_cond_sec_out_C,

        # Legacy names — kept so main.py / notebook need no edits
        "T_water_in_C":     T_cond_sec_in_C,
        "T_water_out_C":    T_cond_sec_out_C,

        "T_evap_C":         k_to_c(T_evap_K),
        "T_cond_C":         k_to_c(T_cond_K),
        "real":             real,
        "iterations":       it + 1,
    }
