# Refrigeration Cycle Model
### Refrigeration and Heat Pump Technology — Project Work
**University of Padova — Energy Engineering - May 2026 - Prof. Azzolin - Prof. Bortolin**

---

## What this does

Models a vapour-compression refrigeration cycle and shows how **cooling capacity (Qe)** and **EER** change with heat-sink temperature — the core objective of the course project work.

Uses a **10-coefficient Bitzer polynomial** for the compressor, **CoolProp** for thermodynamic states, and **LMTD-based HX matching** with iterative convergence. Supports air or water/brine on both sides.

---

## Running your own project — step by step

### 1. Fork this repository

Click **Fork** on GitHub (top-right). All your edits go into your own fork.

Then open your fork in Google Colab via `run_project.ipynb`

---

### 2. Choose your refrigerant and compressor

Go to **[bitzer.de/websoftware](https://www.bitzer.de/websoftware)** and set:

- **Refrigerant** — choose based on your application (R32, R410A, R134a, R290…)
- **Cooling capacity** — your nominal Qe from the assignment
- **Evaporating SST** ≈ secondary fluid outlet − 7 K
- **Condensing SDT** ≈ heat-sink inlet + 10 K (air) or + 5 K (water)
- **Subcooling / Suction gas temperature** 

Select a compressor model and go to the **Polynomial** tab. Export the coefficients using the **Excel icon** next to the compressor name.

---

### 3. Edit `src/config.py`

Open the file. You will see the `ACTIVE PROJECT SETTINGS` block with the current active project. 

**First — comment out the active block**.

**Then — add your own block** below it and edit all the values in the file according your nominal condition


---

### 4. Edit `src/compressor.py`

Open the file and find `COMPRESSOR_REGISTRY`. Add a new entry for your compressor.
The key must **exactly match** `COMPRESSOR_MODEL` in `config.py`:

```python
"YOUR_MODEL": {
    "info": {
        "manufacturer": "Bitzer",
        "series":        "ORBIT+",
        "refrigerant":   "R410A",
        "type":          "Scroll, Single Compressor",
        "student":       "Your Name",
    },
    "Q": [C0, C1, C2, C3, C4, C5, C6, C7, C8, C9],   # cooling capacity [W]
    "P": [C0, C1, C2, C3, C4, C5, C6, C7, C8, C9],   # compressor power [W]
    "M": [C0, C1, C2, C3, C4, C5, C6, C7, C8, C9],   # mass flow rate [kg/h]
},
```

Coefficient order (ARI-540 / Bitzer standard):
```
C0 + C1·To + C2·Tc + C3·To² + C4·To·Tc + C5·Tc²
   + C6·To³ + C7·To²·Tc + C8·To·Tc² + C9·Tc³
```

---

### 5. Run

Open `run_project.ipynb` in Colab and run all cells in order.
Cell 3 confirms which project is active before anything runs — check it before Cell 4.

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
│   ├── __init__.py
│   ├── config.py           ← EDIT THIS — your project settings
│   ├── compressor.py       ← EDIT THIS — your compressor coefficients
│   ├── thermodynamics.py   ← CoolProp cycle reconstruction
│   ├── heat_exchanger.py   ← LMTD KA design + temperature solvers
│   ├── solver.py           ← iterative operating-point solver
│   ├── plots_ph_ts.py      ← P-h and T-s diagrams
│   ├── plots_others.py     ← EER, Qe, Pc, efficiency plots
│   ├── utils.py            ← unit conversions, LMTD, helpers
│   └── main.py             ← orchestrates everything
│
└── UNIPD_Ref_HP_Project.pdf
```

---

## Outputs

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

Results are exported automatically to `refrigeration_results_<REF>_<LastName>.csv`.

---

## Branch overview

| Branch | Description |
|---|---|
| `main` | Original — Amirhossein Naeejnezhad's project only (R32, data center, 50 kW) |
| `universal-model` | This branch — any student project via config |

---

*Original implementation: Amirhossein Naeejnezhad, University of Padova, 2025*
