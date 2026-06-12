"""Rise, transit, and set time calculations with atmospheric refraction."""
import numpy as np
from .time_utils import jd_to_centuries, lst_at_jd, jd_at_midnight_utc
from .coordinates import apparent_position, equatorial_to_horizontal
from .refraction import STANDARD_HORIZON_REFRACTION


def rise_transit_set(ra_j2000: float, dec_j2000: float, lat: float, lon: float,
                     jd_date: float, h0: float = -STANDARD_HORIZON_REFRACTION):
    """Compute rise, transit, set times for a celestial object.

    Args:
        ra_j2000, dec_j2000: J2000 coordinates in degrees
        lat, lon: observer location in degrees
        jd_date: JD at 0h UT of the date
        h0: altitude threshold for rise/set (degrees), default includes refraction

    Returns:
        dict with keys: rise (JD|None), transit (JD|None), set (JD|None),
        is_circumpolar (bool), never_rises (bool)
    """
    # Get apparent position for the date
    ra, dec = apparent_position(ra_j2000, dec_j2000, jd_date + 0.5)

    lat_r = np.radians(lat)
    dec_r = np.radians(dec)
    h0_r = np.radians(h0)

    # Hour angle at rise/set
    cos_H0 = (np.sin(h0_r) - np.sin(lat_r) * np.sin(dec_r)) / (np.cos(lat_r) * np.cos(dec_r))

    if cos_H0 < -1.0:
        return {"rise": None, "transit": None, "set": None,
                "is_circumpolar": True, "never_rises": False}
    if cos_H0 > 1.0:
        return {"rise": None, "transit": None, "set": None,
                "is_circumpolar": False, "never_rises": True}

    H0 = np.degrees(np.arccos(cos_H0))

    # Sidereal time at 0h UT
    lst_0 = lst_at_jd(jd_date, lon)

    # Approximate transit (fraction of day)
    m0 = (ra - lst_0) / 360.0
    m1 = m0 - H0 / 360.0  # rise
    m2 = m0 + H0 / 360.0  # set

    # Normalize to [0, 1)
    m0 = m0 % 1.0
    m1 = m1 % 1.0
    m2 = m2 % 1.0

    # Iterative refinement (3 iterations usually sufficient)
    for _ in range(5):
        # Transit refinement
        lst_m0 = (lst_0 + 360.985647 * m0) % 360.0
        ha_m0 = lst_m0 - ra
        if ha_m0 > 180:
            ha_m0 -= 360
        elif ha_m0 < -180:
            ha_m0 += 360
        dm0 = -ha_m0 / 360.0
        m0 = (m0 + dm0) % 1.0

        # Rise refinement
        jd_m1 = jd_date + m1
        alt_m1, _ = equatorial_to_horizontal(ra, dec, lat, lon, jd_m1)
        dm1 = (alt_m1 - h0) / (360.0 * np.cos(dec_r) * np.cos(lat_r) *
               np.sin(np.radians(lst_at_jd(jd_m1, lon) - ra)))
        if abs(dm1) < 1e-6:
            break
        m1 = (m1 + dm1) % 1.0

        # Set refinement
        jd_m2 = jd_date + m2
        alt_m2, _ = equatorial_to_horizontal(ra, dec, lat, lon, jd_m2)
        dm2 = (alt_m2 - h0) / (360.0 * np.cos(dec_r) * np.cos(lat_r) *
               np.sin(np.radians(lst_at_jd(jd_m2, lon) - ra)))
        if abs(dm2) < 1e-6:
            break
        m2 = (m2 + dm2) % 1.0

    return {
        "rise": jd_date + m1,
        "transit": jd_date + m0,
        "set": jd_date + m2,
        "is_circumpolar": False,
        "never_rises": False,
    }


def altitude_curve(ra_j2000: float, dec_j2000: float, lat: float, lon: float,
                   jd_start: float, jd_end: float, step_minutes: float = 5.0):
    """Compute altitude and azimuth over a time range.

    Returns arrays of (jd_times, altitudes, azimuths).
    """
    step_days = step_minutes / 1440.0
    n_steps = int((jd_end - jd_start) / step_days) + 1
    jd_times = np.linspace(jd_start, jd_end, n_steps)

    altitudes = np.zeros(n_steps)
    azimuths = np.zeros(n_steps)

    # Get apparent position at midpoint (good enough for one night)
    jd_mid = (jd_start + jd_end) / 2.0
    ra_app, dec_app = apparent_position(ra_j2000, dec_j2000, jd_mid)

    for i, jd in enumerate(jd_times):
        alt, az = equatorial_to_horizontal(ra_app, dec_app, lat, lon, jd)
        altitudes[i] = alt
        azimuths[i] = az

    return jd_times, altitudes, azimuths


def find_transit_altitude(ra_j2000: float, dec_j2000: float, lat: float) -> float:
    """Maximum possible altitude (at transit) for an object from a given latitude."""
    dec = np.radians(dec_j2000)
    lat_r = np.radians(lat)
    return 90.0 - abs(lat - dec_j2000)
