cmake_minimum_required(VERSION 3.0)
project(my_project)

# Find CGAL library
find_package(CGAL REQUIRED)

# Include CGAL headers
include_directories(${CGAL_INCLUDE_DIRS} )

# Add executable and link with CGAL library
add_executable(my_exe main.cpp)
target_link_libraries(my_exe ${CGAL_LIBRARIES})

# Include all sources in src directory
file(GLOB SOURCES "src/*.cpp")
target_sources(my_exe PRIVATE ${SOURCES})
