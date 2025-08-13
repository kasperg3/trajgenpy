import concurrent.futures
import json
import time

import contextily as cx
import matplotlib.pyplot as plt
import numpy as np
from scipy.__config__ import show
import shapely
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.widgets import Slider
from PIL import Image
from scipy.ndimage import gaussian_filter
from shapely.geometry import LineString

from trajgenpy import Logging, Utils
from trajgenpy.Geometries import GeoMultiPolygon, GeoMultiTrajectory, GeoPolygon
from trajgenpy.Query import query_features

log = Logging.get_logger()
from collections import defaultdict

import cv2
from shapely import plotting as shplt
from skimage.draw import polygon as ski_polygon


class EnvironmentBuilder:
    def __init__(self):
        self.polygon_file = None
        self.sample_distance = 1
        self.meter_per_bin = 3
        self.buffer = 0
        self.tags = {}

    def set_polygon_file(self, polygon_file):
        self.polygon_file = polygon_file
        return self

    def set_sample_distance(self, sample_distance):
        self.sample_distance = sample_distance
        return self

    def set_meter_per_bin(self, meter_per_bin):
        self.meter_per_bin = meter_per_bin
        return self

    def set_buffer(self, buffer):
        self.buffer = buffer
        return self

    def set_feature(self, name, tags):
        self.tags[name] = tags
        return self

    def build(self):
        return Environment(
            self.polygon_file,
            self.sample_distance,
            self.meter_per_bin,
            self.buffer,
            self.tags,
        )


def image_to_world(x, y, meters_per_bin, minx, miny, buffer):
    x = x * meters_per_bin + minx - buffer
    y = y * meters_per_bin + miny - buffer
    return x, y


def world_to_image(x, y, meters_per_bin, minx, miny, buffer):
    x = (x - minx + buffer) / meters_per_bin
    y = (y - miny + buffer) / meters_per_bin
    return int(x), int(y)  # Figure out if this rounding is bad


