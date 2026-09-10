"""Geometry classes and coverage-planning utilities for TrajGenPy.

This module provides CRS-aware wrappers around Shapely geometry types and the
core algorithmic functions needed for coverage path planning:

- **GeoData** – abstract base for all geometry wrappers.
- **GeoTrajectory** / **GeoMultiTrajectory** – single and multi-path trajectories.
- **GeoPoint** – single geographic point.
- **GeoPolygon** / **GeoMultiPolygon** – area representations with holes.
- :func:`decompose_polygon` – Boustrophedon Cell Decomposition via CGAL.
- :func:`generate_sweep_pattern` – boustrophedon sweep lines over a single cell.
- :func:`get_sweep_offset` – calculate inter-sweep spacing from sensor parameters.
"""

import math
import random

import geojson
import pyproj
import shapely
import shapely.plotting as shplt
from shapely.geometry.polygon import orient
from shapely.ops import transform as _shapely_transform

import trajgenpy.bindings as bindings
from trajgenpy import Logging

log = Logging.get_logger()


class GeoData:
    """Abstract base class for CRS-aware geometry wrappers.

    All concrete geometry classes (e.g. :class:`GeoPolygon`,
    :class:`GeoTrajectory`) inherit from this class.  It stores a Shapely
    geometry together with its coordinate reference system string and provides
    common operations such as CRS conversion, buffering, and GeoJSON export.

    Args:
        geometry: Any Shapely geometry object.
        crs: EPSG string or ``"WGS84"`` identifying the geometry's CRS.
            Defaults to ``"WGS84"``.
    """

    def __init__(self, geometry, crs="WGS84"):
        self.geometry = geometry
        self.crs = crs

    def set_crs(self, crs):
        """Reproject the geometry to a new coordinate reference system.

        If *crs* differs from the current CRS the geometry coordinates are
        transformed in-place using :mod:`pyproj`.

        Args:
            crs: Target CRS as a string (e.g. ``"EPSG:32632"``).

        Returns:
            GeoData: ``self`` (for method chaining).

        Raises:
            ValueError: If *crs* is not a string.
        """
        if not isinstance(crs, str):
            msg = "New CRS must be a string."
            raise ValueError(msg)

        if crs != self.crs:
            # Apply the transformer to the geometry
            self._convert_to_crs(crs)
        self.crs = crs
        return self

    def _convert_to_crs(self, crs):
        """Reproject the underlying Shapely geometry to *crs*.

        Uses :func:`shapely.ops.transform` to recurse through every
        coordinate of the geometry (including polygon interior rings and
        ``Multi*`` parts) and apply a :class:`pyproj.Transformer`.  The
        ``z=None`` default on the inner lambda preserves the historical
        behaviour of dropping any Z coordinate during reprojection.
        """
        transformer = pyproj.Transformer.from_crs(self.crs, crs, always_xy=True)
        self.geometry = _shapely_transform(
            # z=None accepts the Z coordinate shapely.transform forwards for
            # 3D geometries and drops it, preserving historical behaviour.
            lambda x, y, z=None: transformer.transform(x, y),  # noqa: ARG005
            self.geometry,
        )

    def is_geometry_of_type(self, geometry, expected_class):
        """Raise :exc:`ValueError` if *geometry* is not an instance of *expected_class*.

        Args:
            geometry: The geometry object to check.
            expected_class: The expected type (or union of types).

        Raises:
            ValueError: When the type check fails.
        """
        if expected_class and not isinstance(geometry, expected_class):
            msg = f"Geometry must be a {expected_class.__name__}."
            raise ValueError(msg)

    def get_geometry(self):
        """Return the underlying Shapely geometry object.

        Returns:
            shapely.geometry.base.BaseGeometry: The wrapped Shapely geometry.
        """
        return self.geometry

    def buffer(self, distance, quad_segs=1, cap_style="square", join_style="bevel"):
        """Expand or contract the geometry by *distance* units.

        Delegates to :meth:`shapely.geometry.base.BaseGeometry.buffer`.  The
        geometry is replaced in-place.

        Args:
            distance: Buffer distance in the geometry's CRS units (metres for
                metric CRS, degrees for WGS84).  Negative values shrink the
                geometry.
            quad_segs: Number of segments used to approximate a quarter circle
                (default ``1`` for a rectilinear buffer).
            cap_style: End-cap style for linear geometries.  One of
                ``"round"``, ``"flat"``, or ``"square"`` (default).
            join_style: Corner join style.  One of ``"round"``, ``"mitre"``,
                or ``"bevel"`` (default).

        Returns:
            GeoData: ``self`` (for method chaining).
        """
        self.geometry = self.geometry.buffer(
            distance,
            quad_segs=quad_segs,
            cap_style=cap_style,
            join_style=join_style,
        )
        return self

    def __str__(self):
        return f"Geometry in CRS: {self.crs}\nGeometry: {self.geometry}"

    def __geo_interface__(self):
        return self.geometry.__geo_interface__

    def to_geojson(self, id=None, name=None, properties=None):
        """Serialise the geometry as a GeoJSON :class:`geojson.Feature`.

        Args:
            id: Feature identifier.  A random integer is used when ``None``
                (default).
            name: Human-readable name stored in ``properties["name"]``.
                Defaults to ``str(id)``.
            properties: Additional key/value pairs to include in the feature
                properties.  The keys ``"crs"`` and ``"name"`` are added
                automatically.

        Returns:
            geojson.Feature: The serialised feature.
        """
        if id is None:
            id = random.randint(0, 1000000000)
        if name is None:
            name = str(id)
        if properties is None:
            properties = {}

        properties["crs"] = self.crs
        properties["name"] = name
        return geojson.Feature(id, self.geometry, properties=properties)


