import os
import datetime
from dotenv import load_dotenv
from openai import OpenAI
from jinja2 import Template

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

HTML_TEMPLATE = """
<html>
<head><meta charset='utf-8'><title>Collision Report</title></head>
<body>
<h1>AI-Generated Collision Report</h1>
<p>Generated at: {{ generated_at }}</p>

<pre style="white-space: pre-wrap; font-size: 14px;">
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
        "final_maneuver": "Raise STARLINK-1011 orbit by 1 km"
      }
    ]
    """

    prompt = f"""
You are a professional space mission control engineer.

Generate a structured collision mission report using this data:
{risk_data}

Must include:
- Executive Summary
- High Risk Encounters
- Recommended Maneuvers
- Safety Notes
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    report_text = response.choices[0].message.content

    tpl = Template(HTML_TEMPLATE)
    html = tpl.render(
        generated_at=str(datetime.datetime.utcnow()),
        report_text=report_text
    )

    with open(out_html_path, "w", encoding="utf-8") as f:
        f.write(html)

    if out_pdf_path:
        try:
            import pdfkit
            pdfkit.from_file(out_html_path, out_pdf_path)
        except Exception as e:
            print("PDF conversion failed:", e)

    return out_html_path
