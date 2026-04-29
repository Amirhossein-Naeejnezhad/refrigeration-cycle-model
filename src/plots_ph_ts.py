# ============================================================
# P-h AND T-s DIAGRAMS
# Full thermodynamic visualization (with superheat & subcooling)
# ============================================================
"""
This module builds high-quality thermodynamic diagrams:

  - P-h diagram (log-pressure)
  - T-s diagram
  - Saturation dome
  - Full cycle paths
  - Explicit visualisation of superheating and subcooling

Diagrams are built from CoolProp states stored in the result DataFrame.
All project-specific values (refrigerant, student name, case temperatures)
are read from config at call time — no hardcoded strings.
"""

import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI

from src import config as cfg
from src.utils import k_to_c


# ============================================================
# INTERNAL HELPER — resolve x-column and case temperatures
# ============================================================

def _hs_col(df):
    """Return the heat-sink inlet column present in df."""
    if "HS in [°C]" in df.columns:
        return "HS in [°C]"
    return "Water in [°C]"


def _select_ph_cases(df):
    """
    Pick three representative heat-sink temperatures evenly spread across
    the parametric sweep actually present in df.
    Falls back gracefully if fewer than three rows exist.
    """
    col    = _hs_col(df)
    temps  = df[col].values
    t_min, t_max = temps[0], temps[-1]
    t_mid  = 0.5 * (t_min + t_max)
    candidates = [t_min, t_mid, t_max]
    return candidates


# ============================================================
# P-h DIAGRAM — curve builders
# ============================================================

def build_ph_dome(ref=None):
    if ref is None:
        ref = cfg.REF
    T_triple = PropsSI(ref, "Ttriple")
    T_crit   = PropsSI(ref, "Tcrit")
    T_list   = np.linspace(T_triple + 1.0, T_crit - 0.5, 500)

    h_liq, h_vap, P_sat = [], [], []
    for T in T_list:
        try:
            h_liq.append(PropsSI("H", "T", T, "Q", 0, ref) / 1000.0)
            h_vap.append(PropsSI("H", "T", T, "Q", 1, ref) / 1000.0)
            P_sat.append(PropsSI("P", "T", T, "Q", 0, ref) / 1e5)
        except Exception:
            pass
    return np.array(h_liq), np.array(h_vap), np.array(P_sat)


def build_curve_constP(P, h_start, h_end, ref=None, n=100):
    if ref is None:
        ref = cfg.REF
    hs = np.linspace(h_start, h_end, n)
    Ps = np.full_like(hs, P / 1e5)
    return hs / 1000.0, Ps


def build_curve_constH(h, P_start, P_end, ref=None, n=100):
    if ref is None:
        ref = cfg.REF
    Ps = np.linspace(P_start, P_end, n)
    hs = np.full_like(Ps, h)
    return hs / 1000.0, Ps / 1e5


def build_curve_compression(states, ref=None, n=100):
    if ref is None:
        ref = cfg.REF
    P1 = states[1]["P"]
    P2 = states[2]["P"]
    h1 = states[1]["h"]
    h2 = states[2]["h"]
    Ps = np.linspace(P1, P2, n)
    hs = np.linspace(h1, h2, n)
    return hs / 1000.0, Ps / 1e5


# ============================================================
# P-h DIAGRAM — main plot
# ============================================================

