# Installation

TrajGenPy publishes **pre-built manylinux wheels** on PyPI for CPython
3.10–3.14 on Linux x86_64. On those platforms a plain

```bash
pip install trajgenpy
```

needs **no** system dependencies — the wheel bundles the compiled C++
extension (CGAL, pybind11), and the sweep/decomposition algorithms run
without any local CGAL installation.

The package is regularly updated; upgrade to the latest release with:

```bash
pip install --upgrade trajgenpy
```

On any other platform (other Linux architectures, macOS, Windows, or other
Python versions), pip falls back to the source distribution and you must
build the C++ extension yourself — the system requirements below then apply.

---

## System requirements (source builds only)

Only needed when installing from the source distribution (no matching wheel):

| Requirement | Version | Notes |
|---|---|---|
| Python | ≥ 3.10 | CPython only |
| libcgal-dev | any | Computational Geometry Algorithms Library |
| pybind11-dev | any | C++/Python bindings header library |
| cmake | ≥ 3.15 | Required when building from source |

### Ubuntu / Debian

```bash
sudo apt-get update
sudo apt-get install -y libcgal-dev pybind11-dev
```

### macOS (Homebrew)

```bash
brew install cgal pybind11
```

---

## Build from source

Use this approach if you want the latest unreleased changes or need to modify
the C++ bindings.

```bash
# 1. Clone the repository
git clone https://github.com/kasperg3/trajgenpy.git
cd trajgenpy

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Build and install in editable mode
#    (re-run this step if you change any C++ code)
pip install -e .
```

The `-e` flag (editable install) means Python source changes are reflected
immediately without reinstalling, but you **must** re-run `pip install -e .`
after every change to the C++ extension code in `trajgenpy_bindings/`.

---

## Verify the installation

```python
import trajgenpy
print(trajgenpy.__version__)

# Quick functional check
import shapely
from trajgenpy.Geometries import decompose_polygon, generate_sweep_pattern, get_sweep_offset

poly = shapely.box(0, 0, 100, 100)
cells = decompose_polygon(poly)
offset = get_sweep_offset(overlap=0.1, height=10, field_of_view=90)
sweeps = generate_sweep_pattern(cells[0], offset)
print(f"Generated {len(sweeps)} sweep lines — installation OK")
```
