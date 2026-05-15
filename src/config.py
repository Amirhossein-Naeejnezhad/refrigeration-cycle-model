"""Project configuration for the refrigeration-cycle model.

Only this file and ``compressor.py`` should normally be edited for a new
student case. The active case below is Amirhossein Naeejnezhad's assigned
project: data-center cooling, 50 kW nominal target, air-side evaporator,
water-cooled condenser.
"""

# =============================================================================
# 1) Project identity and assignment
# =============================================================================
STUDENT_NAME = "Amirhossein Naeejnezhad"
APPLICATION = "Cooling data center"
ASSIGNED_ROOM_AIR_TEMP_C = 12.0          # [°C] assignment condition
Q_NOMINAL_TARGET = 50.0e3                # [W] assignment target

# =============================================================================
# 2) Refrigerant and compressor
# =============================================================================
REF = "R32"
COMPRESSOR_MODEL = "GSU60182VL_4"
COMPRESSOR_TYPE = "Single Compressor"
COMPRESSOR_SERIES = "ORBIT+"
CAPACITY_CONTROL = "without"

VDOT_SWEPT_50HZ_M3_H = 30.2              # [m³/h]
VDOT_SWEPT_50HZ_M3_S = VDOT_SWEPT_50HZ_M3_H / 3600.0

MAX_PRESSURE_LP_BAR = 34.2
MAX_PRESSURE_HP_BAR = 45.0
MAX_POWER_INPUT_KW = 16.7

# Manufacturer/check point used to validate the polynomial model.
# This compressor is the closest available R32 Bitzer scroll option to the
# 50 kW assignment target at the selected nominal operating point.
nominal_map_point = {
    "Tevap_C": 2.0,
    "Tcond_C": 37.5,
    "Qe_kW": 47.7,
    "Pc_kW": 9.69,
    "mdot_kg_h": 664.0,
    "discharge_T_C": 80.3,
    "COP": 4.92,
}

# Conservative operating envelope used only to flag suspicious polynomial use.
# It is not a replacement for the official manufacturer validity limits.
MAP_CHECK_LIMITS = {
    "Tevap_C_min": -10.0,
    "Tevap_C_max": 15.0,
    "Tcond_C_min": 25.0,
    "Tcond_C_max": 65.0,
}

# =============================================================================
# 3) Secondary fluids and cycle assumptions
# =============================================================================
EVAP_SECONDARY = "air"                   # "air", "water", or "brine"
COND_SECONDARY = "water"                 # "water" or "air"

# Data-center interpretation:
# the assigned 12 °C room/air condition is treated as the cold supply-air
# condition; a 24 °C return-air temperature is assumed to close the evaporator
# energy balance and calculate the air mass flow rate.
T_AIR_IN_C = 24.0                         # [°C] evaporator air inlet / return air
T_AIR_OUT_C = ASSIGNED_ROOM_AIR_TEMP_C     # [°C] evaporator air outlet / supply air
T_WATER_RISE_K = 5.0                       # [K] condenser-water temperature rise

SUPERHEAT_K = 6.0                          # [K] compressor-suction superheat
SUBCOOLING_K = 3.0                         # [K] condenser-outlet subcooling

CP_AIR_J_KG_K = 1005.0
CP_WATER_J_KG_K = 4180.0

# =============================================================================
# 4) Heat-exchanger design assumptions
# =============================================================================
APPROACH_EVAP_AIR_K = 10.0
APPROACH_EVAP_WATER_K = 5.0
APPROACH_COND_WATER_K = 5.0
APPROACH_COND_AIR_K = 15.0

# Initial values are only fallbacks. The design step recomputes KA values from
# the nominal point and then keeps them constant during the sweep.
KA_EVAP_INITIAL = 7.5e3                    # [W/K]
KA_COND_INITIAL = 9.5e3                    # [W/K]

# =============================================================================
# 5) Solver, sweep, plotting, and output
# =============================================================================
MAX_ITER = 100
TOL = 1e-4
RELAX = 0.45

T_HEATSINK_RANGE_C = {
    "start": 20.0,
    "end": 40.0,
    "step": 2.0,
}
T_WATER_RANGE_C = T_HEATSINK_RANGE_C       # backward-compatible alias
REFERENCE_HEATSINK_TEMP_C = 30.0
REFERENCE_WATER_TEMP_C = REFERENCE_HEATSINK_TEMP_C

HIGH_PR_ANALYSIS = {
    "Tevap_fixed_C": nominal_map_point["Tevap_C"],
    "Tcond_min_C": 30.0,
    "Tcond_max_C": 70.0,
    "num_points": 20,
}

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

OUTPUT_CSV_NAME = f"refrigeration_results_{REF}_{STUDENT_NAME.split()[-1]}.csv"
