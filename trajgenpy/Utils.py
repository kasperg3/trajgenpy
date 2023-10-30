import contextily as ctx
import matplotlib.pyplot as plt
import shapely
from shapely.affinity import translate

# Example usage:


# A function to plot a map using the contextily library
def plot_basemap(ax=None, provider=ctx.providers.Esri.WorldImagery, crs="WGS84"):
    if ax is None:
        ax = plt.gca()
    return ctx.add_basemap(ax, source=provider, crs=crs)


def normalize_coordinates(boundary, geometries=None):
    normalized_geoms = []
    translation_vector = shapely.Point(boundary.bounds[0], boundary.bounds[1])
    for geom in list(geometries.geoms):
        normalized_geoms.append(
            translate(geom, xoff=-translation_vector.x, yoff=-translation_vector.y)
        )

    return normalized_geoms


# lines = MultiLineString(
#     [LineString([(100, 100), (200, 200)]), LineString([(300, 300), (400, 400)])]
# )
# image_width = 800
# image_height = 600
# resulting_image = create_image_from_multilinestring(lines, image_width, image_height)


# import cv2
# def create_image_from_multilinestring(
#     multilinestring: shapely.MultiLineString,
#     thickness=5,
#     line_sigma=5,
#     intensity=10,
#     line_color=(0, 0, 255),
# ):
#     # Create a blank white image
#     image_width = int(multilinestring.bounds[2]) + 100
#     image_height = int(multilinestring.bounds[3]) + 100
#     image = np.zeros((image_height, image_width), np.uint8)

#     # Convert MultiLineString to a list of LineStrings
#     linestrings = list(multilinestring.geoms)
#     for linestring in linestrings:
#         coords = np.array(linestring.coords)

#         # Iterate over each pair of points and interpolate
#         for i in range(len(coords) - 1):
#             x1, y1 = coords[i]
#             x2, y2 = coords[i + 1]

#             # Create a Gaussian line kernel
#             line_kernel = np.zeros((image_height, image_width), np.uint8)
#             # cv2.rectangle(
#             #     line_kernel,
#             #     (int(x1), int(y1)),
#             #     (int(x2), int(y2)),
#             #     intensity,
#             #     thickness,
#             # )

#             cv2.line(
#                 line_kernel,
#                 (int(x1), int(y1)),
#                 (int(x2), int(y2)),
#                 intensity,
#                 thickness,
#             )

#             # Apply Gaussian blur to the line kernel
#             line_kernel = gaussian_filter(line_kernel, sigma=line_sigma)
#             # Add the colored line to the image
#             image = np.clip(
#                 image.astype(np.int64) + line_kernel.astype(np.int64), 0, 255
#             ).astype(np.uint8)

#     cv2.flip(image, 0, image)
#     image = cv2.normalize(image, image, 0, 255, cv2.NORM_MINMAX)

#     image = cv2.applyColorMap(image, cv2.COLORMAP_JET)
#     # Display and save the resulting image
#     # cv2.imshow("Image with Colored Gaussian Lines", image)
#     # cv2.waitKey(0)
#     # cv2.destroyAllWindows()
#     cv2.imwrite("image_with_colored_gaussian_lines.png", image)

#     return image


# # trajectory_list = Utils.normalize_coordinates(
# #     geo_poly.geometry, multi_traj.get_geometry()
# # )

# # Utils.create_image_from_multilinestring(
# #     shapely.MultiLineString(trajectory_list),
# #     thickness=int(offset * 1.2),
# #     intensity=30,
# # )
