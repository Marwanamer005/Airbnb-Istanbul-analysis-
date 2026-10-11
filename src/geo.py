"""Geographic helpers shared by the notebooks and the app.

All coordinates are (lat, lon) in degrees. GeoJSON stores [lon, lat], so
load_points() swaps them for you.
"""
import json

import numpy as np
from sklearn.neighbors import BallTree

EARTH_RADIUS_M = 6_371_000

ASIAN_DISTRICTS = {
    "Adalar", "Atasehir", "Beykoz", "Cekmekoy", "Kadikoy", "Kartal", "Maltepe",
    "Pendik", "Sancaktepe", "Sile", "Sultanbeyli", "Tuzla", "Umraniye", "Uskudar",
}


def haversine_m(lat1, lon1, lat2, lon2):
    """Great-circle distance in metres. Works on scalars or numpy arrays."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_RADIUS_M * np.arcsin(np.sqrt(a))


def load_points(geojson_path):
    """Return (latlon array of shape (n, 2), list of property dicts) from a GeoJSON file."""
    with open(geojson_path, encoding="utf-8") as f:
        features = json.load(f)["features"]
    pts, props = [], []
    for ft in features:
        geom = ft.get("geometry") or {}
        if geom.get("type") != "Point":
            continue
        lon, lat = geom["coordinates"][:2]
        pts.append((lat, lon))
        props.append(ft.get("properties", {}))
    return np.array(pts), props


class PointIndex:
    """Fast nearest-neighbour and radius queries on a set of (lat, lon) points."""

    def __init__(self, latlon):
        self.tree = BallTree(np.radians(latlon), metric="haversine")

    def nearest_m(self, latlon):
        """Distance in metres from each query point to its nearest indexed point."""
        dist, _ = self.tree.query(np.radians(latlon), k=1)
        return dist[:, 0] * EARTH_RADIUS_M

    def count_within(self, latlon, radius_m):
        """Number of indexed points within radius_m of each query point."""
        return self.tree.query_radius(np.radians(latlon), r=radius_m / EARTH_RADIUS_M,
                                      count_only=True)

    def within(self, latlon, radius_m):
        """Indices of indexed points within radius_m of each query point."""
        return self.tree.query_radius(np.radians(latlon), r=radius_m / EARTH_RADIUS_M)
