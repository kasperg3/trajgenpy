
#include "include/bcd.h"
#include "include/cgal_comm.h"
#include "include/decomposition.h"
#include "include/sweep.h"
#include "include/weakly_monotone.h"
#include "include/CoveragePlanner.h"

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <vector>

#include <CGAL/Exact_predicates_exact_constructions_kernel.h>

#define STRINGIFY(x) #x
#define MACRO_STRINGIFY(x) STRINGIFY(x)

namespace py = pybind11;

// Utility functions
// parse GeoJson to Polygon and PolygonWithHoles
// serialize sweeps and polygons to GeoJson

// functions to bind
// decompose
// sweep generation

Polygon_2 parsePolygon(std::string geojson){
    return Polygon_2();
}

std::string polygon_to_string(const Polygon_2& poly) {
    std::stringstream ss;
    ss << "Polygon with " << poly.size() << " vertices:";
    for (auto v = poly.vertices_begin(); v != poly.vertices_end(); ++v) {
        ss << " (" << v->x() << ", " << v->y() << ")";
    }
    return ss.str();
}

py::list decompose(const PolygonWithHoles& pwh){

    std::vector<Polygon_2> decomposedPolygons;
    std::vector<Line_2> cell_dirs;
    double msa;

    // TODO before calculating BCD, check whether it is a valid polygon with holes and check that the function does not fail
    polygon_coverage_planning::computeBestBCDFromPolygonWithHoles(pwh, decomposedPolygons, cell_dirs,msa);
    py::list result;
    for(auto poly: decomposedPolygons){
        std::cout << polygon_to_string(poly) << std::endl;
        result.append(poly);
    }
    return result;
}

py::list generate_sweeps(const Polygon_2& poly){
    py::list result;
    // // Traverse through all polygons
    std::vector<std::vector<Segment_2>> sweeps;
    // TODO Reuse the directions from the polygon decomposition for performance optimisation
    Direction_2 bestDir;
    polygon_coverage_planning::findBestSweepDir(poly, &bestDir);
    // Construct the sweep plan
    const double maxSweepOffset = 0.1; // TODO this should be changed to an appropriate value, this should be calculated based on altitude and 
    std::vector<Segment_2> sweep;
    if (!polygon_coverage_planning::computeSweep(
        poly, maxSweepOffset, bestDir, false,
        sweep))
    {
    } else {
        for(auto segment: sweep)
            result.append(segment);
    }
    
    return result; 


}

PYBIND11_MODULE(_core, m) {
    m.doc() = R"pbdoc(
        Pybind11 example plugin
        -----------------------

        .. currentmodule:: coverage_planner

        .. autosummary::
           :toctree: _generate

           add
           subtract
    )pbdoc";

    // Expose the Point_2 type to Python
    py::class_<Point_2>(m, "Point_2")
        .def(py::init<double, double>())
        .def_property_readonly("x", [](const Point_2& p) { return CGAL::to_double(p.x()); })
        .def_property_readonly("y", [](const Point_2& p) { return CGAL::to_double(p.y()); });

    // Expose the Polygon_2 type to Python
    py::class_<Polygon_2>(m, "Polygon_2")
        .def(py::init<>())
        .def(py::init([](const std::vector<Point_2>& points) {return Polygon_2(points.begin(), points.end());}))
        .def("is_simple", &Polygon_2::is_simple)
        .def("is_convex", &Polygon_2::is_convex)
        .def("push_back", &Polygon_2::push_back)
        .def_property_readonly("vertices", [](const Polygon_2& self) {
            py::list vertices;
            for (auto v = self.vertices_begin(); v != self.vertices_end(); ++v) {
                vertices.append(py::cast(*v));
            }
            return vertices;
        })
        .def("__str__", [](const Polygon_2& self) {
            std::stringstream ss;
            ss << "[";

            py::list vertices;
            for (auto v = self.vertices_begin(); v != self.vertices_end(); ++v) {
                ss << *v;
                if (v != self.vertices_end()- 1) {
                    ss << ", ";
                }            }
            ss << "]";
            return ss.str();
        })
        .def("__len__", [](const Polygon_2& p) { return p.size(); })
        .def("__iter__", [](const Polygon_2& p) { return py::make_iterator(p.vertices_begin(), p.vertices_end()); }, py::keep_alive<0, 1>());

    py::class_<PolygonWithHoles>(m, "Polygon_with_holes_2")
        .def(py::init<>([](const Polygon_2 poly) {return PolygonWithHoles(poly);}))
        .def("add_hole",&PolygonWithHoles::add_hole)
        .def_property_readonly("holes", [](PolygonWithHoles& p) -> std::vector<Polygon_2> {
            std::vector<Polygon_2> holes;
            for (auto it = p.holes_begin(); it != p.holes_end(); ++it) {
                holes.push_back(*it);
            }
            return holes;
        });
    
    py::class_<Segment_2>(m, "Segment_2")
        .def(py::init<>())
        .def(py::init<K::Point_2, K::Point_2>())
        .def_property_readonly("source", &Segment_2::source)
        .def_property_readonly("target", &Segment_2::target)
        .def("__str__", [](const Segment_2& s) {
            std::stringstream ss;
            ss << "[" << s.source() << ", " << s.target() << "]";
            return ss.str();
        });

    m.def("decompose", &decompose, R"pbdoc(
        TODO add description
    )pbdoc");

    m.def("generate_sweeps", &generate_sweeps, R"pbdoc(
        TODO add description
    )pbdoc");

    #ifdef VERSION_INFO
        m.attr("__version__") = MACRO_STRINGIFY(VERSION_INFO);
    #else
        m.attr("__version__") = "dev";
    #endif
}