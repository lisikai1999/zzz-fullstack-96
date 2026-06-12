"""Sun position and twilight calculations (Meeus Ch.25 low-precision)."""
import numpy as np
from .time_utils import jd_to_centuries
from .coordinates import equatorial_to_horizontal


def sun_position(jd: float):
    """Low-precision solar RA/Dec in degrees (accuracy ~0.01 degree)."""
    T = jd_to_centuries(jd)

    L0 = (280.46646 + 36000.76983 * T + 0.0003032 * T**2) % 360.0
    M = (357.52911 + 35999.05029 * T - 0.0001537 * T**2) % 360.0
    M_r = np.radians(M)

    # Equation of center
    C = ((1.914602 - 0.004817 * T - 0.000014 * T**2) * np.sin(M_r)
         + (0.019993 - 0.000101 * T) * np.sin(2 * M_r)
         + 0.000289 * np.sin(3 * M_r))

    sun_lon = L0 + C  # Sun true longitude
    omega = 125.04 - 1934.136 * T
    sun_lon_app = sun_lon - 0.00569 - 0.00478 * np.sin(np.radians(omega))

    # Obliquity
    eps0 = 23.439291 - 0.0130042 * T
    eps = eps0 + 0.00256 * np.cos(np.radians(omega))

    sun_lon_r = np.radians(sun_lon_app)
    eps_r = np.radians(eps)

    ra = np.degrees(np.arctan2(np.cos(eps_r) * np.sin(sun_lon_r), np.cos(sun_lon_r)))
    dec = np.degrees(np.arcsin(np.sin(eps_r) * np.sin(sun_lon_r)))

    return ra % 360.0, dec


def sun_altitude(lat: float, lon: float, jd: float) -> float:
    """Sun altitude at given location and time."""
    ra, dec = sun_position(jd)
    alt, _ = equatorial_to_horizontal(ra, dec, lat, lon, jd)
    return alt


def _find_sun_crossing(lat: float, lon: float, jd_start: float, jd_end: float,
                       target_alt: float, rising: bool = True) -> float | None:
    """Find when the Sun crosses a target altitude using bisection."""
    steps = 200
    jds = np.linspace(jd_start, jd_end, steps)
    alts = np.array([sun_altitude(lat, lon, j) for j in jds])

    crossings = []
    for i in range(len(alts) - 1):
        if (alts[i] - target_alt) * (alts[i + 1] - target_alt) < 0:
            slope_positive = alts[i + 1] > alts[i]
            if rising and slope_positive:
                crossings.append(i)
            elif not rising and not slope_positive:
                crossings.append(i)

    if not crossings:
        return None

    idx = crossings[0]
    a, b = jds[idx], jds[idx + 1]
    for _ in range(50):
        mid = (a + b) / 2.0
        alt_mid = sun_altitude(lat, lon, mid)
        if (alt_mid - target_alt) * (sun_altitude(lat, lon, a) - target_alt) < 0:
            b = mid
        else:
            a = mid
    return (a + b) / 2.0


def twilight_times(lat: float, lon: float, jd_midnight: float) -> dict:
    """Compute twilight events for the night containing jd_midnight.

    Returns dict with keys: sunset, civil_dusk, nautical_dusk, astro_dusk,
    astro_dawn, nautical_dawn, civil_dawn, sunrise. Values are JD or None.
    """
    jd_start = jd_midnight - 0.5  # noon before
    jd_end = jd_midnight + 0.5    # noon after

    result = {}
    thresholds = [
        ("sunset", -0.8333, False),
        ("civil_dusk", -6.0, False),
        ("nautical_dusk", -12.0, False),
        ("astro_dusk", -18.0, False),
        ("astro_dawn", -18.0, True),
        ("nautical_dawn", -12.0, True),
        ("civil_dawn", -6.0, True),
        ("sunrise", -0.8333, True),
    ]

    for name, alt, rising in thresholds:
        result[name] = _find_sun_crossing(lat, lon, jd_start, jd_end, alt, rising)

    return result
