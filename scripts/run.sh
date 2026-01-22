#!/usr/bin/env bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py SAT-A SAT-B --distance-km 0.12 --format yaml --verbose