from shapely.geometry import Polygon
from trajgenpy.Geometries import GeoPolygon
from trajgenpy.Query import query_features


def test_query_features_returns_tag_map_on_osmnx_failure(monkeypatch):
    def _raise(*args, **kwargs):
        message = "network down"
        raise RuntimeError(message)

    monkeypatch.setattr("trajgenpy.Query.ox.features_from_polygon", _raise)

    area = GeoPolygon(Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]), crs="WGS84")
    tags = {"highway": True, "natural": ["coastline"]}

    result = query_features(area, tags)

    assert result == {"highway": [], "natural": []}
