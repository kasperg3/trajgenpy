import geojson
import matplotlib.pyplot as plt
import shapely
from trajgenpy import Utils
from trajgenpy.Geometries import (
    GeoMultiPolygon,
    GeoMultiTrajectory,
    GeoPolygon,
    decompose_polygon,
    generate_sweep_pattern,
    get_sweep_offset,
)
from trajgenpy.Query import query_features


if __name__ == "__main__":
    # Download the water features data within the bounding box
    tags = {
        # "natural": ["water", "wetland"],
        "natural": ["coastline"],
        # "landuse": ["farmland"],
        "highway": [
            "primary",
            "secondary",
            "secondary_link",
            "tertiary",
            "unclassified",
            "road",
            "service",
            "path",
            "track",
        ],
        "building": True,
        "height": True,
    }

    # Amagerværket: shapely.Polygon([(12.620400,55.687962),(12.632788,55.691589),(12.637446,55.687689),(12.624924,55.683489)])
    # Davinde: shapely.Polygon([(10.490913, 55.315346), (10.576744, 55.315346), (10.576744, 55.337417), (10.490913, 55.337417)])
    polygon = GeoPolygon(
        shapely.Polygon(
            [
                (12.620400, 55.687962),
                (12.632788, 55.691989),
                (12.637446, 55.687689),
                (12.624924, 55.683489),
            ]
        ),
        crs="WGS84",
    )  # Download the water features data within the bounding box

    features = query_features(polygon, tags)
    polygon.set_crs("EPSG:2197")

    # polygon.plot(facecolor="none", edgecolor="black", linewidth=2)

    # Plot highways
    roads = GeoMultiTrajectory(features["highway"], crs="WGS84").set_crs("EPSG:2197")
    # roads.plot()

    # Plot Buildings
    obstacles = GeoMultiPolygon(features["building"], crs="WGS84").set_crs("EPSG:2197")
    obstacles.buffer(5)
    # obstacles.plot(color="red")

    # Plot natural features
    coastline = GeoPolygon(features["natural"], crs="WGS84").set_crs("EPSG:2197")
    coastline.plot(color="green", facecolor="none")

    extra_search = GeoPolygon(
        shapely.Polygon(
            [
                [12.63313389260452, 55.688680108812235],
                [12.631452519091368, 55.68805370657546],
                [12.632195079795991, 55.68729833042721],
                [12.633739947469763, 55.68788531188278],
                [12.633099751882298, 55.68842992615794],
                [12.63313389260452, 55.688680108812235],
            ]
        ),
        crs="WGS84",
    ).set_crs("EPSG:2197")
    extra_search.plot(color="green")

    polygon_list = decompose_polygon(
        coastline.get_geometry(), obstacles=extra_search.get_geometry()
    )

    # GeoMultiPolygon(
    #     shapely.MultiPolygon(polygon_list), crs="EPSG:2197"
    # ).plot(facecolor="none", edgecolor="blue", linewidth=2)

    # Export the polygon and the buildings as a GeoJSON file
    geojson_collection = geojson.FeatureCollection(
        [
            polygon.to_geojson(id="boundary"),
            obstacles.to_geojson(id="obstacles"),
        ]
    )

    offset = get_sweep_offset(0.15, 10, 90)
    result = []
    for decomposed_poly in polygon_list:
        sweeps_connected = generate_sweep_pattern(
            decomposed_poly, offset, clockwise=True, connect_sweeps=True
        )

        # Plotting
        result.extend(sweeps_connected)
    multi_traj = GeoMultiTrajectory(result, "EPSG:3857")
    multi_traj.plot(color="red")

    with open("environment.geojson", "w") as f:
        geojson.dump(geojson_collection, f)

    # Plot on a map
    Utils.plot_basemap(crs="EPSG:2197")

    # No axis on the plot
    plt.axis("equal")
    plt.axis("off")
    plt.show()
