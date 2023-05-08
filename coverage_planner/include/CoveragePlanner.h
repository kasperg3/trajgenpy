#ifndef COVERAGE_PLANNER_H_H
#define COVERAGE_PLANNER_H_H

#include "CGALDefinitions.h"

#pragma once
class CoveragePlanner
{
public:
  CoveragePlanner();
  ~CoveragePlanner();
  void setSearchArea(Polygon_2 poly);
  void setRestrictedAreas(std::vector<Polygon_2> polys);
  void setSweepOffset(double);
  double getSweepOffset();
  PolygonWithHoles getPolygonWithHoles();
  std::vector<Polygon_2> getDecomposedPolygons();
  std::vector<std::vector<Segment_2>> getSweepSegments();

private:
  Polygon_2 searchArea;
  std::vector<Polygon_2> restrictedAreas;
  double sweepOffset = 2.0;
  PolygonWithHoles polygonWithHoles = PolygonWithHoles();
};
#endif
