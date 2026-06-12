"""Pydantic models for request/response schemas."""
from pydantic import BaseModel
from typing import Optional


class LocationCreate(BaseModel):
    name: str
    latitude: float
    longitude: float
    elevation: float = 0.0
    timezone: str = "UTC"


class LocationResponse(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    elevation: float
    timezone: str


class TargetResponse(BaseModel):
    id: int
    catalog: str
    designation: str
    common_name: Optional[str]
    ra_j2000: float
    dec_j2000: float
    magnitude: Optional[float]
    object_type: str
    size_arcmin: Optional[float]
    constellation: Optional[str]


class TargetListResponse(BaseModel):
    items: list[TargetResponse]
    total: int


class PositionResponse(BaseModel):
    altitude: float
    azimuth: float
    is_above_horizon: bool


class AltitudePoint(BaseModel):
    time_utc: str
    altitude: float
    azimuth: float


class AltitudeCurveResponse(BaseModel):
    points: list[AltitudePoint]
    rise_time: Optional[str]
    transit_time: Optional[str]
    set_time: Optional[str]
    max_altitude: float
    is_circumpolar: bool
    never_rises: bool


class TwilightResponse(BaseModel):
    sunset: Optional[str]
    civil_dusk: Optional[str]
    nautical_dusk: Optional[str]
    astro_dusk: Optional[str]
    astro_dawn: Optional[str]
    nautical_dawn: Optional[str]
    civil_dawn: Optional[str]
    sunrise: Optional[str]


class MoonResponse(BaseModel):
    phase_name: str
    illumination: float
    rise_time: Optional[str]
    set_time: Optional[str]
    altitude_curve: list[AltitudePoint]


class ObservationWindowResponse(BaseModel):
    optimal_start: Optional[str]
    optimal_end: Optional[str]
    peak_time: Optional[str]
    peak_altitude: float
    moon_separation_deg: float
    quality_score: float


class CalendarDayResponse(BaseModel):
    date: str
    quality_score: float
    moon_illumination: float
    window_hours: float
    peak_alt: float


class CalendarResponse(BaseModel):
    days: list[CalendarDayResponse]


class TonightTarget(BaseModel):
    target_id: int
    designation: str
    common_name: Optional[str]
    quality_score: float
    optimal_start: Optional[str]
    optimal_end: Optional[str]
    peak_altitude: float
    moon_separation: float


class TonightResponse(BaseModel):
    targets: list[TonightTarget]


class FovResponse(BaseModel):
    fov_width_deg: float
    fov_height_deg: float
    fov_width_arcmin: float
    fov_height_arcmin: float
    fov_diagonal_deg: float


class EquipmentProfileCreate(BaseModel):
    name: str
    focal_length_mm: float
    sensor_width_mm: float
    sensor_height_mm: float


class EquipmentProfileResponse(BaseModel):
    id: int
    name: str
    focal_length_mm: float
    sensor_width_mm: float
    sensor_height_mm: float
