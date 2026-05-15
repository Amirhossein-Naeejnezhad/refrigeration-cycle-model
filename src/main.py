"""Top-level project runner."""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src import config as cfg
from src.heat_exchanger import compute_KA_values
from src.plots_others import plot_basic_performance, plot_high_pressure_ratio
from src.plots_ph_ts import plot_ph_diagram, plot_ts_diagram
from src.solver import solve_operating_point
from src.thermodynamics import compressor_performance_from_map
from src.utils import c_to_k, k_to_c


def _mdot_from_duty(q_w: float, cp: float, delta_t: float) -> float:
    """Return secondary-fluid mass flow rate [kg/s] from Q = m*cp*dT."""
    return np.nan if cp <= 0 or delta_t <= 0 else q_w / (cp * delta_t)


def evaporator_secondary_mdot(qe_w: float) -> float:
    """Estimate evaporator secondary-fluid mass flow rate [kg/s]."""
    sec = cfg.EVAP_SECONDARY.lower()
    if sec == "air":
        return _mdot_from_duty(qe_w, cfg.CP_AIR_J_KG_K, cfg.T_AIR_IN_C - cfg.T_AIR_OUT_C)
    if sec in {"water", "brine"}:
        return _mdot_from_duty(qe_w, cfg.CP_WATER_J_KG_K, cfg.T_BRINE_IN_C - cfg.T_BRINE_OUT_C)
    return np.nan


def condenser_secondary_mdot(qc_w: float, t_in_c: float, t_out_c: float) -> float:
    """Estimate condenser secondary-fluid mass flow rate [kg/s]."""
    cp = cfg.CP_WATER_J_KG_K if cfg.COND_SECONDARY.lower() == "water" else cfg.CP_AIR_J_KG_K
    return _mdot_from_duty(qc_w, cp, t_out_c - t_in_c)


def print_project_overview() -> None:
    """Print the assumptions that must also be stated in the report."""
    print(f"""
PROJECT OVERVIEW
----------------
Student      : {cfg.STUDENT_NAME}
Application  : {cfg.APPLICATION}
Assignment   : {cfg.Q_NOMINAL_TARGET/1000:.0f} kW, air condition {cfg.ASSIGNED_ROOM_AIR_TEMP_C:.0f} °C, water-cooled condenser
Refrigerant  : {cfg.REF}
Compressor   : {cfg.COMPRESSOR_MODEL} ({cfg.COMPRESSOR_SERIES})

Evaporator interpretation:
  Assigned air condition = {cfg.ASSIGNED_ROOM_AIR_TEMP_C:.0f} °C.
  Modelled as data-center supply air at {cfg.T_AIR_OUT_C:.0f} °C with assumed return air at {cfg.T_AIR_IN_C:.0f} °C.
  This closes the air-side energy balance and gives the required evaporator air mass flow rate.

Cycle assumptions:
  Superheat = {cfg.SUPERHEAT_K:.1f} K, subcooling = {cfg.SUBCOOLING_K:.1f} K.
  KA_EVAP and KA_COND are calculated at the nominal point and then held constant.
""")


def nominal_validation_table() -> pd.DataFrame:
    """Compare manufacturer nominal values with the polynomial/CoolProp reconstruction."""
    nmp = cfg.nominal_map_point
    perf = compressor_performance_from_map(c_to_k(nmp["Tevap_C"]), c_to_k(nmp["Tcond_C"]))
    rows = [
        ("Qe [kW]", nmp["Qe_kW"], perf["Qe_map"] / 1000, perf["Qe"] / 1000),
        ("Pc [kW]", nmp["Pc_kW"], perf["Pc_map"] / 1000, perf["Pc"] / 1000),
        ("mdot [kg/h]", nmp["mdot_kg_h"], perf["mdot"] * 3600, perf["mdot"] * 3600),
        ("EER/COP [-]", nmp["COP"], perf["Qe_map"] / perf["Pc_map"], perf["EER"]),
    ]
    return pd.DataFrame(rows, columns=["Quantity", "Manufacturer", "Polynomial", "Thermo reconstruction"])


