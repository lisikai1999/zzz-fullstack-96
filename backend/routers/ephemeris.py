"""Ephemeris calculation endpoints: altitude curves, rise/set, twilight, moon."""
from datetime import date as date_type
import numpy as np
from fastapi import APIRouter, Query, HTTPException
from ..database import get_db
from ..models import (
    AltitudeCurveResponse, AltitudePoint, TwilightResponse,
    MoonResponse, PositionResponse,
)
from ..astro.time_utils import calendar_to_jd, jd_to_datetime, datetime_to_jd
from ..astro.coordinates import full_transform, apparent_position, batch_full_transform
from ..astro.rise_set import rise_transit_set, altitude_curve
from ..astro.sun import twilight_times, sun_altitude
from ..astro.moon import (
    moon_position, moon_illumination, moon_phase_name_accurate,
    moon_altitude as calc_moon_alt,
)
from ..astro.coordinates import equatorial_to_horizontal

router = APIRouter(prefix="/api/ephemeris", tags=["ephemeris"])


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


@router.get("/altitude-curve", response_model=AltitudeCurveResponse)
def get_altitude_curve(
    target_id: int = Query(...),
    location_id: int = Query(...),
    date: str = Query(..., description="YYYY-MM-DD"),
):
    loc = _get_location(location_id)
    target = _get_target(target_id)
    lat, lon = loc["latitude"], loc["longitude"]
    ra, dec = target["ra_j2000"], target["dec_j2000"]

    parts = date.split("-")
    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    jd_midnight = calendar_to_jd(year, month, day)

    # Compute altitude curve from sunset-2h to sunrise+2h (roughly 16h window)
    jd_start = jd_midnight - 0.25  # 6pm previous day
    jd_end = jd_midnight + 0.5     # noon next

    jd_times, alts, azs = altitude_curve(ra, dec, lat, lon, jd_start, jd_end, step_minutes=5.0)

    points = []
    for i in range(len(jd_times)):
        dt = jd_to_datetime(jd_times[i])
        points.append(AltitudePoint(
            time_utc=dt.isoformat(),
            altitude=round(float(alts[i]), 3),
            azimuth=round(float(azs[i]), 2),
        ))

    # Rise/transit/set
    rts = rise_transit_set(ra, dec, lat, lon, jd_midnight)

    rise_str = jd_to_datetime(rts["rise"]).isoformat() if rts["rise"] else None
    transit_str = jd_to_datetime(rts["transit"]).isoformat() if rts["transit"] else None
    set_str = jd_to_datetime(rts["set"]).isoformat() if rts["set"] else None

    max_alt = float(alts.max())

    return AltitudeCurveResponse(
        points=points,
        rise_time=rise_str,
        transit_time=transit_str,
        set_time=set_str,
        max_altitude=round(max_alt, 2),
        is_circumpolar=rts["is_circumpolar"],
        never_rises=rts["never_rises"],
    )


@router.get("/rise-transit-set")
def get_rise_transit_set(
    target_id: int = Query(...),
    location_id: int = Query(...),
    date: str = Query(...),
):
    loc = _get_location(location_id)
    target = _get_target(target_id)
    parts = date.split("-")
    jd_midnight = calendar_to_jd(int(parts[0]), int(parts[1]), int(parts[2]))

    rts = rise_transit_set(
        target["ra_j2000"], target["dec_j2000"],
        loc["latitude"], loc["longitude"], jd_midnight
    )

    return {
        "rise": jd_to_datetime(rts["rise"]).isoformat() if rts["rise"] else None,
        "transit": jd_to_datetime(rts["transit"]).isoformat() if rts["transit"] else None,
        "set": jd_to_datetime(rts["set"]).isoformat() if rts["set"] else None,
        "is_circumpolar": rts["is_circumpolar"],
        "never_rises": rts["never_rises"],
    }


@router.get("/twilight", response_model=TwilightResponse)
def get_twilight(
    location_id: int = Query(...),
    date: str = Query(...),
):
    loc = _get_location(location_id)
    parts = date.split("-")
    jd_midnight = calendar_to_jd(int(parts[0]), int(parts[1]), int(parts[2]))

    tw = twilight_times(loc["latitude"], loc["longitude"], jd_midnight)

    result = {}
    for key, jd_val in tw.items():
        result[key] = jd_to_datetime(jd_val).isoformat() if jd_val else None

    return result


