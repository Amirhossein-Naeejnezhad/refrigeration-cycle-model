# ============================================================
# COMPRESSOR MODEL
# Bitzer Polynomial Model (10-coefficient)
# ============================================================

"""
This module implements the Bitzer compressor polynomial model.

It provides:
- Polynomial evaluation
- Compressor performance (Qe, Pc, mdot)

The model is based on manufacturer data fitted with a 10-coefficient
polynomial in evaporating and condensing temperatures.
"""

import numpy as np


# =========================
# 1) Polynomial coefficients
# =========================

# Cooling capacity coefficients [W]
COEFF_Q = [
    59389.6460596508, 1974.93337183458, -434.566222820298,
    24.594529451844, -10.2181966843594, 2.24802179597381,
    0.138811158034248, -0.128352894275604,
    -0.0267504276592594, -0.0326303848448441
]

# Compressor power coefficients [W]
COEFF_P = [
    3944.28593095782, 31.3520381363774, 132.717560894121,
    2.64300871010126, -0.107609643518827, -0.311738942469663,
    0.055610010979593, -0.0364250886707346,
    -0.0014218709419455, 0.0217787638875563
]

# Mass flow rate coefficients [kg/h]
COEFF_M = [
    658.966504520555, 21.4502351673649, -1.91676125550773,
    0.262853524276791, -0.0208074335044084, 0.0397107668517898,
    0.0020691014229269, 0.000198789706841437,
    0.000310832175464325, -0.000429702580661385
]


# =========================
# 2) Polynomial evaluation
# =========================
def poly_eval(coeff, to, tc):
    """
    Evaluate 10-coefficient Bitzer polynomial.

    Parameters:
        coeff : list of 10 coefficients
        to    : evaporating temperature [°C]
        tc    : condensing temperature  [°C]

    Returns:
        scalar value (Qe, Pc, or mdot depending on coeff)
    """
    return (
        coeff[0]
        + coeff[1]*to
        + coeff[2]*tc
        + coeff[3]*to**2
        + coeff[4]*to*tc
        + coeff[5]*tc**2
        + coeff[6]*to**3
        + coeff[7]*tc*to**2
        + coeff[8]*to*tc**2
        + coeff[9]*tc**3
    )


# =========================
# 3) Compressor model
# =========================
def compressor_polynomial_model(Tevap_C, Tcond_C):
    """
    Evaluate compressor performance using Bitzer polynomial model.

    Parameters:
        Tevap_C : evaporating temperature [°C]
        Tcond_C : condensing temperature  [°C]

    Returns:
        dict with:
            Qe   : cooling capacity [W]
            Pc   : compressor power [W]
            mdot : mass flow rate [kg/s]
            was_extrapolated : False (no range flag in polynomial)
    """

    # --- Polynomial evaluation ---
    Qe   = poly_eval(COEFF_Q, Tevap_C, Tcond_C)          # [W]
    Pc   = poly_eval(COEFF_P, Tevap_C, Tcond_C)          # [W]
    mdot = poly_eval(COEFF_M, Tevap_C, Tcond_C) / 3600.0 # [kg/s]

    # --- Numerical safety floor ---
    Qe   = max(Qe,   1e-6)
    Pc   = max(Pc,   1e-6)
    mdot = max(mdot, 1e-8)

    return {
        "Qe": Qe,
        "Pc": Pc,
        "mdot": mdot,
        "was_extrapolated": False  # polynomial has no explicit limits
    }
