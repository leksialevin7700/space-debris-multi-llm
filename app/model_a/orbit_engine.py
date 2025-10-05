# -----------------------------
# File: app/model_a/orbit_engine.py
# -----------------------------
"""
Model A: Orbit Intelligence Engine
- Fetch TLEs (from Celestrak) or accept local TLE list (for offline demos)
- Propagate using sgp4 and produce sample positions
- Build a NetworkX semantic graph: nodes = sat_id, attributes = latest state; edges = potential close approaches
"""
from sgp4.api import Satrec
from sgp4.api import jday
import requests
import numpy as np
import networkx as nx
import datetime
from typing import List, Tuple


CELESTRAK_TLE_URLS = {
    'stations': 'https://celestrak.org/NORAD/elements/stations.txt',
    'active': 'https://celestrak.org/NORAD/elements/active.txt'
}

TLE = Tuple[str, str, str]


def fetch_tles(url: str) -> List[TLE]:
    """Fetch TLEs from a plain-text TLE file (Celestrak-style).

    This parser is robust to small format issues: it looks for a name line followed by two lines
    starting with '1 ' and '2 '. Returns an empty list on error.
    """
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print('fetch_tles: network error or URL problem:', e)
        return []

    lines = [ln.rstrip('\n') for ln in r.text.splitlines() if ln.strip() != '']
    tles: List[TLE] = []
    i = 0
    while i < len(lines):
        name = lines[i].strip()
        # Need at least two following lines
        if i + 2 < len(lines) and lines[i+1].startswith('1 ') and lines[i+2].startswith('2 '):
            l1 = lines[i+1].strip()
            l2 = lines[i+2].strip()
            tles.append((name, l1, l2))
            i += 3
        else:
            # If parsing fails at this line, skip one line and continue
            i += 1
    return tles


def build_graph_from_tles(tles: List[TLE], sample_minutes: int = 120, step_min: int = 10, close_threshold_km: float = 10.0) -> nx.Graph:
    """Build a semantic graph from a list of TLEs.

    Nodes: satellite name
    Edges: if the minimum sampled distance between two objects < close_threshold_km, add an edge with attribute 'min_distance_km'

    NOTE: This function samples positions at regular minute intervals and computes pairwise distances.
    It's a naive O(n^2 * timesteps) algorithm and intended for prototypes/small N only.
    """
    G = nx.Graph()
    if not tles:
        return G

    # create Satrec objects and add nodes
    satrecs = []
    for name, l1, l2 in tles:
        try:
            sat = Satrec.twoline2rv(l1, l2)
            satrecs.append((name, sat))
            G.add_node(name, tle=(l1, l2))
        except Exception as e:
            print(f'Failed to parse TLE for {name}:', e)

    now = datetime.datetime.utcnow()
    times = []
    for m in range(0, sample_minutes + 1, step_min):
        t = now + datetime.timedelta(minutes=m)
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond*1e-6)
        times.append((jd, fr))

    # compute positions for each satellite at each sampled time
    positions = {name: [] for name, _ in satrecs}
    for name, sat in satrecs:
        for jd, fr in times:
            try:
                e, r, v = sat.sgp4(jd, fr)
            except Exception:
                e = 1
                r = None
            if e != 0 or r is None:
                positions[name].append(None)
            else:
                # r is position vector in TEME km
                positions[name].append(np.array(r, dtype=float))

    names = [name for name, _ in satrecs]
    n = len(names)

    for i in range(n):
        for j in range(i + 1, n):
            min_dist = float('inf')
            for k in range(len(times)):
                ri = positions[names[i]][k]
                rj = positions[names[j]][k]
                if ri is None or rj is None:
                    continue
                d = float(np.linalg.norm(ri - rj))
                if d < min_dist:
                    min_dist = d
            if min_dist < close_threshold_km:
                G.add_edge(names[i], names[j], min_distance_km=min_dist)

    return G
