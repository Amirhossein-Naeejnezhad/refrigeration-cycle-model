# ============================================================
# HEAT EXCHANGER MODEL
# LMTD-based KA calculation and temperature solvers
# ============================================================

"""
This module contains the heat exchanger calculations:

1) Design-step KA calculation at the nominal operating point
2) Evaporating temperature solver from evaporator LMTD equation
3) Condensing temperature solver from condenser LMTD equation
"""

import numpy as np

from src.config import (
    REF,
    T_AIR_IN_C,
    T_AIR_OUT_C,
    T_WATER_RISE_K,
    nominal_map_point,
)

from src.utils import c_to_k, lmtd
from src.thermodynamics import compressor_performance_from_map


# =========================
# 1) HX DESIGN: KA calculation
# =========================
def compute_KA_values():
    """
    Compute KA_EVAP and KA_COND from the nominal operating point
    using the LMTD method.

    This is done once as a design step. The calculated KA values are then
    kept constant during the parametric study.
    """

    print("\nCALCULATING HEAT EXCHANGER KA VALUES (DESIGN STEP)")
    print("--------------------------------------------------")

    # --- Nominal temperatures from compressor map / assignment
    Tevap_nom_K = c_to_k(nominal_map_point["Tevap_C"])
    Tcond_nom_K = c_to_k(nominal_map_point["Tcond_C"])

    T_air_in_K  = c_to_k(T_AIR_IN_C)
    T_air_out_K = c_to_k(T_AIR_OUT_C)

    T_w_in_C_nom  = nominal_map_point["Tcond_C"] - 5.0
    T_w_out_C_nom = T_w_in_C_nom - T_WATER_RISE_K

    T_w_in_K  = c_to_k(T_w_in_C_nom)
    T_w_out_K = c_to_k(T_w_out_C_nom)

    # --- Get cycle performance at nominal point
    perf = compressor_performance_from_map(
        Tevap_nom_K,
        Tcond_nom_K,
        ref=REF
    )

    Qe = perf["Qe"]
    Qc = perf["Qc"]

    # =========================
    # EVAPORATOR KA
    # =========================
    dT1_evap = T_air_in_K  - Tevap_nom_K
    dT2_evap = T_air_out_K - Tevap_nom_K

    LMTD_evap = lmtd(dT1_evap, dT2_evap)
    KA_evap = Qe / LMTD_evap

    # =========================
    # CONDENSER KA
    # =========================
    dT1_cond = Tcond_nom_K - T_w_out_K
    dT2_cond = Tcond_nom_K - T_w_in_K

    LMTD_cond = lmtd(dT1_cond, dT2_cond)
    KA_cond = Qc / LMTD_cond

    print(f"KA_EVAP = {KA_evap/1000:.2f} kW/K")
    print(f"KA_COND = {KA_cond/1000:.2f} kW/K")

    return KA_evap, KA_cond


# =========================
# 2) Evaporator temperature solver
# =========================
def solve_evap_temperature_from_hx(
    Q_evap_W,
    T_air_in_K,
    T_air_out_K,
    KA_evap
):
    """
    Solve evaporating temperature from:

        Q_evap = KA_evap * LMTD_evap

    Refrigerant side is approximated at constant Tevap in the evaporator.

    Counterflow assumption:
        DeltaT1 = T_air_in  - Tevap
        DeltaT2 = T_air_out - Tevap
    """

    def f(T_evap):
        dT1 = T_air_in_K  - T_evap
        dT2 = T_air_out_K - T_evap

        if dT1 <= 0 or dT2 <= 0:
            return 1e12

        return KA_evap * lmtd(dT1, dT2) - Q_evap_W

    low  = c_to_k(-25.0)
    high = T_air_out_K - 0.2

    f_low  = f(low)
    f_high = f(high)

    if np.sign(f_low) == np.sign(f_high):
        Ts   = np.linspace(low, high, 300)
        vals = np.array([abs(f(T)) for T in Ts])
        return Ts[np.argmin(vals)]

    for _ in range(80):
        mid   = 0.5 * (low + high)
        f_mid = f(mid)

        if abs(f_mid) < 1e-6:
            return mid

        if np.sign(f_low) * np.sign(f_mid) < 0:
            high   = mid
            f_high = f_mid
        else:
            low   = mid
            f_low = f_mid

    return 0.5 * (low + high)


# =========================
# 3) Condenser temperature solver
# =========================
def solve_cond_temperature_from_hx(
    Q_cond_W,
    T_w_in_K,
    T_w_out_K,
    KA_cond
):
    """
    Solve condensing temperature from:

        Q_cond = KA_cond * LMTD_cond

    Refrigerant side is approximated at constant Tcond in the condenser.

    Counterflow assumption:
        DeltaT1 = Tcond - T_w_out
        DeltaT2 = Tcond - T_w_in
    """

    def f(T_cond):
        dT1 = T_cond - T_w_out_K
        dT2 = T_cond - T_w_in_K

        if dT1 <= 0 or dT2 <= 0:
            return -1e12

        return KA_cond * lmtd(dT1, dT2) - Q_cond_W

    low  = T_w_out_K + 0.2
    high = c_to_k(80.0)

    f_low  = f(low)
    f_high = f(high)

    if np.sign(f_low) == np.sign(f_high):
        Ts   = np.linspace(low, high, 300)
        vals = np.array([abs(f(T)) for T in Ts])
        return Ts[np.argmin(vals)]

    for _ in range(80):
        mid   = 0.5 * (low + high)
        f_mid = f(mid)

        if abs(f_mid) < 1e-6:
            return mid

        if np.sign(f_low) * np.sign(f_mid) < 0:
            high   = mid
            f_high = f_mid
        else:
            low   = mid
            f_low = f_mid

    return 0.5 * (low + high)
