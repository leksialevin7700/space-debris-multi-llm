import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load Gemini API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use fast, free-tier friendly model
model = genai.GenerativeModel("gemini-1.5-flash")


# -----------------------------
# LLM 1: Proposal Agent
# -----------------------------
def llm_propose_maneuver(sat_a: str, sat_b: str, distance_km: float) -> str:
    prompt = f"""
Two satellites ({sat_a} and {sat_b}) will pass within {distance_km:.2f} km.

Propose:
- Which satellite should maneuver
- A simple avoidance action (raise or lower orbit)
- Reason in 2 short lines
"""
    return model.generate_content(prompt).text


# -----------------------------
# LLM 2: Critic Agent
# -----------------------------
def llm_critique_maneuver(proposal: str) -> str:
    prompt = f"""
Critique the following satellite maneuver for:
- Fuel efficiency
- Safety
- Practical feasibility

Plan:
{proposal}
"""
    return model.generate_content(prompt).text


# -----------------------------
# LLM 3: Final Decision Agent
# -----------------------------
def llm_finalize_maneuver(proposal: str, critique: str) -> str:
    prompt = f"""
You are the final decision authority.

Proposal:
{proposal}

Critique:
{critique}

Return ONLY the final approved maneuver in 3 lines.
"""
    return model.generate_content(prompt).text


# -----------------------------
# FULL MULTI-LLM PIPELINE
# -----------------------------
def run_multi_llm_negotiation(sat_a: str, sat_b: str, distance_km: float) -> dict:
    proposal = llm_propose_maneuver(sat_a, sat_b, distance_km)
    critique = llm_critique_maneuver(proposal)
    final_decision = llm_finalize_maneuver(proposal, critique)

    return {
        "proposal": proposal.strip(),
        "critique": critique.strip(),
        "final_decision": final_decision.strip()
    }
