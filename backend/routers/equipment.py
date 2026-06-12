"""Equipment and FOV endpoints."""
from fastapi import APIRouter, Query, HTTPException
from ..database import get_db
from ..models import FovResponse, EquipmentProfileCreate, EquipmentProfileResponse
from ..astro.fov import compute_fov

router = APIRouter(prefix="/api/equipment", tags=["equipment"])


@router.get("/fov", response_model=FovResponse)
def get_fov(
    focal_length_mm: float = Query(..., gt=0),
    sensor_width_mm: float = Query(..., gt=0),
    sensor_height_mm: float = Query(..., gt=0),
):
    result = compute_fov(focal_length_mm, sensor_width_mm, sensor_height_mm)
    return result


@router.get("/profiles", response_model=list[EquipmentProfileResponse])
def list_profiles():
    db = get_db()
    rows = db.execute("SELECT * FROM equipment_profiles ORDER BY name").fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.post("/profiles", response_model=EquipmentProfileResponse, status_code=201)
def create_profile(profile: EquipmentProfileCreate):
    db = get_db()
    cur = db.execute(
        "INSERT INTO equipment_profiles (name, focal_length_mm, sensor_width_mm, sensor_height_mm) VALUES (?, ?, ?, ?)",
        (profile.name, profile.focal_length_mm, profile.sensor_width_mm, profile.sensor_height_mm)
    )
    db.commit()
    row = db.execute("SELECT * FROM equipment_profiles WHERE id = ?", (cur.lastrowid,)).fetchone()
    db.close()
    return dict(row)


@router.delete("/profiles/{profile_id}", status_code=204)
def delete_profile(profile_id: int):
    db = get_db()
    db.execute("DELETE FROM equipment_profiles WHERE id = ?", (profile_id,))
    db.commit()
    db.close()
