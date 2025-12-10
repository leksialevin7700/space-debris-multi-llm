from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
import uvicorn
import os

from app.model_a.orbit_engine import build_graph_from_tles
from app.model_b.risk_predictor import heuristic_risk_scores, explain_edge

# ✅ IMPORT ONLY GEMINI MODELS
from app.model_c.negotiation_planner import run_multi_llm_negotiation
from app.model_d.report_generator import generate_llm_mission_report

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

TLE_SOURCES = {
    "starlink": "starlink.tle",
    "cosmos": "cosmos2251.tle",
    "iridium": "iridium33.tle",
    "active": "active.tle",
}

LAST_REPORT_PATH = "collision_report.html"


# -----------------------------
# Utility: Load Local TLE File
# -----------------------------
def load_local_tles(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
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


# -----------------------------
# ✅ MAIN PIPELINE (FULLY GEMINI)
# -----------------------------
@app.get("/run_pipeline")
async def run_pipeline(
    source: str = Query("starlink", description="starlink | cosmos | iridium | active"),
    sample_minutes: int = 120,
):

    if source not in TLE_SOURCES:
        return {"error": "Invalid source"}

    tles = load_local_tles(TLE_SOURCES[source])

    if not tles:
        return {"error": "No TLEs found"}

    tles = tles[:40]  # performance limit

    # ---------- MODEL A ----------
    G = build_graph_from_tles(
        tles,
        sample_minutes=sample_minutes,
        step_min=10,
        close_threshold_km=20.0,
    )

    # ---------- MODEL B ----------
    heuristic_risk_scores(G)

    edges_info = []

    # ---------- ✅ MODEL C (GEMINI MULTI-LLM) ----------
    for u, v, data in G.edges(data=True):
        explanation = explain_edge(u, v, G)

        min_dist = round(data.get("min_distance_km", 0.0), 2)
        risk_score = round(data.get("risk_score", 0.0), 3)

        llm_result = run_multi_llm_negotiation(u, v, min_dist)

        # Now llm_result includes:
        # - attempts: how many tries the agent made
        # - confidence: final confidence score
        # - all_attempts: history of all attempts (memory!)


        edges_info.append({
            "sat_a": u,
            "sat_b": v,
            "min_distance_km": min_dist,
            "risk_score": risk_score,
            "explanation": explanation,
            "proposal": llm_result["proposal"],
            "critique": llm_result["critique"],
            "final_maneuver": llm_result["final_decision"],
            "agent_attempts": llm_result["attempts"],  # NEW
            "agent_confidence": llm_result["confidence"]  # NEW
        })

    # ---------- ✅ MODEL D (GEMINI REPORT) ----------
    report_html = generate_llm_mission_report(
        edges_info,
        out_html_path=LAST_REPORT_PATH,
    )

    return {
        "dataset": source,
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "report_html": report_html,
    }


# -----------------------------
# ✅ REPORT VIEW
# -----------------------------
@app.get("/report")
async def get_report():
    if os.path.exists(LAST_REPORT_PATH):
        return FileResponse(LAST_REPORT_PATH, media_type="text/html")
    return {"error": "report not found"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
