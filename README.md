# HerdAPI
The polygon_coverage_geometry source files are obtained from https://github.com/ethz-asl/polygon_coverage_planning.

Functions for computing the Boustrophedon Cell Decomposition (BCD) are used by the AreaCoverage-library. The use of the code is covered by GPLv3 license.

Please see https://github.com/ethz-asl/polygon_coverage_planning for details.


docker build -t herd-api .    
docker run -p 5000:5000 herd-api



mkdir build
cd build
cmake ..
make