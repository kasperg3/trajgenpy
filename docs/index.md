# TrajGenPy

[![Build Status](https://github.com/kasperg3/trajgenpy/actions/workflows/test.yml/badge.svg)](https://github.com/kasperg3/trajgenpy/actions/workflows/test.yml)
[![PyPI version](https://img.shields.io/pypi/v/trajgenpy.svg)](https://pypi.org/project/trajgenpy/)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

**TrajGenPy** is a Python library for generating coverage trajectories over arbitrary
polygonal areas using the **Boustrophedon Cell Decomposition** algorithm.

---

## What does it do?

Given an area of interest (and optional obstacle polygons), TrajGenPy will:

1. **Decompose** the area into convex, weakly-monotone cells via the CGAL-backed
   Boustrophedon Cell Decomposition.
2. **Generate** parallel sweep ("lawnmower") lines for each cell with a configurable
   inter-sweep distance and overlap ratio.
3. **Export** the resulting trajectory as Shapely geometries or GeoJSON — ready for
   use with any flight/robot controller.

It also provides helpers for **querying real-world features** from OpenStreetMap and
**reprojecting** geometries between coordinate reference systems.

---

## Key Features

| Feature | Description |
|---|---|
| Boustrophedon decomposition | Splits non-convex polygons into convex cells |
| Configurable sweep offset | Derived from sensor height, FoV, and desired overlap |
| Obstacle avoidance | Holes in the boundary polygon are respected |
| CRS-aware geometry wrappers | Convert between WGS84 and any projected CRS |
| OSM feature extraction | Query buildings, roads, land use, and more |
| GeoJSON export | Save plans as standard GeoJSON FeatureCollections |

---

## Quick example

```python
import shapely
from trajgenpy.Geometries import (
    GeoPolygon,
    decompose_polygon,
    generate_sweep_pattern,
    get_sweep_offset,
)

# 1. Define an area in WGS84 and reproject to UTM for metric planning
area = GeoPolygon(shapely.box(10.38, 55.38, 10.42, 55.42))
area.set_crs("EPSG:32632")

# 2. Decompose into convex cells
cells = decompose_polygon(area.geometry)

# 3. Generate a sweep pattern (20 m height, 90° FoV, 10% overlap)
offset = get_sweep_offset(overlap=0.1, height=20, field_of_view=90)
for cell in cells:
    sweeps = generate_sweep_pattern(cell, offset)
    print(f"Cell covered by {len(sweeps)} sweep lines")
```

---

## Installation

=== "pip (recommended)"

    ```bash
    # System dependencies (Ubuntu/Debian)
    sudo apt-get install -y libcgal-dev pybind11-dev

    pip install trajgenpy
    ```

=== "From source"

    ```bash
    sudo apt-get install -y libcgal-dev pybind11-dev
    git clone https://github.com/kasperg3/trajgenpy.git
    cd trajgenpy
    pip install -e .
    ```

See the [Installation guide](installation.md) for full details.

---

## Citation

If you use TrajGenPy in academic work, please cite:

```bibtex
@inproceedings{grontved2022icar,
  title     = {Decentralized Multi-UAV Trajectory Task Allocation in Search and Rescue Applications},
  author    = {Gr{\o}ntved, Kasper Andreas R{\o}mer and Schultz, Ulrik Pagh and Christensen, Anders Lyhne},
  booktitle = {21st International Conference on Advanced Robotics},
  year      = {2023},
  organization = {IEEE}
}
```
