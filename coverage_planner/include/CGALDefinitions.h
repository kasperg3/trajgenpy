#ifndef CGALDEFINITIONS_H
#define CGALDEFINITIONS_H

#pragma once
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

typedef CGAL::Exact_predicates_exact_constructions_kernel Kernel;
typedef Kernel::FT FT;
typedef Kernel::Point_2 Point_2;
typedef Kernel::Point_3 Point_3;
typedef Kernel::Vector_2 Vector_2;
typedef Kernel::Direction_2 Direction_2;
typedef Kernel::Line_2 Line_2;
typedef Kernel::Ray_2 Ray_2;
typedef Kernel::Intersect_2 Intersect_2;
typedef Kernel::Plane_3 Plane_3;
typedef Kernel::Segment_2 Segment_2;

typedef Kernel::Triangle_2 Triangle_2;
typedef CGAL::Polygon_2<Kernel> Polygon_2;
typedef CGAL::Polygon_set_2<Kernel> Polygon_set_2;
typedef CGAL::Polygon_with_holes_2<Kernel> PolygonWithHoles;

#endif
