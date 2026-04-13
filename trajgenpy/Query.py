"""OpenStreetMap feature querying utilities.

This module wraps `OSMnx <https://osmnx.readthedocs.io/>`_ to provide a
simplified interface for extracting geographic features from OpenStreetMap
within a given area of interest and exporting results to GeoJSON.

Example:
    ::

        from trajgenpy.Geometries import GeoPolygon
        from trajgenpy.Query import query_features, export_as_geojson
        import shapely

        area = GeoPolygon(shapely.box(10.38, 55.38, 10.42, 55.42))

        tags = {"landuse": True, "natural": True}
        features = query_features(area, tags)
"""

from pathlib import Path

import osmnx as ox
import shapely
from geojson import Feature, FeatureCollection, dump

from trajgenpy import Logging
from trajgenpy.Geometries import GeoPolygon

log = Logging.get_logger()


def query_features(area: GeoPolygon, tags: dict):
    """Query OpenStreetMap features within a geographic area.

    Fetches all OSM features whose tags match *tags* and clips the result to
    *area*.  The area geometry must use the ``"WGS84"`` CRS because OSM
    data is stored in geographic coordinates.

    Args:
        area: The region of interest as a :class:`~trajgenpy.Geometries.GeoPolygon`
            in ``"WGS84"`` CRS.
        tags: A dictionary of OSM tag keys (and optional values) to query.
            Use ``{key: True}`` to fetch all features with a given key
            regardless of value, or ``{key: value}`` to filter by a
            specific value.  See the `OSM map features wiki
            <https://wiki.openstreetmap.org/wiki/Map_features>`_ for valid
            tag combinations.

    Returns:
        dict[str, shapely.geometry.base.BaseGeometry]: A dictionary mapping
        each requested tag key to the union of all matching geometries
        clipped to *area*. If the query fails, each requested tag maps to an
        empty list.

    Raises:
        ValueError: If *area* does not use the ``"WGS84"`` CRS.

    Example:
        ::

            tags = {"natural": True, "landuse": ["forest", "farmland"]}
            results = query_features(area, tags)
            forest_geom = results.get("natural")
    """
    # Check that the geometry has the right crs
    if area.crs and area.crs != "WGS84":
        msg = "The geometry must use WGS84 CRS!"
        raise ValueError(msg)

    try:
        geometries = ox.features_from_polygon(area.get_geometry(), tags=tags)
    except Exception as e:
        log.error("Something went wrong while trying to query from OSM: %s", e)
        return {tag: [] for tag in tags}
    results = {tag: [] for tag in tags}
    # Iterate through the features and populate the results dictionary
    for tag in tags:
        # Filter the GeoDataFrame by the specified tag
        filtered_features = geometries[geometries[tag].notna()]
        results[tag] = shapely.intersection(
            area.get_geometry(), filtered_features.geometry.unary_union
        )
        # TODO Also include the metadata of the features for future analysis

    log.info("Extracted %d features with the tags: %s", len(geometries), str(tags))
    return results


def export_as_geojson(boundary: shapely.Polygon, obstacles, features, crs):
    """Export boundary, obstacles, and task features to a GeoJSON file.

    Writes a ``FeatureCollection`` containing three named features — the
    coverage boundary, obstacle polygons, and task trajectories — to a file
    called ``output.json`` in the current working directory.

    Args:
        boundary: The outer boundary :class:`~shapely.Polygon`.
        obstacles: An iterable of obstacle :class:`~shapely.Polygon` objects.
        features: An iterable of :class:`~shapely.LineString` trajectory
            segments representing the coverage tasks.
        crs: CRS identifier string stored as metadata in the GeoJSON output
            (e.g. ``"EPSG:32632"``).

    Returns:
        None

    Side effects:
        Creates (or overwrites) ``output.json`` in the current directory.
    """
    boundary_feature = Feature(geometry=boundary, id="boundary")
    obstacles_feature = Feature(
        geometry=shapely.MultiPolygon(obstacles), id="obstacles"
    )
    task_feature = Feature(geometry=shapely.MultiLineString(features), id="tasks")
    feature_collection = FeatureCollection(
        [boundary_feature, task_feature, obstacles_feature], crs=crs
    )

    # Write the FeatureCollection to a GeoJSON file
    with Path("output.json").open("w") as geojson_file:
        dump(feature_collection, geojson_file)
