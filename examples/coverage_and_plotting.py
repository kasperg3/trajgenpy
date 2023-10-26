import logging

import shapely
import shapely.plotting as shplt
from matplotlib import pyplot as plt
from trajgenpy import Geometries, Logging

log = Logging.get_logger()


def custom_example():
    logging.warning("This is a warning message")
    poly = shapely.Polygon(
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
    # Define the coordinates for the inner polygon
    hole = shapely.Polygon(
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
    result = []
    for decomposed_poly in polygon_list:
        sweeps_connected = Geometries.generate_sweep_pattern(
            decomposed_poly, offset, clockwise=True, connect_sweeps=True
        )
        assert len(sweeps_connected) == 1

        sweeps_disconnected = Geometries.generate_sweep_pattern(
            decomposed_poly, offset, clockwise=False, connect_sweeps=False
        )

        # Plotting
        result.extend(sweeps_disconnected)
    multi_traj = Geometries.GeoMultiTrajectory(result, "EPSG:3857")

    # Convert the geometry back to WGS84(geodesic)
    # multi_traj.set_crs("WGS84")
    # geo_poly.set_crs("WGS84")
    # hole.set_crs("WGS84")
    shplt.plot_polygon(geo_poly.get_geometry())
    shplt.plot_polygon(hole.get_geometry())
    shplt.plot_line(multi_traj.get_geometry())
    plt.axis("equal")
    plt.show()


if __name__ == "__main__":
    custom_example()