@router.get("/moon", response_model=MoonResponse)
def get_moon(
    location_id: int = Query(...),
    date: str = Query(...),
):
    loc = _get_location(location_id)
    lat, lon = loc["latitude"], loc["longitude"]
    parts = date.split("-")
    jd_midnight = calendar_to_jd(int(parts[0]), int(parts[1]), int(parts[2]))

    illum = moon_illumination(jd_midnight)
    phase = moon_phase_name_accurate(jd_midnight)

    # Moon altitude curve over the night
    jd_start = jd_midnight - 0.25
    jd_end = jd_midnight + 0.5
    import numpy as np
    jd_times = np.linspace(jd_start, jd_end, 145)  # 7.5 min steps

    moon_points = []
    for jd in jd_times:
        alt = calc_moon_alt(lat, lon, jd)
        moon_ra, moon_dec = moon_position(jd)
        _, az = equatorial_to_horizontal(moon_ra, moon_dec, lat, lon, jd)
        moon_points.append(AltitudePoint(
            time_utc=jd_to_datetime(jd).isoformat(),
            altitude=round(alt, 2),
            azimuth=round(az, 2),
        ))

    # Find Moon rise/set by scanning
    rise_jd = None
    set_jd = None
    prev_alt = calc_moon_alt(lat, lon, jd_start)
    for jd in jd_times[1:]:
        alt = calc_moon_alt(lat, lon, jd)
        if prev_alt < 0 and alt >= 0 and rise_jd is None:
            rise_jd = jd
        if prev_alt >= 0 and alt < 0 and set_jd is None:
            set_jd = jd
        prev_alt = alt

    return MoonResponse(
        phase_name=phase,
        illumination=round(illum, 3),
        rise_time=jd_to_datetime(rise_jd).isoformat() if rise_jd else None,
        set_time=jd_to_datetime(set_jd).isoformat() if set_jd else None,
        altitude_curve=moon_points,
    )


@router.get("/position", response_model=PositionResponse)
def get_current_position(
    target_id: int = Query(...),
    location_id: int = Query(...),
    datetime_utc: str = Query(None, description="ISO datetime, defaults to now"),
):
    from datetime import datetime, timezone
    loc = _get_location(location_id)
    target = _get_target(target_id)

    if datetime_utc:
        from datetime import datetime as dt_cls
        dt = dt_cls.fromisoformat(datetime_utc.replace("Z", "+00:00"))
        jd = datetime_to_jd(dt)
    else:
        jd = datetime_to_jd(datetime.now(timezone.utc))

    alt, az = full_transform(
        target["ra_j2000"], target["dec_j2000"],
        loc["latitude"], loc["longitude"], jd
    )

    return PositionResponse(
        altitude=round(alt, 3),
        azimuth=round(az, 2),
        is_above_horizon=alt > 0,
    )


@router.get("/visible-targets")
def get_visible_targets(
    location_id: int = Query(...),
    datetime_utc: str = Query(None, description="ISO datetime, defaults to now"),
):
    """Batch compute alt/az for ALL catalog targets. Returns only those above horizon.

    This replaces per-target /position calls for star chart rendering.
    Uses vectorized NumPy — computes 300+ targets in <10ms.
    """
    from datetime import datetime, timezone as tz
    loc = _get_location(location_id)
    lat, lon = loc["latitude"], loc["longitude"]

    if datetime_utc:
        from datetime import datetime as dt_cls
        dt = dt_cls.fromisoformat(datetime_utc.replace("Z", "+00:00"))
        jd = datetime_to_jd(dt)
    else:
        jd = datetime_to_jd(datetime.now(tz.utc))

    db = get_db()
    rows = db.execute(
        "SELECT id, catalog, designation, common_name, ra_j2000, dec_j2000, magnitude, object_type, size_arcmin FROM dso_catalog"
    ).fetchall()
    db.close()

    if not rows:
        return {"targets": []}

    ids = [r["id"] for r in rows]
    catalogs = [r["catalog"] for r in rows]
    designations = [r["designation"] for r in rows]
    common_names = [r["common_name"] for r in rows]
    magnitudes = [r["magnitude"] for r in rows]
    object_types = [r["object_type"] for r in rows]
    sizes = [r["size_arcmin"] for r in rows]
    ra_arr = np.array([r["ra_j2000"] for r in rows])
    dec_arr = np.array([r["dec_j2000"] for r in rows])

    alts, azs = batch_full_transform(ra_arr, dec_arr, lat, lon, jd)

    # Filter to above horizon
    visible = []
    for i in range(len(ids)):
        if alts[i] > 0:
            visible.append({
                "id": ids[i],
                "catalog": catalogs[i],
                "designation": designations[i],
                "common_name": common_names[i],
                "magnitude": magnitudes[i],
                "object_type": object_types[i],
                "size_arcmin": sizes[i],
                "altitude": round(float(alts[i]), 2),
                "azimuth": round(float(azs[i]), 2),
            })

    return {"targets": visible, "total_catalog": len(ids), "visible_count": len(visible)}