class Environment:
    def __init__(self, polygon_file, sample_distance, meter_per_bin, buffer, tags):
        self.polygon_file = polygon_file
        self.sample_distance = sample_distance  # The distance in pixels between each sample on an interpolated line
        self.meter_per_bin = meter_per_bin
        self.buffer = buffer
        self.polygon = None
        self.xedges = None
        self.yedges = None
        self.heatmaps = {}
        self.features = {}
        with open(self.polygon_file, "r") as f:
            data = json.load(f)
        coordinates = data["features"][0]["geometry"]["coordinates"][0]
        query_region = shapely.Polygon(coordinates)
        log.info("Query region bounds: %s", query_region.bounds)
        self.polygon = GeoPolygon(query_region).set_crs("EPSG:2197")
        self.area = self.polygon.geometry.area
        log.info("Area of the polygon: %s km²", self.area / 1e6)
        self.minx, self.miny, self.maxx, self.maxy = self.polygon.geometry.bounds
        num_bins_x = int((self.maxx - self.minx) * 1 / self.meter_per_bin)
        num_bins_y = int((self.maxy - self.miny) * 1 / self.meter_per_bin)
        log.info("Number of bins x: %i y: %i", num_bins_x, num_bins_y)
        self.xedges = np.linspace(
            self.minx - self.buffer, self.maxx + self.buffer, num_bins_x + 1
        )
        self.yedges = np.linspace(
            self.miny - self.buffer, self.maxy + self.buffer, num_bins_y + 1
        )
        print(f"Size of x edges: {len(self.xedges)}")
        print(f"Size of y edges: {len(self.yedges)}")

        def process_feature(key):
            feature = query_features(
                GeoPolygon(query_region),
                tags[key],
            )

            feature_collection = [
                geom for feature in feature.values() for geom in feature.geoms
            ]
            if all(
                isinstance(geom, shapely.geometry.Polygon)
                for geom in feature_collection
            ):
                feature_geom = GeoMultiPolygon(feature_collection).set_crs("EPSG:2197")
            elif all(isinstance(geom, LineString) for geom in feature_collection):
                feature_geom = GeoMultiTrajectory(feature_collection).set_crs(
                    "EPSG:2197"
                )
            else:
                raise ValueError("Invalid feature type in feature collection")
            start_time = time.time()
            heatmap = self.generate_heatmap(feature_geom.geometry, self.sample_distance)
            end_time = time.time()
            print(
                f"Time taken to generate heatmap for {key}: {end_time - start_time} seconds"
            )
            return key, heatmap, feature_geom

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(process_feature, key): key for key in tags.keys()
            }
            for future in concurrent.futures.as_completed(futures):
                key, heatmap, feature_geom = future.result()
                self.heatmaps[key] = heatmap
                self.features[key] = feature_geom

    def image_to_world(self, x, y):
        return image_to_world(
            x, y, self.meter_per_bin, self.minx, self.miny, self.buffer
        )

    def world_to_image(self, x, y):
        return world_to_image(
            x, y, self.meter_per_bin, self.minx, self.miny, self.buffer
        )

    # Function to interpolate points on the line
    def interpolate_line(self, line, distance):
        num_points = int(line.length / distance)
        points = []
        if num_points != 0:
            points = [
                line.interpolate(float(i) / num_points, normalized=True)
                for i in range(num_points + 1)
            ]
        else:
            points = [line.interpolate(2, normalized=True)]
        return points

    # # Apply the heatmap generation to all road lines
    def generate_heatmap(
        self, geometry_collection, sample_distance, infill_geometries=True
    ):
        heatmap = np.zeros((len(self.xedges) - 1, len(self.yedges) - 1))
        for feature in geometry_collection.geoms:
            interpolated_points = []
            if isinstance(feature, LineString):
                line = feature
                interpolated_points = self.interpolate_line(line, sample_distance)
            elif isinstance(feature, shapely.geometry.Polygon):
                if infill_geometries:
                    poly_coordinates = np.array(list(feature.exterior.coords))
                    rr, cc = ski_polygon(poly_coordinates[:, 0], poly_coordinates[:, 1])
                    interpolated_points.extend(
                        [shapely.geometry.Point(x, y) for x, y in zip(rr, cc)]
                    )
                else:
                    line = feature.exterior
                    interpolated_points = self.interpolate_line(line, sample_distance)

            # No intersection between the points and the polygon/line
            if not interpolated_points:
                continue
            x, y = zip(*[(point.x, point.y) for point in interpolated_points])

            temp_heatmap, _, _ = np.histogram2d(x, y, bins=(self.xedges, self.yedges))
            heatmap += temp_heatmap

        # Make sure that overlapping features are not counted multiple times in the histogram
        heatmap = np.clip(heatmap, 0, 1)
        # Normalize based on the number of bins occupied
        heatmap = heatmap / np.sum(heatmap)
        return heatmap

    def get_combined_heatmap(self, sigma_features, alpha_features):
        heatmap = np.zeros((len(self.xedges) - 1, len(self.yedges) - 1))
        for key in self.heatmaps.keys():

            # c = np.zeros((len(self.xedges) - 1, len(self.yedges) - 1))
            # for i in range(len(self.xedges) - 1):
            #     for j in range(len(self.yedges) - 1):
            #         x_center = (self.xedges[i] + self.xedges[i + 1]) / 2
            #         y_center = (self.yedges[j] + self.yedges[j + 1]) / 2
            #         c[j, i] += np.exp(- ((self.heatmaps[key] - x_center) ** 2.0 + (self.heatmaps[key] - y_center) ** 2.0) / (2.0 * sigma_features[key] ** 2))
            # c+=heatmap*alpha_features[key]
            # TODO convert this to use a RBF instead
            heatmap += gaussian_filter(
                (self.heatmaps[key]) * alpha_features[key], sigma=sigma_features[key]
            )
            # normalize the histograms with the number of bins occupied
            # heatmap += temp_heatmap / np.max(temp_heatmap)
            # apply a RBF kernel to the heatmap
            # rbf_kernel = np.exp(-0.5 * (self.heatmaps[key] / np.max(self.heatmaps[key]))**2 / sigma_features[key]**2)
            # heatmap += rbf_kernel * alpha_features[key]

        # Make sure the probabilities sum to 1
        # heatmap = heatmap / np.max(heatmap)

        return heatmap

    def binary_cut(self, lines, max_length):
        result = []
        while lines:
            line = lines.pop(0)
            if line.length > max_length:
                lines.extend(self.cut(line, line.length / 2))
            else:
                result.append(line)
        return result

    def modulus_cut(self, lines, max_length):
        result = []
        while lines:
            line = lines.pop(0)
            if line.length > max_length:
                num_segments = int(np.ceil(line.length / max_length))
                segment_length = line.length / num_segments
                lines.extend(self.cut(line, segment_length))
            else:
                result.append(line)
        return result

    def cut(self, line, distance):
        if line.length >= distance:
            coords = list(line.coords)
            cut_point = line.interpolate(distance)
            cut_index = next(
                (
                    i
                    for i, p in enumerate(coords)
                    if line.project(shapely.Point(p)) >= distance
                ),
                len(coords) - 1,
            )
            return LineString(
                coords[:cut_index] + [(cut_point.x, cut_point.y)]
            ), LineString([(cut_point.x, cut_point.y)] + coords[cut_index:])
        else:
            return line, LineString()

    def shrink_polygon(self, p: shapely.Polygon | shapely.MultiPolygon, buffer_size):
        shrunken_polygon = p.buffer(-buffer_size, join_style="round", single_sided=True)
        if shrunken_polygon.is_empty:
            shrunken_polygon = p.buffer(-buffer_size * 0.5, join_style="round")
            if not shrunken_polygon.is_empty:
                return [p, shrunken_polygon]
            else:
                return [p]

        return [p, *self.shrink_polygon(shrunken_polygon, buffer_size)]

    def create_polygons_from_contours(self, contours, hierarchy, min_area):
        cnt_children = defaultdict(list)
        child_contours = set()
        image_coordinates_min_area = min_area / self.meter_per_bin
        assert hierarchy.shape[0] == 1
        for idx, (_, _, _, parent_idx) in enumerate(hierarchy[0]):
            if parent_idx != -1:
                child_contours.add(idx)
                cnt_children[parent_idx].append(contours[idx])
            all_polygons = []
        for idx, cnt in enumerate(contours):
            if (
                idx not in child_contours
                and cv2.contourArea(cnt) >= image_coordinates_min_area
            ):
                assert cnt.shape[1] == 1
                cnt[:, 0, :] = np.array(
                    [self.image_to_world(x, y) for x, y in cnt[:, 0, :]]
                )
                poly = shapely.Polygon(
                    shell=cnt[:, 0, :],
                    holes=[
                        np.array([self.image_to_world(x, y) for x, y in cnt[:, 0, :]])
                        for c in cnt_children.get(idx, [])
                        if cv2.contourArea(c) >= image_coordinates_min_area
                    ],
                )
                all_polygons.append(poly)
        return all_polygons

    def informative_coverage(
        self,
        heatmap,
        sensor_radius=8,
        max_length=500,
        contour_smoothing=5,
        contour_threshold=0.00001,
    ):
        start_time = time.time()
        mask = np.zeros_like(heatmap, dtype=np.uint8)
        mask[heatmap > contour_threshold] = 1
        min_area = 0.01  # Should be the area of the sensor footprint
        contours, hierarchy = cv2.findContours(
            mask.T, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE
        )
        if not contours:
            raise ValueError("No probability contours found")

        all_polygons = self.create_polygons_from_contours(contours, hierarchy, min_area)
        print(f"Number of polygons: {len(all_polygons)}")
        coverage_polygons = []
        for polygon in all_polygons:
            polygon = polygon.simplify(contour_smoothing, preserve_topology=False)
            coverage_polygons.extend(self.shrink_polygon(polygon, sensor_radius * 2))
        result_list = []
        for poly_item in coverage_polygons:
            if isinstance(poly_item, shapely.geometry.MultiPolygon):
                result_list.extend(list(poly_item.geoms))
            else:
                result_list.append(poly_item)
        result_list = [poly for poly in result_list if poly.area >= 1]

        # Define the starting point of the polygon as the point closest to the origin this provides better coverage paths
        for i, poly in enumerate(result_list):
            coords = list(poly.exterior.coords)
            initial_point = shapely.geometry.Point(0, 0)
            min_dist_index = min(
                range(len(coords)),
                key=lambda index: initial_point.distance(
                    shapely.geometry.Point(coords[index])
                ),
            )
            min_dist_index = min(
                range(len(coords)),
                key=lambda index: coords[index][0] ** 2 + coords[index][1] ** 2,
            )
            new_coords = coords[min_dist_index:] + coords[:min_dist_index]
            result_list[i] = shapely.geometry.Polygon(new_coords)

        # # Evaluation of the line partitioning
        # def calculate_sum_min_distances(lines):
        #     initial_points = [shapely.geometry.Point(line.coords[0]) for line in lines]
        #     sum_min_distances = 0
        #     for poly in lines:
        #         min_distance = min(poly.distance(point) for point in initial_points if point != shapely.geometry.Point(poly.coords[0]))
        #         sum_min_distances += min_distance
        #     return sum_min_distances

        # start_time = time.time()
        # binary_result = self.binary_cut([LineString(poly.exterior.coords) for poly in result_list], max_length)
        # binary_time = time.time() - start_time
        # print(f"Binary cut time: {binary_time} seconds, number of lines: {len(binary_result)}")
        # binary_sum_min_distances = calculate_sum_min_distances(binary_result)
        # print(f"Binary cut: Sum of distances to the nearest start-point: {binary_sum_min_distances}")

        # start_time = time.time()
        result = self.modulus_cut(
            [LineString(poly.exterior.coords) for poly in result_list], max_length
        )
        # modulus_time = time.time() - start_time
        # print(f"Modulus cut time: {modulus_time} seconds, number of lines: {len(result)}")
        # modulus_sum_min_distances = calculate_sum_min_distances(result)
        # print(f"Modulus cut: Sum of distances to the nearest start-point: {modulus_sum_min_distances}")

        # Remove the same distance from the linestrings as the sensor footprint
        result = [
            self.cut(line, sensor_radius)[1]
            for line in result
            if line.length >= sensor_radius
        ]
        end_time = time.time()
        print(
            f"Time taken to generate coverage patterns: {end_time - start_time} seconds with {len(result)} coverage-paths"
        )
        # shplt.plot_line(shapely.MultiLineString(result), add_points=False)
        # shplt.plot_points([shapely.Point(line.coords[0][0], line.coords[0][1]) for line in result], color='green', marker='o', label='Start Points')
        # shplt.plot_points([shapely.Point(line.coords[-1][0], line.coords[-1][1])  for line in result], color='red', marker='x', label='End Points')
        # # self.polygon.plot(linestyle="--", facecolor="none", edgecolor="black")
        # plt.grid(False)
        # plt.show()
        return result

    def plot(
        self,
        show_basemap=True,
        show_features=False,
        show_heatmap=True,
        show_coverage=False,
    ):
        fig, ax = plt.subplots()
        ax.set_xlim(self.minx - self.buffer, self.maxx + self.buffer)
        ax.set_ylim(self.miny - self.buffer, self.maxy + self.buffer)
        if show_features:
            self.polygon.plot(linestyle="--", facecolor="none", edgecolor="black")
            for key, feature in self.features.items():
                if isinstance(feature, GeoMultiPolygon):
                    feature.plot()
                elif isinstance(feature, GeoMultiTrajectory):
                    feature.plot(color="red", linestyle="--")
        if show_basemap:
            Utils.plot_basemap(
                provider=cx.providers.OpenStreetMap.Mapnik, crs="EPSG:2197"
            )
            alpha = 0.4
        if show_heatmap:
            if alpha is not None:
                alpha = 1
            colors = [
                (1, 1, 1),  # White
                (0, 0, 1),  # Blue
                (0, 0.5, 1),  # Blue
                (0, 1, 1),  # Cyan
                (0.7, 1, 0),  # Green
                (1, 1, 0),  # Yellow
                (1, 0.5, 0),  # Orange
                (1, 0, 0),  # Red
                (0.5, 0, 0),  # Dark red
            ]

            # Create the colormap
            custom_cmap = LinearSegmentedColormap.from_list("jet_fade_to_white", colors)
            # custom_cmap = "jet"

            # Use the custom colormap for the heatmap
            # cbar = plt.colorbar(plt.cm.ScalarMappable(cmap=custom_cmap), ax=ax, orientation='vertical')
            # cbar.mappable.set_clim(vmin=heatmap.min(), vmax=heatmap.max())
            # cbar.set_label('Target Distribution')
            # cbar.mappable.set_clim(vmin=heatmap.min(), vmax=heatmap.max())
            extent = [self.xedges[0], self.xedges[-1], self.yedges[0], self.yedges[-1]]
            sigma_features = {
                key: 3 for key in self.heatmaps.keys()
            }  # Example sigma value
            alpha_features = {
                key: 1 for key in self.heatmaps.keys()
            }  # Example alpha value
            heatmap = self.get_combined_heatmap(sigma_features, alpha_features)
            heatmap[heatmap < 0.00001] = 0
            plt.imshow(
                heatmap.T, extent=extent, origin="lower", cmap=custom_cmap, alpha=0.4
            )
        if show_coverage:
            sensor_radius = 8
            lines = self.informative_coverage(heatmap, sensor_radius=sensor_radius)
            coverage = GeoMultiTrajectory(lines, crs="EPSG:2197")
            coverage.plot(ax, color=plt.cm.tab10(3), add_points=False, alpha=1)
            for line in lines:
                for i in range(len(line.coords) - 1):
                    start = line.coords[i]
                    end = line.coords[i + 1]
                    num_points = (
                        int(
                            np.linalg.norm(np.array(end) - np.array(start))
                            / (sensor_radius / 2)
                        )
                        + 1
                    )
                    for j in range(num_points + 1):
                        x = start[0] + j * (end[0] - start[0]) / num_points
                        y = start[1] + j * (end[1] - start[1]) / num_points
                        circle = plt.Circle(
                            (x, y),
                            sensor_radius,
                            color=plt.cm.tab10(3),
                            fill=True,
                            alpha=0.1,
                            edgecolor="none",
                        )
                        ax.add_patch(circle)
        ax.set_xlim(self.minx - self.buffer, self.maxx + self.buffer)
        ax.set_ylim(self.miny - self.buffer, self.maxy + self.buffer)
        # plt.axis("equal")
        plt.tight_layout()
        ax.set_axis_off()
        plt.savefig("testplot.png", bbox_inches="tight")
        plt.show()

    def interactive_plot(
        self,
        heatmap,
        use_sliders=True,
        show_basemap=True,
        show_features=False,
        export=False,
        show_heatmap=True,
        show_coverage=False,
    ):
        # Create a figure and axis for the slider
        fig, ax = plt.subplots()
        # Set xlim and ylim based on the bounding box of the polygon
        # to ensure the basemap has the right location
        ax.set_xlim(self.minx - self.buffer, self.maxx + self.buffer)
        ax.set_ylim(self.miny - self.buffer, self.maxy + self.buffer)
        if show_features:
            self.polygon.plot(linestyle="--", facecolor="none", edgecolor="black")
            for key, feature in self.features.items():
                if isinstance(feature, GeoMultiPolygon):
                    feature.plot()
                elif isinstance(feature, GeoMultiTrajectory):
                    feature.plot(color="red", linestyle="--")

        if show_basemap:
            alpha = 0.4
            Utils.plot_basemap(
                provider=cx.providers.OpenStreetMap.Mapnik, crs="EPSG:2197"
            )
        if show_heatmap:
            colors = [
                (1, 1, 1),  # White
                (0, 0, 1),  # Blue
                (0, 0.5, 1),  # Blue
                (0, 1, 1),  # Cyan
                (0.7, 1, 0),  # Green
                (1, 1, 0),  # Yellow
                (1, 0.5, 0),  # Orange
                (1, 0, 0),  # Red
                (0.5, 0, 0),  # Dark red
            ]

            # Create the colormap
            custom_cmap = LinearSegmentedColormap.from_list("jet_fade_to_white", colors)
            # custom_cmap = "jet"

            # Use the custom colormap for the heatmap
            cbar = plt.colorbar(
                plt.cm.ScalarMappable(cmap=custom_cmap), ax=ax, orientation="vertical"
            )
            cbar.mappable.set_clim(vmin=heatmap.min(), vmax=heatmap.max())
            cbar.set_label("Target Distribution")
            extent = [self.xedges[0], self.xedges[-1], self.yedges[0], self.yedges[-1]]
            heatmap[heatmap < 0.00001] = 0
            heatmap_img = plt.imshow(
                heatmap.T,
                extent=extent,
                origin="lower",
                cmap=custom_cmap,
                alpha=alpha if alpha is not None else 1,
            )
        if show_coverage:
            lines = self.informative_coverage(heatmap)
            coverage = GeoMultiTrajectory(lines, crs="EPSG:2197")
            coverage.plot(ax, color=plt.cm.tab10(4), add_points=False, alpha=1)
        if use_sliders:
            filter_sliders = {}
            multiplier_sliders = {}
            for key in self.heatmaps.keys():
                y_position = 0 + 0.05 * list(self.heatmaps.keys()).index(key)

                ax_filter_slider = plt.axes([0.25, y_position, 0.25, 0.03])
                ax_multiplier_slider = plt.axes([0.60, y_position, 0.25, 0.03])

                filter_sliders[key] = Slider(
                    ax_filter_slider,
                    f"{key}:  sigma",
                    0.0,
                    10.0,
                    valinit=3,
                    valstep=0.1,
                )
                multiplier_sliders[key] = Slider(
                    ax_multiplier_slider, "alpha", 0.0, 10.0, valinit=1, valstep=0.1
                )
                ax_sensor_slider = plt.axes([0.25, 0.95, 0.25, 0.03])
                sensor_slider = Slider(
                    ax_sensor_slider, "Sensor Width", 1.0, 20.0, valinit=8, valstep=0.5
                )
            # Save button
            save_ax = plt.axes([0.5, 0.9, 0.1, 0.04])
            save_button = plt.Button(save_ax, "Save", color="white", hovercolor="0.975")

            def update(val):
                sigma_features = {
                    key: slider.val for key, slider in filter_sliders.items()
                }
                alpha_features = {
                    key: multiplier_sliders[key].val for key in filter_sliders.keys()
                }

                combined_heatmap = self.get_combined_heatmap(
                    sigma_features, alpha_features
                )
                if show_heatmap:
                    heatmap_img.set_data(combined_heatmap.T)
                    cbar.mappable.set_clim(
                        vmin=combined_heatmap.min(), vmax=combined_heatmap.max()
                    )
                    heatmap_img.set_cmap(custom_cmap)

                for artist in ax.patches:
                    artist.remove()

                if show_coverage:
                    lines = self.informative_coverage(
                        combined_heatmap, sensor_radius=sensor_slider.val
                    )
                    coverage = GeoMultiTrajectory(lines, crs="EPSG:2197")
                    coverage.plot(ax, color=plt.cm.tab10(4), add_points=False, alpha=1)
                plt.draw()

            def save(event):
                sigma_features = {
                    key: slider.val for key, slider in filter_sliders.items()
                }
                alpha_features = {
                    key: multiplier_sliders[key].val for key in filter_sliders.keys()
                }
                combined_heatmap = self.get_combined_heatmap(
                    sigma_features, alpha_features
                )
                # Normalize the heatmap to the range 0-255
                # combined_heatmap = (combined_heatmap - combined_heatmap.min()) / (combined_heatmap.max() - combined_heatmap.min()) * 127

                temp_heatmap = np.flipud(
                    combined_heatmap.T
                )  # Makes sure that the map is oriented correctly

                height, width = temp_heatmap.shape
                greyscale_with_alpha = np.zeros((height, width, 2), dtype=np.uint8)
                # Set the grayscale channel based on the matrix values
                greyscale_with_alpha[..., 0] = (
                    temp_heatmap  # Greyscale (intensity) values
                )
                # Set the alpha channel: 255 where matrix > 0, otherwise 0 (transparent)
                greyscale_with_alpha[..., 1] = np.where(temp_heatmap > -1, 255, 0)

                # Convert to a greyscale image with alpha
                img = Image.fromarray(greyscale_with_alpha, mode="LA")
                # Create a filename with the slider values
                slider_values = "_".join(
                    [
                        f"{key}_sigma{filter_sliders[key].val:.1f}_alpha{multiplier_sliders[key].val:.1f}"
                        for key in filter_sliders.keys()
                    ]
                )
                filename = f"data/plots/heatmap_{slider_values}.png"

                # Save the image with the generated filename
                img.save(filename)
                print("Heatmap saved as heatmap.png")

                # Save the plot itself as a png
                # Temporarily hide the sliders and buttons
                for slider in filter_sliders.values():
                    slider.ax.set_visible(False)
                for slider in multiplier_sliders.values():
                    slider.ax.set_visible(False)
                save_button.ax.set_visible(False)

                # Save the plot area
                plt.savefig("data/plots/plot.png", bbox_inches="tight")

                # Restore the visibility of sliders and buttons
                for slider in filter_sliders.values():
                    slider.ax.set_visible(True)
                for slider in multiplier_sliders.values():
                    slider.ax.set_visible(True)
                save_button.ax.set_visible(True)

            save_button.on_clicked(save)

            for slider in filter_sliders.values():
                # slider.on_changed(update)
                slider.connect_event("button_release_event", update)

            for slider in multiplier_sliders.values():
                slider.connect_event("button_release_event", update)
                # slider.on_changed(update)

        # plt.axis("equal")
        ax.set_axis_off()

        if export:
            plt.savefig("data/plots/plot.png", bbox_inches="tight")
        plt.show()


def get_filter_sigma(filter_width_meters, env):
    filter_width_pixels = filter_width_meters / env.meter_per_bin

    # Calculate the sigma value for the Gaussian filter
    sigma = filter_width_pixels / (2 * np.sqrt(2 * np.log(2)))
    return sigma