def run_project():
    """Run the full project workflow and return result tables."""
    plt.rcParams.update(cfg.PLOT_STYLE)
    print_project_overview()

    ka_evap, ka_cond = compute_KA_values()

    validation = nominal_validation_table()
    print("NOMINAL COMPRESSOR VALIDATION")
    print("-----------------------------")
    print(validation.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    heat_sink_values = np.arange(
        cfg.T_HEATSINK_RANGE_C["start"],
        cfg.T_HEATSINK_RANGE_C["end"] + 0.001,
        cfg.T_HEATSINK_RANGE_C["step"],
    )

    records = []
    for t_hs in heat_sink_values:
        point = solve_operating_point(t_hs, KA_EVAP=ka_evap, KA_COND=ka_cond)
        real = point["real"]
        p_evap_bar = real["P_evap"] / 1e5
        p_cond_bar = real["P_cond"] / 1e5

        records.append({
            "HS in [°C]": point["T_heatsink_in_C"],
            "HS out [°C]": point["T_heatsink_out_C"],
            "Tevap [°C]": point["T_evap_C"],
            "Tcond [°C]": point["T_cond_C"],
            "Pevap [bar]": p_evap_bar,
            "Pcond [bar]": p_cond_bar,
            "PR [-]": real["PR"],
            "eta_is [-]": real["eta_is"],
            "eta_vol [-]": real["eta_vol"],
            "m_dot_ref [kg/s]": real["mdot"],
            "m_dot_evap_sec [kg/s]": evaporator_secondary_mdot(real["Qe"]),
            "m_dot_cond_sec [kg/s]": condenser_secondary_mdot(real["Qc"], point["T_heatsink_in_C"], point["T_heatsink_out_C"]),
            "Qe [kW]": real["Qe"] / 1000,
            "Pc [kW]": real["Pc"] / 1000,
            "Qc [kW]": real["Qc"] / 1000,
            "Qe_poly [kW]": real["Qe_map"] / 1000,
            "Pc_poly [kW]": real["Pc_map"] / 1000,
            "EER [-]": real["EER"],
            "Map outside check range": real["map_extrapolated"],
            "LP limit OK": p_evap_bar <= cfg.MAX_PRESSURE_LP_BAR,
            "HP limit OK": p_cond_bar <= cfg.MAX_PRESSURE_HP_BAR,
            "Power limit OK": (real["Pc"] / 1000) <= cfg.MAX_POWER_INPUT_KW,
            "Iterations": point["iterations"],
            "Cycle object": point,
        })

    df = pd.DataFrame(records)
    df_print = df.drop(columns=["Cycle object"])

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 220)
    pd.set_option("display.precision", 4)

    print("\nPARAMETRIC STUDY RESULTS")
    print("------------------------")
    print(df_print.to_string(index=False))

    ref_idx = np.argmin(np.abs(df["HS in [°C]"] - cfg.REFERENCE_HEATSINK_TEMP_C))
    ref_case = df.iloc[ref_idx]["Cycle object"]
    ref_real = ref_case["real"]

    states = []
    for i in [1, 2, 3, 4]:
        st = ref_real["states"][i]
        states.append({
            "State": i,
            "T [°C]": k_to_c(st["T"]),
            "P [bar]": st["P"] / 1e5,
            "h [kJ/kg]": st["h"] / 1000,
            "s [kJ/kgK]": np.nan if st["s"] is None else st["s"] / 1000,
        })
    df_states = pd.DataFrame(states)

    print("\nREFERENCE-CASE STATES")
    print("---------------------")
    print(f"Heat-sink inlet = {ref_case['T_heatsink_in_C']:.1f} °C")
    print(df_states.to_string(index=False))

    plot_basic_performance(df)
    plot_ph_diagram(df)
    plot_ts_diagram(df)
    plot_high_pressure_ratio(
        compressor_function=compressor_performance_from_map,
        Tevap_fixed_C=cfg.HIGH_PR_ANALYSIS["Tevap_fixed_C"],
        Tcond_range_C=np.linspace(
            cfg.HIGH_PR_ANALYSIS["Tcond_min_C"],
            cfg.HIGH_PR_ANALYSIS["Tcond_max_C"],
            cfg.HIGH_PR_ANALYSIS["num_points"],
        ),
        c_to_k_func=c_to_k,
    )

    q_drop = 100 * (df["Qe [kW]"].iloc[0] - df["Qe [kW]"].iloc[-1]) / df["Qe [kW]"].iloc[0]
    eer_drop = 100 * (df["EER [-]"].iloc[0] - df["EER [-]"].iloc[-1]) / df["EER [-]"].iloc[0]
    pc_rise = 100 * (df["Pc [kW]"].iloc[-1] - df["Pc [kW]"].iloc[0]) / df["Pc [kW]"].iloc[0]

    print("\nENGINEERING INTERPRETATION")
    print("--------------------------")
    print(
        f"From {df['HS in [°C]'].iloc[0]:.0f} °C to {df['HS in [°C]'].iloc[-1]:.0f} °C heat-sink inlet temperature:"
    )
    print(f"  Cooling capacity change : -{q_drop:.1f} %")
    print(f"  EER change              : -{eer_drop:.1f} %")
    print(f"  Compressor power change : +{pc_rise:.1f} %")
    print("Higher heat-sink temperature raises Tcond and pressure ratio, increasing compressor work and reducing EER.")

    if df["Map outside check range"].any():
        print("\nWARNING: at least one point is outside the configured polynomial-check envelope.")
    if not (df["LP limit OK"].all() and df["HP limit OK"].all() and df["Power limit OK"].all()):
        print("\nWARNING: at least one compressor pressure/power limit check failed.")

    df_print.to_csv(cfg.OUTPUT_CSV_NAME, index=False)
    print(f"\nResults exported to: {cfg.OUTPUT_CSV_NAME}")
    return df, df_print, df_states, validation
