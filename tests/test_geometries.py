import math

import pytest
from shapely.geometry import LineString, Point, Polygon
from trajgenpy import Geometries, Logging

log = Logging.get_logger()

# Import your class from the 'trajectory' module


# TESTs
# Plot trajectories:
# import matplotlib.pyplot as plt
#     # plot test using matplotlib
#     # Extract the x and y coordinates for plotting
#     fig, ax = plt.subplots()

#     for multilinestring in list(test.geoms):
#         x, y = multilinestring.xy
#         ax.plot(x, y)
#     plt.show()

# Plot polygons:
# import matplotlib.pyplot as plt
#     # plot the shapely multi_polygon
#     fig, ax = plt.subplots()
#     for polygon in multi_polygon:
#         x, y = polygon.exterior.xy
#         ax.plot(x, y)

#     x, y = geo_poly.get_geometry().exterior.xy
#     ax.plot(x, y)
#     plt.show()


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
    trajectory = Geometries.GeoTrajectory(linestring)

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
    point_data = Geometries.GeoPoint(point)

    # Check initial CRS
    assert point_data.crs == "WGS84"

    # Convert to a different CRS
    point_data.set_crs("EPSG:3857")

    # Check the new CRS
    assert point_data.crs == "EPSG:3857"

    # Check converted geometry
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
    polygon_data = Geometries.GeoPolygon(polygon)

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
    with pytest.raises(
        ValueError, match="Overlap percentage has to be a float between 0 and 1!"
    ):
        Geometries.get_sweep_offset(1.2, 30, 90)


def test_negative_overlap():
    with pytest.raises(
        ValueError, match="Overlap percentage has to be a float between 0 and 1!"
    ):
        Geometries.get_sweep_offset(-0.1, 30, 90)


def test_decompose():
    poly = Polygon(
        [
            (12.620400, 55.687962),
            (12.632788, 55.691589),
            (12.637446, 55.687689),
            (12.624924, 55.683489),
            (12.628446, 55.686489),
            (12.625924, 55.688489),
            (12.630924, 55.689489),
        ]
    )

    geo_poly = Geometries.GeoPolygon(poly)
    geo_poly.set_crs("EPSG:3857")

    polygon_list = Geometries.decompose_polygon(geo_poly.get_geometry(), obstacles=None)

    # Define the coordinates for the hole (inner polygon)

    hole = Polygon(
        [
            (12.629, 55.688),
            (12.631, 55.689),
            (12.632, 55.687),
        ]
    )

    hole = Geometries.GeoPolygon(hole)
    hole.set_crs("EPSG:3857")

    polygon_list = Geometries.decompose_polygon(
        geo_poly.get_geometry(), obstacles=hole.get_geometry()
    )

    # Assert that the sum of areas of the decomposed polygons is equal to the area of the
    # snapped polygon minus the snapped hole. decompose_polygon snaps coordinates to 10 cm
    # precision before CGAL calls, so the reference areas must be computed from the same
    # snapped geometries rather than the original unsnapped inputs.
    snapped_boundary = Geometries._snap_polygon(geo_poly.get_geometry())
    snapped_hole = Geometries._snap_polygon(hole.get_geometry())
    total_area = snapped_boundary.area - snapped_hole.area
    assert pytest.approx(sum([poly.area for poly in polygon_list]), rel=1e-3) == total_area
    assert len(polygon_list) > 0


def test_sweep_gen():
    offset = Geometries.get_sweep_offset(0.1, 30, 90)
    poly = Polygon(
        [
            (12.620400, 55.687962),
            (12.632788, 55.691589),
            (12.637446, 55.687689),
            (12.624924, 55.683489),
        ]
    )
    geo_poly = Geometries.GeoPolygon(poly)
    geo_poly.set_crs("EPSG:3857")

    test = Geometries.generate_sweep_pattern(
        geo_poly.get_geometry(), offset, clockwise=False, connect_sweeps=True
    )
    assert len(test) == 1


