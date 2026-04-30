# Refrigeration Cycle Model

Modular Python project for a vapor-compression refrigeration cycle used for data-center cooling.

The model uses:

- R32 refrigerant
- CoolProp thermodynamic properties
- Bitzer 10-coefficient polynomial compressor model
- LMTD-based evaporator and condenser calculations
- Iterative coupling between the refrigeration cycle and heat exchangers
- Parametric study versus condenser water inlet temperature
- P-h and T-s diagrams
- High pressure ratio extrapolation study

---

## Project Structure

```text
refrigeration-cycle-model/
│
├── README.md
├── requirements.txt
├── run_project.ipynb
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── compressor.py
│   ├── thermodynamics.py
│   ├── heat_exchanger.py
│   ├── solver.py
│   ├── plots_ph_ts.py
│   ├── plots_others.py
│   ├── utils.py
│   └── main.py
│
├── UNIPD_Ref_HP_Project.pdf
│
└── data/