def plot_ph_diagram(df):
    ref     = cfg.REF
    col     = _hs_col(df)
    cases   = _select_ph_cases(df)
    colors  = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    h_liq, h_vap, P_sat = build_ph_dome(ref)

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.semilogy(h_liq, P_sat, color="black", label="Saturation dome")
    ax.semilogy(h_vap, P_sat, color="black")

    last_st = None   # kept for smart zoom after loop

    for idx_case, T_case in enumerate(cases):
        idx = np.argmin(np.abs(df[col] - T_case))
        res = df.iloc[idx]["Cycle object"]
        cyc = res["real"]
        st  = cyc["states"]
        last_st = st

        color = colors[idx_case % len(colors)]

        T_hs_val     = df.iloc[idx][col]
        h_sat_vap    = PropsSI("H", "P", st[1]["P"], "Q", 1, ref)
        h_sat_liq    = PropsSI("H", "P", st[3]["P"], "Q", 0, ref)

        h12,  P12  = build_curve_compression(st, ref=ref)
        h23a, P23a = build_curve_constP(st[2]["P"], st[2]["h"], h_sat_liq, ref=ref)
        h23b, P23b = build_curve_constP(st[3]["P"], h_sat_liq, st[3]["h"], ref=ref)
        h34,  P34  = build_curve_constH(st[3]["h"], st[3]["P"], st[4]["P"], ref=ref)
        h41a, P41a = build_curve_constP(st[4]["P"], st[4]["h"], h_sat_vap, ref=ref)
        h41b, P41b = build_curve_constP(st[1]["P"], h_sat_vap, st[1]["h"], ref=ref)

        label = f"Cycle, T_hs = {T_hs_val:.0f} °C"

        ax.semilogy(h12,  P12,  color=color, label=label)
        ax.semilogy(h23a, P23a, color=color)
        ax.semilogy(h23b, P23b, color=color, linestyle="--")
        ax.semilogy(h34,  P34,  color=color)
        ax.semilogy(h41a, P41a, color=color)
        ax.semilogy(h41b, P41b, color=color, linestyle="--")

        for i in [1, 2, 3, 4]:
            h_i = st[i]["h"] / 1000.0
            P_i = st[i]["P"] / 1e5
            ax.semilogy(h_i, P_i, marker="o", color=color)
            ax.text(h_i + 2, P_i * 1.05, str(i), fontsize=9)

        h_1sat = h_sat_vap / 1000.0
        P_1sat = st[1]["P"] / 1e5
        h_3sat = h_sat_liq / 1000.0
        P_3sat = st[3]["P"] / 1e5

        ax.semilogy(h_1sat, P_1sat, marker="x", color=color)
        ax.semilogy(h_3sat, P_3sat, marker="x", color=color)
        ax.text(h_1sat + 2, P_1sat * 1.05, "1s", fontsize=9)
        ax.text(h_3sat + 2, P_3sat * 1.05, "3s", fontsize=9)

    # Smart zoom on last case states (representative)
    if last_st is not None:
        all_h = [last_st[i]["h"] / 1000.0 for i in [1, 2, 3, 4]]
        all_P = [last_st[i]["P"] / 1e5    for i in [1, 2, 3, 4]]
        ax.set_xlim(min(all_h) - 50, max(all_h) + 50)
        ax.set_ylim(min(all_P) * 0.7, max(all_P) * 1.3)

    ax.set_xlabel("Specific enthalpy [kJ/kg]")
    ax.set_ylabel("Pressure [bar]")
    ax.set_title(
        f"P-h diagram — superheating & subcooling visible\n"
        f"{cfg.STUDENT_NAME} — {cfg.APPLICATION} — {ref}"
    )
    ax.legend()
    plt.tight_layout()
    plt.show()


# ============================================================
# T-s DIAGRAM — curve builders
# ============================================================

def build_ts_dome(ref=None):
    if ref is None:
        ref = cfg.REF
    T_triple = PropsSI(ref, "Ttriple")
    T_crit   = PropsSI(ref, "Tcrit")
    T_list   = np.linspace(T_triple + 1.0, T_crit - 0.5, 500)

    s_liq, s_vap, T_sat_C = [], [], []
    for T in T_list:
        try:
            s_liq.append(PropsSI("S", "T", T, "Q", 0, ref) / 1000.0)
            s_vap.append(PropsSI("S", "T", T, "Q", 1, ref) / 1000.0)
            T_sat_C.append(T - 273.15)
        except Exception:
            pass
    return np.array(s_liq), np.array(s_vap), np.array(T_sat_C)


def build_process_curve_constP_h(P, h_start, h_end, ref=None, n=80):
    if ref is None:
        ref = cfg.REF
    hs = np.linspace(h_start, h_end, n)
    s_list, T_list = [], []
    for h in hs:
        T = PropsSI("T", "P", P, "H", h, ref)
        s = PropsSI("S", "P", P, "H", h, ref)
        T_list.append(T - 273.15)
        s_list.append(s / 1000.0)
    return np.array(s_list), np.array(T_list)


def build_process_curve_constH_P(h, P_start, P_end, ref=None, n=80):
    if ref is None:
        ref = cfg.REF
    Ps = np.linspace(P_start, P_end, n)
    s_list, T_list = [], []
    for P in Ps:
        T = PropsSI("T", "P", P, "H", h, ref)
        s = PropsSI("S", "P", P, "H", h, ref)
        T_list.append(T - 273.15)
        s_list.append(s / 1000.0)
    return np.array(s_list), np.array(T_list)


