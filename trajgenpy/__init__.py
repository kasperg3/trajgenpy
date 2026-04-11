from importlib.metadata import PackageNotFoundError, version as _package_version

from trajgenpy import Geometries, Query, Utils

try:
    __version__ = _package_version("trajgenpy")
except PackageNotFoundError:
    __version__ = "dev"

__all__ = ["__doc__", "__version__", "Geometries", "Query", "Utils"]
