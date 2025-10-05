
# -----------------------------
# File: app/model_b/risk_predictor.py
# -----------------------------
"""
Model B: Collision Risk Predictor (heuristic placeholder)
- Computes a per-edge risk score using simple heuristics.
- Provides a short explain function.
"""
import networkx as nx
import numpy as np


def heuristic_risk_scores(G: nx.Graph):
    scores = {}
    for u, v, data in G.edges(data=True):
        d = data.get('min_distance_km', None)
        if d is None:
            score = 0.0
        else:
            deg = max(G.degree(u), G.degree(v), 1)
            raw = max(0.0, 1.0 - (d / 100.0)) * (1.0 + 0.1 * (deg - 1))
            score = float(np.clip(raw, 0.0, 1.0))
        scores[(u, v)] = score
        G.edges[u, v]['risk_score'] = score
    return scores


def explain_edge(u: str, v: str, G: nx.Graph) -> str:
    d = G.edges[u, v].get('min_distance_km', None)
    s = G.edges[u, v].get('risk_score', None)
    if d is None or s is None:
        return f"No detailed data for {u} - {v}."
    explanation = f"Satellites {u} and {v}: min distance ~ {d:.1f} km → risk score {s:.2f}."
    if (G.degree(u) > 2 or G.degree(v) > 2):
        explanation += " High node degree increases conjunction clustering risk."
    return explanation
