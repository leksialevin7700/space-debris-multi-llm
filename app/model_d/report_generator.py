import os
import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from jinja2 import Template

# Load Gemini API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


HTML_TEMPLATE = """
<html>
<head>
    <meta charset='utf-8'>
    <title>Collision Report</title>
</head>
<body>
    <h1>AI-Generated Collision Report</h1>
    <p>Generated at: {{ generated_at }}</p>

    <pre style="white-space: pre-wrap; font-size: 14px; background:#f5f5f5; padding:12px; border-radius:8px;">
{{ report_text }}
    </pre>

</body>
</html>
"""


def generate_llm_mission_report(risk_data, out_html_path="collision_report.html", out_pdf_path=None):
    """
    risk_data example:
    [
      {
        "sat_a": "STARLINK-1011",
        "sat_b": "COSMOS-2251",
        "min_distance_km": 3.4,
        "risk_score": 0.82,
        "explanation": "...",
        "proposal": "...",
        "critique": "...",
        "final_maneuver": "..."
      }
    ]
    """

    prompt = f"""
You are a professional space mission control engineer.

Generate a structured collision mission report using this data:
{risk_data}

The report MUST include:
- Executive Summary
- High Risk Encounters
- Recommended Maneuvers
- Safety Notes

Use clean technical formatting.
"""

    report_text = model.generate_content(prompt).text

    tpl = Template(HTML_TEMPLATE)
    html = tpl.render(
        generated_at=str(datetime.datetime.utcnow()),
        report_text=report_text
    )

    with open(out_html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return out_html_path
