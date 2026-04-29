# ============================================================
# COMPRESSOR MODEL
# Bitzer / Copeland / Frascold — 10-coefficient Polynomial
# ============================================================
"""
This module implements the standard 10-coefficient compressor
polynomial model used by Bitzer, Copeland and Frascold software.

It provides:
  - A registry of compressor coefficient sets (one entry per student /
    compressor model).
  - Polynomial evaluation (poly_eval).
  - Compressor performance lookup (Qe, Pc, mdot) for any registered model.

HOW TO ADD YOUR COMPRESSOR
===========================
1.  Run the manufacturer selection software (Bitzer websoftware,
    Copeland Select, Frascold Select) for your refrigerant and compressor.
2.  Export or read off the 10 polynomial coefficients for:
        - Cooling capacity  Qe  [W]
        - Compressor power  Pc  [W]
        - Mass flow rate    mdot [kg/h]
3.  Add a new entry to COMPRESSOR_REGISTRY below, following the
    template at the bottom of this section.
4.  In config.py set  COMPRESSOR_MODEL = "<your key>"
    The rest of the code picks it up automatically.

COEFFICIENT ORDER (standard Bitzer / ARI 540 form):
    C0
    + C1*To  + C2*Tc
    + C3*To² + C4*To*Tc + C5*Tc²
    + C6*To³ + C7*To²*Tc + C8*To*Tc² + C9*Tc³
where To = evaporating SST [°C], Tc = condensing SDT [°C].
"""

import numpy as np
from src import config as cfg


# ============================================================
# COMPRESSOR REGISTRY
# ============================================================
# Key   : must match COMPRESSOR_MODEL string in config.py
# Value : dict with keys "Q", "P", "M" (lists of 10 floats each)
#         Q  → cooling capacity  [W]
#         P  → compressor power  [W]
#         M  → mass flow rate    [kg/h]
#         "info" sub-dict is optional but recommended for traceability.
# ============================================================

COMPRESSOR_REGISTRY = {

    # ----------------------------------------------------------
    # Amirhossein Naeejnezhad
    # Bitzer GSU60182VL_4  |  ORBIT+  |  R32  |  Single
    # Nominal: To=5°C, Tc=35°C → Qe=53.9kW, Pc=9.31kW
    # ----------------------------------------------------------
    "GSU60182VL_4": {
        "info": {
            "manufacturer": "Bitzer",
            "series":        "ORBIT+",
            "refrigerant":   "R32",
            "type":          "Scroll, Single Compressor",
            "student":       "Amirhossein Naeejnezhad",
        },
        "Q": [
            59389.6460596508,  1974.93337183458,  -434.566222820298,
               24.594529451844,  -10.2181966843594,    2.24802179597381,
                0.138811158034248,  -0.128352894275604,
               -0.0267504276592594,  -0.0326303848448441,
        ],
        "P": [
            3944.28593095782,   31.3520381363774,  132.717560894121,
               2.64300871010126,  -0.107609643518827,  -0.311738942469663,
               0.055610010979593,  -0.0364250886707346,
              -0.0014218709419455,   0.0217787638875563,
        ],
        "M": [
             658.966504520555,   21.4502351673649,   -1.91676125550773,
               0.262853524276791,  -0.0208074335044084,   0.0397107668517898,
               0.0020691014229269,   0.000198789706841437,
               0.000310832175464325, -0.000429702580661385,
        ],
    },

    # ----------------------------------------------------------
    # TEMPLATE — copy, rename key, fill in your coefficients
    # ----------------------------------------------------------
    # "YOUR_COMPRESSOR_MODEL": {
    #     "info": {
    #         "manufacturer": "Bitzer / Copeland / Frascold",
    #         "series":        "XXXXX",
    #         "refrigerant":   "R410A",   # must match config.REF
    #         "type":          "Scroll / Reciprocating / Screw",
    #         "student":       "Your Name",
    #     },
    #     "Q": [C0, C1, C2, C3, C4, C5, C6, C7, C8, C9],   # [W]
    #     "P": [C0, C1, C2, C3, C4, C5, C6, C7, C8, C9],   # [W]
    #     "M": [C0, C1, C2, C3, C4, C5, C6, C7, C8, C9],   # [kg/h]
    # },
    # ----------------------------------------------------------

}


# ============================================================
# HELPER — retrieve coefficients
# ============================================================

def get_compressor_coeffs(model: str = None) -> dict:
    """
    Return the coefficient dict for *model* from the registry.

    Parameters
    ----------
    model : str, optional
        Key into COMPRESSOR_REGISTRY.  Defaults to cfg.COMPRESSOR_MODEL.

    Returns
    -------
    dict with keys "Q", "P", "M", "info"

    Raises
    ------
    KeyError if the model is not in the registry.
    """
    if model is None:
        model = cfg.COMPRESSOR_MODEL

    if model not in COMPRESSOR_REGISTRY:
        registered = list(COMPRESSOR_REGISTRY.keys())
        raise KeyError(
            f"Compressor model '{model}' not found in COMPRESSOR_REGISTRY.\n"
            f"Registered models: {registered}\n"
            f"Add your coefficients to compressor.py following the template."
        )
    return COMPRESSOR_REGISTRY[model]


# ============================================================
# POLYNOMIAL EVALUATION
# ============================================================

def poly_eval(coeff, to, tc):
    """
    Evaluate the standard 10-coefficient ARI-540 polynomial.

    Parameters
    ----------
    coeff : array-like, length 10
    to    : evaporating SST [°C]
    tc    : condensing  SDT [°C]

    Returns
    -------
    float
    """
    c = coeff
    return (
        c[0]
        + c[1]*to
        + c[2]*tc
        + c[3]*to**2
        + c[4]*to*tc
        + c[5]*tc**2
        + c[6]*to**3
        + c[7]*tc*to**2
        + c[8]*to*tc**2
        + c[9]*tc**3
    )


# ============================================================
# MAIN COMPRESSOR PERFORMANCE FUNCTION
# ============================================================

def compressor_polynomial_model(Tevap_C, Tcond_C, model: str = None):
    """
    Evaluate compressor performance at the given operating point.

    Parameters
    ----------
    Tevap_C : float  — evaporating saturation temperature [°C]
    Tcond_C : float  — condensing  saturation temperature [°C]
    model   : str, optional
        Compressor model key.  Defaults to cfg.COMPRESSOR_MODEL so
        existing call sites require no change.

    Returns
    -------
    dict
        Qe               : cooling capacity   [W]
        Pc               : compressor power   [W]
        mdot             : mass flow rate     [kg/s]
        was_extrapolated : always False (polynomial has no explicit limits)
    """
    coeffs = get_compressor_coeffs(model)

    Qe   = poly_eval(coeffs["Q"], Tevap_C, Tcond_C)           # [W]
    Pc   = poly_eval(coeffs["P"], Tevap_C, Tcond_C)           # [W]
    mdot = poly_eval(coeffs["M"], Tevap_C, Tcond_C) / 3600.0  # [kg/s]

    # Numerical safety floor
    Qe   = max(Qe,   1e-6)
    Pc   = max(Pc,   1e-6)
    mdot = max(mdot, 1e-8)

    return {
        "Qe":               Qe,
        "Pc":               Pc,
        "mdot":             mdot,
        "was_extrapolated": False,
    }
