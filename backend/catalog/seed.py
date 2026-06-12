"""Seed the DSO catalog from JSON data files."""
import json
import os
from ..database import get_db


def _ra_hms_to_deg(h: int, m: int, s: float) -> float:
    return (h + m / 60.0 + s / 3600.0) * 15.0


def _dec_dms_to_deg(sign: str, d: int, m: int, s: float) -> float:
    deg = d + m / 60.0 + s / 3600.0
    return -deg if sign == "-" else deg


def seed_catalog():
    """Load catalog JSON files into the database if empty."""
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM dso_catalog").fetchone()[0]
    if count > 0:
        db.close()
        return

    catalog_dir = os.path.dirname(__file__)

    # Load Messier
    messier_path = os.path.join(catalog_dir, "messier.json")
    if os.path.exists(messier_path):
        with open(messier_path, "r") as f:
            messier = json.load(f)
        for obj in messier:
            ra_deg = _ra_hms_to_deg(obj["ra_h"], obj["ra_m"], obj["ra_s"])
            dec_deg = _dec_dms_to_deg(obj["dec_sign"], obj["dec_d"], obj["dec_m"], obj["dec_s"])
            db.execute(
                "INSERT OR IGNORE INTO dso_catalog (catalog, designation, common_name, ra_j2000, dec_j2000, magnitude, object_type, size_arcmin, constellation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("M", obj["designation"], obj.get("common_name"),
                 ra_deg, dec_deg, obj.get("magnitude"),
                 obj["object_type"], obj.get("size_arcmin"),
                 obj.get("constellation"))
            )

    # Load NGC/IC
    ngc_path = os.path.join(catalog_dir, "ngc_ic.json")
    if os.path.exists(ngc_path):
        with open(ngc_path, "r") as f:
            ngc = json.load(f)
        for obj in ngc:
            ra_deg = _ra_hms_to_deg(obj["ra_h"], obj["ra_m"], obj["ra_s"])
            dec_deg = _dec_dms_to_deg(obj["dec_sign"], obj["dec_d"], obj["dec_m"], obj["dec_s"])
            catalog = "NGC" if obj["designation"].startswith("NGC") else "IC"
            db.execute(
                "INSERT OR IGNORE INTO dso_catalog (catalog, designation, common_name, ra_j2000, dec_j2000, magnitude, object_type, size_arcmin, constellation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (catalog, obj["designation"], obj.get("common_name"),
                 ra_deg, dec_deg, obj.get("magnitude"),
                 obj["object_type"], obj.get("size_arcmin"),
                 obj.get("constellation"))
            )

    db.commit()
    db.close()
