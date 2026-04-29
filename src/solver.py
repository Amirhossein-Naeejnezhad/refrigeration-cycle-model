# ============================================================
# SYSTEM-LEVEL SOLVER
# Iterative coupling between refrigeration cycle and heat exchangers
# ============================================================

"""
This module solves the operating point of the full system.

For a given condenser water inlet temperature, it:
1) guesses Tevap and Tcond,
2) evaluates the thermodynamic cycle,
3) updates Tevap and Tcond from heat exchanger equations,
4) iterates until convergence.
"""

from src.config import (
    REF,
    T_AIR_IN_C,
    T_AIR_OUT_C,
    T_WATER_RISE_K,
    MAX_ITER,
    TOL,
    RELAX,
)

from src.utils import c_to_k, k_to_c
from src.thermodynamics import compressor_performance_from_map
from src.heat_exchanger import (
    solve_evap_temperature_from_hx,
    solve_cond_temperature_from_hx,
)


def solve_operating_point(
    T_water_in_C,
    KA_EVAP,
    KA_COND,
    ref=REF,
    verbose=False
):
    """
    Solve full operating point for a given condenser water inlet temperature.

    Parameters:
        T_water_in_C : condenser water inlet temperature [°C]
        KA_EVAP      : evaporator conductance [W/K]
        KA_COND      : condenser conductance [W/K]
        ref          : refrigerant
        verbose      : print iteration history if True

    Returns:
        result dictionary
    """

    T_air_in_K  = c_to_k(T_AIR_IN_C)
    T_air_out_K = c_to_k(T_AIR_OUT_C)

    T_w_in_K  = c_to_k(T_water_in_C)
    T_w_out_K = c_to_k(T_water_in_C + T_WATER_RISE_K)

    # Initial guesses
    T_evap_K = c_to_k(5.0)
    T_cond_K = c_to_k(T_water_in_C + 7.0)

    for it in range(MAX_ITER):
        cyc = compressor_performance_from_map(
            T_evap_K,
            T_cond_K,
            ref=ref
        )

        Qe = cyc["Qe"]
        Qc = cyc["Qc"]

        T_evap_new = solve_evap_temperature_from_hx(
            Qe,
            T_air_in_K,
            T_air_out_K,
            KA_EVAP
        )

        T_cond_new = solve_cond_temperature_from_hx(
            Qc,
            T_w_in_K,
            T_w_out_K,
            KA_COND
        )

        T_evap_next = (1 - RELAX) * T_evap_K + RELAX * T_evap_new
        T_cond_next = (1 - RELAX) * T_cond_K + RELAX * T_cond_new

        err = max(
            abs(T_evap_next - T_evap_K),
            abs(T_cond_next - T_cond_K)
        )

        T_evap_K = T_evap_next
        T_cond_K = T_cond_next

        if verbose:
            print(
                f"Iter {it:02d}: "
                f"Tevap={k_to_c(T_evap_K):.3f} °C, "
                f"Tcond={k_to_c(T_cond_K):.3f} °C, "
                f"err={err:.6f}"
            )

        if err < TOL:
            break

    real = compressor_performance_from_map(
        T_evap_K,
        T_cond_K,
        ref=ref
    )

    result = {
        "T_water_in_C":  T_water_in_C,
        "T_water_out_C": T_water_in_C + T_WATER_RISE_K,
        "T_evap_C":      k_to_c(T_evap_K),
        "T_cond_C":      k_to_c(T_cond_K),
        "real":          real,
        "iterations":    it + 1
    }

    return result
