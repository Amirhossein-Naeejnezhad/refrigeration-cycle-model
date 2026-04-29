# ============================================================
# Refrigeration Cycle Model Package
# ============================================================
"""
Modular vapour-compression refrigeration cycle model.

Supports any application from the Refrigeration and Heat Pump
Technology project work, including:
  - Any CoolProp-supported refrigerant
  - Bitzer / Copeland / Frascold 10-coefficient polynomial compressor model
  - Air or water/brine secondary fluid on evaporator and condenser
  - LMTD-based heat exchanger matching
  - Iterative operating-point solver
  - P-h and T-s thermodynamic diagrams

Active project settings are controlled entirely via src/config.py.
"""

__version__ = "2.0.0"   # universal-model branch
__author__  = "Amirhossein Naeejnezhad"