class GeoTrajectory(GeoData):
    """CRS-aware wrapper for a single-path trajectory (Shapely :class:`~shapely.LineString`).

    Args:
        geometry: A Shapely :class:`~shapely.LineString` representing the path.
        crs: Coordinate reference system string.  Defaults to ``"WGS84"``.

    Raises:
        ValueError: If *geometry* is not a :class:`~shapely.LineString`.
    """

    def __init__(self, geometry, crs="WGS84"):
        self.is_geometry_of_type(geometry, shapely.LineString)
        super().__init__(geometry, crs)

    def plot(self, ax=None, add_points=True, color=None, linewidth=2, **kwargs):
        """Render the trajectory on a Matplotlib axes.

        A warning is issued when the current CRS is ``"WGS84"`` because
        geographic coordinates distort the visual representation.

        Args:
            ax: Matplotlib :class:`~matplotlib.axes.Axes` to draw on.
                Uses the current active axes when ``None``.
            add_points: Overlay vertex markers when ``True`` (default).
            color: Line colour accepted by Matplotlib.
            linewidth: Stroke width in points (default ``2``).
            **kwargs: Additional keyword arguments forwarded to
                :func:`shapely.plotting.plot_line`.
        """
        if self.crs == "WGS84":
            log.warning(
                "Plotting in WGS84 is not recomended as this distorts the geometry!"
            )
        shplt.plot_line(self.geometry, ax, add_points, color, linewidth, **kwargs)


