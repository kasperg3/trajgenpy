from importlib.metadata import version

from trajgenpy import Geometries, Query, Utils

__version__ = version("trajgenpy")
__all__ = ["Geometries", "Query", "Utils", "__doc__", "__version__"]
