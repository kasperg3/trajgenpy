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

#include "bcd.h"
#include "decomposition.h"
#include "weakly_monotone.h"
#include "compute_altitude.h"


namespace polygon_coverage_planning
{

std::vector<Direction_2> findEdgeDirections(const PolygonWithHoles & pwh)
{
  // Get all possible polygon directions.
  std::vector<Direction_2> directions;
  for (size_t i = 0; i < pwh.outer_boundary().size(); ++i) {
    directions.push_back(pwh.outer_boundary().edge(i).direction());
  }
  for (PolygonWithHoles::Hole_const_iterator hit = pwh.holes_begin();
    hit != pwh.holes_end(); ++hit)
  {
    for (size_t i = 0; i < hit->size(); i++) {
      directions.push_back(hit->edge(i).direction());
    }
  }

  // Remove redundant directions.
  std::set<size_t> to_remove;
  for (size_t i = 0; i < directions.size() - 1; ++i) {
    for (size_t j = i + 1; j < directions.size(); ++j) {
      if (CGAL::orientation(directions[i].vector(), directions[j].vector()) ==
        CGAL::COLLINEAR)
      {
        to_remove.insert(j);
      }
    }
  }
  for (std::set<size_t>::reverse_iterator rit = to_remove.rbegin();
    rit != to_remove.rend(); ++rit)
  {
    directions.erase(std::next(directions.begin(), *rit));
  }

  // Add opposite directions.
  std::vector<Direction_2> temp_directions = directions;
  for (size_t i = 0; i < temp_directions.size(); ++i) {
    directions.push_back(-temp_directions[i]);
  }

  return directions;
}

std::vector<Direction_2> findPerpEdgeDirections(const PolygonWithHoles & pwh)
{
  std::vector<Direction_2> directions = findEdgeDirections(pwh);
  for (auto & d : directions) {
    d = Direction_2(-d.dy(), d.dx());
  }

  return directions;
}

std::vector<Direction_2> getAllSweepDirections(const Polygon_2 & in)
{
  // Get all directions.
  std::vector<Direction_2> dirs;
  for (EdgeConstIterator it = in.edges_begin(); it != in.edges_end(); ++it) {
    // Check if this edge direction is already in the set.
    std::vector<Direction_2>::iterator last =
      std::find_if(
      dirs.begin(), dirs.end(), [&it](const Direction_2 & dir) {
        return CGAL::orientation(dir.vector(), it->to_vector()) ==
        CGAL::COLLINEAR;
      });
    if (last != dirs.end()) {continue;}
    dirs.push_back(it->direction());
    // Check if the polygon is monotone perpendicular to this edge direction.
  }

  return dirs;
}

double findBestSweepDir(const Polygon_2 & cell, Direction_2 * best_dir)
{
  // Get all sweepable edges.
  PolygonWithHoles pwh(cell);
  std::vector<Direction_2> edge_dirs = getAllSweepDirections(cell);

  // Find minimum altitude.
  /* double min_altitude = std::numeric_limits<double>::max(); */
  FT min_altitude = std::numeric_limits<double>::max();
  for (const auto & dir : edge_dirs) {
    auto s = findSouth(cell, Line_2(Point_2(CGAL::ORIGIN), dir));
    auto n = findNorth(cell, Line_2(Point_2(CGAL::ORIGIN), dir));
    auto orthogonal_vec =
      dir.vector().perpendicular(CGAL::Orientation::POSITIVE);
    Line_2 line_through_n(*n, orthogonal_vec.direction());
    auto s_proj = line_through_n.projection(*s);
    FT altitude = CGAL::squared_distance(*n, s_proj);
    /* double altitude = std::sqrt(CGAL::to_double(CGAL::squared_distance(*n, s_proj))); */
    if (altitude < min_altitude) {
      min_altitude = altitude;
      if (best_dir) {*best_dir = dir;}
    }
  }

  return std::sqrt(CGAL::to_double(min_altitude));
}

bool computeBestBCDFromPolygonWithHoles(
  const PolygonWithHoles & pwh,
  std::vector<Polygon_2> & bcd_polygons,
  std::vector<Line_2> & cell_dirs,
  double & msa)
{
  double min_altitude_sum = std::numeric_limits<double>::max();

  // Get all possible decomposition directions.
  std::vector<Direction_2> directions = findPerpEdgeDirections(pwh);
  std::vector<Line_2> optimal_dirs;
  std::vector<Polygon_2> optimal_bcd;

  Direction_2 best_bcd_dir;
  // For all possible rotations:
  for (const auto & dir : directions) {
    // Calculate decomposition.
    std::vector<Polygon_2> cells = computeBCD(pwh, dir);
    std::vector<Line_2> dirs;

    // Calculate minimum altitude sum for each cell.
    double min_altitude_sum_tmp = 0.0;
    for (const auto & cell : cells) {
      if (cell.size() == 0) {
        continue;
      }
      Direction_2 cell_dir;
      Vector_2 cell_vec;
      double altitudeac;
      ComputeBestAltitude(cell, cell_vec, altitudeac);
      dirs.push_back(Line_2(cell[0], cell_vec));
      min_altitude_sum_tmp += altitudeac;

    }

    // Update best decomposition.
    if (min_altitude_sum_tmp < min_altitude_sum) {
      /* std::cout << "MSA dir: " << dir << std::endl; */
      min_altitude_sum = min_altitude_sum_tmp;
      optimal_bcd = cells;
      optimal_dirs = dirs;
      best_bcd_dir = dir;
    }
  }

  msa = min_altitude_sum;
  bcd_polygons.clear();
  cell_dirs.clear();
  for (const auto & cell: optimal_bcd) {
    bcd_polygons.push_back(cell);
  }
  for (const auto & dir: optimal_dirs) {
    cell_dirs.push_back(dir);
  }

  if (bcd_polygons.empty()) {
    return false;
  } else {
    return true;
  }
}

FT computeMSASquared(const Polygon_2 & cell, const Direction_2 & dir)
{
  // Find minimum altitude.
  auto s = findSouth(cell, Line_2(Point_2(CGAL::ORIGIN), dir));
  auto n = findNorth(cell, Line_2(Point_2(CGAL::ORIGIN), dir));
  auto orthogonal_vec = dir.vector().perpendicular(CGAL::Orientation::POSITIVE);
  Line_2 line_through_n(*n, orthogonal_vec.direction());
  /* Line_2 line_through_n(*n, dir); */
  auto s_proj = line_through_n.projection(*s);
  /* double altitude = std::sqrt(CGAL::to_double(CGAL::squared_distance(*n, s_proj))); */
  return CGAL::squared_distance(*n, s_proj);
}

double computeMSA(const Polygon_2 & cell, const Direction_2 & dir)
{
  // Find minimum altitude.
  auto s = findSouth(cell, Line_2(Point_2(CGAL::ORIGIN), dir));
  auto n = findNorth(cell, Line_2(Point_2(CGAL::ORIGIN), dir));
  auto orthogonal_vec = dir.vector().perpendicular(CGAL::Orientation::POSITIVE);
  Line_2 line_through_n(*n, orthogonal_vec.direction());
  /* Line_2 line_through_n(*n, dir); */
  auto s_proj = line_through_n.projection(*s);
  double altitude =
    std::sqrt(CGAL::to_double(CGAL::squared_distance(*n, s_proj)));
  return altitude;
}

bool computeBCDFromPolygonWithHoles(
  const PolygonWithHoles & pwh,
  std::vector<Polygon_2> * bcd_polygons, double & msa,
  Line_2 & longitudinal_dir)
{
  bcd_polygons->clear();
  FT min_altitude_sum = std::numeric_limits<double>::max();

  std::vector<Direction_2> directions = findEdgeDirections(pwh);
  std::vector<Direction_2> perp_directions = directions;
  for (auto & d : perp_directions) {
    d = Direction_2(-d.dy(), d.dx());
  }

  // For all possible rotations:
  Direction_2 optimal_dir;
  bool flag = false;
  for (size_t i = 0; i < directions.size(); ++i) {
    auto min_altitude_sum_tmp = computeMSASquared(pwh.outer_boundary(), directions[i]);

    if (min_altitude_sum_tmp < min_altitude_sum) {
      Line_2 l(Point_2(CGAL::ORIGIN), directions[i]);
      if (isWeaklyMonotone(pwh.outer_boundary(), l)) {
        flag = true;
        min_altitude_sum = min_altitude_sum_tmp;
        /* *bcd_polygons = cells; */
        optimal_dir = directions[i];
      }
    }
  }
  msa = std::sqrt(CGAL::to_double(min_altitude_sum));
  longitudinal_dir = Line_2(pwh.outer_boundary()[0], optimal_dir);

  if (flag == false) {
    return 1;
  }
  return 0;
}

}  // namespace polygon_coverage_planning
