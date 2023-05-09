import coverage_planner._core as planner
from coverage_planner._core import Point_2, Polygon_2
from flask import Flask, jsonify


def test1():
    # Construct a polygon from a list of points
    points = [Point_2(0, 0), Point_2(1, 0), Point_2(1, 1), Point_2(0, 1)]
    polygon = Polygon_2(points)

    # Check if the polygon is simple and convex
    print(polygon.is_simple())   # True
    print(polygon.is_convex())   # True

    for vertex in polygon.vertices:
        print(vertex.x, vertex.y)


# create the outer polygon with holes

outer_boundary = planner.Polygon_2()
outer_boundary.push_back(planner.Point_2(0, 0))
outer_boundary.push_back(planner.Point_2(0, 10))
outer_boundary.push_back(planner.Point_2(10, 10))
outer_boundary.push_back(planner.Point_2(10, 0))

outer_poly = planner.Polygon_with_holes_2(outer_boundary)

inner_boundary = planner.Polygon_2()
inner_boundary.push_back(planner.Point_2(2, 2))
inner_boundary.push_back(planner.Point_2(2, 8))
inner_boundary.push_back(planner.Point_2(8, 8))
inner_boundary.push_back(planner.Point_2(8, 2))

outer_poly.add_hole(inner_boundary)

# create the list of polygons
poly_list = []
polygon1 = planner.Polygon_2()
polygon1.push_back(planner.Point_2(3, 3))
polygon1.push_back(planner.Point_2(3, 5))
polygon1.push_back(planner.Point_2(5, 5))
polygon1.push_back(planner.Point_2(5, 3))
poly_list.append(polygon1)

polygon2 = planner.Polygon_2()
polygon2.push_back(planner.Point_2(6, 6))
polygon2.push_back(planner.Point_2(6, 8))
polygon2.push_back(planner.Point_2(8, 8))
polygon2.push_back(planner.Point_2(8, 6))
poly_list.append(polygon2)


decomposed_polygons = planner.decompose(outer_poly)
segments = []
for poly in decomposed_polygons:
    segments.extend(planner.generate_sweeps(poly))


# app = Flask(__name__)

# @app.route('/example', methods=['post'])
# def example():
#     return jsonify({'result': 'success'})  # Return a JSON response

# if __name__ == '__main__':
#     app.run(debug=True, host="0.0.0.0", port=5000)