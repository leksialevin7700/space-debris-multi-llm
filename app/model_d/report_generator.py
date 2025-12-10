import os
import datetime
import mimetypes
from dotenv import load_dotenv

# FIX for Python 3.12 Windows registry issue
if not mimetypes.inited:
    mimetypes.init()
    mimetypes.add_type("image/webp", ".webp")

import google.generativeai as genai
from jinja2 import Template

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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

Generate a structured mission report from this data:
{risk_data}

Must include:
- Executive Summary
- High Risk Encounters
- Recommended Maneuvers
- Safety Notes
"""

    model = genai.GenerativeModel("gemini-2.5-flash")  # ✅ Changed from pro to flash
    response = model.generate_content(prompt)

    report_text = response.text

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