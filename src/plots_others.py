# ============================================================
# GENERAL PLOTS MODULE
# All standard performance and analysis plots
# ============================================================

"""
This module contains all plots EXCEPT P-h and T-s diagrams.

Includes:
- Performance plots (EER, Qe, Pc)
- Temperature plots
- Pressure ratio
- Efficiencies
- Polynomial consistency comparison
- High pressure ratio extrapolation study
"""

import numpy as np
import matplotlib.pyplot as plt

from src.utils import make_plot
from src.config import REF


# =========================
# 1) Standard performance plots
# =========================
def plot_basic_performance(df):
    """
    Generate standard performance plots.
    """

    make_plot(
        df["Water in [°C]"],
        [df["EER [-]"]],
        ["EER"],
        "Condenser water inlet temperature [°C]",
        "EER [-]",
        "Energy Efficiency Ratio vs Condenser Water Temperature"
    )

    make_plot(
        df["Water in [°C]"],
        [df["Qe [kW]"]],
        ["Cooling capacity"],
        "Condenser water inlet temperature [°C]",
        "Cooling capacity [kW]",
        "Cooling Capacity vs Condenser Water Temperature"
    )

    make_plot(
        df["Water in [°C]"],
        [df["Pc [kW]"]],
        ["Compressor power"],
        "Condenser water inlet temperature [°C]",
        "Power [kW]",
        "Compressor Power vs Condenser Water Temperature"
    )

    make_plot(
        df["Water in [°C]"],
        [df["Tevap [°C]"], df["Tcond [°C]"]],
        ["Evaporating temperature", "Condensing temperature"],
        "Condenser water inlet temperature [°C]",
        "Temperature [°C]",
        "Cycle Temperatures vs Condenser Water Temperature"
    )

    make_plot(
        df["Water in [°C]"],
        [df["PR [-]"]],
        ["Pressure ratio"],
        "Condenser water inlet temperature [°C]",
        "PR [-]",
        "Pressure Ratio vs Condenser Water Temperature"
    )

    make_plot(
        df["Water in [°C]"],
        [df["eta_is [-]"], df["eta_vol [-]"]],
        ["Isentropic efficiency", "Volumetric efficiency"],
        "Condenser water inlet temperature [°C]",
        "Efficiency [-]",
        "Compressor Efficiencies vs Operating Conditions"
    )


# =========================
# 2) High pressure ratio exploration
# =========================
def plot_high_pressure_ratio(
    compressor_function,
    Tevap_fixed_C,
    Tcond_range_C,
    c_to_k_func
):
    """
    Explore compressor efficiency behavior at high pressure ratios.
    """

    print("\nHIGH PRESSURE RATIO EXPLORATION (QUALITATIVE)")
    print("---------------------------------------------")

    eta_is_ext = []
    eta_vol_ext = []
    PR_ext = []

    for Tc in Tcond_range_C:
        try:
            perf = compressor_function(
                c_to_k_func(Tevap_fixed_C),
                c_to_k_func(Tc)
            )

            eta_is_ext.append(perf["eta_is"])
            eta_vol_ext.append(perf["eta_vol"])
            PR_ext.append(perf["PR"])

        except:
            eta_is_ext.append(np.nan)
            eta_vol_ext.append(np.nan)
            PR_ext.append(np.nan)

    eta_is_ext = np.array(eta_is_ext)
    eta_vol_ext = np.array(eta_vol_ext)
    PR_ext = np.array(PR_ext)

    fig, ax = plt.subplots(figsize=(7, 4.5))

    ax.plot(PR_ext, eta_is_ext, marker="o", label="eta_is (extrapolated)")
    ax.plot(PR_ext, eta_vol_ext, marker="s", label="eta_vol (extrapolated)")

    ax.set_xlabel("Pressure ratio [-]")
    ax.set_ylabel("Efficiency [-]")
    ax.set_title("Compressor efficiency vs pressure ratio (extrapolated)")
    ax.legend()

    plt.tight_layout()
    plt.show()
