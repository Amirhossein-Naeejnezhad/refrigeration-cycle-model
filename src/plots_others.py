# ============================================================
# GENERAL PLOTS MODULE
# All standard performance and analysis plots
# ============================================================
"""
This module contains all plots EXCEPT P-h and T-s diagrams.

  1) Standard performance plots  (EER, Qe, Pc, temperatures, PR, eta)
  2) High pressure-ratio exploration
"""

import numpy as np
import matplotlib.pyplot as plt

from src import config as cfg
from src.utils import make_plot


# ============================================================
# INTERNAL HELPER — x-axis column and label
# ============================================================

def _hs_col(df):
    """
    Return the heat-sink inlet temperature column name present in df.
    Prefers the generic 'HS in [°C]'; falls back to legacy 'Water in [°C]'.
    """
    if "HS in [°C]" in df.columns:
        return "HS in [°C]"
    return "Water in [°C]"


def _hs_label():
    """
    Return a human-readable x-axis label based on COND_SECONDARY.
    """
    sec = cfg.COND_SECONDARY.lower()
    if sec == "water":
        return "Condenser water inlet temperature [°C]"
    if sec == "air":
        return "Ambient / condenser air inlet temperature [°C]"
    return "Heat-sink inlet temperature [°C]"


# ============================================================
# 1) Standard performance plots
# ============================================================

def plot_basic_performance(df):
    """
    Generate the six standard performance plots for the parametric study.

    All x-axis labels and column references are derived from config so
    the same function works for water-cooled and air-cooled condensers.
    """
    x_col   = _hs_col(df)
    x_label = _hs_label()
    x       = df[x_col]

    make_plot(
        x,
        [df["EER [-]"]],
        ["EER"],
        x_label,
        "EER [-]",
        f"Energy Efficiency Ratio vs Heat-Sink Temperature\n"
        f"{cfg.STUDENT_NAME} — {cfg.APPLICATION} — {cfg.REF}",
    )

    make_plot(
        x,
        [df["Qe [kW]"]],
        ["Cooling capacity"],
        x_label,
        "Cooling capacity [kW]",
        f"Cooling Capacity vs Heat-Sink Temperature\n"
        f"{cfg.STUDENT_NAME} — {cfg.APPLICATION} — {cfg.REF}",
    )

    make_plot(
        x,
        [df["Pc [kW]"]],
        ["Compressor power"],
        x_label,
        "Power [kW]",
        f"Compressor Power vs Heat-Sink Temperature\n"
        f"{cfg.STUDENT_NAME} — {cfg.APPLICATION} — {cfg.REF}",
    )

    make_plot(
        x,
        [df["Tevap [°C]"], df["Tcond [°C]"]],
        ["Evaporating temperature", "Condensing temperature"],
        x_label,
        "Temperature [°C]",
        f"Cycle Temperatures vs Heat-Sink Temperature\n"
        f"{cfg.STUDENT_NAME} — {cfg.APPLICATION} — {cfg.REF}",
    )

    make_plot(
        x,
        [df["PR [-]"]],
        ["Pressure ratio"],
        x_label,
        "PR [-]",
        f"Pressure Ratio vs Heat-Sink Temperature\n"
        f"{cfg.STUDENT_NAME} — {cfg.APPLICATION} — {cfg.REF}",
    )

    make_plot(
        x,
        [df["eta_is [-]"], df["eta_vol [-]"]],
        ["Isentropic efficiency", "Volumetric efficiency"],
        x_label,
        "Efficiency [-]",
        f"Compressor Efficiencies vs Operating Conditions\n"
        f"{cfg.STUDENT_NAME} — {cfg.APPLICATION} — {cfg.REF}",
    )


# ============================================================
# 2) High pressure-ratio exploration
# ============================================================

def plot_high_pressure_ratio(
    compressor_function,
    Tevap_fixed_C,
    Tcond_range_C,
    c_to_k_func,
):
    """
    Explore compressor efficiency behaviour at high pressure ratios.

    Parameters
    ----------
    compressor_function : callable
        compressor_performance_from_map(T_evap_K, T_cond_K)
    Tevap_fixed_C : float — fixed evaporating temperature [°C]
    Tcond_range_C : array-like — condensing temperatures to sweep [°C]
    c_to_k_func   : callable — temperature conversion utility
    """
    print("\nHIGH PRESSURE RATIO EXPLORATION (QUALITATIVE)")
    print("----------------------------------------------")

    eta_is_ext  = []
    eta_vol_ext = []
    PR_ext      = []

    for Tc in Tcond_range_C:
        try:
            perf = compressor_function(
                c_to_k_func(Tevap_fixed_C),
                c_to_k_func(Tc),
            )
            eta_is_ext.append(perf["eta_is"])
            eta_vol_ext.append(perf["eta_vol"])
            PR_ext.append(perf["PR"])
        except Exception:
            eta_is_ext.append(np.nan)
            eta_vol_ext.append(np.nan)
            PR_ext.append(np.nan)

    eta_is_ext  = np.array(eta_is_ext)
    eta_vol_ext = np.array(eta_vol_ext)
    PR_ext      = np.array(PR_ext)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(PR_ext, eta_is_ext,  marker="o", label=r"$\eta_{is}$")
    ax.plot(PR_ext, eta_vol_ext, marker="s", label=r"$\eta_{vol}$")
    ax.set_xlabel("Pressure ratio [-]")
    ax.set_ylabel("Efficiency [-]")
    ax.set_title(
        f"Compressor efficiency vs pressure ratio\n"
        f"{cfg.COMPRESSOR_MODEL} — {cfg.REF} — "
        f"$T_{{evap}}$ = {Tevap_fixed_C:.0f} °C (extrapolated range)"
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend()
    plt.tight_layout()
    plt.show()