class GeoMultiTrajectory(GeoData):
    """CRS-aware wrapper for a collection of path trajectories.

    Accepts several input formats and normalises them to a
    :class:`~shapely.MultiLineString` internally.

    Args:
        geometry: One of:

            - :class:`~shapely.MultiLineString` – used directly.
            - :class:`list` of :class:`~shapely.LineString` – combined into a
              :class:`~shapely.MultiLineString`.
            - :class:`list` of :class:`GeoTrajectory` – geometries extracted
              and combined.
            - A single :class:`~shapely.LineString` – wrapped in a
              :class:`~shapely.MultiLineString`.

        crs: Coordinate reference system string.  Defaults to ``"WGS84"``.

    Raises:
        ValueError: If an element in a list input is not a
            :class:`~shapely.LineString`, or if a non-list input is not a
            recognised type.
    """

    def __init__(
        self,
        geometry: (
            shapely.MultiLineString
            | list[shapely.LineString]
            | list[GeoTrajectory]
            | shapely.LineString
        ),
        crs="WGS84",
    ):
        if isinstance(geometry, list):
            for line in geometry:
                self.is_geometry_of_type(line, shapely.LineString)
            geometry = shapely.MultiLineString(geometry)
        elif isinstance(geometry, shapely.LineString):
            geometry = shapely.MultiLineString([geometry])
        elif isinstance(geometry, GeoTrajectory):
            geometry = shapely.MultiLineString([geometry.geometry])
        else:
            self.is_geometry_of_type(geometry, shapely.MultiLineString)
        super().__init__(geometry, crs)

    def plot(self, ax=None, add_points=False, color=None, linewidth=2, **kwargs):
        """Render all trajectories on a Matplotlib axes.

        A warning is issued when the current CRS is ``"WGS84"``.

        Args:
            ax: Matplotlib :class:`~matplotlib.axes.Axes`.  Defaults to the
                current active axes.
            add_points: Overlay vertex markers (default ``False``).
            color: Line colour accepted by Matplotlib.
            linewidth: Stroke width in points (default ``2``).
            **kwargs: Additional keyword arguments forwarded to
                :func:`shapely.plotting.plot_line`.
        """
        if self.crs == "WGS84":
            log.warning(
                "Plotting in WGS84 is not recomended as this distorts the geometry!"
            )
        for line in self.geometry.geoms:
            shplt.plot_line(line, ax, add_points, color, linewidth, **kwargs)


class GeoPoint(GeoData):
    """CRS-aware wrapper for a single geographic point.

    Args:
        geometry: A Shapely :class:`~shapely.Point`.
        crs: Coordinate reference system string.  Defaults to ``"WGS84"``.

    Raises:
        ValueError: If *geometry* is not a :class:`~shapely.Point`.
    """

    def __init__(self, geometry: shapely.Point, crs="WGS84"):
        self.is_geometry_of_type(geometry, shapely.Point)
        super().__init__(geometry, crs)

    def plot(self, ax=None, add_points=True, color=None, linewidth=2, **kwargs):
        """Render the point on a Matplotlib axes.

        Args:
            ax: Matplotlib :class:`~matplotlib.axes.Axes`.
            add_points: Show the point marker (default ``True``).
            color: Marker colour.
            linewidth: Marker size (default ``2``).
            **kwargs: Forwarded to :func:`shapely.plotting.plot_points`.
        """
        if self.crs == "WGS84":
            log.warning(
                "Plotting in WGS84 is not recomended as this distorts the geometry!"
            )
        shplt.plot_points(self.geometry, ax, add_points, color, linewidth, **kwargs)


class GeoPolygon(GeoData):
    """CRS-aware wrapper for a simple or holed polygon.

    Args:
        geometry: A Shapely :class:`~shapely.Polygon` or
            :class:`~shapely.LineString` (the latter is closed into a
            polygon automatically).
        crs: Coordinate reference system string.  Defaults to ``"WGS84"``.

    Raises:
        ValueError: If *geometry* is neither a
            :class:`~shapely.Polygon` nor a :class:`~shapely.LineString`.
    """

    def __init__(self, geometry: shapely.Polygon | shapely.LineString, crs="WGS84"):
        self.is_geometry_of_type(geometry, shapely.Polygon | shapely.LineString)
        geometry = shapely.Polygon(geometry)
        super().__init__(geometry, crs)

    def plot(
        self,
        ax=None,
        add_points=False,
        color=None,
        facecolor=None,
        edgecolor=None,
        linewidth=2,
        **kwargs,
    ):
        """Render the polygon on a Matplotlib axes.

        Args:
            ax: Matplotlib :class:`~matplotlib.axes.Axes`.
            add_points: Overlay vertex markers (default ``False``).
            color: Fill and edge colour (overridden by *facecolor*/*edgecolor*).
            facecolor: Polygon fill colour.
            edgecolor: Polygon edge colour.
            linewidth: Edge stroke width in points (default ``2``).
            **kwargs: Forwarded to :func:`shapely.plotting.plot_polygon`.
        """
        if self.crs == "WGS84":
            log.warning(
                "Plotting in WGS84 is not recomended as this distorts the geometry!"
            )
        shplt.plot_polygon(
            polygon=self.geometry,
            ax=ax,
            add_points=add_points,
            color=color,
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=linewidth,
            **kwargs,
        )


