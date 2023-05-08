/**
 * This file is part of the AreaCoverage-library.
 * The file contains functions for computing altitude of a polygon (with or without holes). It uses the MSA formulation.
 *
 * TODO:
 *
 * @author Saurav Agarwal
 * @contact sagarw10@uncc.edu
 * @contact agr.saurav1@gmail.com
 * Repository: https://github.com/UNCCharlotte-Robotics/AreaCoverage-library
 *
 * Copyright (C) 2020--2022 University of North Carolina at Charlotte.
 * The AreaCoverage-library is owned by the University of North Carolina at Charlotte and is protected by United States copyright laws and applicable international treaties and/or conventions.
 *
 * The AreaCoverage-library is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
 *
 * DISCLAIMER OF WARRANTIES: THE SOFTWARE IS PROVIDED "AS-IS" WITHOUT WARRANTY OF ANY KIND INCLUDING ANY WARRANTIES OF PERFORMANCE OR MERCHANTABILITY OR FITNESS FOR A PARTICULAR USE OR PURPOSE OR OF NON-INFRINGEMENT. YOU BEAR ALL RISK RELATING TO QUALITY AND PERFORMANCE OF THE SOFTWARE OR HARDWARE.
 *
 * SUPPORT AND MAINTENANCE: No support, installation, or training is provided.
 *
 * You should have received a copy of the GNU General Public License along with AreaCoverage-library. If not, see <https://www.gnu.org/licenses/>.
 */

#ifndef ACLIBRARY_COMPUTE_ALTITUDE_H_
#define ACLIBRARY_COMPUTE_ALTITUDE_H_

