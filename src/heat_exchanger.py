# ============================================================
# HEAT EXCHANGER MODEL
# LMTD-based KA calculation and temperature solvers
# ============================================================
"""
This module contains the heat exchanger calculations:

  1) Design-step KA calculation at the nominal operating point
  2) Evaporating temperature solver  (LMTD on evaporator)
  3) Condensing temperature solver   (LMTD on condenser)

Secondary-fluid type is read from config:
  EVAP_SECONDARY : "air"   → uses T_AIR_IN_C  / T_AIR_OUT_C
                   "water" / "brine" → uses T_BRINE_IN_C / T_BRINE_OUT_C
  COND_SECONDARY : "air"   → uses an air-side inlet temperature range
                   "water" → uses T_WATER_RISE_K

Both sides support counterflow LMTD with a constant refrigerant
saturation temperature (standard assumption for phase-change HXs).
"""

import numpy as np

from src import config as cfg
from src.utils import c_to_k, lmtd
from src.thermodynamics import compressor_performance_from_map


# ============================================================
# INTERNAL HELPERS — secondary-fluid temperature readers
# ============================================================

def _evap_secondary_temps_K():
    """
    Return (T_sec_in_K, T_sec_out_K) for the evaporator secondary fluid,
    based on cfg.EVAP_SECONDARY.

    "air"          → T_AIR_IN_C  / T_AIR_OUT_C
    "water"/"brine"→ T_BRINE_IN_C / T_BRINE_OUT_C
    """
    sec = cfg.EVAP_SECONDARY.lower()

    if sec == "air":
        return c_to_k(cfg.T_AIR_IN_C), c_to_k(cfg.T_AIR_OUT_C)

    if sec in ("water", "brine"):
        # Students with water/brine evaporators must set these in config
        try:
            return c_to_k(cfg.T_BRINE_IN_C), c_to_k(cfg.T_BRINE_OUT_C)
        except AttributeError:
            raise AttributeError(
                "EVAP_SECONDARY is 'water'/'brine' but T_BRINE_IN_C / "
                "T_BRINE_OUT_C are not defined in config.py.\n"
                "Add them under your project block, e.g.:\n"
                "  T_BRINE_IN_C  = 18.0\n"
                "  T_BRINE_OUT_C = 12.0"
            )

    raise ValueError(
        f"Unknown EVAP_SECONDARY='{cfg.EVAP_SECONDARY}'. "
        "Use 'air', 'water', or 'brine'."
    )


def _cond_secondary_temps_K(T_cond_C_nom):
    """
    Return (T_sec_in_K, T_sec_out_K) for the condenser secondary fluid
    at the nominal operating point, based on cfg.COND_SECONDARY.

    "water" → inlet = Tcond_nom - 5 K approach (standard design guess),
               outlet = inlet - T_WATER_RISE_K
    "air"   → inlet taken from the parametric study midpoint
               (Tcond_nom - 10 K is a reasonable air-cooled design point),
               outlet = inlet + T_AIR_RISE_K  (default 5 K if not set)
    """
    sec = cfg.COND_SECONDARY.lower()

    if sec == "water":
        T_w_in_C  = T_cond_C_nom - 5.0          # 5 K approach (design)
        T_w_out_C = T_w_in_C - cfg.T_WATER_RISE_K
        return c_to_k(T_w_in_C), c_to_k(T_w_out_C)

    if sec == "air":
        # For air-cooled condensers the "heat-sink temperature" in the
        # parametric study is the air inlet temperature.
        # At the design (nominal) point we use the midpoint of the sweep range.
        T_air_in_C  = 0.5 * (cfg.T_HEATSINK_RANGE_C["start"] +
                              cfg.T_HEATSINK_RANGE_C["end"])
        # Air temperature rise: use config value if defined, else default 5 K
        T_air_rise  = getattr(cfg, "T_AIR_COND_RISE_K", 5.0)
        T_air_out_C = T_air_in_C + T_air_rise
        return c_to_k(T_air_in_C), c_to_k(T_air_out_C)

    raise ValueError(
        f"Unknown COND_SECONDARY='{cfg.COND_SECONDARY}'. "
        "Use 'water' or 'air'."
    )


