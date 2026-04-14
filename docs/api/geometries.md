# trajgenpy.Geometries

CRS-aware geometry wrappers and coverage-planning algorithms.

Backward compatibility note: public planning function interfaces remain stable.
Geometry validity checks and repairs are handled internally by
`decompose_polygon` and `generate_sweep_pattern` (configurable through optional
`validation_strategy`), so existing call sites keep working without required
parameter changes.

---

## Geometry classes

::: trajgenpy.Geometries.GeoData

---

::: trajgenpy.Geometries.GeoPoint

---

::: trajgenpy.Geometries.GeoPolygon

---

::: trajgenpy.Geometries.GeoMultiPolygon

---

::: trajgenpy.Geometries.GeoTrajectory

---

::: trajgenpy.Geometries.GeoMultiTrajectory

---

## Planning functions

::: trajgenpy.Geometries.get_sweep_offset

---

::: trajgenpy.Geometries.decompose_polygon

---

::: trajgenpy.Geometries.generate_sweep_pattern

---

## Low-level helpers

::: trajgenpy.Geometries.is_convex

---

::: trajgenpy.Geometries.shapely_polygon_to_cgal

---

::: trajgenpy.Geometries.multi_polygon_to_polygon_with_holes
