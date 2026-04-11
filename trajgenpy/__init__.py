from importlib.metadata import PackageNotFoundError, version as _package_version

try:
    __version__ = _package_version(__name__)
except PackageNotFoundError:
    __version__ = "dev"

from trajgenpy import Geometries, Query, Utils
__all__ = ["__doc__", "__version__", "Geometries", "Query", "Utils"]
