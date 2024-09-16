import json
import random

import contextily as cx
import geojson
from matplotlib.lines import lineStyles
import matplotlib.pyplot as plt
from numpy import poly
import shapely
import trajgenpy.Logging
from trajgenpy import Utils
from trajgenpy.Geometries import (
    GeoMultiPolygon,
    GeoMultiTrajectory,
    GeoPolygon,
    GeoTrajectory,
    decompose_polygon,
    generate_sweep_pattern,
    get_sweep_offset,
)
from trajgenpy.Query import query_features


log = trajgenpy.Logging.get_logger()


def get_line_segments(polygon: GeoPolygon):
    polygon_list = decompose_polygon(polygon.get_geometry())

    log.info(f"Number of polygons: {len(polygon_list)}")

    offset = get_sweep_offset(0.1, 15, 90)
    result = []
    for decomposed_poly in polygon_list:
        sweeps_connected = generate_sweep_pattern(
            decomposed_poly, offset, connect_sweeps=False
        )
        result.extend(sweeps_connected)
    return result


def export_to_geojson(tasks: GeoMultiTrajectory, polygon: GeoPolygon):
    log.info(f"Number of sweeps: {len(tasks.get_geometry().geoms)}")
    geojson_collection = geojson.FeatureCollection(
        [
            polygon.to_geojson(id="boundary"),
            multi_traj.to_geojson(id="tasks"),
        ]
    )
    with open("environment.geojson", "w") as f:
        geojson.dump(geojson_collection, f)


if __name__ == "__main__":
    polygon_file = "examples/DemaScenarios/FlatTerrainNature.geojson"
    # polygon_file = "examples/DemaScenarios/HillyTerrainNature.geojson"
    # polygon_file = "examples/DemaScenarios/Urban.geojson"
    # polygon_file = "examples/DemaScenarios/Water.geojson"

    # Load the GeoJSON data
    with open(polygon_file, "r") as f:
        data = json.load(f)

    # Extract the polygon coordinates
    coordinates = data["features"][0]["geometry"]["coordinates"][0]

    # Create the shapely Polygon object
    polygon = GeoPolygon(shapely.Polygon(coordinates)).set_crs("EPSG:2197")

    tags = {
        "natural": ["water", "wetland"],
    }

    wetland = query_features(
        GeoPolygon(shapely.Polygon(coordinates)),
        {
            "natural": ["water", "wetland"],
        },
    )
    for f in wetland.values():
        GeoMultiPolygon(f).set_crs("EPSG:2197").plot()

    roads = query_features(
        GeoPolygon(shapely.Polygon(coordinates)),
        {
            "highway": ["service", "track"],
        },
    )
    for road in roads.values():
        GeoMultiTrajectory(road).set_crs("EPSG:2197").plot(color="red")

    tasks = get_line_segments(polygon)

    multi_traj = GeoMultiTrajectory(tasks, "EPSG:2197")
    multi_traj.set_crs("EPSG:2197")
    polygon.set_crs("EPSG:2197")

    # remove duplicate lines
    trajectories = multi_traj.get_geometry().geoms
    duplicates = []
    for i in range(len(multi_traj.get_geometry().geoms)):
        for j in range(i + 1, len(multi_traj.get_geometry().geoms)):
            if (
                multi_traj.get_geometry().geoms[i].coords[0]
                == multi_traj.get_geometry().geoms[j].coords[-1]
            ):
                duplicates.append(multi_traj.get_geometry().geoms[i])
                print("found duplicate")
    trajectories = [traj for traj in trajectories if traj not in duplicates]
    multi_traj = GeoMultiTrajectory(trajectories, "EPSG:2197")
    # multi_traj.plot(color="red", linestyle="dashed")

    polygon.plot(facecolor="none", edgecolor="black", linewidth=2)
    polygon.buffer(50).plot(
        facecolor="none",
        edgecolor="orange",
        linewidth=2,
        linestyle="dashed",
    )

    polygon.buffer(100).plot(
        facecolor="none",
        edgecolor="red",
        linewidth=2,
        linestyle="dashed",
    )

    Utils.plot_basemap(provider=cx.providers.CartoDB.Positron, crs="EPSG:2197")
    export_to_geojson(multi_traj, polygon)

    # No axis on the plot
    # plt.axis("equal")
    plt.axis("off")
    plt.show()
