"""Time conversion utilities for astronomical calculations.

All angles in degrees unless otherwise noted. Julian Date based on Meeus Ch.7.
"""
import numpy as np
from datetime import datetime, timezone


def calendar_to_jd(year: int, month: int, day: float) -> float:
    """Convert calendar date to Julian Date. Day can be fractional (includes UT)."""
    if month <= 2:
        year -= 1
        month += 12
    A = int(year / 100)
    B = 2 - A + int(A / 4)
    return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5


def datetime_to_jd(dt: datetime) -> float:
    """Convert Python datetime to Julian Date."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    day = dt.day + dt.hour / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0
    return calendar_to_jd(dt.year, dt.month, day)


def jd_to_centuries(jd: float) -> float:
    """Julian centuries from J2000.0."""
    return (jd - 2451545.0) / 36525.0


def jd_to_gmst(jd: float) -> float:
    """Greenwich Mean Sidereal Time in degrees (Meeus Ch.12)."""
    T = jd_to_centuries(jd)
    gmst = (280.46061837
            + 360.98564736629 * (jd - 2451545.0)
            + 0.000387933 * T * T
            - T * T * T / 38710000.0)
    return gmst % 360.0


def gmst_to_lst(gmst_deg: float, longitude_east_deg: float) -> float:
    """Local Sidereal Time from GMST and east longitude, both in degrees."""
    return (gmst_deg + longitude_east_deg) % 360.0


def lst_at_jd(jd: float, longitude_east_deg: float) -> float:
    """Convenience: LST at a given JD and longitude."""
    return gmst_to_lst(jd_to_gmst(jd), longitude_east_deg)


def jd_to_datetime(jd: float) -> datetime:
    """Convert Julian Date to UTC datetime."""
    jd = jd + 0.5
    Z = int(jd)
    F = jd - Z
    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - int(alpha / 4)
    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)

    day_frac = B - D - int(30.6001 * E) + F
    day = int(day_frac)
    frac = day_frac - day

    month = E - 1 if E < 14 else E - 13
    year = C - 4716 if month > 2 else C - 4715

    hours = frac * 24.0
    hour = int(hours)
    minutes = (hours - hour) * 60.0
    minute = int(minutes)
    second = int((minutes - minute) * 60.0)

    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


def jd_at_midnight_utc(year: int, month: int, day: int) -> float:
    """JD at 0h UT on a given date."""
    return calendar_to_jd(year, month, day)
