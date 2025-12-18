from fastapi import FastAPI, Query, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import json
import asyncio

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

# Global Memory Storage
LAST_GRAPH = None
LAST_RISKS = None
LAST_SATELLITES = None
LAST_REPORT_PATH = "collision_report.html"

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
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
    """Generator that yields Server-Sent Events for live updates"""
    
    global LAST_GRAPH, LAST_RISKS, LAST_SATELLITES

    try:
        # Validate source
        if source not in TLE_SOURCES:
            yield f"data: {json.dumps({'error': 'Invalid TLE dataset source'})}\n\n"
            return

        yield f"data: {json.dumps({'log': '🚀 Starting pipeline...', 'stage': 'init'})}\n\n"
        await asyncio.sleep(0.1)

        # Load TLEs
        yield f"data: {json.dumps({'log': f'📡 Loading TLE data from {source}...', 'stage': 'loading'})}\n\n"
        await asyncio.sleep(0.2)
        
        tles = load_local_tles(TLE_SOURCES[source])
        if not tles:
            yield f"data: {json.dumps({'error': 'TLE dataset is empty'})}\n\n"
            return

        tles = tles[:40]  # limit for speed
        yield f"data: {json.dumps({'log': f'✅ Loaded {len(tles)} satellites', 'stage': 'loaded'})}\n\n"
        await asyncio.sleep(0.2)

        # MODEL A: Orbit Propagation
        yield f"data: {json.dumps({'log': '🛰️ MODEL A: Starting orbit propagation (SGP4)...', 'stage': 'model_a'})}\n\n"
        await asyncio.sleep(0.3)
        
        G = build_graph_from_tles(
            tles,
            sample_minutes=sample_minutes,
            step_min=10,
            close_threshold_km=20,
        )
        
        yield f"data: {json.dumps({'log': f'✅ MODEL A: Propagated {G.number_of_nodes()} nodes, found {G.number_of_edges()} close approaches', 'stage': 'model_a_complete'})}\n\n"
        await asyncio.sleep(0.2)

        # MODEL B: Risk Scoring
        yield f"data: {json.dumps({'log': '⚠️ MODEL B: Computing heuristic risk scores...', 'stage': 'model_b'})}\n\n"
        await asyncio.sleep(0.3)
        
        heuristic_risk_scores(G)
        
        yield f"data: {json.dumps({'log': '✅ MODEL B: Risk analysis complete', 'stage': 'model_b_complete'})}\n\n"
        await asyncio.sleep(0.2)

        edges_info = []

        # MODEL C: LLM Maneuver Negotiation
        yield f"data: {json.dumps({'log': '🤖 MODEL C: Starting multi-LLM negotiation...', 'stage': 'model_c'})}\n\n"
        await asyncio.sleep(0.3)
        
        for idx, (u, v, data) in enumerate(G.edges(data=True)):
            min_dist = round(data.get("min_distance_km", 0.0), 2)
            risk = round(data.get("risk_score", 0.0), 3)

            yield f"data: {json.dumps({'log': f'  Negotiating {u} ↔ {v} ({min_dist}km, risk={risk})...', 'stage': 'model_c_processing'})}\n\n"
            await asyncio.sleep(0.1)

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
        await asyncio.sleep(0.2)

        # MODEL D: Report Generator
        yield f"data: {json.dumps({'log': '📄 MODEL D: Generating mission report...', 'stage': 'model_d'})}\n\n"
        await asyncio.sleep(0.3)
        
        report_html = generate_llm_mission_report(
            edges_info,
            out_html_path=LAST_REPORT_PATH
        )

        yield f"data: {json.dumps({'log': '✅ MODEL D: Report generated successfully', 'stage': 'model_d_complete'})}\n\n"
        await asyncio.sleep(0.2)

        # Save to global state
        LAST_GRAPH = G
        LAST_RISKS = edges_info
        LAST_SATELLITES = list(G.nodes())

        # Send final summary
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
# STREAMING ENDPOINT
# ============================================================
@app.post("/api/analyze")
async def api_analyze_stream(source: str = "starlink", sample_minutes: int = 120):
    """Streaming endpoint that returns Server-Sent Events"""
    return StreamingResponse(
        pipeline_generator(source, sample_minutes),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# ============================================================
# OTHER API ROUTES (keep as-is)
# ============================================================

@app.get("/api/stats")
async def api_stats():
    global LAST_GRAPH, LAST_RISKS

    if LAST_GRAPH is None:
        return {
            "totalSatellites": 0,
            "closeApproaches": 0,
            "highRiskEvents": 0,
            "lastAnalysis": None
        }

    high_risk = sum(1 for r in LAST_RISKS if r["riskScore"] > 0.7)

    return {
        "totalSatellites": LAST_GRAPH.number_of_nodes(),
        "closeApproaches": LAST_GRAPH.number_of_edges(),
        "highRiskEvents": high_risk,
        "lastAnalysis": "just now"
    }

@app.get("/api/risks")
async def api_risks():
    return {"pairs": LAST_RISKS or []}

@app.get("/api/orbit-graph")
async def api_orbit_graph():
    if LAST_GRAPH is None:
        return {"nodes": [], "edges": []}

    nodes = list(LAST_GRAPH.nodes())
    edges = [
        {
            "source": u,
            "target": v,
            "risk_score": data.get("risk_score", 0)
        }
        for u, v, data in LAST_GRAPH.edges(data=True)
    ]

    return {"nodes": nodes, "edges": edges}

@app.post("/api/upload")
async def api_upload(tle_file: UploadFile = File(...)):
    global LAST_GRAPH, LAST_RISKS, LAST_SATELLITES

    path = os.path.join(DATA_DIR, "uploaded.tle")
    content = await tle_file.read()

    with open(path, "wb") as f:
        f.write(content)

    # 🔥 RE-RUN PIPELINE ON UPLOADED FILE
    tles = load_local_tles("uploaded.tle")
    tles = tles[:40]

    G = build_graph_from_tles(
        tles,
        sample_minutes=120,
        step_min=10,
        close_threshold_km=20,
    )

    heuristic_risk_scores(G)

    edges_info = []
    for u, v, data in G.edges(data=True):
        llm = run_multi_llm_negotiation(u, v, data["min_distance_km"])
        edges_info.append({
            "sat1": u,
            "sat2": v,
            "riskScore": data["risk_score"],
            "maneuver": llm["final_decision"],
        })

    LAST_GRAPH = G
    LAST_RISKS = edges_info
    LAST_SATELLITES = list(G.nodes())

    return {"status": "uploaded_and_processed"}


@app.get("/api/satellites")
async def api_satellites():
    sats = LAST_SATELLITES or []
    return {"satellites": [
        {"name": s, "inclination": 55, "period": 95, "status": "OK"}
        for s in sats
    ]}

@app.post("/api/simulate-maneuver")
async def api_simulate(data: dict):
    return {"new_distance": data["distance"] + 15}

@app.get("/api/report/pdf")
async def api_report_pdf():
    if os.path.exists(LAST_REPORT_PATH):
        return FileResponse(LAST_REPORT_PATH, filename="collision_report.html")
    return {"error": "report not found"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)