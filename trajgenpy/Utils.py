import contextily as ctx
import matplotlib.pyplot as plt
import shapely


# A function to plot a map using the contextily library
def plot_basemap(ax=None, provider=ctx.providers.Esri.WorldImagery, crs="WGS84"):
    if ax is None:
        ax = plt.gca()
    return ctx.add_basemap(ax, source=provider, crs=crs)


def normalize_coordinates(boundary, geometries=None):
    normalized_geoms = []
    translation_vector = shapely.Point(
        boundary.bounds["minx"].min(), boundary.bounds["miny"].min()
    )
    for geom in geometries:
        normalized_geoms.append(geom.difference(translation_vector))

    return normalized_geoms