class GeoMultiPolygon(GeoData):
    """CRS-aware wrapper for a collection of polygons.

    Args:
        geometry: Either a :class:`~shapely.MultiPolygon` or a
            :class:`list` of :class:`~shapely.Polygon` objects.
        crs: Coordinate reference system string.  Defaults to ``"WGS84"``.

    Raises:
        ValueError: If a list element is not a :class:`~shapely.Polygon`,
            or if *geometry* is not a :class:`~shapely.MultiPolygon`.
    """

    def __init__(self, geometry, crs="WGS84"):
        if isinstance(geometry, list):
            for geom in geometry:
                self.is_geometry_of_type(geom, shapely.Polygon)
            geometry = shapely.MultiPolygon(geometry)
        else:
            self.is_geometry_of_type(geometry, shapely.MultiPolygon)
        super().__init__(geometry, crs)

    def plot(
        self,
        ax=None,
        add_points=False,
        color=None,
        facecolor=None,
        edgecolor=None,
        linewidth=2,
        **kwargs,
    ):
        """Render all polygons on a Matplotlib axes.

        Args:
            ax: Matplotlib :class:`~matplotlib.axes.Axes`.
            add_points: Overlay vertex markers (default ``False``).
            color: Fill and edge colour.
            facecolor: Polygon fill colour.
            edgecolor: Polygon edge colour.
            linewidth: Edge stroke width in points (default ``2``).
            **kwargs: Forwarded to :func:`shapely.plotting.plot_polygon`.
        """
        if self.crs == "WGS84":
            log.warning(
                "Plotting in WGS84 is not recomended as this distorts the geometry!"
            )
        shplt.plot_polygon(
            polygon=self.geometry,
            ax=ax,
            add_points=add_points,
            color=color,
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=linewidth,
            **kwargs,
        )


def multi_polygon_to_polygon_with_holes(multi_polygon):
    """Convert a Shapely :class:`~shapely.MultiPolygon` to a CGAL ``PolygonWithHoles``.

    Each polygon in *multi_polygon* is added as a *hole* in the resulting
    CGAL structure.  This is a low-level helper used internally when passing
    obstacle geometries to the C++ decomposition kernel.

    Args:
        multi_polygon: An iterable of Shapely :class:`~shapely.Polygon`
            objects (typically a :class:`~shapely.MultiPolygon`).

    Returns:
        bindings.PolygonWithHoles: A CGAL ``Polygon_with_holes_2`` whose
        holes correspond to the input polygons.
    """
    # Create an empty CGAL PolygonWithHoles
    polygon_with_holes = bindings.PolygonWithHoles(bindings.Polygon_2())

    # Iterate through each polygon in the MultiPolygon
    for polygon in multi_polygon:
        # Convert the Shapely polygon to a list of CGAL points
        cgal_points = [
            bindings.Point_2(point.x, point.y) for point in polygon.exterior.coords
        ]

        # Create a CGAL Polygon_2 from the list of points
        cgal_polygon = bindings.Polygon_2(cgal_points)

        # Add the polygon to the PolygonWithHoles as a hole
        polygon_with_holes.add_hole(cgal_polygon)

    # Return the resulting PolygonWithHoles
    return polygon_with_holes


