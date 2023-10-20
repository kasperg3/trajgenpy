import contextily as ctx
import geopandas as gpd
import Logging as log
import matplotlib.pyplot as plt
import osmnx as ox
import shapely
from geojson import Feature, FeatureCollection, dump


# TODO create wrappers for the functions
# They should hide the internal types used for interfacing with the c++ implementations
# TODO implement Task querier which can be used in generator.
def query_features(area: shapely.Polygon, tags: dict, crs: str = "EPSG:2197"):
    try:
        geometries = ox.features_from_polygon(area, tags=tags)
    except:
        log.error("Something went wrong while trying to query from OSM")
        return []

    # Convert individual polygons to a MultiPolygon
    multi_polygon = geometries.geometry.unary_union

    # Create a GeoDataFrame from the MultiPolygon
    gdf = gpd.GeoDataFrame(
        geometry=[shapely.intersection(area, multi_polygon)], crs=geometries.crs
    )

    # Change to different CRS
    gdf = gdf.to_crs(crs)
    result = list(gdf.geometry[0].geoms)

    # TODO make sure this does not fail...
    log.info("Extracted " + str(len(result)) + " features with the tags:" + str(tags))
    return result


# def normalize_coordinates(boundary, geometries = None):

# # # Get the minimum x and y coordinate values
# min_x = boundary.bounds["minx"].min()
# min_y = boundary.bounds["miny"].min()
# for geom in geometries:
#     # gdf["geometry"] = gdf["geometry"].translate(xoff=-min_x, yoff=-min_y)
#     # gdf_polygon["geometry"] = gdf_polygon["geometry"].translate(xoff=-min_x, yoff=-min_y)
#     pass

# # # Apply the normalization to the geometry column of the GeoDataFrame
# boundary["geometry"] = boundary["geometry"].translate(xoff=-min_x, yoff=-min_y)
# gdf_polygon["geometry"] = boundary["geometry"].translate(xoff=-min_x, yoff=-min_y)
# pass


def export_trajectory_tasks(boundary: shapely.Polygon, obstacles, features, crs):
    boundary_feature = Feature(geometry=boundary, id="boundary")
    obstacles_feature = Feature(
        geometry=shapely.MultiPolygon(obstacles), id="obstacles"
    )
    task_feature = Feature(geometry=shapely.MultiLineString(features), id="tasks")
    feature_collection = FeatureCollection(
        [boundary_feature, task_feature, obstacles_feature], crs=crs
    )

    # Write the FeatureCollection to a GeoJSON file
    with open("output.json", "w") as geojson_file:
        dump(feature_collection, geojson_file)


def main():
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
    polygon = shapely.Polygon(
        [
            (12.620400, 55.687962),
            (12.632788, 55.691589),
            (12.637446, 55.687689),
            (12.624924, 55.683489),
        ]
    )  # Download the water features data within the bounding box

    gdf_polygon = gpd.GeoDataFrame(geometry=[polygon], crs="WGS84")
    gdf_polygon = gdf_polygon.to_crs("EPSG:2197")

    roads = query_features(
        polygon,
        {
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
            ]
        },
    )

    buildings = query_features(
        polygon, {"building": ["industrial", "yes", "storage_tank"]}
    )

    coastline = query_features(polygon, {"natural": ["coastline"]})

    export_trajectory_tasks(
        gdf_polygon.unary_union, buildings, roads + coastline, crs="EPSG:2197"
    )

    ax = gdf_polygon.boundary.plot(edgecolor="red")
    ax.set_axis_off()
    gpd.GeoDataFrame(geometry=roads, crs="EPSG:2197").plot(ax=ax, edgecolor="white")
    gpd.GeoDataFrame(geometry=buildings, crs="EPSG:2197").plot(
        ax=ax, edgecolor="red", facecolor="none"
    )
    gpd.GeoDataFrame(geometry=coastline, crs="EPSG:2197").plot(ax=ax, edgecolor="white")
    # ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, crs="EPSG:2197")
    plt.show()


# Example usage:
if __name__ == "__main__":
    main()
