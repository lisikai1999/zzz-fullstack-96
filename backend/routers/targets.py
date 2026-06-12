"""DSO catalog query endpoints."""
from fastapi import APIRouter, Query
from ..database import get_db
from ..models import TargetResponse, TargetListResponse

router = APIRouter(prefix="/api/targets", tags=["targets"])


@router.get("", response_model=TargetListResponse)
def list_targets(
    search: str = Query("", description="Search designation or common name"),
    object_type: str = Query("", description="Filter by object type"),
    catalog: str = Query("", description="Filter by catalog (M, NGC, IC)"),
    constellation: str = Query("", description="Filter by constellation"),
    min_mag: float = Query(None, description="Minimum magnitude"),
    max_mag: float = Query(None, description="Maximum magnitude"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    db = get_db()
    conditions = []
    params = []

    if search:
        conditions.append("(designation LIKE ? OR common_name LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if object_type:
        conditions.append("object_type = ?")
        params.append(object_type)
    if catalog:
        conditions.append("catalog = ?")
        params.append(catalog)
    if constellation:
        conditions.append("constellation = ?")
        params.append(constellation)
    if min_mag is not None:
        conditions.append("magnitude >= ?")
        params.append(min_mag)
    if max_mag is not None:
        conditions.append("magnitude <= ?")
        params.append(max_mag)

    where = " WHERE " + " AND ".join(conditions) if conditions else ""

    total = db.execute(f"SELECT COUNT(*) FROM dso_catalog{where}", params).fetchone()[0]
    rows = db.execute(
        f"SELECT * FROM dso_catalog{where} ORDER BY magnitude ASC NULLS LAST LIMIT ? OFFSET ?",
        params + [limit, offset]
    ).fetchall()
    db.close()

    return {"items": [dict(r) for r in rows], "total": total}


@router.get("/{target_id}", response_model=TargetResponse)
def get_target(target_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM dso_catalog WHERE id = ?", (target_id,)).fetchone()
    db.close()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(404, "Target not found")
    return dict(row)
