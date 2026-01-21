## 🌐 Project Blog / Website

📖 Read the detailed project blog here:  [![Project Blog](https://img.shields.io/badge/Project-Blog-blue)](https://wonderful-trifle-67e81d.netlify.app/)

### **Multi-LLM Space Debris Intelligence & Maneuver Planning System**

##  Key Features

| Component                                   | Description                                                                                                                                      |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
|  **Orbit Intelligence Engine (Model-A)** | Fetches real TLE data, propagates orbits using **SGP4**, and builds a **semantic graph** of satellites & debris with potential conjunction edges |
|  **Collision Risk Predictor (Model-B)**   | Computes heuristic collision risk scores using **distance thresholds** and **orbital traffic density** (GNN-ready design)                        |
|  **LLM Maneuver Agent (Model-C)**         | Agentic LLM system that **proposes, self-critiques, retries, and finalizes** collision-avoidance maneuvers with confidence scoring               |
|  **Agentic Reasoning Loop**               | Confidence-based retry mechanism ensures higher-quality decisions                                                                                |
|  **Mission Report Generation (Model-D)**   | Auto-generates **PDF mission reports** summarizing risks, explanations, and maneuver recommendations                                        |
|  **FastAPI Backend**                       | Production-ready APIs for running pipelines and fetching reports                                                                                 |
| 🐳 **Dockerized Deployment**                | CLI + Web + Compose support                                                                                                                      |

---




##  Model-C: LLM Maneuver Agent (Agentic Core)

> **Replaces traditional heuristic planners with an autonomous AI decision-maker**

###  What Makes It Unique?

* **LLM-agnostic** via adapter (`call_adk_model`)
* Works with **any ADK-compatible LLM**
* Implements an **Agentic Workflow**:

#### 🔁 Agent Loop

**Propose → Self-Critique → Decide → Finalize**

#### Decision Logic

* If **confidence ≥ 80%** → finalize maneuver
* If confidence < threshold → retry with improved reasoning
* Otherwise → finalize best available proposal

---

### Output Schema

```json
{
  "final_decision": "Concise approved maneuver (≤ 3 lines)",
  "proposal": "Initial maneuver proposal",
  "critique": "Self-critique with CONFIDENCE score",
  "confidence": 87,
  "attempts": 2,
  "all_attempts": [
    {"proposal": "...", "confidence": 62},
    {"proposal": "...", "confidence": 87}
  ]
}
```

This structure is **log-ready**, **audit-friendly**, and **pipeline-integratable**.



---

---

##  Installation

```bash
git clone git@github.com:leksialevin7700/space-debris-multi-llm.git
cd space-debris-multi-llm

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

---

##  Usage

### 🔹 Offline Demo

```bash
python run.py
```

Generates a sample collision report using bundled TLE data.

---

### 🔹 API Mode

```bash
uvicorn app.api.main:app --reload
```


##  Maneuver Agent – CLI Usage

```bash
python main.py SAT-A SAT-B --distance-km 0.12 --format yaml -o out.yaml
```

---

##  Maneuver Agent – Web API

```bash
python main.py --start-web --host 0.0.0.0 --port 8000
```

Example request:

```bash
curl -X POST http://localhost:8000/negotiate \
  -H "Content-Type: application/json" \
  -d '{"sat_a":"SAT-A","sat_b":"SAT-B","distance_km":0.12}'
```

---

## 🐳 Docker Support

### Build

```bash
docker build -t orbital-guardian:latest .
```

### Run (Web)

```bash
docker run --rm --env-file .env -p 8000:8000 \
  orbital-guardian:latest
```

---

##  Future Enhancements

* Graph Neural Networks (GNNs) for collision risk prediction
* Multi-agent LLM negotiation between satellite operators
* Real-time TLE streaming
* 3D orbital visualization using **React + Three.js**
* Interplanetary debris modeling

---
## Under Development

## 📜 License

MIT License

---
