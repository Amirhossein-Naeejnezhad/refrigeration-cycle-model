# ============================================================
# CONFIGURATION FILE
# Refrigeration Cycle Model - R32
# Author: Amirhossein Naeejnezhad
# ============================================================

"""
This file contains ALL global constants, assumptions, and settings
used across the project.

Nothing here should contain logic — only parameters.
"""

# =========================
# 1) Refrigerant
# =========================
REF = "R32"

# =========================
# 2) Project target
# =========================
Q_NOMINAL_TARGET = 50.0e3   # [W]

# =========================
# 3) Evaporator (air side)
# =========================
T_AIR_IN_C  = 12.0   # [°C]
T_AIR_OUT_C = 8.0    # [°C]

# =========================
# 4) Condenser (water side)
# =========================
T_WATER_RISE_K = 5.0   # [K]

# =========================
# 5) Refrigeration cycle assumptions
# =========================
SUPERHEAT_K = 6.0   # [K] (from compressor data)
SUBCOOLING_K = 3.0  # [K] (from compressor data)

# =========================
# 6) Heat exchanger conductances (initial values)
# These will be overwritten by design calculation
# =========================
KA_EVAP_INITIAL = 7.5e3   # [W/K]
KA_COND_INITIAL = 9.5e3   # [W/K]

# =========================
# 7) Compressor metadata
# =========================
COMPRESSOR_MODEL  = "GSU60182VL_4"
COMPRESSOR_TYPE   = "Single Compressor"
COMPRESSOR_SERIES = "ORBIT+"
CAPACITY_CONTROL  = "without"

# =========================
# 8) Swept volume
# =========================
VDOT_SWEPT_50HZ_M3_H = 30.2
VDOT_SWEPT_50HZ_M3_S = VDOT_SWEPT_50HZ_M3_H / 3600.0

# =========================
# 9) Operating limits
# =========================
MAX_PRESSURE_LP_BAR = 34.2
MAX_PRESSURE_HP_BAR = 45.0
MAX_POWER_INPUT_KW  = 16.7

# =========================
# 10) Numerical solver settings
# =========================
MAX_ITER = 100
TOL      = 1e-4
RELAX    = 0.45

# =========================
# 11) Nominal compressor map point
# =========================
nominal_map_point = {
    "Tevap_C":        5.0,
    "Tcond_C":        35.0,
    "Qe_kW":          53.9,
    "Pc_kW":          9.31,
    "mdot_kg_h":      735.0,
    "discharge_T_C":  73.3,
    "COP":            5.79
}

# =========================
# 12) Plotting style
# (Applied globally in main or notebook)
# =========================
PLOT_STYLE = {
    "figure.dpi": 150,
    "figure.figsize": (7.5, 4.8),

    "font.family": "serif",
    "font.size": 12,

    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "axes.linewidth": 1.2,

    "axes.grid": True,
    "grid.linestyle": "--",
    "grid.alpha": 0.4,

    "lines.linewidth": 2.2,
    "lines.markersize": 6,

    "legend.fontsize": 10,
    "legend.frameon": False,

    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.size": 5,
    "ytick.major.size": 5,
}

# =========================
# 13) Parametric study settings
# =========================
T_WATER_RANGE_C = {
    "start": 20.0,
    "end":   40.0,
    "step":  2.0
}

# =========================
# 14) Reference case (for detailed states)
# =========================
REFERENCE_WATER_TEMP_C = 30.0

# =========================
# 15) High pressure ratio study
# =========================
HIGH_PR_ANALYSIS = {
    "Tevap_fixed_C": 5.0,
    "Tcond_min_C":   30.0,
    "Tcond_max_C":   70.0,
    "num_points":    20
}

# =========================
# 16) Output settings
# =========================
OUTPUT_CSV_NAME = "refrigeration_project_results_R32_polynomial_model.csv"
