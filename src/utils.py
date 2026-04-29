# ============================================================
# UTILITY FUNCTIONS
# Refrigeration Cycle Model
# ============================================================

"""
This module contains general-purpose helper functions used across
the project:

- Unit conversions
- LMTD calculation
- Plot helper
- Numerical safety utilities
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


# =========================
# 2) Log Mean Temperature Difference (LMTD)
# =========================
def lmtd(deltaT1, deltaT2):
    """
    Compute the log-mean temperature difference with numerical protection.

    Parameters:
        deltaT1 : temperature difference at one end
        deltaT2 : temperature difference at other end

    Returns:
        LMTD value
    """
    eps = 1e-9

    deltaT1 = max(deltaT1, eps)
    deltaT2 = max(deltaT2, eps)

    # Avoid division instability when nearly equal
    if abs(deltaT1 - deltaT2) < 1e-9:
        return 0.5 * (deltaT1 + deltaT2)

    return (deltaT1 - deltaT2) / np.log(deltaT1 / deltaT2)


# =========================
# 3) Plot helper
# =========================
def make_plot(x, y_list, labels, xlabel, ylabel, title):
    """
    Standardized plotting function for consistent style.

    Parameters:
        x       : x-axis values
        y_list  : list of y arrays
        labels  : list of labels
        xlabel  : x-axis label
        ylabel  : y-axis label
        title   : plot title
    """
    fig, ax = plt.subplots()

    markers = ["o", "s", "D", "^", "v", "x"]

    for i, (y, label) in enumerate(zip(y_list, labels)):
        marker = markers[i % len(markers)]
        ax.plot(x, y, marker=marker, label=label)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, pad=10)

    # Clean look
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    if len(labels) > 1:
        ax.legend()

    plt.tight_layout()
    plt.show()


# =========================
# 4) Safety helpers
# =========================
def safe_clip(x, xmin, xmax):
    """
    Clamp a value between xmin and xmax.
    """
    return min(max(x, xmin), xmax)


# =========================
# 5) Array safe evaluation helper
# =========================
def safe_eval_array(func, arr):
    """
    Apply a function to an array safely (catching failures).

    Returns NaN where evaluation fails.
    """
    out = []
    for val in arr:
        try:
            out.append(func(val))
        except:
            out.append(np.nan)
    return np.array(out)
