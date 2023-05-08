/*
 * polygon_coverage_planning implements algorithms for coverage planning in
 * general polygons with holes. Copyright (C) 2019, Rik Bähnemann, Autonomous
 * Systems Lab, ETH Zürich
 *
 * This program is free software: you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free Software
 * Foundation, either version 3 of the License, or (at your option) any later
 * version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
 * details.
 *
 * You should have received a copy of the GNU General Public License along with
 * this program.  If not, see <http://www.gnu.org/licenses/>.
 */


#ifndef POLYGON_COVERAGE_GEOMETRY_CGAL_DEFINITIONS_H_
#define POLYGON_COVERAGE_GEOMETRY_CGAL_DEFINITIONS_H_

#include <CGAL/Arr_linear_traits_2.h>
#include <CGAL/Arr_segment_traits_2.h>
#include <CGAL/Arrangement_2.h>
#include <CGAL/Arrangement_on_surface_2.h>
#include <CGAL/Boolean_set_operations_2.h>
#include <CGAL/Cartesian.h>
#include <CGAL/Exact_predicates_exact_constructions_kernel.h>
#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/General_polygon_with_holes_2.h>
#include <CGAL/MP_Float.h>
#include <CGAL/Partition_traits_2.h>
#include <CGAL/Polygon_with_holes_2.h>
#include <CGAL/Quotient.h>
#include <CGAL/Vector_2.h>
#include <CGAL/centroid.h>
#include <CGAL/min_quadrilateral_2.h>
#include <CGAL/partition_2.h>
#include <CGAL/property_map.h>
#include <CGAL/squared_distance_2.h>
/* #include <CGAL/Aff_transformation_2.h> */
#include <CGAL/minkowski_sum_2.h>
#include <CGAL/partition_2.h>
/* #include <CGAL/Gps_circle_segment_traits_2.h> */
#include <CGAL/Aff_transformation_2.h>
#include <CGAL/Polygon_set_2.h>
#include <CGAL/approximated_offset_2.h>
#include <CGAL/create_offset_polygons_2.h>
#include <CGAL/Exact_predicates_exact_constructions_kernel.h>
#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/Polygon_with_holes_2.h>
typedef CGAL::Exact_predicates_exact_constructions_kernel K;
typedef K::FT FT;
typedef K::Point_2 Point_2;
typedef K::Point_3 Point_3;
typedef K::Vector_2 Vector_2;
typedef K::Direction_2 Direction_2;
typedef K::Line_2 Line_2;
typedef K::Intersect_2 Intersect_2;
typedef K::Plane_3 Plane_3;
typedef K::Segment_2 Segment_2;
typedef K::Triangle_2 Triangle_2;
typedef CGAL::Polygon_2<K> Polygon_2;
typedef Polygon_2::Vertex_const_iterator VertexConstIterator;
typedef Polygon_2::Vertex_const_circulator VertexConstCirculator;
typedef Polygon_2::Vertex_iterator VertexIterator;
typedef Polygon_2::Vertex_circulator VertexCirculator;
typedef Polygon_2::Edge_const_iterator EdgeConstIterator;
typedef Polygon_2::Edge_const_circulator EdgeConstCirculator;
typedef CGAL::Polygon_with_holes_2<K> PolygonWithHoles;
typedef CGAL::Exact_predicates_inexact_constructions_kernel InexactKernel;

#endif  // POLYGON_COVERAGE_GEOMETRY_CGAL_DEFINITIONS_H_
