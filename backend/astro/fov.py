"""Field of view calculations for imaging equipment."""
import numpy as np


def compute_fov(focal_length_mm: float, sensor_width_mm: float,
                sensor_height_mm: float) -> dict:
    """Compute field of view from focal length and sensor dimensions.

    Returns FOV in both degrees and arcminutes for width and height.
    """
    fov_w_rad = 2.0 * np.arctan(sensor_width_mm / (2.0 * focal_length_mm))
    fov_h_rad = 2.0 * np.arctan(sensor_height_mm / (2.0 * focal_length_mm))

    fov_w_deg = np.degrees(fov_w_rad)
    fov_h_deg = np.degrees(fov_h_rad)

    return {
        "fov_width_deg": round(fov_w_deg, 4),
        "fov_height_deg": round(fov_h_deg, 4),
        "fov_width_arcmin": round(fov_w_deg * 60.0, 2),
        "fov_height_arcmin": round(fov_h_deg * 60.0, 2),
        "fov_diagonal_deg": round(np.degrees(
            2.0 * np.arctan(np.sqrt(sensor_width_mm**2 + sensor_height_mm**2) / (2.0 * focal_length_mm))
        ), 4),
    }


def pixel_scale(focal_length_mm: float, pixel_size_um: float) -> float:
    """Pixel scale in arcseconds per pixel."""
    return 206.265 * pixel_size_um / focal_length_mm
