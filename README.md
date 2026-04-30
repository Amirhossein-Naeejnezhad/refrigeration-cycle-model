# Refrigeration Cycle Model
### Refrigeration and Heat Pump Technology — Project Work
**University of Padova — Refrigeration Engineering**

---

## What this repository does

This tool models a **vapour-compression refrigeration cycle** and studies how
**cooling capacity (Qe)** and **EER** change as the heat-sink temperature varies.

It is the base implementation for the course project work. The `universal-model`
branch supports **any student project** from the assignment list — you only need
to edit one file to run your own project.

The model uses:
- A **10-coefficient manufacturer polynomial** (Bitzer / Copeland / Frascold)
  for compressor performance (Qe, Pc, ṁ)
- **CoolProp** for all thermodynamic state calculations
- **LMTD-based heat exchanger matching** with iterative convergence
- Supports **air or water/brine** on both evaporator and condenser sides

---

## Quickstart (Google Colab or Jupyter)

```python
# 1. Clone the universal-model branch
!git clone --branch universal-model \
    https://github.com/Amirhossein-Naeejnezhad/refrigeration-cycle-model.git
%cd refrigeration-cycle-model

# 2. Install dependencies
!pip install -r requirements.txt

# 3. Run
from src.main import run_project
df, df_print, df_states = run_project()
```

Or open and run **`run_project.ipynb`** directly.

---

## How to run your own project

You need to edit **two files only**.

### Step 1 — `src/config.py`

Find the `ACTIVE PROJECT SETTINGS` block. Comment out the current active
project and fill in your own values:

```python
STUDENT_NAME        = "Your Name"
APPLICATION         = "your application"

REF                 = "R410A"         # refrigerant
Q_NOMINAL_TARGET    = 20.0e3          # [W]

EVAP_SECONDARY      = "air"           # "air" | "water" | "brine"
T_AIR_IN_C          = 12.0            # evaporator air inlet  [°C]
T_AIR_OUT_C         = 7.0             # evaporator air outlet [°C]

COND_SECONDARY      = "water"         # "air" | "water"
T_WATER_RISE_K      = 5.0             # condenser water ΔT   [K]

COMPRESSOR_MODEL    = "YOUR_MODEL"
VDOT_SWEPT_50HZ_M3_H = 0.0           # from datasheet
MAX_PRESSURE_LP_BAR  = 0.0
MAX_PRESSURE_HP_BAR  = 0.0
MAX_POWER_INPUT_KW   = 0.0

nominal_map_point = {
    "Tevap_C": 0.0, "Tcond_C": 35.0,
    "Qe_kW": 0.0,   "Pc_kW": 0.0,
    "mdot_kg_h": 0.0, "discharge_T_C": 0.0, "COP": 0.0,
}
```

For **water/brine evaporators** (e.g. water chillers) add instead:

```python
EVAP_SECONDARY  = "water"
T_BRINE_IN_C    = 18.0
T_BRINE_OUT_C   = 12.0
```

### Step 2 — `src/compressor.py`

Add one entry to `COMPRESSOR_REGISTRY` using your 10 polynomial coefficients
from the manufacturer selection software (Bitzer websoftware, Copeland Select,
or Frascold Select):

```python
"YOUR_MODEL": {
    "info": {
        "manufacturer": "Bitzer",
        "series":        "ORBIT+",
        "refrigerant":   "R410A",
        "student":       "Your Name",
    },
    "Q": [C0, C1, C2, C3, C4, C5, C6, C7, C8, C9],   # [W]
    "P": [C0, C1, C2, C3, C4, C5, C6, C7, C8, C9],   # [W]
    "M": [C0, C1, C2, C3, C4, C5, C6, C7, C8, C9],   # [kg/h]
},
```

The coefficient order follows the standard ARI-540 form:

```
C0 + C1·To + C2·Tc + C3·To² + C4·To·Tc + C5·Tc²
   + C6·To³ + C7·To²·Tc + C8·To·Tc² + C9·Tc³
```

where `To` = evaporating SST [°C] and `Tc` = condensing SDT [°C].

---

## Repository structure

```
refrigeration-cycle-model/
│
├── run_project.ipynb       ← start here
├── requirements.txt
├── README.md
│
├── src/
│   ├── config.py           ← EDIT THIS for your project
│   ├── compressor.py       ← ADD YOUR compressor coefficients here
│   ├── thermodynamics.py   ← CoolProp cycle reconstruction
│   ├── heat_exchanger.py   ← LMTD KA calculation + temperature solvers
│   ├── solver.py           ← iterative operating-point solver
│   ├── plots_ph_ts.py      ← P-h and T-s diagrams
│   ├── plots_others.py     ← EER, Qe, Pc, efficiency plots
│   ├── utils.py            ← unit conversions, LMTD, helpers
│   ├── main.py             ← orchestrates everything
│   └── __init__.py
│
└── report/
    └── UNIPD_Ref_HP_Project.pdf
```

---

## Outputs

For each heat-sink temperature step the model reports:

| Column | Description |
|---|---|
| `Tevap [°C]` | Converged evaporating temperature |
| `Tcond [°C]` | Converged condensing temperature |
| `Qe [kW]` | Cooling capacity |
| `Pc [kW]` | Compressor power |
| `EER [-]` | Energy efficiency ratio |
| `eta_is [-]` | Isentropic efficiency (derived) |
| `eta_vol [-]` | Volumetric efficiency (derived) |
| `PR [-]` | Pressure ratio |

Results are exported to a CSV named automatically from your config:
`refrigeration_results_<REF>_<LastName>.csv`

---

The solver iterates `Tevap` and `Tcond` until the heat exchanger LMTD
equations and the compressor polynomial are mutually consistent:

```
Q = KA · ΔTLM
```

`eta_is` and `eta_vol` are **derived** from the polynomial output combined
with CoolProp states — no algebraic correlations are imposed.

---

## Assignment reference

| Student | Application | Qe [kW] | Evap side | Cond side |
|---|---|---|---|---|
| Naeejnezhad Amirhossein | Cooling data center | 50 | air at 12 °C | water |
| Capovilla Daniele | Water chiller | 75 | water 12→7 °C | water |
| LORENZIN FILIPPO | Process chiller | 120 | water 16→11 °C | air |
| BEDA EMMA | Water chiller | 20 | water 18→12 °C | air |
| FONTANIVE GIOVANNI | Cooling data center | 100 | air at 15 °C | water |
| *(see assignments PDF for full list)* | | | | |

---

## Branch overview

| Branch | Description |
|---|---|
| `main` | Original implementation — Amirhossein Naeejnezhad's project (R32, data center, 50 kW) |
| `universal-model` | This branch — supports any student project via config |

---

*Original implementation: Amirhossein Naeejnezhad, University of Padova, 2025*
