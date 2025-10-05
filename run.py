
# -----------------------------
# File: run_demo.py
# -----------------------------
"""
A small CLI demo that runs the pipeline offline using bundled SAMPLE_TLES.

Usage:
    python run_demo.py [--minutes 60] [--step 10] [--threshold 50.0] [--topk 10] [--json]

This script is useful for quickly checking that the pipeline runs in a network-isolated environment.
It now prints a richer terminal summary of close approaches, sorted by risk.
"""
import json
import os
import argparse
from app.model_a.orbit_engine import build_graph_from_tles
from app.model_b.risk_predictor import heuristic_risk_scores, explain_edge
from app.model_c.negotiation_planner import propose_maneuver, consensus_select
from app.model_d.report_generator import generate_report
from app.data.sample_tles import SAMPLE_TLES


def main():
    parser = argparse.ArgumentParser(description='Offline space-debris demo over bundled SAMPLE_TLES')
    parser.add_argument('--minutes', type=int, default=60, help='Total minutes to sample')
    parser.add_argument('--step', type=int, default=10, help='Step in minutes between samples')
    parser.add_argument('--threshold', type=float, default=50.0, help='Close approach threshold in km')
    parser.add_argument('--topk', type=int, default=10, help='Show top-k risky conjunctions')
    parser.add_argument('--json', action='store_true', help='Print machine-readable JSON summary to stdout')
    args = parser.parse_args()

    print('Running offline demo with SAMPLE_TLES...')
    G = build_graph_from_tles(
        SAMPLE_TLES,
        sample_minutes=args.minutes,
        step_min=args.step,
        close_threshold_km=args.threshold,
    )
    heuristic_risk_scores(G)

    edges_info = []
    plans = []
    for u, v, data in G.edges(data=True):
        explanation = explain_edge(u, v, G)
        plan = propose_maneuver(u, v, G)
        plans.append(plan)
        edges_info.append({
            'u': u, 'v': v,
            'min_distance_km': round(data.get('min_distance_km', 0.0), 2),
            'risk_score': round(data.get('risk_score', 0.0), 3),
            'explanation': explanation,
            'plan': plan
        })

    # Sort edges by risk descending for display
    edges_info_sorted = sorted(edges_info, key=lambda e: e['risk_score'], reverse=True)
    final_plan = consensus_select(plans)

    # Pretty terminal output
    print('Nodes:', G.number_of_nodes())
    print('Edges (close approaches):', G.number_of_edges())
    print('Selected plan:', final_plan)

    if edges_info_sorted:
        print('\nTop risky conjunctions:')
        print(f"{'#':>2}  {'U':<18} {'V':<18} {'MinDist(km)':>11} {'Risk':>6} {'Mover':<18} {'dV(km/s)':>9}")
        print('-' * 90)
        for idx, e in enumerate(edges_info_sorted[: max(1, args.topk) ], start=1):
            mover = e['plan']['mover']
            dv = e['plan']['delta_v_km_s']
            print(f"{idx:>2}  {e['u']:<18} {e['v']:<18} {e['min_distance_km']:>11.2f} {e['risk_score']:>6.3f} {mover:<18} {dv:>9.6f}")
    else:
        print('No close approaches under the chosen threshold.')

    # JSON summary if requested
    if args.json:
        summary = {
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'top': edges_info_sorted[: max(1, args.topk) ],
            'selected_plan': final_plan,
        }
        print('\nJSON Summary:')
        print(json.dumps(summary, indent=2))

    out = generate_report(edges_info_sorted, out_html_path='./collision_report.html', out_pdf_path='./collision_report.pdf')
    print('\nReport written to', out)
    if os.path.exists('./collision_report.pdf'):
        print('PDF written to ./collision_report.pdf')


if __name__ == '__main__':
    main()
