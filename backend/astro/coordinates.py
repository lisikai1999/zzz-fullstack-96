"""Coordinate transformations: precession, nutation, equatorial ↔ horizontal.

All angles in degrees. NumPy vectorized where practical.
"""
import numpy as np
from .time_utils import jd_to_centuries, lst_at_jd


def _deg(rad):
    return np.degrees(rad)


def _rad(deg):
    return np.radians(deg)


def precess_j2000(ra_j2000: float, dec_j2000: float, jd: float):
    """Apply precession from J2000.0 to the epoch of jd (Lieske)."""
    T = jd_to_centuries(jd)
    zeta_A = (0.6406161 * T + 0.0000839 * T**2 + 0.0000050 * T**3)
    z_A = (0.6406161 * T + 0.0003041 * T**2 + 0.0000051 * T**3)
    theta_A = (0.5567530 * T - 0.0001185 * T**2 - 0.0000116 * T**3)

    ra0 = _rad(ra_j2000)
    dec0 = _rad(dec_j2000)
    zeta = _rad(zeta_A)
    z = _rad(z_A)
    theta = _rad(theta_A)

    A = np.cos(dec0) * np.sin(ra0 + zeta)
    B = np.cos(theta) * np.cos(dec0) * np.cos(ra0 + zeta) - np.sin(theta) * np.sin(dec0)
    C = np.sin(theta) * np.cos(dec0) * np.cos(ra0 + zeta) + np.cos(theta) * np.sin(dec0)

    ra_now = _deg(np.arctan2(A, B)) + z_A
    dec_now = _deg(np.arcsin(C))
    return ra_now % 360.0, dec_now


def nutation(jd: float):
    """Compute nutation in longitude (Δψ) and obliquity (Δε) in degrees.

    Uses the 5 largest terms of IAU 1980 nutation series.
    Also returns true obliquity ε.
    """
    T = jd_to_centuries(jd)

    # Fundamental arguments (degrees)
    omega = 125.04452 - 1934.136261 * T  # longitude of ascending node of Moon
    L0 = 280.4665 + 36000.7698 * T  # mean longitude of Sun
    Lp = 218.3165 + 481267.8813 * T  # mean longitude of Moon
    D = 297.85036 + 445267.111480 * T  # mean elongation of Moon
    M = 357.52772 + 35999.050340 * T  # mean anomaly of Sun
    Mp = 134.96298 + 477198.867398 * T  # mean anomaly of Moon
    F = 93.27191 + 483202.017538 * T  # Moon argument of latitude

    omega_r = _rad(omega)
    two_L0 = _rad(2 * L0)
    two_Lp = _rad(2 * Lp)
    two_omega = _rad(2 * omega)
    M_r = _rad(M)

    # Δψ in arcseconds
    dpsi = (-17.20 * np.sin(omega_r)
            - 1.32 * np.sin(two_L0)
            - 0.23 * np.sin(two_Lp)
            + 0.21 * np.sin(two_omega)
            + 0.12 * np.sin(M_r))

    # Δε in arcseconds
    deps = (9.20 * np.cos(omega_r)
            + 0.57 * np.cos(two_L0)
            + 0.10 * np.cos(two_Lp)
            - 0.09 * np.cos(two_omega))

    dpsi_deg = dpsi / 3600.0
    deps_deg = deps / 3600.0

    # Mean obliquity (Meeus eq 22.2)
    eps0 = 23.439291 - 0.0130042 * T - 1.64e-7 * T**2 + 5.04e-7 * T**3
    eps = eps0 + deps_deg

    return dpsi_deg, deps_deg, eps


def apply_nutation_ra_dec(ra: float, dec: float, jd: float):
    """Apply nutation correction to RA/Dec."""
    dpsi, deps, eps = nutation(jd)
    eps_r = _rad(eps)
    ra_r = _rad(ra)
    dec_r = _rad(dec)

    # Corrections in arcseconds
    dra = (np.cos(eps_r) + np.sin(eps_r) * np.sin(ra_r) * np.tan(dec_r)) * dpsi * 3600.0 \
        - (np.cos(ra_r) * np.tan(dec_r)) * deps * 3600.0
    ddec = np.sin(eps_r) * np.cos(ra_r) * dpsi * 3600.0 \
         + np.sin(ra_r) * deps * 3600.0

    ra_corrected = ra + dra / 3600.0
    dec_corrected = dec + ddec / 3600.0
    return ra_corrected % 360.0, dec_corrected


