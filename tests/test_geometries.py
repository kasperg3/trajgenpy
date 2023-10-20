import math

import pytest
from shapely.geometry import LineString, Point, Polygon
from trajgenpy import Geometries

# Import your class from the 'trajectory' module
from trajgenpy import Logging as log


# Test initialization and conversion for Trajectory class
def test_trajectory():
    linestring = LineString(
        [
            (12.620400, 55.687962),
            (12.632788, 55.691589),
            (12.637446, 55.687689),
            (12.624924, 55.683489),
        ]
    )
    trajectory = Geometries.Trajectory(linestring)

    # Check initial CRS
    assert trajectory.crs == "WGS84"

    # Convert to a different CRS
    trajectory.set_crs("EPSG:3857")

    # Check the new CRS
    assert trajectory.crs == "EPSG:3857"

    # Check converted geometry
    converted_coords = list(trajectory.get_geometry().coords)
    assert pytest.approx(converted_coords) == [
        (1404896.5016074297, 7496546.845393788),
        (1406275.5274593767, 7497263.139176297),
        (1406794.053647492, 7496492.933496759),
        (1405400.1109837785, 7495663.567131141),
    ]


# Test initialization and conversion for PointData class
def test_point_data():
    point = Point(12.624924, 55.683489)
    point_data = Geometries.Point(point)

    # Check initial CRS
    assert point_data.crs == "WGS84"

    # Convert to a different CRS
    point_data.set_crs("EPSG:3857")

    # Check the new CRS
    assert point_data.crs == "EPSG:3857"

    # Check converted geometry
    converted_coords = point_data.get_geometry().coords
    log.debug(converted_coords)
    assert point_data.get_geometry() == Point(1405400.1109837785, 7495663.567131141)


# Test initialization and conversion for PolygonData class
def test_polygon_data():
    polygon = Polygon(
        [
            (12.620400, 55.687962),
            (12.632788, 55.691589),
            (12.637446, 55.687689),
            (12.624924, 55.683489),
        ]
    )
    polygon_data = Geometries.Polygon(polygon)

    # Check initial CRS
    assert polygon_data.crs == "WGS84"

    # Convert to a different CRS
    polygon_data.set_crs("EPSG:3857")

    # Check the new CRS
    assert polygon_data.crs == "EPSG:3857"

    # Check converted geometry
    converted_coords = list(polygon_data.get_geometry().exterior.coords)
    assert pytest.approx(converted_coords) == [
        (1404896.5016074297, 7496546.845393788),
        (1406275.5274593767, 7497263.139176297),
        (1406794.053647492, 7496492.933496759),
        (1405400.1109837785, 7495663.567131141),
        (1404896.5016074297, 7496546.845393788),
    ]


def test_valid_inputs():
    assert math.isclose(Geometries.get_sweep_offset(0.1, 30, 90), 54, abs_tol=1e-3)
    assert math.isclose(Geometries.get_sweep_offset(0.5, 40, 120), 69.282, abs_tol=1e-3)


def test_invalid_overlap():
    with pytest.raises(ValueError):
        Geometries.get_sweep_offset(1.2, 30, 90)


def test_negative_overlap():
    with pytest.raises(ValueError):
        Geometries.get_sweep_offset(-0.1, 30, 90)


def test_decompose():
    pass


def test_sweep_gen():
    offset = Geometries.get_sweep_offset(0.1, 30, 120)
    # Geometries.generate_sweep_pattern()
    pass


if __name__ == "__main__":
    pytest.main(["-v", "-x", "tests/test_geometries.py"])
