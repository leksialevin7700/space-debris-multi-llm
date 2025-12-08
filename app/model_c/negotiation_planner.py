import os
from dotenv import load_dotenv
from openai import OpenAI

# Load API key from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------------
# LLM 1: Proposal Agent
# -----------------------------
def llm_propose_maneuver(sat_a: str, sat_b: str, distance_km: float) -> str:
    prompt = f"""
Two satellites ({sat_a} and {sat_b}) will pass within {distance_km:.2f} km.

Propose:
- Which satellite should maneuver
- A simple avoidance action (raise or lower orbit)
- Reason in 2 lines
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content


# -----------------------------
# LLM 2: Critic Agent
# -----------------------------
def llm_critique_maneuver(proposal: str) -> str:
    prompt = f"""
Critique the following satellite maneuver plan for:
- Fuel efficiency
- Safety
- Practicality

Plan:
{proposal}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content


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

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content


# -----------------------------
# FULL MULTI-LLM PIPELINE
# -----------------------------
def run_multi_llm_negotiation(sat_a: str, sat_b: str, distance_km: float) -> dict:
    proposal = llm_propose_maneuver(sat_a, sat_b, distance_km)
    critique = llm_critique_maneuver(proposal)
    final_decision = llm_finalize_maneuver(proposal, critique)

    return {
        "proposal": proposal,
        "critique": critique,
        "final_decision": final_decision
    }
