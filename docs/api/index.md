# API Reference

TrajGenPy exposes three public Python modules:

| Module | Purpose |
|---|---|
| [`trajgenpy.Geometries`](geometries.md) | CRS-aware geometry wrappers and coverage-planning algorithms |
| [`trajgenpy.Query`](query.md) | OpenStreetMap feature querying and GeoJSON export |
| [`trajgenpy.Utils`](utils.md) | Basemap visualisation and coordinate normalisation |

The coloured logging system used internally is documented in
[`trajgenpy.Logging`](logging.md).

---

## Module overview

### Geometries

The core module.  It provides:

- **Geometry wrappers** (`GeoData`, `GeoPoint`, `GeoPolygon`, `GeoMultiPolygon`,
  `GeoTrajectory`, `GeoMultiTrajectory`) — Shapely geometries augmented with CRS
  tracking and automatic reprojection via pyproj.
- **Planning functions**:
    - `decompose_polygon` — Boustrophedon Cell Decomposition of a (possibly holed) polygon.
    - `generate_sweep_pattern` — Parallel sweep lines over a convex cell.
    - `get_sweep_offset` — Sensor-based sweep spacing calculation.
    - `shapely_polygon_to_cgal` — Low-level conversion to CGAL's `Polygon_2`.
    - `is_convex` — Convexity test.

### Query

Thin wrapper around [OSMnx](https://osmnx.readthedocs.io/) for extracting
real-world geographic features:

- `query_features` — Fetch OSM features by tag within an area of interest.
- `export_as_geojson` — Write a coverage plan to a `FeatureCollection` GeoJSON file.

### Utils

Visualisation helpers:

- `plot_basemap` — Add a contextily tile layer to a Matplotlib figure.
- `normalize_coordinates` — Translate geometries to a local origin.
