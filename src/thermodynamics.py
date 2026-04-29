# ============================================================
# THERMODYNAMIC MODEL
# CoolProp-based cycle reconstruction + compressor coupling
# ============================================================

"""
This module reconstructs the full vapor-compression cycle using:

1) Bitzer polynomial compressor model (Qe, Pc, mdot)
2) CoolProp thermodynamic states

From these, it derives:
- isentropic efficiency (eta_is)
- volumetric efficiency (eta_vol)
- full cycle thermodynamic consistency

This is the CORE physics module of the project.
"""

import numpy as np
from CoolProp.CoolProp import PropsSI

from src.config import REF, SUPERHEAT_K, SUBCOOLING_K, VDOT_SWEPT_50HZ_M3_S
from src.utils import k_to_c
from src.compressor import compressor_polynomial_model


# =========================
# Main compressor-cycle model
# =========================
def compressor_performance_from_map(T_evap_K, T_cond_K, ref=REF):
    """
    Compute full compressor + cycle thermodynamic performance.

    Workflow:
    1) Call polynomial model → Qe, Pc, mdot
    2) Use CoolProp to compute thermodynamic states
    3) Derive efficiencies and reconstruct cycle

    Parameters:
        T_evap_K : evaporating temperature [K]
        T_cond_K : condensing temperature  [K]
        ref      : refrigerant

    Returns:
        dict with:
            pressures, efficiencies, duties, states, etc.
    """

    # Convert to Celsius for polynomial model
    Tevap_C = k_to_c(T_evap_K)
    Tcond_C = k_to_c(T_cond_K)

    # =========================
    # Saturation pressures
    # =========================
    P_evap = PropsSI("P", "T", T_evap_K, "Q", 1, ref)
    P_cond = PropsSI("P", "T", T_cond_K, "Q", 0, ref)

    # =========================
    # State 1: compressor inlet (superheated vapor)
    # =========================
    T1   = T_evap_K + SUPERHEAT_K
    h1   = PropsSI("H", "T", T1, "P", P_evap, ref)
    s1   = PropsSI("S", "T", T1, "P", P_evap, ref)
    rho1 = PropsSI("D", "T", T1, "P", P_evap, ref)

    # =========================
    # State 3: condenser outlet (subcooled liquid)
    # =========================
    T3 = T_cond_K - SUBCOOLING_K
    h3 = PropsSI("H", "T", T3, "P", P_cond, ref)

    # =========================
    # Polynomial compressor model
    # =========================
    mp = compressor_polynomial_model(Tevap_C, Tcond_C)

    mdot    = mp["mdot"]
    Pc      = mp["Pc"]
    Qe_poly = mp["Qe"]

    # =========================
    # Isentropic reference state
    # =========================
    h2s = PropsSI("H", "P", P_cond, "S", s1, ref)

    # =========================
    # Actual compression process
    # =========================
    dh_actual = Pc / mdot
    h2 = h1 + dh_actual

    T2 = PropsSI("T", "P", P_cond, "H", h2, ref)
    s2 = PropsSI("S", "P", P_cond, "H", h2, ref)

    # =========================
    # Efficiencies
    # =========================
    eta_is = (h2s - h1) / dh_actual

    mdot_ideal = rho1 * VDOT_SWEPT_50HZ_M3_S
    eta_vol    = mdot / mdot_ideal

    # Numerical safety clipping
    eta_is  = float(np.clip(eta_is,  0.01, 1.0))
    eta_vol = float(np.clip(eta_vol, 0.01, 1.20))

    # =========================
    # State 4: expansion valve (isenthalpic)
    # =========================
    h4 = h3
    T4 = PropsSI("T", "P", P_evap, "H", h4, ref)
    s4 = PropsSI("S", "P", P_evap, "H", h4, ref)

    # =========================
    # Thermodynamic duties
    # =========================
    Qe_thermo = mdot * (h1 - h4)
    Pc_thermo = mdot * (h2 - h1)
    Qc_thermo = mdot * (h2 - h3)

    # Pressure ratio
    PR = P_cond / P_evap

    # =========================
    # Return full dataset
    # =========================
    return {
        "P_evap": P_evap,
        "P_cond": P_cond,
        "PR": PR,

        "eta_is": eta_is,
        "eta_vol": eta_vol,

        "mdot": mdot,

        "Qe": Qe_thermo,
        "Pc": Pc_thermo,
        "Qc": Qc_thermo,

        "Qe_map": Qe_poly,
        "Pc_map": Pc,

        "EER": Qe_thermo / Pc_thermo if Pc_thermo > 0 else np.nan,

        "map_extrapolated": mp["was_extrapolated"],

        "states": {
            1: {"T": T1, "P": P_evap, "h": h1, "s": s1},
            2: {"T": T2, "P": P_cond, "h": h2, "s": s2},
            3: {"T": T3, "P": P_cond, "h": h3, "s": None},
            4: {"T": T4, "P": P_evap, "h": h4, "s": s4},
        }
    }
