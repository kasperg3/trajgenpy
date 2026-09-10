"""TrajGenPy: Coverage trajectory generation using Boustrophedon Cell Decomposition.

TrajGenPy is a Python library for generating coverage trajectories over arbitrary
polygonal areas, with optional obstacle avoidance.  It is built on top of a C++
implementation of the Boustrophedon Cell Decomposition algorithm (via CGAL and
pybind11) and provides a high-level Python API for:

- Querying environmental features from OpenStreetMap (OSM).
- Converting geometries between coordinate reference systems (CRS).
- Decomposing polygons (with holes) into convex, weakly-monotone cells.
- Generating boustrophedon ("lawnmower") sweep patterns over each cell.

Example:
    A minimal end-to-end workflow::

        import shapely
        from trajgenpy.Geometries import (
            GeoPolygon,
            decompose_polygon,
            generate_sweep_pattern,
            get_sweep_offset,
        )

        # 1. Define an area of interest in WGS84
        area = GeoPolygon(shapely.box(10.38, 55.38, 10.42, 55.42))

        # 2. Reproject to a metric CRS (UTM zone 32N) for planning
        area.set_crs("EPSG:32632")

        # 3. Decompose into convex cells
        cells = decompose_polygon(area.geometry)

        # 4. Generate a boustrophedon sweep for each cell
        offset = get_sweep_offset(overlap=0.1, height=20, field_of_view=90)
        sweeps = [generate_sweep_pattern(cell, offset) for cell in cells]
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _package_version

try:
    __version__ = _package_version(__name__)
except PackageNotFoundError:
    __version__ = "dev"

from trajgenpy import Geometries, Query, Utils

__all__ = ["Geometries", "Query", "Utils", "__doc__", "__version__"]
