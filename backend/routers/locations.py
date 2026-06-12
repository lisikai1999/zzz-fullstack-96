"""CRUD endpoints for observation locations."""
from fastapi import APIRouter, HTTPException
from ..database import get_db
from ..models import LocationCreate, LocationResponse

router = APIRouter(prefix="/api/locations", tags=["locations"])


@router.get("", response_model=list[LocationResponse])
def list_locations():
    db = get_db()
    rows = db.execute("SELECT * FROM locations ORDER BY name").fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.post("", response_model=LocationResponse, status_code=201)
def create_location(loc: LocationCreate):
    db = get_db()
    cur = db.execute(
        "INSERT INTO locations (name, latitude, longitude, elevation, timezone) VALUES (?, ?, ?, ?, ?)",
        (loc.name, loc.latitude, loc.longitude, loc.elevation, loc.timezone)
    )
    db.commit()
    row = db.execute("SELECT * FROM locations WHERE id = ?", (cur.lastrowid,)).fetchone()
    db.close()
    return dict(row)


@router.get("/{location_id}", response_model=LocationResponse)
def get_location(location_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM locations WHERE id = ?", (location_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, "Location not found")
    return dict(row)


@router.put("/{location_id}", response_model=LocationResponse)
def update_location(location_id: int, loc: LocationCreate):
    db = get_db()
    db.execute(
        "UPDATE locations SET name=?, latitude=?, longitude=?, elevation=?, timezone=?, updated_at=datetime('now') WHERE id=?",
        (loc.name, loc.latitude, loc.longitude, loc.elevation, loc.timezone, location_id)
    )
    db.commit()
    row = db.execute("SELECT * FROM locations WHERE id = ?", (location_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, "Location not found")
    return dict(row)


@router.delete("/{location_id}", status_code=204)
def delete_location(location_id: int):
    db = get_db()
    db.execute("DELETE FROM locations WHERE id = ?", (location_id,))
    db.commit()
    db.close()
