import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-pro")


def llm_propose_maneuver(sat_a: str, sat_b: str, distance_km: float) -> str:
    prompt = f"""
Two satellites ({sat_a} and {sat_b}) will pass within {distance_km:.2f} km.

Propose:
- Which satellite should maneuver
- Raise or lower orbit
- Short reasoning
"""
    return model.generate_content(prompt).text


def llm_critique_maneuver(proposal: str) -> str:
    prompt = f"""
Critique this maneuver based on:
- Fuel efficiency
- Safety
- Practical feasibility

Plan:
{proposal}
"""
    return model.generate_content(prompt).text


def llm_finalize_maneuver(proposal: str, critique: str) -> str:
    prompt = f"""
Final decision authority:

Proposal:
{proposal}

Critique:
{critique}

Return final approved maneuver in 3 lines.
"""
    return model.generate_content(prompt).text


def run_multi_llm_negotiation(sat_a, sat_b, distance_km):
    proposal = llm_propose_maneuver(sat_a, sat_b, distance_km)
    critique = llm_critique_maneuver(proposal)
    final_decision = llm_finalize_maneuver(proposal, critique)

    return {
        "proposal": proposal,
        "critique": critique,
        "final_decision": final_decision
    }
