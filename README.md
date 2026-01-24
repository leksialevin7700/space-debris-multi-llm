
#  Multi-LLM Space Debris Intelligence & Maneuver Planning System


[![Project Blog](https://img.shields.io/badge/Project-Blog-blue)](https://wonderful-trifle-67e81d.netlify.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI-powered platform designed to predict, negotiate, and avoid satellite collisions. It combines orbital mechanics (SGP4) with multi-agent LLMs to generate real-time risk assessments and maneuver plans.

##  Key Features

| Component | Description |
| :--- | :--- |
| **Orbit Intelligence (Model-A)** | Propagates orbits using **SGP4** and builds a semantic graph of satellites. |
| **Risk Predictor (Model-B)** | Computes collision risk scores based on distance thresholds and traffic density. |
| **LLM Maneuver Agent (Model-C)** | An agentic LLM that **proposes and critiques** avoidance maneuvers. |
| **Mission Reports (Model-D)** | Auto-generates **PDF reports** summarizing risks and recommendations. |
| **Interactive Dashboard** | A Next.js frontend for visualizing orbits, uploading TLEs, and viewing reports. |

---

## Installation

### 1. Clone the Repository
```bash
git clone git@github.com:leksialevin7700/space-debris-multi-llm.git
cd space-debris-multi-llm
```

### 2. Backend Setup (Python)
```bash
# Create virtual environment
python -m venv venv
#macOS
source venv/bin/activate
# Windows
venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
```
### 3. Frontend Setup (Next.js)
```bash
cd frontend
npm install
# or
yarn install
```

### 4. Configuration
Create a .env file in the root directory to configure your LLM keys and settings:

```ini
# .env example
GOOGLE_API_KEY=your_gemini_key_here
PORT=8000
```

## Usage
Start the Backend API
```bash
# From the root directory
uvicorn app.api.main:app --reload
# The API will run at http://127.0.0.1:8000
```
Start the Frontend Dashboard
```bash
# From the frontend directory
npm run dev
# Open http://localhost:3000 to view the Orbital Guardian Dashboard
```

#### CLI Mode (Maneuver Agent)
You can also run the maneuver agent directly from the command line:
```bash
python main.py SAT-A SAT-B --distance-km 0.12 --format yaml -o out.yaml
```

#### Docker Support
You can run the entire stack using Docker.

Build & Run
```bash
docker build -t orbital-guardian:latest .
docker run --rm --env-file .env -p 8000:8000 orbital-guardian:latest
```

