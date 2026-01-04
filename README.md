# Orbital Guardian – Multi‑LLM Space Debris Intelligence System

## Overview

A multi-LLM, physics-augmented system designed to predict and mitigate satellite–debris collisions in Low Earth Orbit (LEO). This project integrates orbital mechanics with AI heuristics and LLM-based explanations to provide early warnings, risk assessment, and recommended avoidance maneuvers.


## Features

| Component                               | Description                                                                                                                                                                                                  |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Orbit Intelligence Engine (Model A)     | Fetches Two-Line Element (TLE) data from public sources, propagates satellite orbits using sgp4, and constructs a semantic graph of satellites and debris (nodes = objects, edges = potential conjunctions). |
| Collision Risk Predictor (Model B)      | Uses graph heuristics (placeholder for GNN) to compute risk scores for each potential collision and provides textual explanations.                                                                           |
| Multi-LLM Negotiation Planner (Model C) | Proposes optimal avoidance maneuvers based on satellite traffic, delta-v minimization, and collision risk.                                                                                                   |
| Mission Report Generator (Model D)      | Generates detailed HTML/PDF reports for engineers and mission control, summarizing collision risks and recommended maneuvers.                                                                                |
| FastAPI backend                         | API endpoints for running the full pipeline (/run_pipeline) and fetching reports (/report).                        

## Technical Implementation

### Model A: Orbit Intelligence Engines

* Fetches TLEs from Celestrak URLs.
* Converts TLEs to `Satrec` objects from `sgp4`.
* Propagates satellite positions over time.
* Builds a NetworkX semantic graph where:

  * Nodes represent satellites with TLE attributes.
  * Edges represent potential close approaches, storing minimum distance.

### Model B: Collision Risk Predictor

* Computes a heuristic risk score per edge based on:

  * Minimum distance between satellites.
  * Node degree (satellite traffic).
* Generates textual explanations for each edge.
* Placeholder for future Graph Neural Network integration.

### Model C: Multi-LLM Negotiation Planner

* Simplified prototype uses heuristic to select satellite for maneuver based on traffic degree and distance.
* Computes recommended delta-v to avoid collisions.
* Consensus module picks the maneuver with the lowest delta-v.

### Model D: Mission Report Generator

* Uses Jinja2 templates to create an HTML report.
* Optional PDF generation via `pdfkit`.
* Includes all edges with risk scores, explanations, and maneuver recommendations.
# Space Debris AI System Architecture

This diagram illustrates the architecture of the AI system for predicting space debris collisions:

<img width="512" height="768" alt="image" src="https://github.com/user-attachments/assets/4f5d19cd-9695-4d28-9328-06b4eebd7691" />

## Installation

```bash
# Clone repository
git clone <git@github.com:leksialevin7700/space-debris-multi-llm.git>
cd space-debris-multi-llm

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Offline Demo

```bash
python run.py
```

Generates a sample collision report using bundled TLE data.

### API Mode

```bash
uvicorn app.api.main:app --reload
```

* Run full pipeline: `http://localhost:8000/run_pipeline`
* Fetch report: `http://localhost:8000/report`

## Future Enhancements

* Replace heuristic risk scoring with a trained Graph Neural Network.
* Integrate LLM agents for dynamic negotiation and explanation.
* Interactive visualization dashboard using React/Three.js.
* Support for live TLE streams and interplanetary debris prediction.

## License

MIT License