def build_process_curve_compression(states, ref=None, n=80):
    if ref is None:
        ref = cfg.REF
    P1 = states[1]["P"]
    P2 = states[2]["P"]
    h1 = states[1]["h"]
    h2 = states[2]["h"]
    Ps = np.linspace(P1, P2, n)
    hs = np.linspace(h1, h2, n)
    s_list, T_list = [], []
    for P, h in zip(Ps, hs):
        T = PropsSI("T", "P", P, "H", h, ref)
        s = PropsSI("S", "P", P, "H", h, ref)
        T_list.append(T - 273.15)
        s_list.append(s / 1000.0)
    return np.array(s_list), np.array(T_list)


# ============================================================
# T-s DIAGRAM — main plot
# ============================================================

def plot_ts_diagram(df):
    ref    = cfg.REF
    col    = _hs_col(df)
    cases  = _select_ph_cases(df)
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    s_liq, s_vap, T_sat_C = build_ts_dome(ref)

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(s_liq, T_sat_C, color="black", label="Saturation dome")
    ax.plot(s_vap, T_sat_C, color="black")

    last_st = None

    for idx_case, T_case in enumerate(cases):
        idx = np.argmin(np.abs(df[col] - T_case))
        res = df.iloc[idx]["Cycle object"]
        cyc = res["real"]
        st  = cyc["states"]
        last_st = st

        color = colors[idx_case % len(colors)]

        T_hs_val  = df.iloc[idx][col]
        h_sat_vap = PropsSI("H", "P", st[1]["P"], "Q", 1, ref)
        h_sat_liq = PropsSI("H", "P", st[3]["P"], "Q", 0, ref)

        s12,  T12  = build_process_curve_compression(st, ref=ref, n=100)
        s23a, T23a = build_process_curve_constP_h(st[2]["P"], st[2]["h"], h_sat_liq, ref=ref, n=100)
        s23b, T23b = build_process_curve_constP_h(st[3]["P"], h_sat_liq, st[3]["h"], ref=ref, n=40)
        s34,  T34  = build_process_curve_constH_P(st[3]["h"], st[3]["P"], st[4]["P"], ref=ref, n=100)
        s41a, T41a = build_process_curve_constP_h(st[4]["P"], st[4]["h"], h_sat_vap, ref=ref, n=100)
        s41b, T41b = build_process_curve_constP_h(st[1]["P"], h_sat_vap, st[1]["h"], ref=ref, n=40)

        label = f"Cycle, T_hs = {T_hs_val:.0f} °C"

        ax.plot(s12,  T12,  color=color, label=label)
        ax.plot(s23a, T23a, color=color)
        ax.plot(s23b, T23b, color=color, linestyle="--")
        ax.plot(s34,  T34,  color=color)
        ax.plot(s41a, T41a, color=color)
        ax.plot(s41b, T41b, color=color, linestyle="--")

        for i in [1, 2, 3, 4]:
            s_i = st[i]["s"] / 1000.0 if st[i]["s"] is not None else float("nan")
            T_i = k_to_c(st[i]["T"])
            ax.plot(s_i, T_i, marker="o", color=color)
            ax.text(s_i + 0.01, T_i + 0.8, str(i), fontsize=9)

        s_1sat = PropsSI("S", "P", st[1]["P"], "Q", 1, ref) / 1000.0
        T_1sat = PropsSI("T", "P", st[1]["P"], "Q", 1, ref) - 273.15
        s_3sat = PropsSI("S", "P", st[3]["P"], "Q", 0, ref) / 1000.0
        T_3sat = PropsSI("T", "P", st[3]["P"], "Q", 0, ref) - 273.15

        ax.plot(s_1sat, T_1sat, marker="x", color=color)
        ax.plot(s_3sat, T_3sat, marker="x", color=color)
        ax.text(s_1sat + 0.01, T_1sat, "1s", fontsize=9)
        ax.text(s_3sat + 0.01, T_3sat, "3s", fontsize=9)

    # Smart zoom
    if last_st is not None:
        all_s = [last_st[i]["s"] / 1000.0 for i in [1, 2, 3, 4]
                 if last_st[i]["s"] is not None]
        all_T = [k_to_c(last_st[i]["T"]) for i in [1, 2, 3, 4]]
        ax.set_xlim(min(all_s) - 0.2, max(all_s) + 0.2)
        ax.set_ylim(min(all_T) - 15,  max(all_T) + 15)

    ax.set_xlabel("Specific entropy [kJ/kg·K]")
    ax.set_ylabel("Temperature [°C]")
    ax.set_title(
        f"T-s diagram — superheating & subcooling visible\n"
        f"{cfg.STUDENT_NAME} — {cfg.APPLICATION} — {ref}"
    )
    ax.legend()
    plt.tight_layout()
    plt.show()
