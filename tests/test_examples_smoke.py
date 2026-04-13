import runpy
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import pytest
import trajgenpy.Query as query_module
import trajgenpy.Utils as utils_module
from shapely.geometry import LineString, Polygon

REPO_ROOT = Path(__file__).resolve().parents[1]


def _mock_query_features(_area, tags):
    results = {}
    for tag, value in tags.items():
        if tag == "highway":
            results[tag] = [LineString([(0, 0), (1, 1)])]
        elif tag == "building":
            results[tag] = [Polygon([(0, 0), (0, 0.2), (0.2, 0.2), (0.2, 0)])]
        elif tag == "natural" and value == ["coastline"]:
            results[tag] = Polygon([(0, 0), (0, 2), (2, 2), (2, 0)])
        elif tag == "natural":
            results[tag] = [Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])]
        else:
            results[tag] = []
    return results


@pytest.mark.parametrize(
    "example_script",
    [
        "coverage_and_plotting.py",
        "coverage_on_queried_data.py",
        "envrionemental_featues_and_contingency_zones.py",
        "query_and_plotting.py",
    ],
)
def test_examples_run_without_errors(example_script, monkeypatch, tmp_path):
    monkeypatch.setattr(query_module, "query_features", _mock_query_features)
    monkeypatch.setattr(utils_module, "plot_basemap", lambda *args, **kwargs: None)
    monkeypatch.setattr(plt, "show", lambda *args, **kwargs: None)

    scenarios_src = REPO_ROOT / "examples" / "DemaScenarios"
    scenarios_dst = tmp_path / "examples" / "DemaScenarios"
    scenarios_dst.mkdir(parents=True, exist_ok=True)
    shutil.copy(scenarios_src / "FlatTerrainNature.geojson", scenarios_dst)

    monkeypatch.chdir(tmp_path)
    runpy.run_path(str(REPO_ROOT / "examples" / example_script), run_name="__main__")
