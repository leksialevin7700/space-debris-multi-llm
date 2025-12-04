# ---------------------------------------------
# File: app/model_a/orbit_engine.py
# ---------------------------------------------
"""
Model A: Orbit Intelligence Engine (Static Data Version)

Loads TLEs from local files inside app/data/,
parses them into Satrec objects, propagates orbits,
and constructs a semantic graph based on near approaches.
"""

from sgp4.api import Satrec, jday
import numpy as np
import datetime
import networkx as nx
from pathlib import Path
from typing import List, Tuple


# Path to your static dataset
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

STATIC_TLE_FILES = [
    "starlink.tle",
    "cosmos2251.tle",
    "iridium33.tle",
    "active.tle"
]

# TLE type
TLE = Tuple[str, str, str]   # (name, line1, line2)


# -------------------------------------------------------
# 1) Load TLEs from local .tle files
# -------------------------------------------------------
def load_tles_from_file(path: Path) -> List[TLE]:
    """Load a .tle file and parse it into (name, l1, l2) triples."""
    try:
        lines = [ln.strip() for ln in open(path, "r").read().splitlines()]
    except Exception as e:
        print(f"[ERROR] Could not read {path}: {e}")
        return []

    tles = []
    i = 0
    while i < len(lines) - 2:
        name = lines[i]
        l1 = lines[i + 1]
        l2 = lines[i + 2]

        # Basic format check
        if l1.startswith("1 ") and l2.startswith("2 "):
            tles.append((name, l1, l2))
            i += 3
        else:
            i += 1

    return tles


def load_all_tles() -> List[TLE]:
    """Load and combine all TLE files."""
    all_tles = []
    for fname in STATIC_TLE_FILES:
        all_tles.extend(load_tles_from_file(DATA_DIR / fname))
    return all_tles


# -------------------------------------------------------
# 2) Build semantic graph using orbital propagation
# -------------------------------------------------------
def build_graph_from_tles(
    tles: List[TLE],
    sample_minutes: int = 120,
    step_min: int = 10,
    close_threshold_km: float = 10.0
) -> nx.Graph:
    """
    Build a semantic graph:

    - Nodes: satellite names
    - Edges: satellites that come within `close_threshold_km` distance
    """

    G = nx.Graph()
    if not tles:
        print("[WARN] No TLE data found.")
        return G

    # Parse Satrec objects
    sat_objects = []
    for name, l1, l2 in tles:
        try:
            sat = Satrec.twoline2rv(l1, l2)
            sat_objects.append((name, sat))
            G.add_node(name, tle=(l1, l2))
        except Exception as e:
            print(f"[ERROR] Could not parse TLE for {name}: {e}")

    # Sample times for propagation
    now = datetime.datetime.utcnow()
    time_samples = []
    for m in range(0, sample_minutes + 1, step_min):
        t = now + datetime.timedelta(minutes=m)
        jd, fr = jday(
            t.year, t.month, t.day,
            t.hour, t.minute, t.second + t.microsecond * 1e-6
        )
        time_samples.append((jd, fr))

    # Compute positions
    positions = {name: [] for name, _ in sat_objects}

    for name, sat in sat_objects:
        for jd, fr in time_samples:
            e, r, v = sat.sgp4(jd, fr)
            if e != 0:
                positions[name].append(None)
            else:
                positions[name].append(np.array(r, dtype=float))

    # Pairwise distance detection
    names = [name for name, _ in sat_objects]
    n = len(names)

    for i in range(n):
        for j in range(i + 1, n):
            min_dist = float("inf")

            for k in range(len(time_samples)):
                r1 = positions[names[i]][k]
                r2 = positions[names[j]][k]

                if r1 is None or r2 is None:
                    continue

                d = float(np.linalg.norm(r1 - r2))
                if d < min_dist:
                    min_dist = d

            if min_dist < close_threshold_km:
                G.add_edge(names[i], names[j], min_distance_km=min_dist)

    return G


# -------------------------------------------------------
# 3) Helper: Run Model A end-to-end
# -------------------------------------------------------
def run_orbit_intelligence():
    tles = load_all_tles()
    graph = build_graph_from_tles(tles)
    return graph


if __name__ == "__main__":
    G = run_orbit_intelligence()
    print("Nodes:", len(G.nodes()))
    print("Edges (potential close approaches):", len(G.edges()))

