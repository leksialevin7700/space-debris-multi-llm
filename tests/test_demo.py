
# -----------------------------
# File: tests/test_demo.py
# -----------------------------
"""
Minimal test to ensure the offline demo pipeline runs without importing heavy optional libraries.
Run with: python -m pytest -q
"""
from app.model_a.orbit_engine import build_graph_from_tles
from app.data.sample_tles import SAMPLE_TLES


def test_build_graph_offline():
    # should not raise and should contain the sample nodes
    G = build_graph_from_tles(SAMPLE_TLES, sample_minutes=20, step_min=10, close_threshold_km=1000.0)
    assert G.number_of_nodes() == len(SAMPLE_TLES)
