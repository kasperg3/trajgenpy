"""Visualisation and coordinate utility helpers.

This module provides convenience functions for:

- Overlaying tile-based basemaps on Matplotlib figures using
  `contextily <https://contextily.readthedocs.io/>`_.
- Normalising geometry coordinates relative to a bounding box origin, which
  is useful for producing metric plots that start at ``(0, 0)``.
"""

import contextily as ctx
import matplotlib.pyplot as plt
import shapely
from shapely.affinity import translate


def plot_basemap(ax=None, provider=ctx.providers.Esri.WorldImagery, crs="WGS84"):
    """Overlay a tile-based basemap on a Matplotlib axes.

    Uses :func:`contextily.add_basemap` to fetch and render web map tiles
    behind any geometries already plotted on *ax*.  The axes must already
    have geographic extent set (e.g. by plotting a GeoPolygon first).

    Args:
        ax: Matplotlib :class:`~matplotlib.axes.Axes` to draw on.  Defaults
            to :func:`matplotlib.pyplot.gca` when ``None``.
        provider: Tile provider descriptor from ``contextily.providers``
            (default: ``ctx.providers.Esri.WorldImagery``).  See the
            `contextily providers documentation
            <https://contextily.readthedocs.io/en/latest/providers_deepdive.html>`_
            for a full list of available providers.
        crs: CRS of the axes coordinates (default ``"WGS84"``).  Pass an
            EPSG string (e.g. ``"EPSG:32632"``) when the axes are in a
            projected coordinate system.

    Returns:
        The return value of :func:`contextily.add_basemap` (typically
        ``None``).
    """
    if ax is None:
        ax = plt.gca()
    return ctx.add_basemap(ax, source=provider, crs=crs)


def normalize_coordinates(boundary, geometries=None):
    """Translate geometries so that the bounding-box origin is at ``(0, 0)``.

    Shifts all geometries in *geometries* by the negative of the lower-left
    corner of *boundary*'s bounding box.  This produces a local coordinate
    frame suitable for visualisation or downstream algorithms that expect
    metric coordinates starting at the origin.

    Args:
        boundary: A Shapely geometry whose :attr:`~shapely.Geometry.bounds`
            define the translation offset.
        geometries: A Shapely geometry collection (e.g.
            :class:`~shapely.MultiLineString`) whose individual geometries
            will be translated.  Each element in ``geometries.geoms`` is
            processed separately.

    Returns:
        list[shapely.geometry.base.BaseGeometry]: A list of translated
        geometries in the same order as ``geometries.geoms``.
    """
    normalized_geoms = []
    translation_vector = shapely.Point(boundary.bounds[0], boundary.bounds[1])
    for geom in list(geometries.geoms):
        normalized_geoms.append(
            translate(geom, xoff=-translation_vector.x, yoff=-translation_vector.y)
        )

    return normalized_geoms
