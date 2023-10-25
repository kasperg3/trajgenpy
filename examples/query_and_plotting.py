import matplotlib.pyplot as plt
import shapely
from trajgenpy import Utils
from trajgenpy.Geometries import GeoMultiPolygon, GeoMultiTrajectory, GeoPolygon
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
        "building": ["industrial", "yes", "storage_tank"],
    }

    # Amagerværket: shapely.Polygon([(12.620400,55.687962),(12.632788,55.691589),(12.637446,55.687689),(12.624924,55.683489)])
    # Davinde: shapely.Polygon([(10.490913, 55.315346), (10.576744, 55.315346), (10.576744, 55.337417), (10.490913, 55.337417)])
    polygon = GeoPolygon(
        shapely.Polygon(
            [
                (12.620400, 55.687962),
                (12.632788, 55.691589),
                (12.637446, 55.687689),
                (12.624924, 55.683489),
            ],
        ),
        crs="WGS84",
    )  # Download the water features data within the bounding box

    polygon.plot(add_points=False)
    features = query_features(polygon, tags)

    # Plot highways
    GeoMultiTrajectory(features["highway"], crs="WGS84").plot()
    # Plot Buildings
    GeoMultiPolygon(features["building"], crs="WGS84").plot(
        color="red", add_points=False
    )
    # Plot natural features
    GeoMultiTrajectory(features["natural"], crs="WGS84").plot(color="green")
    Utils.plot_basemap()

    # export_trajectory_tasks(
    #     gdf_polygon.unary_union, buildings, roads + coastline, crs="EPSG:2197"
    # )

    plt.show()
