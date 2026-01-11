from trajgenpy import EnvironmentBuilder, Environment


# generate_urban_dataset()
# generate_flatnature_dataset()
# generate_hillyterrainnature_dataset()
# generate_water_dataset()
# exit(0)
# polygon_file = "data/DemaScenarios/HillyTerrainNature.geojson"
# polygon_file = "data/DemaScenarios/Urban.geojson"
# polygon_file = "data/DemaScenarios/Water.geojson"
polygon_file = "examples/DemaScenarios/FlatTerrainNature.geojson"
sigma_features = {
    "roads": 0,
    "structure": 0,
    "linear": 0,
    "drainage": 0,
    "water": 0,
    "brush": 0,
    "woods": 0,
    "field": 0,
    "rock": 0,
}
alpha_features = {
    "roads": 1,
    "structure": 1,
    "linear": 1,
    "drainage": 1,
    "water": 1,
    "brush": 1,
    "woods": 1,
    "field": 1,
    "rock": 1,
}


env = (
    EnvironmentBuilder()
    .set_polygon_file(polygon_file)
    .set_feature(
        "structure",
        {"building": True, "man_made": True, "bridge": True, "tunnel": True},
    )
    .set_feature("roads", {"highway": True, "tracktype": True})
    .set_feature(
        "linear",
        {
            "railway": True,
            "barrier": True,
            "fence": True,
            "wall": True,
            "pipeline": True,
        },
    )
    .set_feature("drainage", {"waterway": ["drain", "ditch", "culvert", "canal"]})
    .set_feature(
        "water", {"natural": "water", "water": True, "wetland": True, "reservoir": True}
    )
    .set_feature("brush", {"landuse": ["grass", "meadow"]})
    .set_feature("scrub", {"natural": "scrub"})
    .set_feature("woods", {"landuse": ["forest", "wood"], "natural": "wood"})
    .set_feature("field", {"landuse": ["farmland", "farm", "meadow"]})
    .set_feature("rock", {"natural": ["rock", "bare_rock", "scree", "cliff"]})
    .build()
)
heatmap = env.get_combined_heatmap(sigma_features, alpha_features)

env.interactive_plot(
    heatmap,
    use_sliders=True,
    show_basemap=True,
    show_features=False,
    show_heatmap=True,
    export=False,
    show_coverage=False,
)
