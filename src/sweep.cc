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

#include "sweep.h"

namespace polygon_coverage_planning
{

    bool computeSweep(
        const Polygon_2 &in,
        const FT offset, const Direction_2 &dir,
        bool counter_clockwise,
        std::vector<Segment_2> &sweep_segments)
    {
        std::vector<Point_2> waypoints;
        waypoints.clear();
        const FT kSqOffset = offset * offset;

        // Assertions.
        // TODO(rikba): Check monotone perpendicular to dir.
        if (!in.is_counterclockwise_oriented())
        {
            return false;
        }

        // Find start sweep.
        Line_2 sweep(Point_2(0.0, 0.0), dir);
        std::vector<Point_2> sorted_pts = sortVerticesToLine(in, sweep);
        sweep = Line_2(sorted_pts.front(), dir);

        Vector_2 offset_vector = sweep.perpendicular(sorted_pts.front()).to_vector();
        offset_vector = offset * offset_vector /
                        std::sqrt(CGAL::to_double(offset_vector.squared_length()));
        const CGAL::Aff_transformation_2<K> kOffset(CGAL::TRANSLATION, offset_vector);

        Segment_2 sweep_segment;
        bool has_sweep_segment = findSweepSegment(in, sweep, &sweep_segment);
        while (has_sweep_segment)
        {
            // Align sweep segment.
            if (counter_clockwise)
            {
                sweep_segment = sweep_segment.opposite();
            }
            //
            // Traverse sweep.
            waypoints.push_back(sweep_segment.source());
            if (!sweep_segment.is_degenerate())
            {
                waypoints.push_back(sweep_segment.target());
            }
            sweep_segments.push_back(sweep_segment);

            // Offset sweep.
            sweep = sweep.transform(kOffset);
            // Find new sweep segment.
            Segment_2 prev_sweep_segment =
                counter_clockwise ? sweep_segment.opposite() : sweep_segment;
            has_sweep_segment = findSweepSegment(in, sweep, &sweep_segment);
            // Add a final ssweep.
            if (!has_sweep_segment &&
                !((!waypoints.empty() &&
                   *std::prev(waypoints.end(), 1) == sorted_pts.back()) ||
                  (waypoints.size() > 1 &&
                   *std::prev(waypoints.end(), 2) == sorted_pts.back())))
            {
                sweep = Line_2(sorted_pts.back(), dir);
                has_sweep_segment = findSweepSegment(in, sweep, &sweep_segment);
                if (!has_sweep_segment)
                {
                    std::cerr << "Failed to calculate final sweep.\n";
                    return false;
                }
                // Do not add a sweep if it is half the offset, because then it has already been covered
                if (CGAL::squared_distance(sweep_segment, prev_sweep_segment) < offset / 2)
                {
                    break;
                }
            }
            // Check observability of vertices between sweeps.
            if (has_sweep_segment)
            {
                std::vector<Point_2>::const_iterator unobservable_point =
                    sorted_pts.end();
                checkObservability(
                    prev_sweep_segment, sweep_segment, sorted_pts,
                    kSqOffset, &unobservable_point);
                if (unobservable_point != sorted_pts.end())
                {
                    sweep = Line_2(*unobservable_point, dir);
                    has_sweep_segment = findSweepSegment(in, sweep, &sweep_segment);
                    if (!has_sweep_segment)
                    {
                        std::cerr << "Failed to calculate extra sweep at point: " << *unobservable_point << std::endl;
                        return false;
                    }
                }
            }

            // Swap directions.
            counter_clockwise = !counter_clockwise;
        }

        return true;
    }

    bool findSweepSegment(
        const Polygon_2 &p, const Line_2 &l,
        Segment_2 *sweep_segment)
    {
        std::vector<Point_2> intersections = findIntersections(p, l);
        if (intersections.empty())
        {
            return false;
        }
        *sweep_segment = Segment_2(intersections.front(), intersections.back());
        return true;
    }

    void checkObservability(
        const Segment_2 &prev_sweep, const Segment_2 &sweep,
        const std::vector<Point_2> &sorted_pts, const FT max_sq_distance,
        std::vector<Point_2>::const_iterator *lowest_unobservable_point)
    {

        *lowest_unobservable_point = sorted_pts.end();

        // Find first point that is between prev_sweep and sweep and unobservable.
        for (std::vector<Point_2>::const_iterator it = sorted_pts.begin();
             it != sorted_pts.end(); ++it)
        {
            if (prev_sweep.supporting_line().has_on_positive_side(*it))
            {
                continue;
            }
            if (sweep.supporting_line().has_on_negative_side(*it))
            {
                break;
            }
            FT sq_distance_prev = CGAL::squared_distance(prev_sweep, *it);
            FT sq_distance_curr = CGAL::squared_distance(sweep, *it);
            if (sq_distance_prev > max_sq_distance &&
                sq_distance_curr > max_sq_distance)
            {
                *lowest_unobservable_point = it;
                return;
            }
        }
    }

    std::vector<Point_2> sortVerticesToLine(const Polygon_2 &p, const Line_2 &l)
    {
        // Copy points.
        std::vector<Point_2> pts(p.size());
        std::vector<Point_2>::iterator pts_it = pts.begin();
        for (VertexConstIterator it = p.vertices_begin(); it != p.vertices_end();
             ++it)
        {
            *(pts_it++) = *it;
        }

        // Sort.
        std::sort(
            pts.begin(), pts.end(),
            [&l](const Point_2 &a, const Point_2 &b) -> bool
            {
                return CGAL::has_smaller_signed_distance_to_line(l, a, b);
            });

        return pts;
    }

    std::vector<Point_2> findIntersections(const Polygon_2 &p, const Line_2 &l)
    {
        std::vector<Point_2> intersections;
        typedef CGAL::cpp11::result_of<Intersect_2(Segment_2, Line_2)>::type
            Intersection;

        for (EdgeConstIterator it = p.edges_begin(); it != p.edges_end(); ++it)
        {
            Intersection result = CGAL::intersection(*it, l);
            if (result)
            {
                if (const Segment_2 *s = boost::get<Segment_2>(&*result))
                {
                    intersections.push_back(s->source());
                    intersections.push_back(s->target());
                }
                else
                {
                    intersections.push_back(*boost::get<Point_2>(&*result));
                }
            }
        }

        // Sort.
        Line_2 perp_l = l.perpendicular(l.point(0));
        std::sort(
            intersections.begin(), intersections.end(),
            [&perp_l](const Point_2 &a, const Point_2 &b) -> bool
            {
                return CGAL::has_smaller_signed_distance_to_line(perp_l, a, b);
            });

        return intersections;
    }

} // namespace polygon_coverage_planning
