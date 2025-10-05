

# -----------------------------
# File: app/model_c/negotiation_planner.py
# -----------------------------
"""
Model C: Multi-LLM Negotiation Planner (prototype)
- Simple heuristic maneuver proposer and consensus function.
- Replaceable with real LLM negotiation flows later.
"""

def propose_maneuver(u: str, v: str, G):
    du = G.degree(u)
    dv = G.degree(v)
    mover = u if du <= dv else v
    d = G.edges[u, v].get('min_distance_km', 100.0)
    # toy delta-v (km/s) heuristic
    dv_req = min(0.5, max(0.01, (10.0 / max(1.0, d))))
    plan = {
        'mover': mover,
        'delta_v_km_s': round(dv_req, 6),
        'reason': f"Close approach (min_dist={d:.1f} km). Chosen mover has lower traffic degree."
    }
    return plan


def consensus_select(plans):
    if not plans:
        return None
    # choose smallest delta-v plan as a simple consensus
    return sorted(plans, key=lambda p: p['delta_v_km_s'])[0]

