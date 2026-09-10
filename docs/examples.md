# Examples

The `examples/` directory in the repository contains runnable scripts that
demonstrate the most common TrajGenPy workflows.

---

## Basic sweep over a synthetic polygon

**File:** `examples/coverage_and_plotting.py`

Demonstrates sweep pattern generation over a simple polygon defined in a
metric coordinate system.

```python
import shapely
import matplotlib.pyplot as plt
from trajgenpy.Geometries import (
    GeoPolygon,
    GeoMultiTrajectory,
    decompose_polygon,
    generate_sweep_pattern,
    get_sweep_offset,
)

boundary = shapely.Polygon(
    [(0, 0), (500, 0), (500, 300), (250, 400), (0, 300)]
)
area = GeoPolygon(boundary, crs="EPSG:32632")

cells = decompose_polygon(area.geometry)
offset = get_sweep_offset(overlap=0.1, height=20, field_of_view=90)

all_sweeps = []
for cell in cells:
    all_sweeps.extend(generate_sweep_pattern(cell, offset))

fig, ax = plt.subplots(figsize=(8, 6))
area.plot(ax=ax, facecolor="lightgreen", edgecolor="darkgreen", alpha=0.4)
GeoMultiTrajectory(all_sweeps, crs="EPSG:32632").plot(ax=ax, color="crimson")
plt.axis("equal")
plt.title(f"Coverage plan — {len(all_sweeps)} sweep lines")
plt.show()
```

---

## Coverage with obstacles

**File:** `examples/coverage_and_plotting.py`

Demonstrates how to pass keep-out zones (obstacles) to the decomposition.
The planner merges obstacles that intersect the boundary automatically.

```python
import shapely
import matplotlib.pyplot as plt
from trajgenpy.Geometries import (
    GeoPolygon,
    GeoMultiPolygon,
    GeoMultiTrajectory,
    decompose_polygon,
    generate_sweep_pattern,
    get_sweep_offset,
)

boundary = shapely.box(0, 0, 400, 300)
obstacles = shapely.MultiPolygon([
    shapely.box(80, 80, 160, 160),
    shapely.box(240, 100, 320, 200),
])

cells = decompose_polygon(boundary, obstacles=obstacles)
offset = get_sweep_offset(overlap=0.0, height=15, field_of_view=90)

all_sweeps = []
for cell in cells:
    all_sweeps.extend(generate_sweep_pattern(cell, offset))

fig, ax = plt.subplots(figsize=(8, 6))
GeoPolygon(boundary, crs="EPSG:32632").plot(
    ax=ax, facecolor="lightblue", edgecolor="navy", alpha=0.3
)
GeoMultiPolygon(list(obstacles.geoms), crs="EPSG:32632").plot(
    ax=ax, facecolor="salmon", edgecolor="red", alpha=0.6
)
GeoMultiTrajectory(all_sweeps, crs="EPSG:32632").plot(ax=ax, color="blue")
plt.axis("equal")
plt.title(f"{len(cells)} cells — {len(all_sweeps)} sweep lines")
plt.show()
```

---

## OSM feature extraction and coverage

**File:** `examples/coverage_on_queried_data.py`

Queries real land-use features from OpenStreetMap and generates a coverage
plan over the result.

```python
import shapely
import matplotlib.pyplot as plt
from trajgenpy.Geometries import GeoPolygon, GeoMultiTrajectory, decompose_polygon, generate_sweep_pattern, get_sweep_offset
from trajgenpy.Query import query_features
from trajgenpy.Utils import plot_basemap

# Define query area in WGS84
area = GeoPolygon(shapely.box(10.38, 55.38, 10.42, 55.42))

# Fetch features from OSM
tags = {"natural": True, "landuse": True}
features = query_features(area, tags)

# Reproject to UTM for planning
area.set_crs("EPSG:32632")
cells = decompose_polygon(area.geometry)
offset = get_sweep_offset(overlap=0.1, height=30, field_of_view=90)

all_sweeps = []
for cell in cells:
    all_sweeps.extend(generate_sweep_pattern(cell, offset))

# Plot with satellite basemap
fig, ax = plt.subplots(figsize=(10, 8))
area.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2)
GeoMultiTrajectory(all_sweeps, crs="EPSG:32632").plot(ax=ax, color="yellow")
plot_basemap(ax=ax, crs="EPSG:32632")
plt.show()
```

---

## Interactive Jupyter notebook

An interactive version of the examples above is available in the repository
as `examples/examples.ipynb`.  Open it with:

```bash
pip install jupyter
jupyter notebook examples/examples.ipynb
```
