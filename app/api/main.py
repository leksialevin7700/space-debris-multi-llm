from fastapi import FastAPI, Query, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# -----------------------
# Import your model files
# -----------------------
from app.model_a.orbit_engine import build_graph_from_tles
from app.model_b.risk_predictor import heuristic_risk_scores, explain_edge
from app.model_c.negotiation_planner import run_multi_llm_negotiation
from app.model_d.report_generator import generate_llm_mission_report

# FastAPI App
app = FastAPI()

# Allow frontend (localhost:3000 or 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Global Memory Storage
# -----------------------
LAST_GRAPH = None
LAST_RISKS = None
LAST_SATELLITES = None
LAST_REPORT_PATH = "collision_report.html"

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Supported TLE Sources
TLE_SOURCES = {
    "starlink": "starlink.tle",
    "cosmos": "cosmos2251.tle",
    "iridium": "iridium33.tle",
    "active": "active.tle",
}


# -----------------------
# Utility: Load TLE Files
# -----------------------
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
# 🚀 MAIN PIPELINE ENDPOINT (Models A → B → C → D)
# ============================================================
@app.get("/run_pipeline")
async def run_pipeline(
    source: str = Query("starlink"),
    sample_minutes: int = 120,
):
    global LAST_GRAPH, LAST_RISKS, LAST_SATELLITES

    if source not in TLE_SOURCES:
        return {"error": "Invalid TLE dataset source"}

    # Load TLEs
    tles = load_local_tles(TLE_SOURCES[source])
    if not tles:
        return {"error": "TLE dataset is empty"}

    tles = tles[:40]  # limit for speed

    # ---- MODEL A: Orbit Propagation ----
    G = build_graph_from_tles(
        tles,
        sample_minutes=sample_minutes,
        step_min=10,
        close_threshold_km=20,
    )

    # ---- MODEL B: Risk Scoring ----
    heuristic_risk_scores(G)

    edges_info = []

    # ---- MODEL C: LLM Maneuver Negotiation ----
    for u, v, data in G.edges(data=True):
        min_dist = round(data.get("min_distance_km", 0.0), 2)
        risk = round(data.get("risk_score", 0.0), 3)

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

    # ---- MODEL D: Report Generator ----
    report_html = generate_llm_mission_report(
        edges_info,
        out_html_path=LAST_REPORT_PATH
    )

    # Save graph for API routes
    LAST_GRAPH = G
    LAST_RISKS = edges_info
    LAST_SATELLITES = list(G.nodes())

    return {
        "dataset": source,
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "edges_info": edges_info,
        "report_html": report_html,
    }


# ============================================================
# 🌐 API ROUTES USED BY YOUR NEXT.JS FRONTEND
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
    path = os.path.join(DATA_DIR, "uploaded.tle")
    content = await tle_file.read()

    with open(path, "wb") as f:
        f.write(content)

    return {"status": "uploaded"}


@app.post("/api/analyze")
async def api_analyze():
    """Trigger a new analysis using the default dataset."""
    await run_pipeline(source="starlink")
    return {"status": "analysis_complete"}


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


# --------------------------
# Run Local Server
# --------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
