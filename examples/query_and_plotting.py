import geojson
import matplotlib.pyplot as plt
import shapely
from trajgenpy import Utils
from trajgenpy.Geometries import GeoMultiPolygon, GeoMultiTrajectory, GeoPolygon
from trajgenpy.Query import query_features
import trajgenpy.Logging

log = trajgenpy.Logging.get_logger()

if __name__ == "__main__":
    # Download the water features data within the bounding box
    tags = {
        "natural": ["water", "wetland"],
        # "natural": ["coastline"],
        "landuse": ["farmland"],
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
        "building": ["industrial", "yes", "storage_tank"],
    }

    # Amagerværket: shapely.Polygon([(12.620400,55.687962),(12.632788,55.691589),(12.637446,55.687689),(12.624924,55.683489)])
    # Davinde: shapely.Polygon([(10.490913, 55.315346), (10.576744, 55.315346), (10.576744, 55.337417), (10.490913, 55.337417)])
    polygon = GeoPolygon(
        shapely.Polygon(
            [
                (10.490913, 55.315346),
                (10.576744, 55.315346),
                (10.576744, 55.337417),
                (10.490913, 55.337417),
            ]
        ),
        crs="WGS84",
    )  # Download the water features data within the bounding box

    features = query_features(polygon, tags)
    polygon.set_crs("EPSG:2197")

    polygon.plot(facecolor="none", edgecolor="black", linewidth=2)

    # Plot highways
    roads = GeoMultiTrajectory(features["highway"], crs="WGS84").set_crs("EPSG:2197")
    roads.plot()

    # Plot Buildings
    buildings = GeoMultiPolygon(features["building"], crs="WGS84").set_crs("EPSG:2197")

    buildings.plot(color="red")

    # Plot natural features
    # coastline = GeoMultiTrajectory(features["natural"], crs="WGS84").set_crs(
    #     "EPSG:2197"
    # )
    # coastline.plot(color="green")

    # Export the polygon and the buildings as a GeoJSON file
    geojson_collection = geojson.FeatureCollection(
        [
            polygon.to_geojson(id="boundary"),
            buildings.to_geojson(id="obstacles"),
        ]
    )

    with open("environment.geojson", "w") as f:
        geojson.dump(geojson_collection, f)

    # Plot on a map
    Utils.plot_basemap(crs="EPSG:2197")

    # No axis on the plot
    plt.axis("equal")
    plt.axis("off")
    plt.show()
