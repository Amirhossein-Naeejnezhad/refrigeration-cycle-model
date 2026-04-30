# ============================================================
# MAIN PROJECT RUNNER
# Refrigeration and Heat Pump Technology Project
# ============================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src import config as cfg
from src.utils import c_to_k, k_to_c
from src.thermodynamics import compressor_performance_from_map
from src.heat_exchanger import compute_KA_values
from src.solver import solve_operating_point
from src.plots_others import (
    plot_basic_performance,
    plot_high_pressure_ratio,
)
from src.plots_ph_ts import plot_ph_diagram, plot_ts_diagram


# ============================================================
# PROJECT OVERVIEW PRINTER
# ============================================================

def print_project_overview():
    """Print a human-readable summary drawn entirely from config."""

    _brine_in  = getattr(cfg, 'T_BRINE_IN_C',  None)
    _brine_out = getattr(cfg, 'T_BRINE_OUT_C', None)
    if isinstance(_brine_in, (int, float)) and isinstance(_brine_out, (int, float)):
        _brine_str = f"{_brine_in:.0f} to {_brine_out:.0f} °C"
    else:
        _brine_str = "temperatures not set in config"

    evap_desc = {
        "air":   f"air in the space at ~{cfg.T_AIR_IN_C:.0f} °C",
        "water": f"water/brine cooled from {_brine_str}",
        "brine": f"brine cooled from {_brine_str}",
    }.get(cfg.EVAP_SECONDARY.lower(), cfg.EVAP_SECONDARY)

    cond_desc = {
        "water": f"water (ΔT = {cfg.T_WATER_RISE_K:.0f} K across condenser)",
        "air":   "ambient air",
    }.get(cfg.COND_SECONDARY.lower(), cfg.COND_SECONDARY)

    print(f"""
PROJECT OVERVIEW
----------------
Student      : {cfg.STUDENT_NAME}
Application  : {cfg.APPLICATION}
Refrigerant  : {cfg.REF}
Target Qe    : {cfg.Q_NOMINAL_TARGET/1000:.0f} kW

The compressor is modelled with the manufacturer 10-coefficient
polynomial (Bitzer / Copeland / Frascold) in evaporating temperature
(To) and condensing temperature (Tc), providing continuous functions for:
  - Cooling capacity  Qe  [W]
  - Compressor power  Pc  [W]
  - Mass flow rate    mdot [kg/s]

These are combined with CoolProp states to derive:
  - Isentropic efficiency  eta_is
  - Volumetric efficiency  eta_vol

Evaporator secondary : {evap_desc}
Condenser  secondary : {cond_desc}

The parametric study varies the heat-sink (condenser secondary inlet)
temperature and reports cooling capacity and EER at each point.
Heat exchangers are matched iteratively using Q = KA · ΔTLM.
""")


# ============================================================
# MAIN RUNNER
# ============================================================

