
# -----------------------------
# File: app/api/main.py
# -----------------------------
"""
FastAPI app that wires Model A-D into endpoints
Endpoints:
- /run_pipeline -> runs A->B->C->D using live Celestrak fetch (network required)
- /run_demo -> runs the pipeline using bundled SAMPLE_TLES (offline demo)
- /report -> serves last generated HTML report
"""
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
import uvicorn
import os

from app.model_a.orbit_engine import fetch_tles, build_graph_from_tles, CELESTRAK_TLE_URLS
from app.model_b.risk_predictor import heuristic_risk_scores, explain_edge
from app.model_c.negotiation_planner import propose_maneuver, consensus_select
from app.model_d.report_generator import generate_report
from app.data.sample_tles import SAMPLE_TLES

app = FastAPI()
LAST_REPORT_PATH = '/tmp/collision_report.html'
LAST_REPORT_PDF_PATH = '/tmp/collision_report.pdf'


@app.get('/run_pipeline')
async def run_pipeline(source: str = Query('active', description="'active' or 'stations' or a full URL"), sample_minutes: int = 120):
    # choose URL
    if source in CELESTRAK_TLE_URLS:
        url = CELESTRAK_TLE_URLS[source]
    elif source.startswith('http'):
        url = source
    else:
        return {'error': 'invalid source parameter'}

    tles = fetch_tles(url)
    if not tles:
        return {'error': 'failed to fetch or parse TLEs from the provided source'}

    tles = tles[:60]
    G = build_graph_from_tles(tles, sample_minutes=sample_minutes, step_min=10, close_threshold_km=20.0)
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

    final_plan = consensus_select(plans)
    report_html = generate_report(edges_info, out_html_path=LAST_REPORT_PATH, out_pdf_path=LAST_REPORT_PDF_PATH)
    return {
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'report_html': report_html,
        'final_plan': final_plan
    }


@app.get('/run_demo')
async def run_demo(sample_minutes: int = 60):
    """Run the pipeline using bundled SAMPLE_TLES (offline). Good for quick local tests without network."""
    G = build_graph_from_tles(SAMPLE_TLES, sample_minutes=sample_minutes, step_min=10, close_threshold_km=50.0)
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

    final_plan = consensus_select(plans)
    report_html = generate_report(edges_info, out_html_path=LAST_REPORT_PATH, out_pdf_path=LAST_REPORT_PDF_PATH)
    return {
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'report_html': report_html,
        'final_plan': final_plan
    }


@app.get('/report')
async def get_report():
    if os.path.exists(LAST_REPORT_PATH):
        return FileResponse(LAST_REPORT_PATH, media_type='text/html', filename='collision_report.html')
    return {'error': 'report not found'}


@app.get('/report.pdf')
async def get_report_pdf():
    if os.path.exists(LAST_REPORT_PDF_PATH):
        return FileResponse(LAST_REPORT_PDF_PATH, media_type='application/pdf', filename='collision_report.pdf')
    # Try to generate from existing HTML if available
    if os.path.exists(LAST_REPORT_PATH):
        try:
            import pdfkit  # requires wkhtmltopdf installed on system
            pdfkit.from_file(LAST_REPORT_PATH, LAST_REPORT_PDF_PATH)
            if os.path.exists(LAST_REPORT_PDF_PATH):
                return FileResponse(LAST_REPORT_PDF_PATH, media_type='application/pdf', filename='collision_report.pdf')
        except Exception as e:
            return {'error': f'pdf generation failed: {e}'}
    return {'error': 'pdf not found'}


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)