def is_convex(polygon: shapely.Polygon):
    """Check whether a Shapely polygon is convex.

    Uses the sign of successive cross-products to detect any concavity.  A
    polygon with fewer than 4 vertices (i.e. a triangle or degenerate shape)
    is considered non-convex.

    Args:
        polygon: The :class:`~shapely.Polygon` to test.

    Returns:
        bool: ``True`` if *polygon* is convex, ``False`` otherwise.
    """
    coords = polygon.exterior.coords
    num_coords = len(coords)

    if num_coords < 4:
        # A polygon with less than 4 vertices cannot be convex
        return False

    # Calculate the orientation of the first three points
    orientation = 0
    for i in range(num_coords):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % num_coords]
        x3, y3 = coords[(i + 2) % num_coords]

        # Calculate the cross product of the vectors (x2-x1, y2-y1) and (x3-x2, y3-y2)
        cross_product = (x2 - x1) * (y3 - y2) - (y2 - y1) * (x3 - x2)

        if cross_product != 0:
            orientation = cross_product
            break

    # Check the orientation of the remaining vertices
    for i in range(num_coords):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % num_coords]
        x3, y3 = coords[(i + 2) % num_coords]

        cross_product = (x2 - x1) * (y3 - y2) - (y2 - y1) * (x3 - x2)

        if cross_product * orientation < 0:
            return False

    return True


def shapely_polygon_to_cgal(polygon: shapely.Polygon):
    """Convert a Shapely :class:`~shapely.Polygon` to a CGAL ``Polygon_2``.

    Only the exterior ring is transferred; interior rings (holes) are
    ignored.  The last vertex of the exterior ring is dropped because
    Shapely closes rings by repeating the first vertex, while CGAL expects
    an open vertex list.

    Args:
        polygon: A Shapely :class:`~shapely.Polygon`.

    Returns:
        bindings.Polygon_2: A CGAL ``Polygon_2`` built from the exterior
        vertices of *polygon*.
    """
    # Exctract all the points except the last, as this is the same as the first
    cgal_points = [
        bindings.Point_2(point[0], point[1]) for point in polygon.exterior.coords[:-1]
    ]
    # Create a CGAL Polygon_2 from the list of points
    return bindings.Polygon_2(cgal_points)


def get_sweep_offset(overlap=0.1, height=10, field_of_view=90):
    """Calculate the inter-sweep spacing for a given sensor configuration.

    Computes the ground-sample width of the sensor footprint at *height* and
    scales it by ``(1 - overlap)`` to achieve the desired overlap between
    adjacent sweep lines.

    Args:
        overlap: Fractional overlap between adjacent sweeps, in the range
            ``[0, 1]``.  ``0.0`` means no overlap; ``0.5`` means 50 %
            overlap.  Defaults to ``0.1``.
        height: Flight or sensor height above the target surface in metres
            (default ``10``).
        field_of_view: Full horizontal field-of-view angle in degrees
            (default ``90``).

    Returns:
        float: The recommended distance (in the same units as *height*)
        between parallel sweep lines.

    Raises:
        ValueError: If *overlap* is outside the ``[0, 1]`` range.

    Example:
        ::

            >>> get_sweep_offset(overlap=0.1, height=20, field_of_view=90)
            36.0
    """
    if overlap < 0 or overlap > 1:
        msg = "Overlap percentage has to be a float between 0 and 1!"
        raise ValueError(msg)

    return abs(
        2 * height * math.tan((field_of_view * math.pi / 180.0) / 2) * (1 - overlap)
    )


