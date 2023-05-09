#include "CoveragePlanner.h"
#include "CGALDefinitions.h"
#include "decomposition.h"
#include "sweep.h"
#include "math.h"
CoveragePlanner::CoveragePlanner()
{
}

PolygonWithHoles CoveragePlanner::getPolygonWithHoles()
{
  polygonWithHoles = PolygonWithHoles(searchArea);

  for (auto hole : restrictedAreas) {
    polygonWithHoles.add_hole(hole);
  }
  
  return polygonWithHoles;
}

void CoveragePlanner::setRestrictedAreas(std::vector<Polygon_2> polys)
{
  restrictedAreas = polys;
}
void CoveragePlanner::setSearchArea(Polygon_2 poly)
{
  searchArea = poly;
}

void CoveragePlanner::setSweepOffset(double offset)
{
  sweepOffset = offset;
}

double CoveragePlanner::getSweepOffset()
{
  return sweepOffset;
}

std::vector<Polygon_2> CoveragePlanner::getDecomposedPolygons()
{
  // ROS_DEBUG("Decomposition");
  std::vector<Polygon_2> decomposedPolygons;
  // BCD Decomposition
  std::vector<Line_2> cell_dirs;
  double msa;
  if (!polygon_coverage_planning::computeBestBCDFromPolygonWithHoles(
      getPolygonWithHoles(), decomposedPolygons, cell_dirs,
      msa))
  {
    // RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "Could not compute BCD!");
  }
  return decomposedPolygons;
}

std::vector<std::vector<Segment_2>> CoveragePlanner::getSweepSegments()
{
  // Traverse through all polygons
  std::vector<std::vector<Segment_2>> sweeps;
  // TODO Reuse the directions from the polygon decomposition for performance optimisation
  for (auto poly : getDecomposedPolygons()) {
    Direction_2 bestDir;
    polygon_coverage_planning::findBestSweepDir(poly, &bestDir);
    // Construct the sweep plan
    const double maxSweepOffset = getSweepOffset();
    std::vector<Segment_2> sweep;
    if (!polygon_coverage_planning::computeSweep(
        poly, maxSweepOffset, bestDir, false,
        sweep))
    {
      // RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "Could not compute sweep!");
    } else {
      sweeps.push_back(sweep);
    }
  }
  return sweeps;
}

CoveragePlanner::~CoveragePlanner()
{
}

