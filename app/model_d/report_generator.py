
# -----------------------------
# File: app/model_d/report_generator.py
# -----------------------------
"""
Model D: Mission Report Generator
- Renders a simple HTML report using Jinja2.
- PDF export is optional and attempted only if `pdfkit` is available; failures are caught.
"""
from jinja2 import Template
import datetime

REPORT_TEMPLATE = """
<html>
<head><meta charset='utf-8'><title>Collision Report</title></head>
<body>
<h1>Collision Report</h1>
<p>Generated at: {{ generated_at }}</p>
{% if edges|length == 0 %}
  <p>No close approaches detected for the provided inputs.</p>
{% endif %}
{% for edge in edges %}
  <div style='border:1px solid #ddd;padding:8px;margin:8px;'>
    <h2>{{ edge.u }} — {{ edge.v }}</h2>
    <p>Min distance: {{ edge.min_distance_km }} km</p>
    <p>Risk score: {{ edge.risk_score }}</p>
    <p>Explanation: {{ edge.explanation }}</p>
    <p>Recommended maneuver: mover={{ edge.plan.mover }}, delta-v={{ edge.plan.delta_v_km_s }} km/s</p>
  </div>
{% endfor %}
</body>
</html>
"""


def generate_report(edges_info, out_html_path='/tmp/collision_report.html', out_pdf_path=None):
    tpl = Template(REPORT_TEMPLATE)
    html = tpl.render(generated_at=str(datetime.datetime.utcnow()), edges=edges_info)
    with open(out_html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    if out_pdf_path:
        try:
            import pdfkit
            pdfkit.from_file(out_html_path, out_pdf_path)
        except Exception as e:
            print('PDF conversion failed or pdfkit not available:', e)
    return out_html_path