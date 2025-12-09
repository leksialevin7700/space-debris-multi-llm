import os
import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from jinja2 import Template

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ THIS IS THE CORRECT MODEL
model = genai.GenerativeModel("gemini-pro")

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

    response = model.generate_content(prompt)
    report_text = response.text

    tpl = Template(HTML_TEMPLATE)
    html = tpl.render(
        generated_at=str(datetime.datetime.utcnow()),
        report_text=report_text
    )

    with open(out_html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return out_html_path
