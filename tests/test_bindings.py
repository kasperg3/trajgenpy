import pytest
import trajgenpy.bindings as bindings


def _make_polygon(points):
    polygon = bindings.Polygon_2()
    for x, y in points:
        polygon.push_back(bindings.Point_2(x, y))
    return polygon


def _decomposition_coordinates(polygons):
    return [[(vertex.x, vertex.y) for vertex in polygon] for polygon in polygons]


def _canonical_polygon(vertices):
    """Return a canonical polygon ring independent of start vertex and winding."""
    points = [(float(x), float(y)) for x, y in vertices]

    def _rotations(seq):
        return [tuple(seq[i:] + seq[:i]) for i in range(len(seq))]

    return min(_rotations(points) + _rotations(list(reversed(points))))


def _canonical_decomposition(polygons):
    """Return a canonical decomposition independent of polygon ordering."""
    return tuple(sorted(_canonical_polygon(poly) for poly in polygons))


def test_create_polygon():
    # Construct a polygon from a list of points
    points = [
        bindings.Point_2(0, 0),
        bindings.Point_2(1, 0),
        bindings.Point_2(1, 1),
        bindings.Point_2(0, 1),
    ]
    polygon = bindings.Polygon_2(points)

    # Check if the polygon is simple and convex
    assert polygon.is_simple()  # True
    assert polygon.is_convex()  # True


def test_create_sweeps():
    # create the outer polygon with holes
    outer_boundary = bindings.Polygon_2()
    outer_boundary.push_back(bindings.Point_2(0, 0))
    outer_boundary.push_back(bindings.Point_2(0, 10))
    outer_boundary.push_back(bindings.Point_2(10, 10))
    outer_boundary.push_back(bindings.Point_2(10, 0))

    outer_poly = bindings.Polygon_with_holes_2(outer_boundary)

    inner_boundary = bindings.Polygon_2()
    inner_boundary.push_back(bindings.Point_2(2, 2))
    inner_boundary.push_back(bindings.Point_2(2, 8))
    inner_boundary.push_back(bindings.Point_2(8, 8))
    inner_boundary.push_back(bindings.Point_2(8, 2))

    outer_poly.add_hole(inner_boundary)

    # create the list of polygons
    poly_list = []
    polygon1 = bindings.Polygon_2()
    polygon1.push_back(bindings.Point_2(3, 3))
    polygon1.push_back(bindings.Point_2(3, 5))
    polygon1.push_back(bindings.Point_2(5, 5))
    polygon1.push_back(bindings.Point_2(5, 3))
    poly_list.append(polygon1)

    polygon2 = bindings.Polygon_2()
    polygon2.push_back(bindings.Point_2(6, 6))
    polygon2.push_back(bindings.Point_2(6, 8))
    polygon2.push_back(bindings.Point_2(8, 8))
    polygon2.push_back(bindings.Point_2(8, 6))
    poly_list.append(polygon2)

    decomposed_polygons = bindings.decompose(outer_poly)
    segments = []
    for poly in decomposed_polygons:
        if poly.is_convex():
            segments.extend(bindings.generate_sweeps(poly, 0.5))
        else:
            msg = "not able to generate a plan for a non convex polygon"
            raise Exception(msg)
    assert len(segments) == 20


def test_decompose_matches_legacy_cpp_output_square_with_hole():
    """Golden regression: accept legacy C++ partition and GEOS-equivalent partition."""
    outer_poly = bindings.Polygon_with_holes_2(
        _make_polygon([(0, 0), (0, 10), (10, 10), (10, 0)])
    )
    outer_poly.add_hole(_make_polygon([(2, 2), (2, 8), (8, 8), (8, 2)]))

    decomposed_polygons = _decomposition_coordinates(bindings.decompose(outer_poly))

    legacy_cpp = _canonical_decomposition(
        [
            [(10.0, -0.0), (10.0, 10.0), (8.0, 10.0), (8.0, -0.0)],
            [(8.0, 8.0), (8.0, 10.0), (2.0, 10.0), (2.0, 8.0)],
            [(8.0, -0.0), (8.0, 2.0), (2.0, 2.0), (2.0, -0.0)],
            [(2.0, -0.0), (2.0, 10.0), (-0.0, 10.0), (-0.0, 0.0)],
        ]
    )
    geos_equivalent = _canonical_decomposition(
        [
            [(0.0, 0.0), (0.0, 10.0), (2.0, 8.0), (2.0, 2.0)],
            [(2.0, 2.0), (8.0, 2.0), (10.0, 0.0), (0.0, 0.0)],
            [(0.0, 10.0), (10.0, 10.0), (8.0, 8.0), (2.0, 8.0)],
            [(8.0, 2.0), (8.0, 8.0), (10.0, 10.0), (10.0, 0.0)],
        ]
    )
    assert _canonical_decomposition(decomposed_polygons) in {legacy_cpp, geos_equivalent}


def test_decompose_matches_legacy_cpp_output_concave_polygon():
    """Golden regression: accept legacy C++ partition and GEOS-equivalent partition."""
    concave = _make_polygon(
        [
            (12.620400, 55.687962),
            (12.632788, 55.691589),
            (12.637446, 55.687689),
            (12.624924, 55.683489),
            (12.628446, 55.686489),
            (12.625924, 55.688489),
            (12.630924, 55.689489),
        ]
    )
    pwh = bindings.Polygon_with_holes_2(concave)

    decomposed_polygons = _decomposition_coordinates(bindings.decompose(pwh))

    legacy_cpp = _canonical_decomposition(
        [
            [(12.625924, 55.688489), (12.626523990911974, 55.68801319436005), (12.630924, 55.689489)],
            [(12.632788, 55.691589), (12.6204, 55.687962), (12.630924, 55.689489), (12.634045630169595, 55.69053602497608)],
            [
                (12.634045630169595, 55.69053602497608),
                (12.626523990911974, 55.68801319436005),
                (12.628446, 55.686489),
                (12.624924, 55.683489),
                (12.637446, 55.687689),
            ],
        ]
    )
    geos_equivalent = _canonical_decomposition(
        [
            [(12.6204, 55.687962), (12.632788, 55.691589), (12.630924, 55.689489)],
            [(12.624924, 55.683489), (12.628446, 55.686489), (12.637446, 55.687689)],
            [(12.630924, 55.689489), (12.637446, 55.687689), (12.628446, 55.686489), (12.625924, 55.688489)],
            [(12.630924, 55.689489), (12.632788, 55.691589), (12.637446, 55.687689)],
        ]
    )
    assert _canonical_decomposition(decomposed_polygons) in {legacy_cpp, geos_equivalent}


# Run the tests
if __name__ == "__main__":
    pytest.main(["-v", "-x", "tests/test_bindings.py"])