namespace polygon_coverage_planning
{


const double kEps = 1e-12;
const double kDoubleMax = std::numeric_limits<double>::max();
const double kDoubleMin = std::numeric_limits<double>::min();
const size_t kNIL = std::numeric_limits<std::size_t>::max();
const bool kIsRequired = true;
const bool kIsNotRequired = false;
const bool kSuccess = false;
const bool kFail = true;
const Point_2 kOrigin(0, 0);
typedef std::vector<std::array<double, 2>> PtVec;
struct PointType
{
  double x;
  int point_type;
};

inline int GetPointType(double x, double xprev, double xnext)
{
  /* std::cout << "Point_type: " << " " << x << " " << xprev << " " << xnext << std::endl; */
  if (x == xprev and x == xnext) {
    return 0;
  }
  if (x <= xprev and x <= xnext) {
    return 1;
  }
  if (x >= xprev and x >= xnext) {
    return -1;
  }
  return 0;
}

inline void GetServiceDirections(const Polygon_2 & poly, std::vector<Vector_2> & service_dirs)
{
  for (EdgeConstIterator it = poly.edges_begin(); it != poly.edges_end(); ++it) {
    std::vector<Vector_2>::iterator last =
      std::find_if(
      service_dirs.begin(), service_dirs.end(), [&it](const Vector_2 & dir) {
        return CGAL::orientation(dir, it->to_vector()) ==
        CGAL::COLLINEAR;
      });
    if (last != service_dirs.end()) {continue;}
    service_dirs.push_back(it->to_vector());
  }
}

inline void GetAllPoints(const Polygon_2 & poly, std::vector<std::array<double, 2>> & points_vec)
{
  for (const auto & pt: poly) {
    points_vec.push_back(std::array<double, 2> {CGAL::to_double(pt.x()), CGAL::to_double(pt.y())});
  }
}


inline PtVec RotatePolygon(const Polygon_2 & poly, const double & ang)
{
  double cos_ang = cos(ang); double sin_ang = sin(ang);
  PtVec rot_poly;
  for (auto & pt:poly) {
    std::array<double, 2> rot_pt;
    double x, y;
    double ptx = CGAL::to_double(pt[0]);
    double pty = CGAL::to_double(pt[1]);
    x = cos_ang * ptx + sin_ang * pty;
    y = -sin_ang * ptx + cos_ang * pty;
    rot_pt[0] = x; rot_pt[1] = y;
    rot_poly.push_back(rot_pt);
  }
  return rot_poly;
}

inline void GetCellPointTypes(const PtVec & poly, std::vector<PointType> & points_vec)
{
  PointType newPT;
  newPT.x = poly[0][0];
  newPT.point_type = GetPointType(newPT.x, poly[poly.size() - 1][0], poly[1][0]);
  points_vec.push_back(newPT);
  for (size_t i = 1; i < poly.size() - 1; ++i) {
    newPT.x = poly[i][0];
    newPT.point_type = GetPointType(newPT.x, poly[i - 1][0], poly[i + 1][0]);
    points_vec.push_back(newPT);
  }
  newPT.x = poly[poly.size() - 1][0];
  newPT.point_type = GetPointType(newPT.x, poly[poly.size() - 2][0], poly[0][0]);
  points_vec.push_back(newPT);
}

inline void GetCellPointTypes(
  const PolygonWithHoles & pwh, const Vector_2 & dir,
  std::vector<PointType> & points_vec)
{

  double ang = (atan2(CGAL::to_double(dir.y()), CGAL::to_double(dir.x())) - M_PI / 2. + 1e-10);
  auto rot_outer = RotatePolygon(pwh.outer_boundary(), ang);
  std::list<PtVec> rot_holes;
  for (auto it = pwh.holes_begin(); it != pwh.holes_end(); ++it) {
    rot_holes.push_back(RotatePolygon(*it, ang));
  }
  GetCellPointTypes(rot_outer, points_vec);
  for (const auto & hole:rot_holes) {
    GetCellPointTypes(hole, points_vec);
  }
  struct
  {
    bool operator()(PointType a, PointType b) const {return a.x < b.x;}
  } ComparePointTypes;

  std::sort(points_vec.begin(), points_vec.end(), ComparePointTypes);
  double min_x = kDoubleMax;
  for (const auto & pt:points_vec) {
    if (pt.x < min_x) {
      min_x = pt.x;
    }
  }
  for (auto & pt:points_vec) {
    pt.x -= min_x;
  }
}

inline double ComputeAltitude(const std::vector<PointType> & points_vec)
{
  bool start_flag = false;
  double alt = 0;
  int counter = 0;
  PointType pt_prev = points_vec.front();
  for (const auto & pt:points_vec) {
    if (pt.point_type == 0) {
      continue;
    }
    if (start_flag == true) {
      alt = alt + counter * std::abs(pt.x - pt_prev.x);
    } else {start_flag = true;}
    /* std::cout << pt.x << " " << alt << " " << counter << " " << pt.point_type << std::endl; */
    counter += pt.point_type;
    pt_prev = pt;
  }
  return alt;

}

inline void ComputeBestAltitude(
  const PolygonWithHoles & pwh, Vector_2 & best_dir,
  double & best_altitude)
{
  std::vector<Vector_2> service_dirs;
  std::vector<std::array<double, 2>> cell_points;
  GetServiceDirections(pwh.outer_boundary(), service_dirs);
  /* GetAllPoints(pwh.outer_boundary(), cell_points); */
  for (auto it = pwh.holes_begin(); it != pwh.holes_end(); ++it) {
    GetServiceDirections(*it, service_dirs);
    /* GetAllPoints(*it, cell_points); */
  }
  /* std::cout << "ComputeBestAltitude\n"; */
  /* std::cout << pwh << std::endl; */
  best_altitude = kDoubleMax;
  for (const auto & dir:service_dirs) {
    std::vector<PointType> points_vec;
    GetCellPointTypes(pwh, dir, points_vec);
    /* std::cout << "dir: " << dir << std::endl; */
    double alt = ComputeAltitude(points_vec);
    /* std::cout << "alt: " << alt << std::endl; */
    if (alt < best_altitude) {
      best_altitude = alt;
      best_dir = dir;
    }
  }
}

/* inline void ComputeAltitude(const Polygon_with_holes_2 &pwh, const Vector_2 &dir, double &alt) { */
/*      std::vector <std::array<double, 2>> cell_points; */
/*      GetAllPoints(pwh.outer_boundary(), cell_points); */
/*      for(auto it = pwh.holes_begin(); it != pwh.holes_end(); ++it) { */
/*              GetAllPoints(*it, cell_points); */
/*      } */
/*      alt = ComputeAltitude(dir, cell_points); */
/* } */

inline void ComputeBestAltitude(const Polygon_2 & poly, Vector_2 & best_dir, double & width)
{
  ComputeBestAltitude(PolygonWithHoles(poly), best_dir, width);

}
}

#endif