def _snap_polygon(polygon: shapely.Polygon, precision: int = 1) -> shapely.Polygon:
    """Round polygon vertex coordinates to *precision* decimal places.

    CGAL's exact-arithmetic decomposition and sweep-pattern code can produce a
    SIGSEGV when fed coordinates that carry floating-point noise from pyproj
    map-projection (e.g. a WGS-84 rectangle projected to UTM becomes a slightly
    non-rectangular quadrilateral with sub-millimetre jitter on each vertex).
    Snapping to 10 cm (``precision=1``, the default) in the projected metric CRS
    removes that noise and produces clean doubles that CGAL handles without
    issues, while introducing at most 5 cm of positional error — negligible for
    any practical coverage-planning use case.

    Vertices that round to the same grid point are merged by dropping
    consecutive duplicates. If the exterior ring degenerates below three
    distinct points, or the snapped polygon becomes invalid or zero-area, an
    empty polygon is returned so callers can skip the cell instead of feeding
    a degenerate ring to CGAL, whose sweep code rejects collapsed boundaries
    with a hard error.

    Args:
        polygon: Shapely Polygon whose vertices will be snapped.
        precision: Number of decimal places to round to (default 1 → 10 cm in
            a metric CRS such as UTM).

    Returns:
        A new Shapely Polygon with snapped coordinates, or an empty polygon
        if snapping degenerates the input.
    """

    def _snap_ring(coords):
        # Index into each coordinate pair so 3D rings (with a Z coordinate)
        # are handled by dropping Z, matching the reprojection behaviour.
        rounded = [
            (round(point[0], precision), round(point[1], precision))
            for point in coords
        ]
        # Drop consecutive duplicates produced by rounding (shapely re-closes
        # the ring, so also drop a trailing point equal to the first).
        deduped = [
            point
            for i, point in enumerate(rounded)
            if i == 0 or point != rounded[i - 1]
        ]
        if len(deduped) > 1 and deduped[0] == deduped[-1]:
            deduped.pop()
        return deduped

    exterior = _snap_ring(polygon.exterior.coords)
    if len(exterior) < 3:
        return shapely.Polygon()
    interiors = []
    for ring in polygon.interiors:
        snapped = _snap_ring(ring.coords)
        if len(snapped) >= 3:
            interiors.append(snapped)
    snapped_polygon = shapely.Polygon(exterior, interiors)
    if _is_degenerate(snapped_polygon):
        return shapely.Polygon()
    return snapped_polygon


def _is_degenerate(polygon: shapely.Polygon) -> bool:
    """Return whether a polygon has no usable interior for coverage planning."""
    return polygon.is_empty or polygon.area <= 0 or not polygon.is_valid


def generate_sweep_pattern(
    polygon: shapely.Polygon,
    sweep_offset,
    clockwise=True,
    connect_sweeps=False,
):
    """Generate a boustrophedon sweep pattern over a convex polygon.

    Produces a set of parallel sweep lines (or a single connected path)
    covering *polygon*.  The underlying algorithm is the C++ sweep
    implementation from `ethz-asl/polygon_coverage_planning
    <https://github.com/ethz-asl/polygon_coverage_planning>`_ exposed via
    pybind11 bindings.

    Args:
        polygon: The :class:`~shapely.Polygon` to sweep.  Should be a
            convex cell; for non-convex areas call :func:`decompose_polygon`
            first.
        sweep_offset: Distance in the polygon's CRS units between adjacent
            parallel sweep lines.  Use :func:`get_sweep_offset` to derive
            this from sensor parameters.
        clockwise: Sweep direction.  ``True`` (default) starts at the
            clockwise end of each row.
        connect_sweeps: When ``True``, all sweep segments are concatenated
            into a single :class:`~shapely.LineString` (suitable for
            continuous path execution).  When ``False`` (default) each
            segment is returned as a separate :class:`~shapely.LineString`.

    Returns:
        list[shapely.LineString]: A list of sweep line segments, or a
        single-element list containing the connected path when
        *connect_sweeps* is ``True``.

    Raises:
        ValueError: If *polygon* degenerates (zero area or invalid) after
            coordinate snapping.
    """
    # Snap coordinates to 10 cm precision to remove pyproj floating-point noise
    # that can cause CGAL to SIGSEGV on otherwise valid polygon inputs.
    polygon = _snap_polygon(polygon)
    if _is_degenerate(polygon):
        msg = (
            "Polygon degenerated after snapping coordinates to a 10 cm grid "
            "(zero area or invalid ring); sweep patterns cannot be generated "
            "for degenerate polygons. This usually happens when a decomposed "
            "cell is an extremely thin sliver whose vertices collapse onto "
            "each other after rounding."
        )
        raise ValueError(msg)
    # Make sure that the orientation of the polygon is counterclockwise and the interior is clockwise
    cgal_poly = shapely_polygon_to_cgal(orient(polygon=polygon))
    segments = bindings.generate_sweeps(
        cgal_poly, sweep_offset, clockwise, connect_sweeps
    )

    if connect_sweeps:
        # Combine all segments into a single LineString
        combined_line = []
        for seg in segments:
            combined_line.append([seg.source.x, seg.source.y])
            combined_line.append([seg.target.x, seg.target.y])
        result = [shapely.LineString(combined_line)]
    else:
        lines = [
            shapely.LineString(
                [[seg.source.x, seg.source.y], [seg.target.x, seg.target.y]]
            )
            for seg in segments
        ]
        result = lines

    return result


