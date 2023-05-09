
cmake_minimum_required(VERSION 3.15...3.26)
project(${SKBUILD_PROJECT_NAME} VERSION ${SKBUILD_PROJECT_VERSION})

# Find CGAL library
find_package(CGAL REQUIRED)

# pybind11
find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

python_add_library(core MODULE main.cpp WITH_SOABI)
target_link_libraries(core PRIVATE pybind11::headers ${CGAL_LIBRARIES} pybind11::module)
target_compile_definitions(core PRIVATE VERSION_INFO=${PROJECT_VERSION})

# Include CGAL headers
include_directories(${CGAL_INCLUDE_DIRS} )
target_include_directories(core PRIVATE "include/")

# Include all sources in src directory
file(GLOB SOURCES  "src/*.cc" "src/*.cpp")
target_sources(core PRIVATE ${SOURCES})

install(TARGETS core DESTINATION coverage_planner)