
import os
import mimetypes
from dotenv import load_dotenv

# FIX for Python 3.12 Windows registry issue
if not mimetypes.inited:
    mimetypes.init()
    mimetypes.add_type("image/webp", ".webp")

load_dotenv()

from google import genai

API_KEY = os.getenv("GEMINI_API_KEY")


def call_adk_model(prompt: str, model: str = "gemini-2.5-flash", max_tokens: int = 512) -> str:
    """
    Wrapper around the Google Generative AI API.
    """
    if not API_KEY:
        return "ERROR: GEMINI_API_KEY not found in environment."

    try:
        client = genai.Client(api_key=API_KEY)
        
        # Generate content
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                max_output_tokens=max_tokens
            )
        )
        return response.text
    except Exception as e:
        return f"GEMINI_CALL_ERROR: {e}"


def llm_propose_maneuver(sat_a: str, sat_b: str, distance_km: float) -> str:
    prompt = f"""
Two satellites ({sat_a} and {sat_b}) will pass within {distance_km:.2f} km.

Propose:
- Which satellite should maneuver
- A simple avoidance action (raise or lower orbit)
- Reason in 2 lines
"""
    return call_adk_model(prompt, model="gemini-2.5-flash")


def llm_critique_maneuver(proposal: str) -> str:
    prompt = f"""
Critique this maneuver:
{proposal}

Check:
- Fuel efficiency
- Safety
- Practicality

Return your critique and a CONFIDENCE score (0-100) at the end.
Format: "CONFIDENCE: XX"
"""
    return call_adk_model(prompt, model="gemini-2.5-flash")


def llm_finalize_maneuver(proposal: str, critique: str) -> str:
    prompt = f"""
Final decision authority.

Proposal:
{proposal}

Critique:
{critique}

Return final approved maneuver in 3 lines only.
"""
    return call_adk_model(prompt, model="gemini-2.5-flash")


# 🤖 NEW: AGENTIC FUNCTION - Agent that self-corrects!
def run_multi_llm_negotiation(sat_a: str, sat_b: str, distance_km: float, max_attempts: int = 3) -> dict:
    """
    AGENTIC BEHAVIOR: Agent will retry if critique confidence is too low
    """

    attempts = []
    best_proposal = None
    best_confidence = 0

    for attempt in range(max_attempts):
        print(f"🤖 Agent Attempt {attempt + 1}/{max_attempts}")

        # Step 1: Propose
        proposal = llm_propose_maneuver(sat_a, sat_b, distance_km)

        # Step 2: Self-critique
        critique = llm_critique_maneuver(proposal)

        # Step 3: Extract confidence (AGENTIC SELF-EVALUATION)
        confidence = extract_confidence(critique)

        attempts.append({
            "attempt": attempt + 1,
            "proposal": proposal,
            "critique": critique,
            "confidence": confidence
        })

        print(f"   Confidence: {confidence}%")

        # AGENTIC DECISION: Keep best proposal
        if confidence > best_confidence:
            best_confidence = confidence
            best_proposal = proposal

        # AGENTIC STOPPING CONDITION: Stop if confident enough
        if confidence >= 80:
            print(f"✅ Agent satisfied with confidence {confidence}%")
            break
        else:
            print(f"⚠️ Confidence too low ({confidence}%), retrying...")

    # Step 4: Finalize best proposal
    final_decision = llm_finalize_maneuver(best_proposal, attempts[-1]["critique"])

    return {
        "proposal": best_proposal,
        "critique": attempts[-1]["critique"],
        "final_decision": final_decision,
        "attempts": len(attempts),
        "confidence": best_confidence,
        "all_attempts": attempts  # Memory of all attempts
    }


def extract_confidence(critique: str) -> int:
    """Extract confidence score from critique text"""
    try:
        # Look for "CONFIDENCE: XX" pattern
        if "CONFIDENCE:" in critique.upper():
            parts = critique.upper().split("CONFIDENCE:")
            confidence_str = parts[1].strip().split()[0]
            return int(confidence_str.replace("%", ""))
        else:
            # Default medium confidence if not found
            return 50
    except:
        return 50


if __name__ == "__main__":
    # quick manual test run (will return placeholders unless ADK is wired in)
    result = run_multi_llm_negotiation("SAT-A", "SAT-B", 0.12, max_attempts=2)
    import pprint; pprint.pprint(result)