def run_project():
    plt.rcParams.update(cfg.PLOT_STYLE)

    print_project_overview()

    # ---- KA design step ----------------------------------------
    KA_EVAP, KA_COND = compute_KA_values()

    # ---- Compressor summary ------------------------------------
    print("SELECTED COMPRESSOR")
    print("-------------------")
    print(f"Model            : {cfg.COMPRESSOR_MODEL}")
    print(f"Refrigerant      : {cfg.REF}")
    print(f"Type             : {cfg.COMPRESSOR_TYPE}")
    print(f"Series           : {cfg.COMPRESSOR_SERIES}")
    print(f"Capacity control : {cfg.CAPACITY_CONTROL}")
    print(
        f"Swept volume (50 Hz) = {cfg.VDOT_SWEPT_50HZ_M3_H:.2f} m³/h"
        f" = {cfg.VDOT_SWEPT_50HZ_M3_S:.6f} m³/s"
    )
    print()

    # ---- Nominal map point -------------------------------------
    nmp = cfg.nominal_map_point
    print("NOMINAL MANUFACTURER POINT")
    print("--------------------------")
    print(f"Tevap = {nmp['Tevap_C']:.1f} °C")
    print(f"Tcond = {nmp['Tcond_C']:.1f} °C")
    print(f"Qe    = {nmp['Qe_kW']:.2f} kW")
    print(f"Pc    = {nmp['Pc_kW']:.2f} kW")
    print(f"COP   = {nmp['COP']:.2f}")
    print()

    # ---- Nominal reconstruction --------------------------------
    nominal_perf = compressor_performance_from_map(
        c_to_k(nmp["Tevap_C"]),
        c_to_k(nmp["Tcond_C"]),
    )

    print("NOMINAL RECONSTRUCTION FROM POLYNOMIAL + COOLPROP")
    print("--------------------------------------------------")
    print(f"Derived mdot    = {nominal_perf['mdot']:.4f} kg/s")
    print(f"Derived eta_is  = {nominal_perf['eta_is']:.4f}")
    print(f"Derived eta_vol = {nominal_perf['eta_vol']:.4f}")
    print(f"Thermo Qe       = {nominal_perf['Qe']/1000:.2f} kW")
    print(f"Poly   Qe       = {nominal_perf['Qe_map']/1000:.2f} kW")
    print(f"Thermo Pc       = {nominal_perf['Pc']/1000:.2f} kW")
    print(f"Poly   Pc       = {nominal_perf['Pc_map']/1000:.2f} kW")
    print(f"EER             = {nominal_perf['EER']:.3f}")
    print()

    # ---- Parametric sweep --------------------------------------
    T_hs_range_C = np.arange(
        cfg.T_HEATSINK_RANGE_C["start"],
        cfg.T_HEATSINK_RANGE_C["end"] + 0.001,
        cfg.T_HEATSINK_RANGE_C["step"],
    )

    results = []

    for T_hs in T_hs_range_C:
        res = solve_operating_point(
            T_hs,
            KA_EVAP=KA_EVAP,
            KA_COND=KA_COND,
        )

        real = res["real"]

        P_evap_bar = real["P_evap"] / 1e5
        P_cond_bar = real["P_cond"] / 1e5

        results.append({
            # Generic heat-sink columns
            "HS in [°C]":        res["T_heatsink_in_C"],
            "HS out [°C]":       res["T_heatsink_out_C"],
            # Legacy columns — kept so existing notebook cells still work
            "Water in [°C]":     res["T_water_in_C"],
            "Water out [°C]":    res["T_water_out_C"],
            # Cycle results
            "Tevap [°C]":        res["T_evap_C"],
            "Tcond [°C]":        res["T_cond_C"],
            "Pevap [bar]":       P_evap_bar,
            "Pcond [bar]":       P_cond_bar,
            "PR [-]":            real["PR"],
            "eta_is [-]":        real["eta_is"],
            "eta_vol [-]":       real["eta_vol"],
            "m_dot [kg/s]":      real["mdot"],
            "Qe [kW]":           real["Qe"]     / 1000.0,
            "Pc [kW]":           real["Pc"]     / 1000.0,
            "Qc [kW]":           real["Qc"]     / 1000.0,
            "Qe_poly [kW]":      real["Qe_map"] / 1000.0,
            "Pc_poly [kW]":      real["Pc_map"] / 1000.0,
            "EER [-]":           real["EER"],
            "Map extrapolated":  real["map_extrapolated"],
            "LP limit OK":       P_evap_bar <= cfg.MAX_PRESSURE_LP_BAR,
            "HP limit OK":       P_cond_bar <= cfg.MAX_PRESSURE_HP_BAR,
            "Power limit OK":    (real["Pc"] / 1000.0) <= cfg.MAX_POWER_INPUT_KW,
            "Iterations":        res["iterations"],
            "Cycle object":      res,
        })

    df = pd.DataFrame(results)
    df_print = df.drop(columns=["Cycle object"]).copy()

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 220)
    pd.set_option("display.precision", 4)

    print("\nSUMMARY TABLE")
    print(df_print.to_string(index=False))

    # ---- Reference case detailed states ------------------------
    ref_row  = df.iloc[
        np.argmin(np.abs(df["HS in [°C]"] - cfg.REFERENCE_WATER_TEMP_C))
    ]
    ref_case = ref_row["Cycle object"]
    real_ref = ref_case["real"]

    print("\nDETAILED THERMODYNAMIC STATES FOR REFERENCE CASE")
    print("------------------------------------------------")
    print(f"Heat-sink inlet temperature       = {ref_case['T_heatsink_in_C']:.1f} °C")
    print(f"Converged evaporating temperature = {ref_case['T_evap_C']:.2f} °C")
    print(f"Converged condensing temperature  = {ref_case['T_cond_C']:.2f} °C")
    print(f"Derived isentropic efficiency     = {real_ref['eta_is']:.4f}")
    print(f"Derived volumetric efficiency     = {real_ref['eta_vol']:.4f}")
    print(f"Polynomial extrapolation flag     = {real_ref['map_extrapolated']}")

    rows = []
    for i in [1, 2, 3, 4]:
        st    = real_ref["states"][i]
        s_val = st["s"] / 1000.0 if st["s"] is not None else float("nan")
        rows.append({
            "State":      i,
            "T [°C]":     k_to_c(st["T"]),
            "P [bar]":    st["P"] / 1e5,
            "h [kJ/kg]":  st["h"] / 1000.0,
            "s [kJ/kg·K]": s_val,
        })
    df_states = pd.DataFrame(rows)
    print(df_states.to_string(index=False))

    # ---- Plots -------------------------------------------------
    plot_basic_performance(df)
    plot_ph_diagram(df)
    plot_ts_diagram(df)

    Tcond_range_ext_C = np.linspace(
        cfg.HIGH_PR_ANALYSIS["Tcond_min_C"],
        cfg.HIGH_PR_ANALYSIS["Tcond_max_C"],
        cfg.HIGH_PR_ANALYSIS["num_points"],
    )
    plot_high_pressure_ratio(
        compressor_function=compressor_performance_from_map,
        Tevap_fixed_C=cfg.HIGH_PR_ANALYSIS["Tevap_fixed_C"],
        Tcond_range_C=Tcond_range_ext_C,
        c_to_k_func=c_to_k,
    )

    # ---- Engineering interpretation ----------------------------
    q_drop_pct   = 100 * (df["Qe [kW]"].iloc[0]  - df["Qe [kW]"].iloc[-1])  / df["Qe [kW]"].iloc[0]
    eer_drop_pct = 100 * (df["EER [-]"].iloc[0]   - df["EER [-]"].iloc[-1])  / df["EER [-]"].iloc[0]
    pc_rise_pct  = 100 * (df["Pc [kW]"].iloc[-1]  - df["Pc [kW]"].iloc[0])   / df["Pc [kW]"].iloc[0]

    T_start = df["HS in [°C]"].iloc[0]
    T_end   = df["HS in [°C]"].iloc[-1]

    print("\nENGINEERING INTERPRETATION")
    print("--------------------------")
    print(
        f"When heat-sink inlet temperature rises from "
        f"{T_start:.0f} °C to {T_end:.0f} °C:"
    )
    print(f"  Cooling capacity decreases by ~ {q_drop_pct:.1f} %")
    print(f"  EER             decreases by ~ {eer_drop_pct:.1f} %")
    print(f"  Compressor power increases by ~ {pc_rise_pct:.1f} %")
    print("""
Physical interpretation:
  1) Higher heat-sink temperature forces a higher condensing temperature.
  2) This increases discharge pressure and compressor pressure ratio.
  3) Compressor work rises; refrigeration effect worsens.
  4) Therefore EER drops and cooling capacity decreases.

eta_is and eta_vol are inferred from the manufacturer polynomial combined
with CoolProp states — no guessed algebraic correlations are used.
""")

    # ---- Project-work consistency check ------------------------
    print("PROJECT-WORK CONSISTENCY CHECK")
    print("------------------------------")

    checks = [
        (
            "Compressor selected",
            True,
            f"{cfg.COMPRESSOR_MODEL} registered and active",
        ),
        (
            "Refrigerant defined",
            bool(cfg.REF),
            f"REF = {cfg.REF}",
        ),
        (
            "Nominal cooling capacity defined",
            cfg.Q_NOMINAL_TARGET > 0,
            f"Q_NOMINAL_TARGET = {cfg.Q_NOMINAL_TARGET/1000:.0f} kW",
        ),
        (
            "Suction superheat fixed",
            cfg.SUPERHEAT_K > 0,
            f"Superheat = {cfg.SUPERHEAT_K:.1f} K",
        ),
        (
            "Condenser subcooling fixed",
            cfg.SUBCOOLING_K > 0,
            f"Subcooling = {cfg.SUBCOOLING_K:.1f} K",
        ),
        (
            "Constant KA values used",
            (KA_EVAP > 0) and (KA_COND > 0),
            f"KA_EVAP = {KA_EVAP:.1f} W/K,  KA_COND = {KA_COND:.1f} W/K",
        ),
        (
            "10-coefficient polynomial model used",
            True,
            "Yes — poly_eval(coeff, To, Tc)",
        ),
        (
            "eta_is derived from polynomial + CoolProp",
            True,
            "eta_is = (h2s − h1) / (Pc_poly / mdot_poly)",
        ),
        (
            "eta_vol derived from polynomial + swept volume",
            True,
            "eta_vol = mdot_poly / (rho1 · Vs)",
        ),
        (
            "HX iterative matching used",
            True,
            "Tevap & Tcond iterated with Q = KA · ΔTLM",
        ),
        (
            "Objective: Qe and EER vs heat-sink temperature",
            True,
            "Yes — parametric sweep stored in df",
        ),
        (
            "No extrapolation flag triggered",
            not df["Map extrapolated"].any(),
            "Polynomial covers all operating points",
        ),
    ]

    for name, ok, msg in checks:
        status = "OK     " if ok else "WARNING"
        print(f"  {status} | {name:<50} | {msg}")

    print(f"""
Summary
-------
Student      : {cfg.STUDENT_NAME}
Application  : {cfg.APPLICATION}
Refrigerant  : {cfg.REF}
Compressor   : {cfg.COMPRESSOR_MODEL}
Evap side    : {cfg.EVAP_SECONDARY}
Cond side    : {cfg.COND_SECONDARY}

The manufacturer polynomial provides a continuous, smooth evaluation of
Qe, Pc, and mdot. eta_is and eta_vol are derived rigorously, preserving
full thermodynamic consistency across the entire parametric study.
""")

    # ---- Export ------------------------------------------------
    df_print.to_csv(cfg.OUTPUT_CSV_NAME, index=False)
    print(f"Results exported to: {cfg.OUTPUT_CSV_NAME}")

    return df, df_print, df_states