def decompose_polygon(
    boundary: shapely.Polygon, obstacles: shapely.MultiPolygon | shapely.Polygon = None
):
    """Decompose a polygon (with optional obstacles) into convex cells.

    Uses the Boustrophedon Cell Decomposition algorithm implemented in CGAL
    (via pybind11 bindings) to split *boundary* into a set of convex,
    weakly-monotone sub-polygons.  Each returned cell can be passed directly
    to :func:`generate_sweep_pattern`.

    When an obstacle intersects the boundary edge, the two geometries are
    merged so that the boundary is expanded to include the overlapping
    obstacle region rather than creating a degenerate hole.

    Args:
        boundary: The outer boundary polygon to decompose.
        obstacles: Optional obstacles (keep-out zones) inside *boundary*.
            Accepts a single :class:`~shapely.Polygon` or a
            :class:`~shapely.MultiPolygon`.  Pass ``None`` (default) for an
            obstacle-free area.

    Returns:
        list[shapely.Polygon]: The convex decomposition cells.  Each cell is
        a simple :class:`~shapely.Polygon` with no holes.  Cells that
        collapse under coordinate snapping (e.g. extremely thin slivers)
        are dropped.

    Raises:
        ValueError: If *obstacles* is provided but is neither a
            :class:`~shapely.Polygon` nor a :class:`~shapely.MultiPolygon`,
            or if *boundary* degenerates after coordinate snapping.
    """
    # Snap coordinates to 10 cm precision to remove pyproj floating-point noise
    # that can cause CGAL to SIGSEGV on otherwise valid polygon inputs.
    boundary = _snap_polygon(boundary)
    if _is_degenerate(boundary):
        msg = (
            "Boundary polygon degenerated after snapping coordinates to a "
            "10 cm grid; cannot decompose it into coverage cells."
        )
        raise ValueError(msg)
    if obstacles is not None:
        if isinstance(obstacles, shapely.Polygon):
            obstacles = shapely.MultiPolygon([obstacles])
        elif not isinstance(obstacles, shapely.MultiPolygon):
            msg = "Obstacles must be a Shapely MultiPolygon."
            raise ValueError(msg)

        # If the obstacles intersect with the boundary, take the union of the two and remove it from the obstacles list
        updated_obstacles = []
        for obstacle in obstacles.geoms:
            if obstacle.intersects(boundary.boundary):
                log.debug(
                    "Obstacles intersect with the boundary, the geometries will be merged."
                )
                boundary = _snap_polygon(obstacle.union(boundary))
            else:
                updated_obstacles.append(_snap_polygon(obstacle))

        obstacles = shapely.MultiPolygon(updated_obstacles)
    pwh = bindings.Polygon_with_holes_2(shapely_polygon_to_cgal(boundary))
    if obstacles is not None:
        for poly in obstacles.geoms:
            pwh.add_hole(shapely_polygon_to_cgal(poly))
    decompose_polygons = bindings.decompose(pwh)
    cells = []
    for polygon in decompose_polygons:
        # Drop cells that collapse under coordinate snapping (e.g. thin
        # slivers whose vertices land on the same grid point); CGAL sweep
        # generation rejects degenerate rings with a hard error.
        coords = [(vertex.x, vertex.y) for vertex in polygon]
        if len(coords) < 3:
            continue
        cell = _snap_polygon(shapely.Polygon(coords))
        if not _is_degenerate(cell):
            cells.append(cell)
    return cells