def equatorial_to_horizontal(ra: float, dec: float, lat: float, lon: float, jd: float):
    """Convert apparent RA/Dec to Alt/Az for a given location and time.

    Returns (altitude_deg, azimuth_deg) where Az is measured from North clockwise.
    """
    lst = lst_at_jd(jd, lon)
    ha = _rad(lst - ra)
    dec_r = _rad(dec)
    lat_r = _rad(lat)

    sin_alt = np.sin(dec_r) * np.sin(lat_r) + np.cos(dec_r) * np.cos(lat_r) * np.cos(ha)
    alt = _deg(np.arcsin(np.clip(sin_alt, -1, 1)))

    cos_az_num = np.sin(dec_r) - np.sin(lat_r) * np.sin(_rad(alt))
    cos_az_den = np.cos(lat_r) * np.cos(_rad(alt))

    az = _deg(np.arctan2(-np.sin(ha) * np.cos(dec_r), cos_az_num))
    az = az % 360.0

    return alt, az


def apparent_position(ra_j2000: float, dec_j2000: float, jd: float):
    """Full pipeline: J2000 → precession → nutation → apparent RA/Dec."""
    ra_p, dec_p = precess_j2000(ra_j2000, dec_j2000, jd)
    ra_a, dec_a = apply_nutation_ra_dec(ra_p, dec_p, jd)
    return ra_a, dec_a


def full_transform(ra_j2000: float, dec_j2000: float, lat: float, lon: float, jd: float):
    """J2000 equatorial → horizontal (Alt/Az) with all corrections."""
    ra_a, dec_a = apparent_position(ra_j2000, dec_j2000, jd)
    return equatorial_to_horizontal(ra_a, dec_a, lat, lon, jd)


def batch_full_transform(ra_arr, dec_arr, lat: float, lon: float, jd: float):
    """Vectorized J2000 → horizontal for arrays of RA/Dec.

    Args:
        ra_arr, dec_arr: numpy arrays of J2000 coordinates in degrees
        lat, lon: observer location
        jd: Julian Date

    Returns:
        (altitudes, azimuths) as numpy arrays in degrees
    """
    ra_arr = np.asarray(ra_arr, dtype=np.float64)
    dec_arr = np.asarray(dec_arr, dtype=np.float64)

    T = jd_to_centuries(jd)
    zeta_A = 0.6406161 * T + 0.0000839 * T**2 + 0.0000050 * T**3
    z_A = 0.6406161 * T + 0.0003041 * T**2 + 0.0000051 * T**3
    theta_A = 0.5567530 * T - 0.0001185 * T**2 - 0.0000116 * T**3

    zeta = _rad(zeta_A)
    z = _rad(z_A)
    theta = _rad(theta_A)

    ra0 = _rad(ra_arr)
    dec0 = _rad(dec_arr)

    A = np.cos(dec0) * np.sin(ra0 + zeta)
    B = np.cos(theta) * np.cos(dec0) * np.cos(ra0 + zeta) - np.sin(theta) * np.sin(dec0)
    C = np.sin(theta) * np.cos(dec0) * np.cos(ra0 + zeta) + np.cos(theta) * np.sin(dec0)

    ra_p = (_deg(np.arctan2(A, B)) + z_A) % 360.0
    dec_p = _deg(np.arcsin(np.clip(C, -1, 1)))

    # Nutation (computed once for this JD)
    dpsi_deg, deps_deg, eps = nutation(jd)
    eps_r = _rad(eps)
    ra_pr = _rad(ra_p)
    dec_pr = _rad(dec_p)

    dra = ((np.cos(eps_r) + np.sin(eps_r) * np.sin(ra_pr) * np.tan(dec_pr)) * dpsi_deg * 3600.0
           - (np.cos(ra_pr) * np.tan(dec_pr)) * deps_deg * 3600.0)
    ddec = (np.sin(eps_r) * np.cos(ra_pr) * dpsi_deg * 3600.0
            + np.sin(ra_pr) * deps_deg * 3600.0)

    ra_a = (ra_p + dra / 3600.0) % 360.0
    dec_a = dec_p + ddec / 3600.0

    # Equatorial → Horizontal
    lst = lst_at_jd(jd, lon)
    ha = _rad(lst - ra_a)
    dec_r = _rad(dec_a)
    lat_r = _rad(lat)

    sin_alt = np.sin(dec_r) * np.sin(lat_r) + np.cos(dec_r) * np.cos(lat_r) * np.cos(ha)
    alt = _deg(np.arcsin(np.clip(sin_alt, -1, 1)))

    cos_az_num = np.sin(dec_r) - np.sin(lat_r) * np.sin(_rad(alt))
    az = _deg(np.arctan2(-np.sin(ha) * np.cos(dec_r), cos_az_num)) % 360.0

    return alt, az


def angular_separation(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """Angular separation between two points on the sky (degrees)."""
    ra1_r, dec1_r = _rad(ra1), _rad(dec1)
    ra2_r, dec2_r = _rad(ra2), _rad(dec2)
    cos_sep = (np.sin(dec1_r) * np.sin(dec2_r)
               + np.cos(dec1_r) * np.cos(dec2_r) * np.cos(ra1_r - ra2_r))
    return _deg(np.arccos(np.clip(cos_sep, -1, 1)))
