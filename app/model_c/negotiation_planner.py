import os
import mimetypes
from dotenv import load_dotenv

# FIX for Python 3.12 Windows registry issue
if not mimetypes.inited:
    mimetypes.init()
    mimetypes.add_type("image/webp", ".webp")

import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def llm_propose_maneuver(sat_a: str, sat_b: str, distance_km: float) -> str:
    prompt = f"""
Two satellites ({sat_a} and {sat_b}) will pass within {distance_km:.2f} km.

Propose:
- Which satellite should maneuver
- A simple avoidance action (raise or lower orbit)
- Reason in 2 lines
"""
    model = genai.GenerativeModel("gemini-2.5-flash")  # ✅ Using available model
    response = model.generate_content(prompt)
    return response.text


def llm_critique_maneuver(proposal: str) -> str:
    prompt = f"""
Critique this maneuver:
{proposal}

Check:
- Fuel efficiency
- Safety
- Practicality
"""
    model = genai.GenerativeModel("gemini-2.5-flash")  # ✅ Using available model
    response = model.generate_content(prompt)
    return response.text


def llm_finalize_maneuver(proposal: str, critique: str) -> str:
    prompt = f"""
Final decision authority.

Proposal:
{proposal}

Critique:
{critique}

Return final approved maneuver in 3 lines only.
"""
    model = genai.GenerativeModel("gemini-2.5-pro")  # ✅ Using Pro for final decision
    response = model.generate_content(prompt)
    return response.text


def run_multi_llm_negotiation(sat_a: str, sat_b: str, distance_km: float) -> dict:
    proposal = llm_propose_maneuver(sat_a, sat_b, distance_km)
    critique = llm_critique_maneuver(proposal)
    final_decision = llm_finalize_maneuver(proposal, critique)

    return {
        "proposal": proposal,
        "critique": critique,
        "final_decision": final_decision
    }