import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def llm_propose_maneuver(sat_a: str, sat_b: str, distance_km: float) -> str:
    prompt = f"""
Two satellites ({sat_a} and {sat_b}) will pass within {distance_km:.2f} km.

Propose:
- Which satellite should maneuver
- A simple avoidance action (raise or lower orbit)
- Reason in 2 lines
"""
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )
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
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )
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
    response = client.models.generate_content(
        model="gemini-1.5-pro",
        contents=prompt,
    )
    return response.text
