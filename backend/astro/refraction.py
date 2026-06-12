"""Atmospheric refraction corrections (Bennett/Saemundsson).

All inputs/outputs in degrees.
"""
import numpy as np

STANDARD_HORIZON_REFRACTION = 0.5667  # degrees (34 arcminutes)


def refraction_bennett(apparent_alt_deg: float) -> float:
    """Atmospheric refraction for a given apparent altitude (Bennett formula).

    Returns refraction in degrees. Valid for apparent altitude > -1 degree.
    """
    if apparent_alt_deg < -1.0:
        return 0.0
    h = max(apparent_alt_deg, -0.5)
    # R in arcminutes
    R = 1.0 / np.tan(np.radians(h + 7.31 / (h + 4.4)))
    return R / 60.0  # convert to degrees


def refraction_saemundsson(geometric_alt_deg: float) -> float:
    """Refraction from geometric altitude (Saemundsson formula).

    Use this to find apparent altitude from geometric.
    Returns refraction in degrees.
    """
    if geometric_alt_deg < -1.0:
        return 0.0
    h = max(geometric_alt_deg, -0.5)
    R = 1.02 / np.tan(np.radians(h + 10.3 / (h + 5.11)))
    return R / 60.0


def apparent_altitude(geometric_alt_deg: float) -> float:
    """Convert geometric altitude to apparent (refraction-corrected)."""
    return geometric_alt_deg + refraction_saemundsson(geometric_alt_deg)


def geometric_altitude(apparent_alt_deg: float) -> float:
    """Convert apparent altitude to geometric."""
    return apparent_alt_deg - refraction_bennett(apparent_alt_deg)


def refraction_corrected(geometric_alt_deg: float, pressure_mbar: float = 1010.0,
                         temperature_c: float = 10.0) -> float:
    """Refraction with pressure/temperature correction."""
    R = refraction_saemundsson(geometric_alt_deg)
    R *= (pressure_mbar / 1010.0) * (283.0 / (273.0 + temperature_c))
    return R