def test_sweep_gen_with_obstacle():
    poly = Polygon(
        [
            (12.620400, 55.687962),
            (12.632788, 55.691589),
            (12.637446, 55.687689),
            (12.624924, 55.683489),
            (12.628446, 55.686489),
            (12.625924, 55.688489),
            (12.630924, 55.689489),
        ]
    )

    geo_poly = Geometries.GeoPolygon(poly)
    geo_poly.set_crs("EPSG:3857")

    polygon_list = Geometries.decompose_polygon(geo_poly.get_geometry(), obstacles=None)

    # Define the coordinates for the hole (inner polygon)

    hole = Polygon(
        [
            (12.629, 55.688),
            (12.631, 55.689),
            (12.632, 55.687),
        ]
    )

    hole = Geometries.GeoPolygon(hole)
    hole.set_crs("EPSG:3857")

    polygon_list = Geometries.decompose_polygon(
        geo_poly.get_geometry(), obstacles=hole.get_geometry()
    )

    offset = Geometries.get_sweep_offset(0.1, 30, 90)
    for decomposed_poly in polygon_list:
        sweeps_connected = Geometries.generate_sweep_pattern(
            decomposed_poly, offset, clockwise=True, connect_sweeps=True
        )
        assert len(sweeps_connected) == 1

        sweeps_disconnected = Geometries.generate_sweep_pattern(
            decomposed_poly, offset, clockwise=True, connect_sweeps=False
        )
        assert len(sweeps_disconnected) != 1


def test_shapely_polygon_to_cgal():
    poly = Polygon(
        [
            (12.620400, 55.687962),
            (12.632788, 55.691589),
            (12.637446, 55.687689),
            (12.624924, 55.683489),
        ]
    )
    cgal_poly = Geometries.shapely_polygon_to_cgal(poly)
    assert cgal_poly is not None


def test_obstacle_polygon_overlaps_boundary():
    poly = Polygon(
        [
            (12.620400, 55.687962),
            (12.632788, 55.691589),
            (12.637446, 55.687689),
            (12.624924, 55.683489),
            (12.628446, 55.686489),
            (12.625924, 55.688489),
            (12.630924, 55.689489),
        ]
    )

    geo_poly = Geometries.GeoPolygon(poly)
    geo_poly.set_crs("EPSG:3857")

    polygon_list = Geometries.decompose_polygon(geo_poly.get_geometry(), obstacles=None)

    # Define the coordinates for the hole (inner polygon)

    hole = Polygon(
        [
            (12.620400, 55.688),
            (12.631, 55.689),
            (12.632, 55.687),
        ]
    )

    hole = Geometries.GeoPolygon(hole)
    hole.set_crs("EPSG:3857")

    polygon_list = Geometries.decompose_polygon(
        geo_poly.get_geometry(), obstacles=hole.get_geometry()
    )
    assert polygon_list is not None


def test_decompose_polygon_filters_degenerate_cells(monkeypatch):
    small_poly = Geometries.bindings.Polygon_2(
        [
            Geometries.bindings.Point_2(0.0, 0.0),
            Geometries.bindings.Point_2(0.5, 0.0),
            Geometries.bindings.Point_2(0.0, 0.5),
        ]
    )
    large_poly = Geometries.bindings.Polygon_2(
        [
            Geometries.bindings.Point_2(0.0, 0.0),
            Geometries.bindings.Point_2(2.0, 0.0),
            Geometries.bindings.Point_2(0.0, 2.0),
        ]
    )

    monkeypatch.setattr(
        Geometries.bindings, "decompose", lambda _pwh: [small_poly, large_poly]
    )

    boundary = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
    cells = Geometries.decompose_polygon(boundary)

    assert len(cells) == 1
    assert cells[0].area >= Geometries.MIN_DECOMPOSE_POLYGON_AREA


def test_generate_sweep_pattern_returns_empty_for_small_area(monkeypatch):
    def _fail_if_called(*_args, **_kwargs):
        msg = "generate_sweeps should not be called for below-threshold polygons"
        raise AssertionError(msg)

    monkeypatch.setattr(Geometries.bindings, "generate_sweeps", _fail_if_called)

    # Area is 0.25, below Geometries.MIN_SWEEP_POLYGON_AREA (= 1.0).
    small_polygon = Polygon([(0, 0), (1, 0), (0, 0.5)])
    sweeps = Geometries.generate_sweep_pattern(small_polygon, sweep_offset=1.0)

    assert sweeps == []


if __name__ == "__main__":
    pytest.main(["-v", "-x", "tests/test_geometries.py"])