# ============================================================
# 1) HX DESIGN — KA calculation at nominal point
# ============================================================

def compute_KA_values():
    """
    Compute KA_EVAP and KA_COND from the nominal operating point
    using the LMTD method.

    This is run once as a design step.  The returned KA values are
    then held constant throughout the parametric study.

    Works for any combination of:
      EVAP_SECONDARY : "air" | "water" | "brine"
      COND_SECONDARY : "water" | "air"
    """

    print("\nCALCULATING HEAT EXCHANGER KA VALUES (DESIGN STEP)")
    print("--------------------------------------------------")
    print(f"  Evaporator secondary : {cfg.EVAP_SECONDARY}")
    print(f"  Condenser  secondary : {cfg.COND_SECONDARY}")

    # ---- nominal saturation temperatures -------------------
    Tevap_nom_K = c_to_k(cfg.nominal_map_point["Tevap_C"])
    Tcond_nom_K = c_to_k(cfg.nominal_map_point["Tcond_C"])

    # ---- secondary-fluid temperatures ----------------------
    T_evap_sec_in_K, T_evap_sec_out_K = _evap_secondary_temps_K()
    T_cond_sec_in_K, T_cond_sec_out_K = _cond_secondary_temps_K(
        cfg.nominal_map_point["Tcond_C"]
    )

    # ---- cycle performance at nominal point ----------------
    perf = compressor_performance_from_map(Tevap_nom_K, Tcond_nom_K)
    Qe   = perf["Qe"]
    Qc   = perf["Qc"]

    # ---- EVAPORATOR KA -------------------------------------
    # Counterflow: refrigerant at Tevap (constant), secondary cools down
    #   hot end (secondary inlet)  Δ1 = T_sec_in  − Tevap
    #   cold end (secondary outlet) Δ2 = T_sec_out − Tevap
    dT1_evap  = T_evap_sec_in_K  - Tevap_nom_K
    dT2_evap  = T_evap_sec_out_K - Tevap_nom_K
    LMTD_evap = lmtd(dT1_evap, dT2_evap)
    KA_evap   = Qe / LMTD_evap

    # ---- CONDENSER KA --------------------------------------
    # Counterflow: refrigerant at Tcond (constant), secondary heats up
    #   hot end (secondary outlet) Δ1 = Tcond − T_sec_out
    #   cold end (secondary inlet) Δ2 = Tcond − T_sec_in
    dT1_cond  = Tcond_nom_K - T_cond_sec_out_K
    dT2_cond  = Tcond_nom_K - T_cond_sec_in_K
    LMTD_cond = lmtd(dT1_cond, dT2_cond)
    KA_cond   = Qc / LMTD_cond

    print(f"  KA_EVAP = {KA_evap/1000:.2f} kW/K")
    print(f"  KA_COND = {KA_cond/1000:.2f} kW/K")

    return KA_evap, KA_cond


# ============================================================
# 2) Evaporator temperature solver
# ============================================================

