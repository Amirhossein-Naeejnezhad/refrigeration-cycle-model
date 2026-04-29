# ============================================================
# THERMODYNAMIC MODEL
# CoolProp-based cycle reconstruction + compressor coupling
# ============================================================
"""
This module reconstructs the full vapour-compression cycle using:

1) Polynomial compressor model (Bitzer / Copeland / Frascold)
2) CoolProp thermodynamic states

From these it derives:
  - isentropic efficiency  (eta_is)
  - volumetric efficiency  (eta_vol)
  - full cycle thermodynamic consistency

This is the CORE physics module of the project.
No project-specific numbers live here — everything is read from
config.py and compressor.py at call time.
"""

import numpy as np
from CoolProp.CoolProp import PropsSI

from src import config as cfg
from src.utils import k_to_c
from src.compressor import compressor_polynomial_model, get_compressor_coeffs


# ============================================================
# Main compressor-cycle model
# ============================================================

def compressor_performance_from_map(T_evap_K, T_cond_K,
                                    ref=None, model=None):
    """
    Compute full compressor + cycle thermodynamic performance.

    Workflow
    --------
    1. Call polynomial model  → Qe, Pc, mdot
    2. Use CoolProp to build  → thermodynamic states 1-4
    3. Derive efficiencies and reconstruct cycle energy balance.

    Parameters
    ----------
    T_evap_K : float — evaporating saturation temperature [K]
    T_cond_K : float — condensing  saturation temperature [K]
    ref      : str, optional
        Refrigerant string passed to CoolProp.
        Defaults to cfg.REF (set in config.py).
    model    : str, optional
        Compressor model key in COMPRESSOR_REGISTRY.
        Defaults to cfg.COMPRESSOR_MODEL (set in config.py).
        Pass explicitly only when comparing multiple compressors.

    Returns
    -------
    dict — see "Return full dataset" section at the bottom.
    """

    # ---- resolve defaults from config ----------------------
    if ref   is None:
        ref   = cfg.REF
    if model is None:
        model = cfg.COMPRESSOR_MODEL

    # Swept volume for the active compressor
    # (read from config; config derives it from VDOT_SWEPT_50HZ_M3_H)
    Vs = cfg.VDOT_SWEPT_50HZ_M3_S

    SH = cfg.SUPERHEAT_K
    SC = cfg.SUBCOOLING_K

    # ---- convert to °C for polynomial model ----------------
    Tevap_C = k_to_c(T_evap_K)
    Tcond_C = k_to_c(T_cond_K)

    # =========================================================
    # Saturation pressures
    # =========================================================
    P_evap = PropsSI("P", "T", T_evap_K, "Q", 1, ref)
    P_cond = PropsSI("P", "T", T_cond_K, "Q", 0, ref)

    # =========================================================
    # State 1 — compressor inlet (superheated vapour)
    # =========================================================
    T1   = T_evap_K + SH
    h1   = PropsSI("H", "T", T1, "P", P_evap, ref)
    s1   = PropsSI("S", "T", T1, "P", P_evap, ref)
    rho1 = PropsSI("D", "T", T1, "P", P_evap, ref)

    # =========================================================
    # State 3 — condenser outlet (subcooled liquid)
    # =========================================================
    T3 = T_cond_K - SC
    h3 = PropsSI("H", "T", T3, "P", P_cond, ref)

    # =========================================================
    # Polynomial compressor model
    # =========================================================
    mp = compressor_polynomial_model(Tevap_C, Tcond_C, model=model)

    mdot    = mp["mdot"]    # [kg/s]
    Pc      = mp["Pc"]      # [W]
    Qe_poly = mp["Qe"]      # [W]

    # =========================================================
    # Isentropic reference state (State 2s)
    # =========================================================
    h2s = PropsSI("H", "P", P_cond, "S", s1, ref)

    # =========================================================
    # Actual compression (State 2)
    # =========================================================
    dh_actual = Pc / mdot
    h2 = h1 + dh_actual

    T2 = PropsSI("T", "P", P_cond, "H", h2, ref)
    s2 = PropsSI("S", "P", P_cond, "H", h2, ref)

    # =========================================================
    # Efficiencies
    # =========================================================
    eta_is  = (h2s - h1) / dh_actual
    eta_vol = mdot / (rho1 * Vs)

    # Numerical safety clipping
    eta_is  = float(np.clip(eta_is,  0.01, 1.00))
    eta_vol = float(np.clip(eta_vol, 0.01, 1.20))

    # =========================================================
    # State 4 — expansion valve outlet (isenthalpic)
    # =========================================================
    h4 = h3
    T4 = PropsSI("T", "P", P_evap, "H", h4, ref)
    s4 = PropsSI("S", "P", P_evap, "H", h4, ref)

    # =========================================================
    # Thermodynamic duties
    # =========================================================
    Qe_thermo = mdot * (h1 - h4)   # [W]
    Pc_thermo = mdot * (h2 - h1)   # [W]
    Qc_thermo = mdot * (h2 - h3)   # [W]

    PR = P_cond / P_evap

    # =========================================================
    # Return full dataset
    # =========================================================
    return {
        # Pressures
        "P_evap": P_evap,
        "P_cond": P_cond,
        "PR":     PR,

        # Efficiencies
        "eta_is":  eta_is,
        "eta_vol": eta_vol,

        # Mass flow
        "mdot": mdot,

        # Thermodynamic duties (from cycle energy balance)
        "Qe": Qe_thermo,
        "Pc": Pc_thermo,
        "Qc": Qc_thermo,

        # Polynomial map values (for cross-checking)
        "Qe_map": Qe_poly,
        "Pc_map": Pc,

        # EER
        "EER": Qe_thermo / Pc_thermo if Pc_thermo > 0 else np.nan,

        # Extrapolation flag from polynomial model
        "map_extrapolated": mp["was_extrapolated"],

        # Cycle states (all in SI: T[K], P[Pa], h[J/kg], s[J/kg/K])
        "states": {
            1: {"T": T1,   "P": P_evap, "h": h1, "s": s1},
            2: {"T": T2,   "P": P_cond, "h": h2, "s": s2},
            3: {"T": T3,   "P": P_cond, "h": h3, "s": None},
            4: {"T": T4,   "P": P_evap, "h": h4, "s": s4},
        },
    }
