
#include "bcd.h"
#include "cgal_comm.h"
#include "decomposition.h"
#include "sweep.h"
#include "weakly_monotone.h"

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <vector>

#include <CGAL/Exact_predicates_exact_constructions_kernel.h>

#define STRINGIFY(x) #x
#define MACRO_STRINGIFY(x) STRINGIFY(x)

namespace py = pybind11;

std::string polygon_to_string(const Polygon_2 &poly)
{
    std::stringstream ss;
    ss << "Polygon with " << poly.size() << " vertices:";
    for (auto v = poly.vertices_begin(); v != poly.vertices_end(); ++v)
    {
        ss << " (" << v->x() << ", " << v->y() << ")";
    }
    return ss.str();
}

py::list decompose(const PolygonWithHoles &pwh)
{
    std::vector<Polygon_2> decomposedPolygons;
    std::vector<Line_2> cell_dirs;
    double msa;
    // std::cout<< "boundary: " << polygon_to_string(pwh.outer_boundary()) << std::endl;
    // for(auto poly: pwh.holes()){
    //     std::cout<< "hole: " << polygon_to_string(poly) << std::endl;
    // }
    // TODO before calculating BCD, check whether it is a valid polygon with holes and check that the function does not fail

    polygon_coverage_planning::computeBestBCDFromPolygonWithHoles(pwh, &decomposedPolygons);
    py::list result;
    for (auto poly : decomposedPolygons)
    {
        result.append(poly);
    }
    return result;
}

py::list generate_sweeps(const Polygon_2 &poly, const double sweep_offset, bool clockwise = false)
{
    py::list result;
    // // Traverse through all polygons
    std::vector<std::vector<Segment_2>> sweeps;
    // TODO Reuse the directions from the polygon decomposition for performance optimisation
    Direction_2 bestDir;
    polygon_coverage_planning::findBestSweepDir(poly, &bestDir);
    // Line_2 line(Point_2(0, 0), bestDir);
    // if (polygon_coverage_planning::isWeaklyMonotone(poly, line))
    // {
    // Construct the sweep plan
    std::vector<Segment_2> sweep;
    if (polygon_coverage_planning::computeSweep(poly, sweep_offset, bestDir, clockwise, sweep))
    {
        for (auto segment : sweep)
            result.append(segment);
    }
    else
    {
        // TODO error handling
    }
    // }

    return result;
}

PYBIND11_MODULE(bindings, m)
{
    m.doc() = R"pbdoc(
        Pybind11 core plugin
        -----------------------

        .. currentmodule:: core

        .. autosummary::
           :toctree: _generate

           decompose
           generate_sweeps
    )pbdoc";

    // Expose the Point_2 type to Python
    py::class_<Point_2>(m, "Point_2")
        .def(py::init<double, double>())
        .def_property_readonly("x", [](const Point_2 &p)
                               { return CGAL::to_double(p.x()); })
        .def_property_readonly("y", [](const Point_2 &p)
                               { return CGAL::to_double(p.y()); });

    // Expose the Polygon_2 type to Python
    py::class_<Polygon_2>(m, "Polygon_2")
        .def(py::init<>())
        .def(py::init([](const std::vector<Point_2> &points)
                      { return Polygon_2(points.begin(), points.end()); }))
        .def("is_simple", &Polygon_2::is_simple)
        .def("is_convex", &Polygon_2::is_convex)
        .def("push_back", &Polygon_2::push_back)
        .def_property_readonly("vertices", [](const Polygon_2 &self)
                               {
            py::list vertices;
            for (auto v = self.vertices_begin(); v != self.vertices_end(); ++v) {
                vertices.append(py::cast(*v));
            }
            return vertices; })
        .def("__str__", [](const Polygon_2 &self)
             {
            std::stringstream ss;
            ss << "[";

            py::list vertices;
            for (auto v = self.vertices_begin(); v != self.vertices_end(); ++v) {
                ss << *v;
                if (v != self.vertices_end()- 1) {
                    ss << ", ";
                }            }
            ss << "]";
            return ss.str(); })
        .def("__len__", [](const Polygon_2 &p)
             { return p.size(); })
        .def(
            "__iter__", [](const Polygon_2 &p)
            { return py::make_iterator(p.vertices_begin(), p.vertices_end()); },
            py::keep_alive<0, 1>());

    py::class_<PolygonWithHoles>(m, "Polygon_with_holes_2")
        .def(py::init<>([](const Polygon_2 poly)
                        { return PolygonWithHoles(poly); }))
        .def("add_hole", &PolygonWithHoles::add_hole)
        .def_property_readonly("holes", [](PolygonWithHoles &p) -> std::vector<Polygon_2>
                               {
            std::vector<Polygon_2> holes;
            for (auto it = p.holes_begin(); it != p.holes_end(); ++it) {
                holes.push_back(*it);
            }
            return holes; })
        .def_property_readonly("boundary", [](const PolygonWithHoles &p)
                               { return p.outer_boundary(); });

    py::class_<Segment_2>(m, "Segment_2")
        .def(py::init<>())
        .def(py::init<K::Point_2, K::Point_2>())
        .def_property_readonly("source", &Segment_2::source)
        .def_property_readonly("target", &Segment_2::target)
        .def("__str__", [](const Segment_2 &s)
             {
            std::stringstream ss;
            ss << "[" << s.source() << ", " << s.target() << "]";
            return ss.str(); });

    m.def("decompose", &decompose, R"pbdoc(
        Decomposes the input polygon into a list of polygons.

            Args:
                polygon: A Polygon_with_holes_2 object.

            Returns:
                A list of Polygon_2 objects. 
    )pbdoc",
          py::arg("pwh"), "PolygonWithHoles");

    m.def("generate_sweeps", &generate_sweeps, R"pbdoc(
        Generates a sweep pattern from the input polygon.

            Args:
                polygon: A Polygon_2 object.

            Returns:
                A tuple containing a Segment_2 object.
    )pbdoc",
          py::arg("polygon"), py::arg("sweep_offset"), py::arg("clockwise") = false);

#ifdef VERSION_INFO
    m.attr("__version__") = MACRO_STRINGIFY(VERSION_INFO);
#else
    m.attr("__version__") = "dev";
#endif
}