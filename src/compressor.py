"""Manufacturer compressor-polynomial models.

The model uses the common 10-coefficient ARI/Bitzer form:

    C0 + C1*To + C2*Tc + C3*To² + C4*To*Tc + C5*Tc²
       + C6*To³ + C7*To²*Tc + C8*To*Tc² + C9*Tc³

where To is evaporating SST [°C] and Tc is condensing SDT [°C].
"""

from src import config as cfg


COMPRESSOR_REGISTRY = {
    "GSU60182VL_4": {
        "info": {
            "manufacturer": "Bitzer",
            "series": "ORBIT+",
            "refrigerant": "R32",
            "type": "Scroll, Single Compressor",
            "student": "Amirhossein Naeejnezhad",
            "nominal_note": "To=2°C, Tc=37.5°C, SH=6 K, SC=3 K",
        },
        # Bitzer result at To=2°C, Tc=37.5°C, SH=6 K, SC=3 K:
        # Qe≈47.7 kW, Pc≈9.69 kW, mdot≈664 kg/h, COP/EER≈4.92.
        "Q": [
            59389.6460596508,
            1974.93337183458,
            -434.566222820298,
            24.594529451844,
            -10.2181966843594,
            2.24802179597381,
            0.138811158034248,
            -0.128352894275604,
            -0.0267504276592594,
            -0.0326303848448441,
        ],
        "P": [
            3944.28593095782,
            31.3520381363774,
            132.717560894121,
            2.64300871010126,
            -0.107609643518827,
            -0.311738942469663,
            0.055610010979593,
            -0.0364250886707346,
            -0.0014218709419455,
            0.0217787638875563,
        ],
        "M": [
            658.966504520555,
            21.4502351673649,
            -1.91676125550773,
            0.262853524276791,
            -0.0208074335044084,
            0.0397107668517898,
            0.0020691014229269,
            0.000198789706841437,
            0.000310832175464325,
            -0.000429702580661385,
        ],
    },
    "GSD60235VL_4": {
        "info": {
            "manufacturer": "Bitzer",
            "series": "ORBIT",
            "refrigerant": "R32",
            "type": "Scroll, Single Compressor",
            "student": "Amirhossein Naeejnezhad",
            "nominal_note": "Larger alternative kept for comparison only",
        },
        "Q": [
            73446.8373756723,
            2496.8391109652,
            -379.101645156863,
            34.2514659596201,
            -11.1852584201678,
            -1.77478983916493,
            0.175476007225224,
            -0.232985716823553,
            -0.0786089613965629,
            -0.00972777782733276,
        ],
        "P": [
            5854.45124261931,
            -28.9178565078233,
            177.727197670058,
            -0.948024939028451,
            1.51054946511522,
            -0.92312886644243,
            0.0633013505269406,
            0.0518367653777389,
            -0.00623972079835261,
            0.0380171629395705,
        ],
        "M": [
            810.665540626957,
            26.7872015638543,
            -0.241273656259664,
            0.369391412843452,
            0.0185907732658233,
            -0.0040500039014634,
            0.00254078742078858,
            -0.000548479753430461,
            -0.000536412651590738,
            -0.000242090579128942,
        ],
    },
    "8FE-60Y": {
        "info": {
            "manufacturer": "Bitzer",
            "series": "Standard",
            "refrigerant": "R134a",
            "type": "Reciprocating Semi-Hermetic, Single Compressor",
            "student": "Lorenzin Filippo",
        },
        "Q": [
            165377.308884489, 6567.691188123390, -1272.576403840480,
            101.699092803528, -48.410109177167, -3.853718361953570,
            0.548606336809447, -0.815442644235109, -0.033125563119440,
            0.024750639199226,
        ],
        "P": [
            8402.374424335500, -462.027893314629, 870.151710801510,
            -20.748788074267, 28.129439365977, -8.802693245487120,
            -0.255304455885587, 0.305509000001234, -0.102852102857835,
            0.034137233095716,
        ],
        "M": [
            2660.123992744080, 108.038146913105, -4.300220736764890,
            1.884036953500180, -0.104503939241857, -0.069975946447452,
            0.016369796579762, -0.004513060551634, -0.001091857208693,
            -0.000101634482628,
        ],
    },
}


def get_compressor_coeffs(model: str | None = None) -> dict:
    """Return coefficient data for a registered compressor model."""
    model = model or cfg.COMPRESSOR_MODEL
    if model not in COMPRESSOR_REGISTRY:
        available = ", ".join(COMPRESSOR_REGISTRY)
        raise KeyError(f"Unknown compressor '{model}'. Available models: {available}")
    return COMPRESSOR_REGISTRY[model]


def poly_eval(coeff: list[float], to: float, tc: float) -> float:
    """Evaluate the 10-coefficient compressor polynomial."""
    c = coeff
    return (
        c[0]
        + c[1] * to
        + c[2] * tc
        + c[3] * to**2
        + c[4] * to * tc
        + c[5] * tc**2
        + c[6] * to**3
        + c[7] * to**2 * tc
        + c[8] * to * tc**2
        + c[9] * tc**3
    )


def _outside_configured_map_check(tevap_c: float, tcond_c: float) -> bool:
    """Flag operation outside the configured polynomial-check envelope."""
    limits = getattr(cfg, "MAP_CHECK_LIMITS", {})
    return not (
        limits.get("Tevap_C_min", -1e9) <= tevap_c <= limits.get("Tevap_C_max", 1e9)
        and limits.get("Tcond_C_min", -1e9) <= tcond_c <= limits.get("Tcond_C_max", 1e9)
    )


def compressor_polynomial_model(Tevap_C: float, Tcond_C: float, model: str | None = None) -> dict:
    """Return Qe [W], Pc [W], mdot [kg/s], and a map-check flag."""
    coeffs = get_compressor_coeffs(model)
    qe = poly_eval(coeffs["Q"], Tevap_C, Tcond_C)
    pc = poly_eval(coeffs["P"], Tevap_C, Tcond_C)
    mdot = poly_eval(coeffs["M"], Tevap_C, Tcond_C) / 3600.0

    if qe <= 0 or pc <= 0 or mdot <= 0:
        raise ValueError(
            "Compressor polynomial returned a non-physical value: "
            f"Qe={qe:.3g} W, Pc={pc:.3g} W, mdot={mdot:.3g} kg/s."
        )

    return {
        "Qe": qe,
        "Pc": pc,
        "mdot": mdot,
        "was_extrapolated": _outside_configured_map_check(Tevap_C, Tcond_C),
    }
