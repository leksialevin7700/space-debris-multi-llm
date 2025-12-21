from fastapi import FastAPI, Query, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import json
import asyncio
import datetime

# Import your model files
from app.model_a.orbit_engine import build_graph_from_tles
from app.model_b.risk_predictor import heuristic_risk_scores, explain_edge
from app.model_c.negotiation_planner import run_multi_llm_negotiation
from app.model_d.report_generator import generate_llm_mission_report

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# GLOBAL STORAGE & CONFIG
# ============================================================
LAST_GRAPH = None
LAST_RISKS = None
LAST_SATELLITES = None

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LAST_REPORT_PATH = os.path.join(BASE_DIR, "collision_report.pdf")

DATA_DIR = os.path.join(BASE_DIR, "data")

TLE_SOURCES = {
    "starlink": "starlink.tle",
    "cosmos": "cosmos2251.tle",
    "iridium": "iridium33.tle",
    "active": "active.tle",
}

def load_local_tles(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print("TLE file not found:", path)
        return []

    tles = []
    with open(path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    i = 0
    while i + 2 < len(lines):
        name = lines[i]
        l1 = lines[i + 1]
        l2 = lines[i + 2]
        tles.append((name, l1, l2))
        i += 3
    return tles

# ============================================================
# STREAMING GENERATOR FUNCTION
# ============================================================
async def pipeline_generator(source: str, sample_minutes: int):
    global LAST_GRAPH, LAST_RISKS, LAST_SATELLITES

    try:
        if source not in TLE_SOURCES:
            yield f"data: {json.dumps({'error': 'Invalid TLE dataset source'})}\n\n"
            return

        yield f"data: {json.dumps({'log': '🚀 Starting pipeline...', 'stage': 'init'})}\n\n"
        await asyncio.sleep(0.1)

        # Load TLEs
        yield f"data: {json.dumps({'log': f'📡 Loading TLE data from {source}...', 'stage': 'loading'})}\n\n"
        tles = load_local_tles(TLE_SOURCES[source])
        if not tles:
            yield f"data: {json.dumps({'error': 'TLE dataset is empty'})}\n\n"
            return

        tles = tles[:40]
        yield f"data: {json.dumps({'log': f'✅ Loaded {len(tles)} satellites', 'stage': 'loaded'})}\n\n"
        await asyncio.sleep(0.2)

        # MODEL A
        yield f"data: {json.dumps({'log': '🛰️ MODEL A: Starting orbit propagation (SGP4)...', 'stage': 'model_a'})}\n\n"
        G = build_graph_from_tles(
            tles,
            sample_minutes=sample_minutes,
            step_min=10,
            close_threshold_km=20,
        )
        yield f"data: {json.dumps({'log': f'✅ MODEL A: Found {G.number_of_edges()} close approaches', 'stage': 'model_a_complete'})}\n\n"
        await asyncio.sleep(0.2)

        # MODEL B
        yield f"data: {json.dumps({'log': '⚠️ MODEL B: Computing heuristic risk scores...', 'stage': 'model_b'})}\n\n"
        heuristic_risk_scores(G)
        yield f"data: {json.dumps({'log': '✅ MODEL B: Risk analysis complete', 'stage': 'model_b_complete'})}\n\n"

        edges_info = []

        # MODEL C
        yield f"data: {json.dumps({'log': '🤖 MODEL C: Starting multi-LLM negotiation...', 'stage': 'model_c'})}\n\n"
        for u, v, data in G.edges(data=True):
            min_dist = round(data.get("min_distance_km", 0.0), 2)
            risk = round(data.get("risk_score", 0.0), 3)

            yield f"data: {json.dumps({'log': f'  Negotiating {u} ↔ {v}...', 'stage': 'model_c_processing'})}\n\n"
            await asyncio.sleep(0.05)

            explanation = explain_edge(u, v, G)
            llm = run_multi_llm_negotiation(u, v, min_dist)

            edges_info.append({
                "sat1": u,
                "sat2": v,
                "minDistance": min_dist,
                "riskScore": risk,
                "severity": "high" if risk > 0.7 else "medium" if risk > 0.4 else "low",
                "description": explanation,
                "maneuver": llm["final_decision"],
                "proposal": llm["proposal"],
                "critique": llm["critique"],
            })

        yield f"data: {json.dumps({'log': f'✅ MODEL C: Negotiated {len(edges_info)} maneuvers', 'stage': 'model_c_complete'})}\n\n"

        # MODEL D
        yield f"data: {json.dumps({'log': '📄 MODEL D: Generating PDF mission report...', 'stage': 'model_d'})}\n\n"
        _, pdf_path = generate_llm_mission_report(
            edges_info,
            out_pdf_path=LAST_REPORT_PATH
        )

        if pdf_path:
            yield f"data: {json.dumps({'log': '✅ MODEL D: PDF generated successfully', 'stage': 'model_d_complete'})}\n\n"
        else:
            yield f"data: {json.dumps({'log': '❌ MODEL D: PDF generation failed', 'stage': 'model_d_error'})}\n\n"

        LAST_GRAPH = G
        LAST_RISKS = edges_info
        LAST_SATELLITES = list(G.nodes())

        summary = {
            "log": "🎉 Pipeline complete!",
            "stage": "complete",
            "summary": {
                "dataset": source,
                "num_nodes": G.number_of_nodes(),
                "num_edges": G.number_of_edges(),
                "high_risk": sum(1 for r in edges_info if r["riskScore"] > 0.7)
            }
        }
        yield f"data: {json.dumps(summary)}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e), 'stage': 'error'})}\n\n"

# ============================================================
# API ROUTES
# ============================================================

@app.post("/api/analyze")
async def api_analyze_stream(source: str = "starlink", sample_minutes: int = 120):
    return StreamingResponse(
        pipeline_generator(source, sample_minutes),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/api/report/pdf")
async def api_report_pdf():
    print("Checking PDF at:", LAST_REPORT_PATH)

    if os.path.exists(LAST_REPORT_PATH):
        return FileResponse(
            LAST_REPORT_PATH,
            media_type="application/pdf",
            filename="collision_report.pdf",
        )

    return JSONResponse(
        status_code=404,
        content={"error": "PDF not generated yet"}
    )

@app.get("/api/stats")
async def api_stats():
    if LAST_GRAPH is None:
        return {"totalSatellites": 0, "closeApproaches": 0, "highRiskEvents": 0}
    
    high_risk = sum(1 for r in LAST_RISKS if r["riskScore"] > 0.7)
    return {
        "totalSatellites": LAST_GRAPH.number_of_nodes(),
        "closeApproaches": LAST_GRAPH.number_of_edges(),
        "highRiskEvents": high_risk
    }

@app.get("/api/risks")
async def api_risks():
    return {"pairs": LAST_RISKS or []}

@app.get("/api/orbit-graph")
async def api_orbit_graph():
    if LAST_GRAPH is None:
        return {"nodes": [], "edges": []}
    return {
        "nodes": list(LAST_GRAPH.nodes()),
        "edges": [{"source": u, "target": v, "risk_score": d.get("risk_score", 0)} 
                  for u, v, d in LAST_GRAPH.edges(data=True)]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
