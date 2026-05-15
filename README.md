# Refrigeration Cycle Model

Refrigeration and Heat Pump Technology project work — University of Padova.

This repository models a vapour-compression refrigeration cycle and studies how
cooling capacity and EER change when the condenser heat-sink temperature varies.
The active case is Amirhossein Naeejnezhad's assigned project:

- Application: data-center cooling
- Nominal target cooling capacity: 50 kW
- Assigned air condition: 12 °C
- Condenser secondary fluid: water
- Refrigerant: R32
- Compressor: Bitzer GSU60182VL_4

The assigned 12 °C air condition is modelled as the data-center supply-air
temperature. A 24 °C return-air temperature is assumed to close the evaporator
energy balance and estimate the air mass flow rate. This is an additional
modelling assumption because the assignment provides only one air-side
temperature.

The selected compressor provides about 47.7 kW at the nominal compressor-selection
point, which is slightly below the 50 kW assignment target. It was selected because
it is closer to the assigned capacity than the next larger Bitzer R32 scroll option.

---

## Model summary

The code combines:

1. a 10-coefficient manufacturer compressor polynomial for `Qe`, `Pc`, and
   refrigerant mass flow rate;
2. CoolProp thermodynamic-state reconstruction;
3. LMTD heat-exchanger matching for evaporator and condenser;
4. an iterative solver for the coupled cycle and heat exchangers;
5. a parametric sweep of condenser heat-sink inlet temperature.

The main reported quantities are:

- converged evaporating and condensing temperatures;
- cooling capacity `Qe`;
- compressor power `Pc`;
- condenser heat rejection `Qc`;
- EER;
- pressure ratio;
- derived isentropic and volumetric efficiencies;
- secondary-fluid mass flow rates.

---

## Run in Google Colab

Open `run_project.ipynb` and run all cells in order.

The notebook imports and runs:

```python
from src.main import run_project

df, df_print, df_states, validation = run_project()
```

Results are exported to:

```text
refrigeration_results_R32_Naeejnezhad.csv
```

---

## Repository structure

```text
refrigeration-cycle-model/
├── README.md
├── requirements.txt
├── run_project.ipynb
├── src/
│   ├── config.py           # project assumptions and active case
│   ├── compressor.py       # compressor-polynomial registry
│   ├── thermodynamics.py   # CoolProp cycle reconstruction
│   ├── heat_exchanger.py   # LMTD and KA calculations
│   ├── solver.py           # coupled operating-point solver
│   ├── plots_ph_ts.py      # p-h and T-s diagrams
│   ├── plots_others.py     # performance plots
│   ├── utils.py            # shared helper functions
│   └── main.py             # project runner
└── UNIPD_Ref_HP_Project.pdf
```

---

## How to adapt it to another student project

1. Edit `src/config.py`:
   - project name and application;
   - refrigerant;
   - target cooling capacity;
   - evaporator secondary-fluid temperatures;
   - condenser secondary fluid;
   - compressor metadata and nominal point.

2. Edit `src/compressor.py`:
   - add the 10 coefficients for cooling capacity, compressor power, and mass
     flow rate;
   - set `COMPRESSOR_MODEL` in `config.py` equal to the registry key.

3. Run `run_project.ipynb` again.

---

## Important assumptions and limitations

- Superheat at compressor suction is fixed.
- Subcooling at condenser outlet is fixed.
- Pressure drops are neglected.
- Heat exchangers are treated with counterflow LMTD.
- The assigned 12 °C air condition is interpreted as supply air; the 24 °C
  return-air temperature is assumed only to close the evaporator-side energy
  balance.
- `KA_EVAP` and `KA_COND` are computed at the nominal point and then kept
  constant during the heat-sink sweep.
- CoolProp is used for thermophysical properties.
- The compressor polynomial is checked against a configured operating envelope;
  this is a warning system, not a replacement for official manufacturer limits.
