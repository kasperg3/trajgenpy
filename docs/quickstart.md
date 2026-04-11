# Quick Start

This guide walks through the most common TrajGenPy workflows, from a simple
synthetic polygon to a real-world OSM-based coverage plan.

---

## 1. Sweep a simple polygon

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

# --- Define area ---
polygon = shapely.Polygon([(0, 0), (200, 0), (200, 150), (100, 200), (0, 150)])
area = GeoPolygon(polygon, crs="EPSG:32632")  # UTM zone 32N (metres)

# --- Decompose into convex cells ---
cells = decompose_polygon(area.geometry)
print(f"Decomposed into {len(cells)} cell(s)")

# --- Compute sweep offset (10 m height, 90° FoV, 10% overlap) ---
offset = get_sweep_offset(overlap=0.1, height=10, field_of_view=90)

# --- Generate and plot sweep patterns ---
fig, ax = plt.subplots()
area.plot(ax=ax, facecolor="lightblue", edgecolor="navy")

all_sweeps = []
for cell in cells:
    sweeps = generate_sweep_pattern(cell, offset)
    all_sweeps.extend(sweeps)

GeoMultiTrajectory(all_sweeps, crs="EPSG:32632").plot(ax=ax, color="red")
plt.axis("equal")
plt.show()
```

---

## 2. Add obstacles (keep-out zones)

```python
import shapely
from trajgenpy.Geometries import decompose_polygon, generate_sweep_pattern, get_sweep_offset

boundary = shapely.box(0, 0, 300, 300)
obstacle = shapely.box(100, 100, 200, 200)  # square hole in the middle

cells = decompose_polygon(boundary, obstacles=obstacle)
offset = get_sweep_offset(overlap=0.0, height=15, field_of_view=60)

sweeps = []
for cell in cells:
    sweeps.extend(generate_sweep_pattern(cell, offset))

print(f"{len(sweeps)} sweep segments over {len(cells)} cells")
```

---

## 3. Work with real-world coordinates

TrajGenPy geometry wrappers are CRS-aware.  Always reproject from WGS84 to a
metric CRS before planning so that distances are in metres.

```python
import shapely
from trajgenpy.Geometries import GeoPolygon, decompose_polygon, generate_sweep_pattern, get_sweep_offset

# Bounding box near Odense, Denmark (WGS84)
area = GeoPolygon(shapely.box(10.38, 55.38, 10.42, 55.42))

# Reproject to UTM zone 32N (EPSG:32632) for metric planning
area.set_crs("EPSG:32632")

cells = decompose_polygon(area.geometry)
offset = get_sweep_offset(overlap=0.1, height=30, field_of_view=90)

all_sweeps = []
for cell in cells:
    all_sweeps.extend(generate_sweep_pattern(cell, offset))

print(f"Plan: {len(all_sweeps)} sweeps over {area.geometry.area / 1e6:.2f} km²")
```

---

## 4. Query features from OpenStreetMap

```python
import shapely
import matplotlib.pyplot as plt
from trajgenpy.Geometries import GeoPolygon, GeoMultiTrajectory, decompose_polygon, generate_sweep_pattern, get_sweep_offset
from trajgenpy.Query import query_features
from trajgenpy.Utils import plot_basemap

# --- Query area in WGS84 ---
area_wgs84 = GeoPolygon(shapely.box(10.38, 55.38, 10.42, 55.42))

# --- Fetch land-use and natural features from OSM ---
tags = {"landuse": True, "natural": True}
features = query_features(area_wgs84, tags)

# --- Reproject for planning ---
area_wgs84.set_crs("EPSG:32632")

# --- Plan coverage ---
cells = decompose_polygon(area_wgs84.geometry)
offset = get_sweep_offset(overlap=0.1, height=20, field_of_view=90)
sweeps = [s for cell in cells for s in generate_sweep_pattern(cell, offset)]

# --- Plot ---
fig, ax = plt.subplots(figsize=(10, 8))
area_wgs84.plot(ax=ax, facecolor="none", edgecolor="black")
GeoMultiTrajectory(sweeps, crs="EPSG:32632").plot(ax=ax, color="red")
plt.show()
```

---

## 5. Export to GeoJSON

```python
from trajgenpy.Query import export_as_geojson

# Assumes `boundary`, `obstacles`, `sweeps` are available from previous steps
export_as_geojson(
    boundary=area_wgs84.geometry,
    obstacles=[],          # pass a list of Shapely Polygons
    features=sweeps,
    crs="EPSG:32632",
)
# Creates output.json in the current directory
```

---

## Next steps

- Read the [API Reference](api/index.md) for full parameter documentation.
- Browse the [Examples](examples.md) for complete runnable scripts.
- Check out the Jupyter notebook at `examples/examples.ipynb` for interactive exploration.
