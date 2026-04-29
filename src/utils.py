# ============================================================
# UTILITY FUNCTIONS
# Refrigeration Cycle Model
# ============================================================
"""
General-purpose helper functions used across the project.
No project-specific values live here.

  1) Unit conversions
  2) LMTD calculation
  3) Standardised plot helper
  4) Numerical safety utilities
  5) Array safe-evaluation helper
  6) Pretty-print helper for operating-point dicts
"""

import numpy as np
import matplotlib.pyplot as plt


# =========================
# 1) Unit conversions
# =========================

def c_to_k(T_c):
    """Convert temperature from °C to K."""
    return T_c + 273.15


def k_to_c(T_k):
    """Convert temperature from K to °C."""
    return T_k - 273.15


def bar_to_pa(p_bar):
    """Convert pressure from bar to Pa."""
    return p_bar * 1e5


def pa_to_bar(p_pa):
    """Convert pressure from Pa to bar."""
    return p_pa / 1e5


# =========================
# 2) Log Mean Temperature Difference (LMTD)
# =========================

def lmtd(deltaT1, deltaT2):
    """
    Log-mean temperature difference with numerical protection.

    Parameters
    ----------
    deltaT1, deltaT2 : temperature differences at the two HX ends [any unit]

    Returns
    -------
    float — LMTD in the same unit as the inputs

    Notes
    -----
    - Both inputs are floored at 1e-9 to prevent log(0).
    - When the two differences are nearly equal the arithmetic mean is
      returned (L'Hôpital limit), avoiding 0/0.
    """
    eps = 1e-9
    deltaT1 = max(deltaT1, eps)
    deltaT2 = max(deltaT2, eps)

    if abs(deltaT1 - deltaT2) < 1e-9:
        return 0.5 * (deltaT1 + deltaT2)

    return (deltaT1 - deltaT2) / np.log(deltaT1 / deltaT2)


# =========================
# 3) Plot helper
# =========================

def make_plot(x, y_list, labels, xlabel, ylabel, title, ax=None):
    """
    Standardised line plot for consistent style across the project.

    Parameters
    ----------
    x      : array-like — x-axis values
    y_list : list of array-like — one array per series
    labels : list of str — one label per series
    xlabel : str
    ylabel : str
    title  : str
    ax     : matplotlib Axes, optional
        If provided, plot into this Axes instead of creating a new figure.
        Useful for multi-panel layouts in the notebook.

    Returns
    -------
    fig, ax — only when a new figure was created (ax=None);
               returns (None, ax) when an existing Axes was passed.
    """
    created = ax is None
    if created:
        fig, ax = plt.subplots()
    else:
        fig = None

    markers = ["o", "s", "D", "^", "v", "x"]

    for i, (y, label) in enumerate(zip(y_list, labels)):
        ax.plot(x, y, marker=markers[i % len(markers)], label=label)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, pad=10)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    if len(labels) > 1:
        ax.legend()

    if created:
        plt.tight_layout()
        plt.show()
        return fig, ax

    return None, ax


# =========================
# 4) Safety helpers
# =========================

def safe_clip(x, xmin, xmax):
    """Clamp a scalar value between xmin and xmax."""
    return min(max(x, xmin), xmax)


# =========================
# 5) Array safe-evaluation helper
# =========================

def safe_eval_array(func, arr):
    """
    Apply *func* to every element of *arr*, returning NaN on failure.

    Parameters
    ----------
    func : callable  — single-argument function
    arr  : iterable  — input values

    Returns
    -------
    np.ndarray — same length as arr; failed evaluations become np.nan
    """
    out = []
    for val in arr:
        try:
            out.append(func(val))
        except Exception:
            out.append(np.nan)
    return np.array(out)


# =========================
# 6) Pretty-print helper
# =========================

def print_operating_point(result: dict, label: str = "Operating point"):
    """
    Print a human-readable summary of a result dict returned by
    solver.solve_operating_point().

    Parameters
    ----------
    result : dict  — as returned by solve_operating_point()
    label  : str   — header label
    """
    real = result.get("real", {})
    print(f"\n{label}")
    print("-" * len(label))
    print(f"  Heat-sink in   : {result.get('T_heatsink_in_C',  result.get('T_water_in_C',  float('nan'))):.2f} °C")
    print(f"  Heat-sink out  : {result.get('T_heatsink_out_C', result.get('T_water_out_C', float('nan'))):.2f} °C")
    print(f"  Tevap          : {result.get('T_evap_C', float('nan')):.2f} °C")
    print(f"  Tcond          : {result.get('T_cond_C', float('nan')):.2f} °C")
    if real:
        print(f"  Qe             : {real.get('Qe', float('nan'))/1000:.2f} kW")
        print(f"  Pc             : {real.get('Pc', float('nan'))/1000:.2f} kW")
        print(f"  EER            : {real.get('EER', float('nan')):.3f}")
        print(f"  eta_is         : {real.get('eta_is', float('nan')):.4f}")
        print(f"  eta_vol        : {real.get('eta_vol', float('nan')):.4f}")
        print(f"  Iterations     : {result.get('iterations', '?')}")
