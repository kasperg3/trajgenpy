import math

import pyproj
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
    coords = [
        (12.620400, 55.687962),
        (12.632788, 55.691589),
        (12.637446, 55.687689),
        (12.624924, 55.683489),
    ]
    linestring = LineString(coords)
    trajectory = Geometries.GeoTrajectory(linestring)

    # Check initial CRS
    assert trajectory.crs == "WGS84"

    # Convert to a different CRS
    trajectory.set_crs("EPSG:3857")

    # Check the new CRS
    assert trajectory.crs == "EPSG:3857"

    # Check converted geometry. Expected values are computed with pyproj at
    # runtime instead of hardcoded, so the test stays valid across PROJ
    # versions.
    transformer = pyproj.Transformer.from_crs("WGS84", "EPSG:3857", always_xy=True)
    expected = [transformer.transform(x, y) for x, y in coords]
    converted_coords = list(trajectory.get_geometry().coords)
    assert pytest.approx(converted_coords) == expected


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

    # Check converted geometry. Expected values are computed with pyproj at
    # runtime instead of hardcoded, so the test stays valid across PROJ
    # versions.
    transformer = pyproj.Transformer.from_crs("WGS84", "EPSG:3857", always_xy=True)
    expected = transformer.transform(12.624924, 55.683489)
    assert point_data.get_geometry() == Point(*expected)


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

    # Check converted geometry. Expected values are computed with pyproj at
    # runtime instead of hardcoded, so the test stays valid across PROJ
    # versions.
    transformer = pyproj.Transformer.from_crs("WGS84", "EPSG:3857", always_xy=True)
    expected = [transformer.transform(x, y) for x, y in polygon.exterior.coords]
    converted_coords = list(polygon_data.get_geometry().exterior.coords)
    assert pytest.approx(converted_coords) == expected


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

    # Assert that the sum of areas of the decomposed polygons is equal to the area of the original polygon
    total_area = geo_poly.get_geometry().area - hole.get_geometry().area
    # Cells are returned on a 10 cm grid, so allow for the small rounding loss.
    assert pytest.approx(sum([poly.area for poly in polygon_list]), rel=1e-3) == total_area
    assert len(polygon_list) > 0
    assert all(poly.is_valid and poly.area > 0 for poly in polygon_list)


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


def test_snap_polygon_deduplicates_collapsed_vertices():
    # A quad whose two middle vertices are ~1.4 cm apart collapses to a valid
    # triangle instead of carrying a zero-length edge into CGAL.
    quad = Polygon(
        [
            (0.0, 0.0),
            (50.0, 0.0),
            (50.01, 0.01),
            (0.0, 50.0),
        ]
    )
    snapped = Geometries._snap_polygon(quad)
    assert not snapped.is_empty
    assert snapped.is_valid
    assert snapped.area > 0
    coords = list(snapped.exterior.coords)
    assert len(coords) == 4  # three distinct vertices plus the ring closure


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


def test_generate_sweep_pattern_rejects_degenerate_polygon():
    # A zero-width sliver whose vertices all collapse onto a single line when
    # snapped to the 10 cm grid. CGAL would reject the collapsed ring with
    # "Outer polygon is not counterclockwise oriented"; the Python wrapper must
    # fail with an actionable message instead.
    sliver = Polygon(
        [
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 0.01),
            (0.0, 0.02),
        ]
    )
    with pytest.raises(ValueError, match="degenerated"):
        Geometries.generate_sweep_pattern(sliver, 40.0)


def test_decompose_survives_snap_collapsed_sliver():
    # Regression: real-world farmland polygon (vt_kentland_farm farmland_2)
    # whose eroded UTM form decomposes into a ~920 m long sliver with two
    # vertices ~1 cm apart. Snapping previously collapsed the sliver into a
    # zero-area ring that CGAL rejected with "Outer polygon is not
    # counterclockwise oriented".
    farmland_2_wgs84 = [
        (-80.564768, 37.199826),
        (-80.565262, 37.19962),
        (-80.566511, 37.199026),
        (-80.567106, 37.198662),
        (-80.568439, 37.197897),
        (-80.569795, 37.197109),
        (-80.572261, 37.195472),
        (-80.573466, 37.194633),
        (-80.574323, 37.194076),
        (-80.575211, 37.194813),
        (-80.575586, 37.194591),
        (-80.576373, 37.195287),
        (-80.576714, 37.195063),
        (-80.577754, 37.195522),
        (-80.577024, 37.196719),
        (-80.5766, 37.19768),
        (-80.574444, 37.198616),
        (-80.572673, 37.198637),
        (-80.570174, 37.199227),
        (-80.56939, 37.199423),
        (-80.568645, 37.19971),
        (-80.567127, 37.200368),
        (-80.565319, 37.200889),
        (-80.565009, 37.200291),
        (-80.564768, 37.199826),
    ]

    poly = Polygon(farmland_2_wgs84)
    geo_poly = Geometries.GeoPolygon(poly)
    geo_poly.set_crs("EPSG:32617")
    geo_poly.buffer(-2)

    cells = Geometries.decompose_polygon(geo_poly.get_geometry(), obstacles=None)
    assert len(cells) > 0
    assert all(cell.is_valid and cell.area > 0 for cell in cells)

    # Mirrors the swarm-steward worker: 20.2 m altitude, 75.7° FOV, 20% overlap.
    offset = Geometries.get_sweep_offset(0.2, 20.2, 75.7)
    for cell in cells:
        sweeps = Geometries.generate_sweep_pattern(
            cell, offset, clockwise=True, connect_sweeps=False
        )
        assert len(sweeps) > 0


if __name__ == "__main__":
    pytest.main(["-v", "-x", "tests/test_geometries.py"])
