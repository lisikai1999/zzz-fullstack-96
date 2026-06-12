"""Observation planning endpoints: windows, calendar, tonight's best."""
import numpy as np
from datetime import date as date_type
from fastapi import APIRouter, Query, HTTPException
from ..database import get_db
from ..models import (
    ObservationWindowResponse, CalendarResponse, CalendarDayResponse,
    TonightResponse, TonightTarget,
)
from ..astro.time_utils import calendar_to_jd, jd_to_datetime
from ..astro.coordinates import full_transform, apparent_position
from ..astro.rise_set import altitude_curve
from ..astro.sun import twilight_times, sun_altitude
from ..astro.moon import moon_illumination, moon_separation_from_target, moon_altitude

router = APIRouter(prefix="/api/planning", tags=["planning"])


def _get_location(location_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM locations WHERE id = ?", (location_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, "Location not found")
    return dict(row)


def _get_target(target_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM dso_catalog WHERE id = ?", (target_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, "Target not found")
    return dict(row)


def _compute_quality(target_alt: float, sun_alt: float,
                     moon_illum: float, moon_sep: float) -> float:
    """Compute observation quality score (0-1)."""
    # Altitude score: linear from 15° (0) to 60° (1)
    alt_score = max(0.0, min(1.0, (target_alt - 15.0) / 45.0))

    # Darkness score
    if sun_alt > -12.0:
        dark_score = 0.0
    elif sun_alt > -18.0:
        dark_score = (-sun_alt - 12.0) / 6.0
    else:
        dark_score = 1.0

    # Moon score: penalize bright moon close to target
    moon_score = 1.0
    if moon_illum > 0.1:
        proximity_penalty = max(0.0, 1.0 - moon_sep / 90.0) * moon_illum
        moon_score = 1.0 - proximity_penalty * 0.7

    quality = alt_score * 0.35 + dark_score * 0.40 + moon_score * 0.25
    return round(quality, 3)


def _compute_window(target, loc, jd_midnight):
    """Compute observation window for a target on a given night."""
    lat, lon = loc["latitude"], loc["longitude"]
    ra, dec = target["ra_j2000"], target["dec_j2000"]

    # Night window: sunset (evening before) to sunrise (morning after)
    tw = twilight_times(lat, lon, jd_midnight)
    if not tw["sunset"] or not tw["sunrise"]:
        return None

    jd_start = tw["sunset"]
    jd_end = tw["sunrise"]

    # If sunrise is before sunset in JD (timezone offset issue), get next day's sunrise
    if jd_end <= jd_start:
        tw_next = twilight_times(lat, lon, jd_midnight + 1.0)
        jd_end = tw_next["sunrise"] if tw_next["sunrise"] else jd_start + 0.5

    # Sample every 10 minutes through the night
    step = 10.0 / 1440.0
    n_steps = int((jd_end - jd_start) / step) + 1
    jd_times = np.linspace(jd_start, jd_end, n_steps)

    # Get apparent position once for the night
    ra_app, dec_app = apparent_position(ra, dec, jd_midnight)

    best_score = 0.0
    best_jd = jd_midnight
    window_start = None
    window_end = None
    peak_alt = 0.0
    scores = []

    moon_illum = moon_illumination(jd_midnight)

    from ..astro.coordinates import equatorial_to_horizontal

    for jd in jd_times:
        alt, _ = equatorial_to_horizontal(ra_app, dec_app, lat, lon, jd)
        s_alt = sun_altitude(lat, lon, jd)
        moon_sep = moon_separation_from_target(ra_app, dec_app, jd)

        score = _compute_quality(alt, s_alt, moon_illum, moon_sep)
        scores.append((jd, score, alt))

        if score > best_score:
            best_score = score
            best_jd = jd
            peak_alt = alt

    # Find contiguous window above threshold (score >= 0.4)
    threshold = 0.4
    in_window = False
    for jd, score, alt in scores:
        if score >= threshold and not in_window:
            window_start = jd
            in_window = True
        elif score < threshold and in_window:
            window_end = jd
            break
    if in_window and window_end is None:
        window_end = jd_end

    moon_sep = moon_separation_from_target(ra_app, dec_app, best_jd)

    return {
        "optimal_start": window_start,
        "optimal_end": window_end,
        "peak_time": best_jd,
        "peak_altitude": peak_alt,
        "moon_separation_deg": moon_sep,
        "quality_score": best_score,
    }


@router.get("/observation-window", response_model=ObservationWindowResponse)
def get_observation_window(
    target_id: int = Query(...),
    location_id: int = Query(...),
    date: str = Query(...),
):
    loc = _get_location(location_id)
    target = _get_target(target_id)
    parts = date.split("-")
    jd_midnight = calendar_to_jd(int(parts[0]), int(parts[1]), int(parts[2]))

    result = _compute_window(target, loc, jd_midnight)
    if not result:
        return ObservationWindowResponse(
            optimal_start=None, optimal_end=None, peak_time=None,
            peak_altitude=0, moon_separation_deg=0, quality_score=0
        )

    return ObservationWindowResponse(
        optimal_start=jd_to_datetime(result["optimal_start"]).isoformat() if result["optimal_start"] else None,
        optimal_end=jd_to_datetime(result["optimal_end"]).isoformat() if result["optimal_end"] else None,
        peak_time=jd_to_datetime(result["peak_time"]).isoformat() if result["peak_time"] else None,
        peak_altitude=round(result["peak_altitude"], 2),
        moon_separation_deg=round(result["moon_separation_deg"], 1),
        quality_score=result["quality_score"],
    )


@router.get("/calendar", response_model=CalendarResponse)
def get_calendar(
    target_id: int = Query(...),
    location_id: int = Query(...),
    year: int = Query(...),
    month: int = Query(...),
):
    import calendar
    loc = _get_location(location_id)
    target = _get_target(target_id)

    _, days_in_month = calendar.monthrange(year, month)
    days = []

    for day in range(1, days_in_month + 1):
        jd = calendar_to_jd(year, month, day)
        result = _compute_window(target, loc, jd)

        if result and result["quality_score"] > 0:
            window_hours = 0.0
            if result["optimal_start"] and result["optimal_end"]:
                window_hours = (result["optimal_end"] - result["optimal_start"]) * 24.0
            days.append(CalendarDayResponse(
                date=f"{year:04d}-{month:02d}-{day:02d}",
                quality_score=result["quality_score"],
                moon_illumination=round(moon_illumination(jd), 2),
                window_hours=round(window_hours, 1),
                peak_alt=round(result["peak_altitude"], 1),
            ))
        else:
            days.append(CalendarDayResponse(
                date=f"{year:04d}-{month:02d}-{day:02d}",
                quality_score=0.0,
                moon_illumination=round(moon_illumination(jd), 2),
                window_hours=0.0,
                peak_alt=0.0,
            ))

    return CalendarResponse(days=days)


@router.get("/tonight", response_model=TonightResponse)
def get_tonight(
    location_id: int = Query(...),
    date: str = Query(...),
    min_altitude: float = Query(30.0),
    min_score: float = Query(0.3),
    limit: int = Query(20),
):
    loc = _get_location(location_id)
    parts = date.split("-")
    jd_midnight = calendar_to_jd(int(parts[0]), int(parts[1]), int(parts[2]))

    db = get_db()
    targets = db.execute("SELECT * FROM dso_catalog ORDER BY magnitude ASC NULLS LAST").fetchall()
    db.close()

    results = []
    for t in targets:
        target = dict(t)
        result = _compute_window(target, loc, jd_midnight)
        if not result:
            continue
        if result["peak_altitude"] < min_altitude:
            continue
        if result["quality_score"] < min_score:
            continue

        results.append(TonightTarget(
            target_id=target["id"],
            designation=target["designation"],
            common_name=target["common_name"],
            quality_score=result["quality_score"],
            optimal_start=jd_to_datetime(result["optimal_start"]).isoformat() if result["optimal_start"] else None,
            optimal_end=jd_to_datetime(result["optimal_end"]).isoformat() if result["optimal_end"] else None,
            peak_altitude=round(result["peak_altitude"], 1),
            moon_separation=round(result["moon_separation_deg"], 1),
        ))

    results.sort(key=lambda x: x.quality_score, reverse=True)
    return TonightResponse(targets=results[:limit])
