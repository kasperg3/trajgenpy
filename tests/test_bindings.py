import pytest
import trajgenpy.bindings as bindings
from trajgenpy.Logging import debug


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

    for vertex in polygon.vertices:
        debug(vertex.x, vertex.y)


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
    debug(len(decomposed_polygons))
    segments = []
    for poly in decomposed_polygons:
        if poly.is_convex():
            segments.extend(bindings.generate_sweeps(poly, 0.1))
        else:
            raise Exception("not able to generate a plan for a non convex polygon")
    assert len(segments) == 80


# Run the tests
if __name__ == "__main__":
    pytest.main(["-v", "-x", "tests/test_bindings.py"])
