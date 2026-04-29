# ============================================================
# CONFIGURATION FILE
# Refrigeration Cycle Model
# ============================================================
"""
HOW TO USE THIS FILE
====================
This file is the ONLY file you need to edit to run a different project.

Steps:
  1. Find the block labelled "ACTIVE PROJECT SETTINGS" below.
  2. Comment out the current active project block.
  3. Uncomment (or fill in) the block for your project.
  4. Adjust compressor data (sections 7-11) to match your chosen compressor.
  5. Run main.py or run_project.ipynb as usual.

Sections that are project-specific and must be changed:
  - Section 0  : Student / project identity
  - Section 1  : Refrigerant
  - Section 2  : Nominal cooling capacity
  - Section 3  : Evaporator secondary fluid
  - Section 4  : Condenser secondary fluid
  - Section 7  : Compressor metadata
  - Section 8  : Swept volume
  - Section 9  : Operating limits
  - Section 11 : Nominal compressor map point

Sections that usually stay the same:
  - Section 5  : Cycle assumptions (superheat / subcooling)
  - Section 6  : Initial KA values  ← solver recomputes these anyway
  - Section 10 : Numerical solver settings
  - Section 12 : Plotting style
  - Section 13 : Parametric study range
  - Section 14 : Reference case temperature
  - Section 15 : High-PR analysis
  - Section 16 : Output file name
"""

# ============================================================
# >>>  ACTIVE PROJECT SETTINGS  <<<
# ============================================================
# Only ONE project block should be active at a time.
# To switch projects: comment out the active block and
# uncomment the one you want (or paste your own values).
# ============================================================

# ------------------------------------------------------------
# PROJECT: Amirhossein Naeejnezhad
# Application : Cooling data center
# Nominal Q   : 50 kW
# Evap side   : air in the room at 12 °C
# Cond side   : water
# Compressor  : Bitzer GSU60182VL_4 (ORBIT+, R32)
# ------------------------------------------------------------
STUDENT_NAME        = "Amirhossein Naeejnezhad"
APPLICATION         = "Cooling data center"

REF                 = "R32"
Q_NOMINAL_TARGET    = 50.0e3          # [W]

# Evaporator — air side
EVAP_SECONDARY      = "air"           # "air" or "water" or "brine"
T_AIR_IN_C          = 12.0            # [°C]  secondary fluid inlet
T_AIR_OUT_C         = 8.0             # [°C]  secondary fluid outlet

# Condenser — water side
COND_SECONDARY      = "water"         # "air" or "water"
T_WATER_RISE_K      = 5.0             # [K]   temperature rise across condenser

COMPRESSOR_MODEL    = "GSU60182VL_4"
COMPRESSOR_TYPE     = "Single Compressor"
COMPRESSOR_SERIES   = "ORBIT+"
CAPACITY_CONTROL    = "without"

VDOT_SWEPT_50HZ_M3_H = 30.2
MAX_PRESSURE_LP_BAR   = 34.2
MAX_PRESSURE_HP_BAR   = 45.0
MAX_POWER_INPUT_KW    = 16.7

nominal_map_point = {
    "Tevap_C":       5.0,
    "Tcond_C":       35.0,
    "Qe_kW":         53.9,
    "Pc_kW":         9.31,
    "mdot_kg_h":     735.0,
    "discharge_T_C": 73.3,
    "COP":           5.79,
}
# ------------------------------------------------------------
# END Amirhossein Naeejnezhad
# ------------------------------------------------------------


# ============================================================
# >>>  OTHER PROJECT TEMPLATES  <<<
# ============================================================
# To activate one of these:
#   1. Comment out the active block above.
#   2. Uncomment the block you need.
#   3. Fill in compressor data from the Bitzer / Copeland /
#      Frascold selection software for your refrigerant.
# ============================================================

