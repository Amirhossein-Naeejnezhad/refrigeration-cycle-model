# ============================================================
# THERMODYNAMIC MODEL
# CoolProp-based cycle reconstruction + compressor coupling
# ============================================================
"""Reconstruct the vapour-compression cycle from compressor-map data."""

import numpy as np
from CoolProp.CoolProp import PropsSI

from src import config as cfg
from src.compressor import compressor_polynomial_model
from src.utils import k_to_c


def compressor_performance_from_map(T_evap_K, T_cond_K, ref=None, model=None):
    """Compute compressor and thermodynamic-cycle performance."""
    ref = ref or cfg.REF
    model = model or cfg.COMPRESSOR_MODEL

    tevap_c = k_to_c(T_evap_K)
    tcond_c = k_to_c(T_cond_K)

    p_evap = PropsSI("P", "T", T_evap_K, "Q", 1, ref)
    p_cond = PropsSI("P", "T", T_cond_K, "Q", 0, ref)

    # State 1: compressor inlet, superheated vapour.
    T1 = T_evap_K + cfg.SUPERHEAT_K
    h1 = PropsSI("H", "T", T1, "P", p_evap, ref)
    s1 = PropsSI("S", "T", T1, "P", p_evap, ref)
    rho1 = PropsSI("D", "T", T1, "P", p_evap, ref)

    # State 3: condenser outlet, subcooled liquid.
    T3 = T_cond_K - cfg.SUBCOOLING_K
    h3 = PropsSI("H", "T", T3, "P", p_cond, ref)
    s3 = PropsSI("S", "T", T3, "P", p_cond, ref)

    comp = compressor_polynomial_model(tevap_c, tcond_c, model=model)
    mdot = comp["mdot"]
    pc_map = comp["Pc"]
    qe_map = comp["Qe"]

    h2s = PropsSI("H", "P", p_cond, "S", s1, ref)
    h2 = h1 + pc_map / mdot
    T2 = PropsSI("T", "P", p_cond, "H", h2, ref)
    s2 = PropsSI("S", "P", p_cond, "H", h2, ref)

    eta_is = (h2s - h1) / (pc_map / mdot)
    eta_vol = mdot / (rho1 * cfg.VDOT_SWEPT_50HZ_M3_S)
    eta_is = float(np.clip(eta_is, 0.01, 1.00))
    eta_vol = float(np.clip(eta_vol, 0.01, 1.20))

    # State 4: expansion-valve outlet, isenthalpic throttling.
    h4 = h3
    T4 = PropsSI("T", "P", p_evap, "H", h4, ref)
    s4 = PropsSI("S", "P", p_evap, "H", h4, ref)

    qe = mdot * (h1 - h4)
    pc = mdot * (h2 - h1)
    qc = mdot * (h2 - h3)

    return {
        "P_evap": p_evap,
        "P_cond": p_cond,
        "PR": p_cond / p_evap,
        "eta_is": eta_is,
        "eta_vol": eta_vol,
        "mdot": mdot,
        "Qe": qe,
        "Pc": pc,
        "Qc": qc,
        "Qe_map": qe_map,
        "Pc_map": pc_map,
        "EER": qe / pc if pc > 0 else np.nan,
        "map_extrapolated": comp["was_extrapolated"],
        "states": {
            1: {"T": T1, "P": p_evap, "h": h1, "s": s1},
            2: {"T": T2, "P": p_cond, "h": h2, "s": s2},
            3: {"T": T3, "P": p_cond, "h": h3, "s": s3},
            4: {"T": T4, "P": p_evap, "h": h4, "s": s4},
        },
    }
