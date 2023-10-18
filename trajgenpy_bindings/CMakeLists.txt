# python_add_library(core MODULE src/Bindings.cpp WITH_SOABI)
pybind11_add_module(trajgenpy_bindings ${CMAKE_CURRENT_SOURCE_DIR}/Bindings.cpp)

target_link_libraries(trajgenpy_bindings PRIVATE pybind11::headers ${CGAL_LIBRARIES} pybind11::module)

# Include CGAL headers
include_directories(${CGAL_INCLUDE_DIRS})
target_include_directories(trajgenpy_bindings PRIVATE "include/")

# Include all sources in src directory
file(GLOB SOURCES  ${CMAKE_CURRENT_SOURCE_DIR}/*.cc ${CMAKE_CURRENT_SOURCE_DIR}/*.cpp)
target_sources(trajgenpy_bindings PRIVATE ${SOURCES})

install(TARGETS trajgenpy_bindings LIBRARY DESTINATION trajgenpy)