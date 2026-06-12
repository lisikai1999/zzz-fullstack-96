"""Moon position and phase calculations (simplified Meeus Ch.47)."""
import numpy as np
from .time_utils import jd_to_centuries
from .coordinates import equatorial_to_horizontal, angular_separation
from .sun import sun_position


def moon_position(jd: float):
    """Low-precision Moon RA/Dec in degrees."""
    T = jd_to_centuries(jd)

    # Fundamental arguments (degrees)
    Lp = (218.3165 + 481267.8813 * T) % 360.0  # Mean longitude
    D = (297.8502 + 445267.1115 * T) % 360.0   # Mean elongation
    M = (357.5291 + 35999.0503 * T) % 360.0    # Sun mean anomaly
    Mp = (134.9634 + 477198.8676 * T) % 360.0  # Moon mean anomaly
    F = (93.2720 + 483202.0175 * T) % 360.0    # Argument of latitude

    # Convert to radians
    D_r = np.radians(D)
    M_r = np.radians(M)
    Mp_r = np.radians(Mp)
    F_r = np.radians(F)
    Lp_r = np.radians(Lp)

    # Ecliptic longitude (main terms)
    lon = Lp + (6.289 * np.sin(Mp_r)
                + 1.274 * np.sin(2 * D_r - Mp_r)
                + 0.658 * np.sin(2 * D_r)
                + 0.214 * np.sin(2 * Mp_r)
                - 0.186 * np.sin(M_r)
                - 0.114 * np.sin(2 * F_r)
                + 0.059 * np.sin(2 * D_r - 2 * Mp_r)
                + 0.057 * np.sin(2 * D_r - M_r - Mp_r))

    # Ecliptic latitude
    lat = (5.128 * np.sin(F_r)
           + 0.281 * np.sin(Mp_r + F_r)
           + 0.278 * np.sin(Mp_r - F_r)
           + 0.173 * np.sin(2 * D_r - F_r)
           + 0.055 * np.sin(2 * D_r - Mp_r + F_r))

    # Obliquity
    eps = 23.439291 - 0.0130042 * T
    eps_r = np.radians(eps)
    lon_r = np.radians(lon)
    lat_r = np.radians(lat)

    # Ecliptic → Equatorial
    ra = np.degrees(np.arctan2(
        np.sin(lon_r) * np.cos(eps_r) - np.tan(lat_r) * np.sin(eps_r),
        np.cos(lon_r)
    ))
    dec = np.degrees(np.arcsin(
        np.sin(lat_r) * np.cos(eps_r) + np.cos(lat_r) * np.sin(eps_r) * np.sin(lon_r)
    ))

    return ra % 360.0, dec


def moon_illumination(jd: float) -> float:
    """Moon illumination fraction (0=new, 1=full)."""
    T = jd_to_centuries(jd)

    D = (297.8502 + 445267.1115 * T) % 360.0
    M = (357.5291 + 35999.0503 * T) % 360.0
    Mp = (134.9634 + 477198.8676 * T) % 360.0

    D_r = np.radians(D)
    M_r = np.radians(M)
    Mp_r = np.radians(Mp)

    # Phase angle (simplified)
    i = 180.0 - D - 6.289 * np.sin(Mp_r) + 2.1 * np.sin(M_r) - 1.274 * np.sin(2 * D_r - Mp_r)
    i_r = np.radians(i)

    k = (1.0 + np.cos(i_r)) / 2.0
    return float(np.clip(k, 0.0, 1.0))


def moon_phase_name(illumination: float) -> str:
    """Human-readable phase name from illumination fraction."""
    if illumination < 0.02:
        return "New Moon"
    elif illumination < 0.25:
        return "Waxing Crescent"
    elif illumination < 0.45:
        return "First Quarter"
    elif illumination < 0.75:
        return "Waxing Gibbous"
    elif illumination < 0.98:
        if illumination > 0.75:
            return "Waning Gibbous" if illumination < 0.95 else "Full Moon"
        return "Waxing Gibbous"
    else:
        return "Full Moon"


def moon_phase_name_accurate(jd: float) -> str:
    """More accurate phase name using elongation sign."""
    T = jd_to_centuries(jd)
    D = (297.8502 + 445267.1115 * T) % 360.0
    illum = moon_illumination(jd)

    # D < 180 means waxing, D > 180 means waning
    waxing = D < 180.0

    if illum < 0.02:
        return "New Moon"
    elif illum >= 0.98:
        return "Full Moon"
    elif illum < 0.45:
        return "Waxing Crescent" if waxing else "Waning Crescent"
    elif illum < 0.55:
        return "First Quarter" if waxing else "Last Quarter"
    else:
        return "Waxing Gibbous" if waxing else "Waning Gibbous"


def moon_altitude(lat: float, lon: float, jd: float) -> float:
    """Moon altitude at given location and time."""
    ra, dec = moon_position(jd)
    alt, _ = equatorial_to_horizontal(ra, dec, lat, lon, jd)
    return alt


def moon_separation_from_target(target_ra: float, target_dec: float, jd: float) -> float:
    """Angular separation between Moon and a target (degrees)."""
    moon_ra, moon_dec = moon_position(jd)
    return angular_separation(target_ra, target_dec, moon_ra, moon_dec)
