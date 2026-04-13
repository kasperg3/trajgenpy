"""Pure-Python compatibility layer for the former CGAL pybind11 bindings."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise

import shapely
from shapely.affinity import rotate
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import substring

_EPS = 1e-9


@dataclass(frozen=True)
class Point_2:
    x: float
    y: float


@dataclass(frozen=True)
class Segment_2:
    source: Point_2
    target: Point_2

    def __str__(self):
        return f"[({self.source.x}, {self.source.y}), ({self.target.x}, {self.target.y})]"


class Polygon_2:
    def __init__(self, points: list[Point_2] | None = None):
        self._points: list[Point_2] = list(points) if points is not None else []

    def push_back(self, point: Point_2):
        self._points.append(point)

    @property
    def vertices(self):
        return list(self._points)

    def is_simple(self):
        poly = _polygon2_to_shapely(self)
        return (not poly.is_empty) and poly.is_valid and poly.boundary.is_simple

    def is_convex(self):
        poly = _polygon2_to_shapely(self)
        if poly.is_empty:
            return False
        return abs(poly.convex_hull.area - poly.area) <= _EPS

    def __len__(self):
        return len(self._points)

    def __iter__(self):
        return iter(self._points)

    def __str__(self):
        return "[" + ", ".join(f"({p.x}, {p.y})" for p in self._points) + "]"


class Polygon_with_holes_2:
    def __init__(self, poly: Polygon_2):
        self._boundary = poly
        self._holes: list[Polygon_2] = []

    def add_hole(self, hole: Polygon_2):
        self._holes.append(hole)

    @property
    def holes(self):
        return list(self._holes)

    @property
    def boundary(self):
        return self._boundary


# Backward compatibility for existing internal helper naming.
PolygonWithHoles = Polygon_with_holes_2


def _polygon2_to_shapely(poly: Polygon_2) -> Polygon:
    coords = [(p.x, p.y) for p in poly]
    if len(coords) < 3:
        return Polygon()
    return Polygon(coords)


def _pwh_to_shapely(pwh: Polygon_with_holes_2) -> Polygon:
    boundary = _polygon2_to_shapely(pwh.boundary)
    hole_rings = []
    for hole in pwh.holes:
        hole_ring = [(p.x, p.y) for p in hole]
        if len(hole_ring) >= 3:
            hole_rings.append(hole_ring)
    if boundary.is_empty:
        return Polygon()
    return Polygon(boundary.exterior.coords, hole_rings)


def _is_convex_polygon(poly: Polygon) -> bool:
    return (not poly.is_empty) and abs(poly.convex_hull.area - poly.area) <= _EPS


def _polygon_to_polygon2(poly: Polygon) -> Polygon_2:
    pts = [Point_2(float(x), float(y)) for x, y in list(poly.exterior.coords)[:-1]]
    return Polygon_2(pts)


def _best_sweep_direction(poly: Polygon) -> tuple[float, float]:
    coords = list(poly.exterior.coords)[:-1]
    best_width = None
    best_dir = (1.0, 0.0)
    for i, (x1, y1) in enumerate(coords):
        x2, y2 = coords[(i + 1) % len(coords)]
        dx = x2 - x1
        dy = y2 - y1
        norm = math.hypot(dx, dy)
        if norm <= _EPS:
            continue
        ux = dx / norm
        uy = dy / norm
        nx = -uy
        ny = ux
        projs = [x * nx + y * ny for x, y in coords]
        width = max(projs) - min(projs)
        if best_width is None or width < best_width - _EPS:
            best_width = width
            best_dir = (ux, uy)
    return best_dir


def decompose(pwh: Polygon_with_holes_2):
    region = _pwh_to_shapely(pwh)
    if region.is_empty or not region.is_valid:
        return []

    triangulated = shapely.constrained_delaunay_triangles(region)
    if triangulated.is_empty:
        return []

    cells = []
    for tri in triangulated.geoms:
        if tri.geom_type != "Polygon" or tri.area <= _EPS:
            continue
        clipped = tri.intersection(region)
        if clipped.geom_type == "Polygon" and clipped.area > _EPS:
            cells.append(clipped)

    changed = True
    while changed:
        changed = False
        for i in range(len(cells)):
            if changed:
                break
            for j in range(i + 1, len(cells)):
                merged = cells[i].union(cells[j])
                if merged.geom_type != "Polygon":
                    continue
                if len(merged.interiors) != 0:
                    continue
                if not _is_convex_polygon(merged):
                    continue
                cells = [c for k, c in enumerate(cells) if k not in {i, j}] + [merged]
                changed = True
                break

    cells.sort(key=lambda g: (g.centroid.x, g.centroid.y, g.area))
    return [_polygon_to_polygon2(cell) for cell in cells]


def generate_sweeps(
    polygon: Polygon_2,
    sweep_offset: float = 50.0,
    clockwise: bool = False,
    connect_sweeps: bool = False,
):
    if sweep_offset <= 0:
        return []

    poly = _polygon2_to_shapely(polygon)
    if poly.is_empty or not poly.is_valid:
        return []

    ux, uy = _best_sweep_direction(poly)
    angle_deg = math.degrees(math.atan2(uy, ux))
    rotated = rotate(poly, -angle_deg, origin=(0, 0))
    minx, miny, maxx, maxy = rotated.bounds
    pad = max(maxx - minx, maxy - miny) + sweep_offset + 1.0

    sweep_lines: list[LineString] = []
    y = miny
    while y <= maxy + _EPS:
        cutter = LineString([(minx - pad, y), (maxx + pad, y)])
        inter = rotated.intersection(cutter)
        if inter.is_empty:
            y += sweep_offset
            continue
        if inter.geom_type == "LineString":
            if inter.length > _EPS:
                sweep_lines.append(inter)
        elif inter.geom_type == "MultiLineString":
            segments = sorted(inter.geoms, key=lambda seg: seg.bounds[0])
            for seg in segments:
                if seg.length > _EPS:
                    sweep_lines.append(seg)
        y += sweep_offset

    if clockwise:
        sweep_lines = list(reversed(sweep_lines))

    if connect_sweeps and len(sweep_lines) > 1:
        connected: list[LineString] = []
        current_end = None
        ring = LineString(list(rotated.exterior.coords))

        def _path_along_ring(start, end):
            start_distance = ring.project(Point(start))
            end_distance = ring.project(Point(end))
            total = ring.length

            def _forward_path(a, b):
                if a <= b:
                    coords = list(substring(ring, a, b).coords)
                else:
                    coords = list(substring(ring, a, total).coords)
                    wrap = list(substring(ring, 0, b).coords)
                    if wrap:
                        coords.extend(wrap[1:])
                return coords

            path_a_b = _forward_path(start_distance, end_distance)
            path_b_a = list(reversed(_forward_path(end_distance, start_distance)))
            if len(path_a_b) < 2:
                return [start, end]
            if len(path_b_a) < 2:
                return path_a_b
            length_a_b = LineString(path_a_b).length
            length_b_a = LineString(path_b_a).length
            return path_a_b if length_a_b <= length_b_a else path_b_a

        for idx, seg in enumerate(sweep_lines):
            x0, y0 = seg.coords[0]
            x1, y1 = seg.coords[-1]
            if idx % 2 == 1:
                x0, y0, x1, y1 = x1, y1, x0, y0
            current = LineString([(x0, y0), (x1, y1)])
            if current_end is not None:
                direct_connector = LineString([current_end, (x0, y0)])
                if rotated.covers(direct_connector):
                    connected.append(direct_connector)
                else:
                    boundary_path = _path_along_ring(current_end, (x0, y0))
                    for start, end in pairwise(boundary_path):
                        connector_segment = LineString([start, end])
                        if connector_segment.length > _EPS:
                            connected.append(connector_segment)
            connected.append(current)
            current_end = (x1, y1)
        sweep_lines = connected

    result = []
    for seg in sweep_lines:
        unrot = rotate(seg, angle_deg, origin=(0, 0))
        start = Point_2(float(unrot.coords[0][0]), float(unrot.coords[0][1]))
        end = Point_2(float(unrot.coords[-1][0]), float(unrot.coords[-1][1]))
        result.append(Segment_2(start, end))
    return result
