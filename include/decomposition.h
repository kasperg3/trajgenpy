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

#ifndef POLYGON_COVERAGE_GEOMETRY_DECOMPOSITION_H_
#define POLYGON_COVERAGE_GEOMETRY_DECOMPOSITION_H_

#include "cgal_definitions.h"

namespace polygon_coverage_planning
{

// Get all unique polygon edge directions including opposite directions.
std::vector<Direction_2> findEdgeDirections(const PolygonWithHoles & pwh);

std::vector<Direction_2> getAllSweepDirections(const Polygon_2 & in);
// Get all directions that are perpendicular to the edges found with
// findEdgeDirections.
std::vector<Direction_2> findPerpEdgeDirections(const PolygonWithHoles & pwh);

// Find the best edge direction to sweep. The best direction is the direction
// with the smallest polygon altitude. Returns the smallest altitude.
double findBestSweepDir(const Polygon_2 & cell, Direction_2 * best_dir = nullptr);

FT computeMSASquared(const Polygon_2 & cell, const Direction_2 & dir);
// Compute BCDs for every edge direction. Return any with the smallest possible
// altitude sum.
bool computeBestBCDFromPolygonWithHoles(
  const PolygonWithHoles & pwh,
  std::vector<Polygon_2> & bcd_polygons,
  std::vector<Line_2> &, double & msa);
inline bool computeBestBCDFromPolygonWithHoles(const PolygonWithHoles & pwh, double & msa)
{
  std::vector<Polygon_2> decomposition;
  std::vector<Line_2> dirs;
  return computeBestBCDFromPolygonWithHoles(pwh, decomposition, dirs, msa);
}

bool computeBCDFromPolygonWithHoles(
  const PolygonWithHoles & pwh,
  std::vector<Polygon_2> * bcd_polygons, double & msa,
  Line_2 & longitudinal_dir);
bool computeBCDFromPolygonWithHoles1(
  const PolygonWithHoles & pwh,
  std::vector<Polygon_2> * bcd_polygons, double & msa,
  Line_2 & longitudinal_dir);

double computeMSA(const Polygon_2 & cell, const Direction_2 & dir);

// Compute TCDs for every edge direction. Return any with the smallest possible
// altitude sum.

enum DecompositionType
{
  kBCD = 0,  // Boustrophedon.
  kTCD       // Trapezoidal.
};

inline bool checkDecompositionTypeValid(const int type)
{
  return (type == DecompositionType::kBCD) || (type == DecompositionType::kTCD);
}

inline std::string getDecompositionTypeName(const DecompositionType & type)
{
  switch (type) {
    case DecompositionType::kBCD:
      return "Boustrophedon Cell Decomposition";
    case DecompositionType::kTCD:
      return "Trapezoidal Cell Decomposition";
    default:
      return "Unknown!";
  }
}

}  // namespace polygon_coverage_planning

#endif  // POLYGON_COVERAGE_GEOMETRY_DECOMPOSITION_H_
