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
- Explicit visualization of:
    • superheating
    • subcooling

These plots are reconstructed using CoolProp states.
"""

import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI

from src.config import REF
from src.utils import k_to_c


# =========================
# -------- P-h DIAGRAM ----
# =========================

def build_ph_dome(ref=REF):
    T_triple = PropsSI(ref, "Ttriple")
    T_crit   = PropsSI(ref, "Tcrit")

    T_list = np.linspace(T_triple + 1.0, T_crit - 0.5, 500)

    h_liq, h_vap, P_sat = [], [], []

    for T in T_list:
        try:
            h_liq.append(PropsSI("H", "T", T, "Q", 0, ref) / 1000.0)
            h_vap.append(PropsSI("H", "T", T, "Q", 1, ref) / 1000.0)
            P_sat.append(PropsSI("P", "T", T, "Q", 0, ref) / 1e5)
        except:
            pass

    return np.array(h_liq), np.array(h_vap), np.array(P_sat)


def build_curve_constP(P, h_start, h_end, ref=REF, n=100):
    hs = np.linspace(h_start, h_end, n)
    Ps = np.full_like(hs, P / 1e5)
    return hs / 1000.0, Ps


def build_curve_constH(h, P_start, P_end, ref=REF, n=100):
    Ps = np.linspace(P_start, P_end, n)
    hs = np.full_like(Ps, h)
    return hs / 1000.0, Ps / 1e5


def build_curve_compression(states, ref=REF, n=100):
    P1 = states[1]["P"]
    P2 = states[2]["P"]
    h1 = states[1]["h"]
    h2 = states[2]["h"]

    Ps = np.linspace(P1, P2, n)
    hs = np.linspace(h1, h2, n)

    return hs / 1000.0, Ps / 1e5


def plot_ph_diagram(df):
    h_liq, h_vap, P_sat = build_ph_dome(REF)

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.semilogy(h_liq, P_sat, color="black", label="Saturation dome")
    ax.semilogy(h_vap, P_sat, color="black")

    ph_cases = [24.0, 30.0, 36.0]
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

    for idx_case, Tw in enumerate(ph_cases):
        idx = np.argmin(np.abs(df["Water in [°C]"] - Tw))
        res = df.iloc[idx]["Cycle object"]
        cyc = res["real"]
        st  = cyc["states"]

        color = colors[idx_case % len(colors)]

        h_sat_vap = PropsSI("H", "P", st[1]["P"], "Q", 1, REF)
        h_sat_liq = PropsSI("H", "P", st[3]["P"], "Q", 0, REF)

        # Build segments
        h12, P12 = build_curve_compression(st)
        h23a, P23a = build_curve_constP(st[2]["P"], st[2]["h"], h_sat_liq)
        h23b, P23b = build_curve_constP(st[3]["P"], h_sat_liq, st[3]["h"])
        h34, P34 = build_curve_constH(st[3]["h"], st[3]["P"], st[4]["P"])
        h41a, P41a = build_curve_constP(st[4]["P"], st[4]["h"], h_sat_vap)
        h41b, P41b = build_curve_constP(st[1]["P"], h_sat_vap, st[1]["h"])

        label = f"Cycle, water in = {df.iloc[idx]['Water in [°C]']:.0f}°C"

        ax.semilogy(h12,  P12,  color=color, label=label)
        ax.semilogy(h23a, P23a, color=color)
        ax.semilogy(h23b, P23b, color=color, linestyle="--")
        ax.semilogy(h34,  P34,  color=color)
        ax.semilogy(h41a, P41a, color=color)
        ax.semilogy(h41b, P41b, color=color, linestyle="--")

        # Points
        for i in [1, 2, 3, 4]:
            h_i = st[i]["h"] / 1000.0
            P_i = st[i]["P"] / 1e5
            ax.semilogy(h_i, P_i, marker="o", color=color)
            ax.text(h_i + 2, P_i * 1.05, str(i), fontsize=9)

    ax.set_xlabel("Specific enthalpy [kJ/kg]")
    ax.set_ylabel("Pressure [bar]")
    ax.set_title(f"P-h diagram ({REF})")
    ax.legend()
    plt.tight_layout()
    plt.show()


# =========================
# -------- T-s DIAGRAM ----
# =========================

def build_ts_dome(ref=REF):
    T_triple = PropsSI(ref, "Ttriple")
    T_crit   = PropsSI(ref, "Tcrit")

    T_list = np.linspace(T_triple + 1.0, T_crit - 0.5, 500)

    s_liq, s_vap, T_sat_C = [], [], []

    for T in T_list:
        try:
            s_liq.append(PropsSI("S", "T", T, "Q", 0, ref) / 1000.0)
            s_vap.append(PropsSI("S", "T", T, "Q", 1, ref) / 1000.0)
            T_sat_C.append(T - 273.15)
        except:
            pass

    return np.array(s_liq), np.array(s_vap), np.array(T_sat_C)


def build_process_curve_constP_h(P, h_start, h_end, ref=REF, n=80):
    hs = np.linspace(h_start, h_end, n)
    s_list, T_list = [], []

    for h in hs:
        T = PropsSI("T", "P", P, "H", h, ref)
        s = PropsSI("S", "P", P, "H", h, ref)
        T_list.append(T - 273.15)
        s_list.append(s / 1000.0)

    return np.array(s_list), np.array(T_list)


def build_process_curve_constH_P(h, P_start, P_end, ref=REF, n=80):
    Ps = np.linspace(P_start, P_end, n)
    s_list, T_list = [], []

    for P in Ps:
        T = PropsSI("T", "P", P, "H", h, ref)
        s = PropsSI("S", "P", P, "H", h, ref)
        T_list.append(T - 273.15)
        s_list.append(s / 1000.0)

    return np.array(s_list), np.array(T_list)


def build_process_curve_compression(states, ref=REF, n=80):
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


def plot_ts_diagram(df):
    s_liq, s_vap, T_sat_C = build_ts_dome(REF)

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(s_liq, T_sat_C, color="black", label="Saturation dome")
    ax.plot(s_vap, T_sat_C, color="black")

    ts_cases = [24.0, 30.0, 36.0]
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

    for idx_case, Tw in enumerate(ts_cases):
        idx = np.argmin(np.abs(df["Water in [°C]"] - Tw))
        res = df.iloc[idx]["Cycle object"]
        cyc = res["real"]
        st  = cyc["states"]

        color = colors[idx_case % len(colors)]

        h_sat_vap = PropsSI("H", "P", st[1]["P"], "Q", 1, REF)
        h_sat_liq = PropsSI("H", "P", st[3]["P"], "Q", 0, REF)

        s12, T12 = build_process_curve_compression(st)
        s23a, T23a = build_process_curve_constP_h(st[2]["P"], st[2]["h"], h_sat_liq)
        s23b, T23b = build_process_curve_constP_h(st[3]["P"], h_sat_liq, st[3]["h"])
        s34, T34 = build_process_curve_constH_P(st[3]["h"], st[3]["P"], st[4]["P"])
        s41a, T41a = build_process_curve_constP_h(st[4]["P"], st[4]["h"], h_sat_vap)
        s41b, T41b = build_process_curve_constP_h(st[1]["P"], h_sat_vap, st[1]["h"])

        label = f"Cycle, water in = {df.iloc[idx]['Water in [°C]']:.0f}°C"

        ax.plot(s12,  T12,  color=color, label=label)
        ax.plot(s23a, T23a, color=color)
        ax.plot(s23b, T23b, color=color, linestyle="--")
        ax.plot(s34,  T34,  color=color)
        ax.plot(s41a, T41a, color=color)
        ax.plot(s41b, T41b, color=color, linestyle="--")

        for i in [1, 2, 3, 4]:
            s_i = st[i]["s"] / 1000.0 if st[i]["s"] is not None else np.nan
            T_i = k_to_c(st[i]["T"])
            ax.plot(s_i, T_i, marker="o", color=color)
            ax.text(s_i + 0.01, T_i + 0.8, str(i), fontsize=9)

    ax.set_xlabel("Specific entropy [kJ/kg-K]")
    ax.set_ylabel("Temperature [°C]")
    ax.set_title(f"T-s diagram ({REF})")
    ax.legend()
    plt.tight_layout()
    plt.show()
