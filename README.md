# Polygon Coverage Planning python bindings
The polygon_coverage_geometry source files are obtained from https://github.com/ethz-asl/polygon_coverage_planning.

Functions for computing the Boustrophedon Cell Decomposition (BCD) are used by the AreaCoverage-library. The use of the code is covered by GPLv3 license. 
## Install the requirements
```sudo apt-get update && apt-get -y install libcgal-dev pybind11-dev```

```pip install -r requirements.txt```

## Build the pip wheel:
```pip wheel . -v```

and install the wheel
```pip install somethin.whl -v```

## or install directly
```pip install . -v```