# # ------------------------------------------------------------
# # PROJECT TEMPLATE — fill in your details
# # ------------------------------------------------------------
# STUDENT_NAME        = "Your Name"
# APPLICATION         = "your application"
#
# REF                 = "R410A"         # e.g. R410A, R134a, R32, R290 …
# Q_NOMINAL_TARGET    = 20.0e3          # [W]  nominal cooling capacity
#
# # Evaporator secondary fluid
# EVAP_SECONDARY      = "air"           # "air" | "water" | "brine"
# T_AIR_IN_C          = 12.0            # [°C]  if air-cooled evaporator
# T_AIR_OUT_C         = 7.0             # [°C]  if air-cooled evaporator
# # (for water/brine evaporator use T_BRINE_IN_C / T_BRINE_OUT_C below)
# # T_BRINE_IN_C      = 18.0            # [°C]
# # T_BRINE_OUT_C     = 12.0            # [°C]
#
# # Condenser secondary fluid
# COND_SECONDARY      = "air"           # "air" | "water"
# T_WATER_RISE_K      = 5.0             # [K]   (used for water-cooled condenser)
#
# # Compressor — from manufacturer selection software
# COMPRESSOR_MODEL    = "XXXXX"
# COMPRESSOR_TYPE     = "Single Compressor"
# COMPRESSOR_SERIES   = "XXXXX"
# CAPACITY_CONTROL    = "without"
#
# VDOT_SWEPT_50HZ_M3_H = 0.0           # [m³/h]  from datasheet
# MAX_PRESSURE_LP_BAR   = 0.0           # [bar]
# MAX_PRESSURE_HP_BAR   = 0.0           # [bar]
# MAX_POWER_INPUT_KW    = 0.0           # [kW]
#
# nominal_map_point = {
#     "Tevap_C":       0.0,             # [°C]  nominal evaporating SST
#     "Tcond_C":       35.0,            # [°C]  nominal condensing SDT
#     "Qe_kW":         0.0,             # [kW]  cooling capacity at nominal pt
#     "Pc_kW":         0.0,             # [kW]  compressor power at nominal pt
#     "mdot_kg_h":     0.0,             # [kg/h] refrigerant mass flow
#     "discharge_T_C": 0.0,             # [°C]  discharge gas temperature
#     "COP":           0.0,             # [-]   COP at nominal point
# }
# # ------------------------------------------------------------
# # END template
# # ------------------------------------------------------------


# ============================================================
# DERIVED CONSTANT  (do not edit)
# ============================================================
VDOT_SWEPT_50HZ_M3_S = VDOT_SWEPT_50HZ_M3_H / 3600.0   # [m³/s]


# =========================
# 5) Refrigeration cycle assumptions
# =========================
SUPERHEAT_K  = 6.0   # [K]  superheating at compressor suction
SUBCOOLING_K = 3.0   # [K]  subcooling at condenser outlet


# =========================
# 6) Heat exchanger conductances (initial guesses)
# These are overwritten by the design calculation in the solver.
# =========================
KA_EVAP_INITIAL = 7.5e3   # [W/K]
KA_COND_INITIAL = 9.5e3   # [W/K]


# =========================
# 10) Numerical solver settings
# =========================
MAX_ITER = 100
TOL      = 1e-4
RELAX    = 0.45


# =========================
# 12) Plotting style
# =========================
PLOT_STYLE = {
    "figure.dpi":      150,
    "figure.figsize":  (7.5, 4.8),
    "font.family":     "serif",
    "font.size":       12,
    "axes.titlesize":  14,
    "axes.labelsize":  12,
    "axes.linewidth":  1.2,
    "axes.grid":       True,
    "grid.linestyle":  "--",
    "grid.alpha":      0.4,
    "lines.linewidth": 2.2,
    "lines.markersize": 6,
    "legend.fontsize": 10,
    "legend.frameon":  False,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.size": 5,
    "ytick.major.size": 5,
}


# =========================
# 13) Parametric study settings
# Heat-sink temperature sweep
# =========================
T_HEATSINK_RANGE_C = {
    "start": 20.0,
    "end":   40.0,
    "step":  2.0,
}
# Keep old name as alias so existing code still works
T_WATER_RANGE_C = T_HEATSINK_RANGE_C


# =========================
# 14) Reference case (for detailed states output)
# =========================
REFERENCE_WATER_TEMP_C = 30.0


# =========================
# 15) High pressure-ratio study
# =========================
HIGH_PR_ANALYSIS = {
    "Tevap_fixed_C": 5.0,
    "Tcond_min_C":   30.0,
    "Tcond_max_C":   70.0,
    "num_points":    20,
}


# =========================
# 16) Output settings
# =========================
OUTPUT_CSV_NAME = (
    f"refrigeration_results_{REF}_{STUDENT_NAME.split()[-1]}.csv"
)