def solve_evap_temperature_from_hx(
    Q_evap_W,
    T_sec_in_K,
    T_sec_out_K,
    KA_evap,
):
    """
    Solve evaporating temperature from the LMTD equation:

        Q_evap = KA_evap · LMTD_evap

    Refrigerant side is at constant Tevap (phase-change assumption).
    Counterflow:
        ΔT1 = T_sec_in  − Tevap   (hot end)
        ΔT2 = T_sec_out − Tevap   (cold end)

    Parameters
    ----------
    Q_evap_W    : float  — evaporator duty [W]
    T_sec_in_K  : float  — secondary fluid inlet  temperature [K]
    T_sec_out_K : float  — secondary fluid outlet temperature [K]
    KA_evap     : float  — evaporator conductance [W/K]

    Returns
    -------
    float — evaporating temperature [K]

    Notes
    -----
    The argument names are generic (*_sec_*) so the same function
    handles air, water, and brine without change.
    Callers that previously passed T_air_in_K / T_air_out_K are
    fully compatible — only the parameter names changed.
    """

    def f(T_evap):
        dT1 = T_sec_in_K  - T_evap
        dT2 = T_sec_out_K - T_evap
        if dT1 <= 0 or dT2 <= 0:
            return 1e12
        return KA_evap * lmtd(dT1, dT2) - Q_evap_W

    low  = c_to_k(-40.0)          # extended lower bound for freezer apps
    high = T_sec_out_K - 0.2

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
            high, f_high = mid, f_mid
        else:
            low,  f_low  = mid, f_mid

    return 0.5 * (low + high)


# ============================================================
# 3) Condenser temperature solver
# ============================================================

def solve_cond_temperature_from_hx(
    Q_cond_W,
    T_sec_in_K,
    T_sec_out_K,
    KA_cond,
):
    """
    Solve condensing temperature from the LMTD equation:

        Q_cond = KA_cond · LMTD_cond

    Refrigerant side is at constant Tcond (phase-change assumption).
    Counterflow:
        ΔT1 = Tcond − T_sec_out   (hot end)
        ΔT2 = Tcond − T_sec_in    (cold end)

    Parameters
    ----------
    Q_cond_W    : float  — condenser duty [W]
    T_sec_in_K  : float  — secondary fluid inlet  temperature [K]
    T_sec_out_K : float  — secondary fluid outlet temperature [K]
    KA_cond     : float  — condenser conductance [W/K]

    Returns
    -------
    float — condensing temperature [K]
    """

    def f(T_cond):
        dT1 = T_cond - T_sec_out_K
        dT2 = T_cond - T_sec_in_K
        if dT1 <= 0 or dT2 <= 0:
            return -1e12
        return KA_cond * lmtd(dT1, dT2) - Q_cond_W

    low  = T_sec_out_K + 0.2
    high = c_to_k(90.0)           # extended upper bound for high-lift apps

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
            high, f_high = mid, f_mid
        else:
            low,  f_low  = mid, f_mid

    return 0.5 * (low + high)


# ============================================================
# 4) Convenience wrapper — returns secondary temps for a given
#    heat-sink temperature (used by solver.py in the sweep loop)
# ============================================================

def cond_secondary_temps_at(T_heatsink_C):
    """
    Return (T_sec_in_K, T_sec_out_K) for the condenser secondary fluid
    at a given heat-sink temperature, based on cfg.COND_SECONDARY.

    "water" → T_sec_in  = T_heatsink_C  (water supply temperature)
               T_sec_out = T_sec_in + T_WATER_RISE_K
    "air"   → T_sec_in  = T_heatsink_C  (ambient / inlet air temperature)
               T_sec_out = T_sec_in + T_AIR_COND_RISE_K (default 5 K)

    This is called once per parametric step so that solver.py does
    not need to know which fluid is on the condenser side.
    """
    sec = cfg.COND_SECONDARY.lower()

    T_in_K = c_to_k(T_heatsink_C)

    if sec == "water":
        T_out_K = c_to_k(T_heatsink_C + cfg.T_WATER_RISE_K)
        return T_in_K, T_out_K

    if sec == "air":
        T_air_rise = getattr(cfg, "T_AIR_COND_RISE_K", 5.0)
        T_out_K    = c_to_k(T_heatsink_C + T_air_rise)
        return T_in_K, T_out_K

    raise ValueError(
        f"Unknown COND_SECONDARY='{cfg.COND_SECONDARY}'. "
        "Use 'water' or 'air'."
    )
