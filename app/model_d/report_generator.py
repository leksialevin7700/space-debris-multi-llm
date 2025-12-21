import os
import datetime
import mimetypes
from dotenv import load_dotenv
import google.generativeai as genai

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

# FIX for Python 3.12 Windows registry issue
if not mimetypes.inited:
    mimetypes.init()
    mimetypes.add_type("image/webp", ".webp")

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_llm_mission_report(risk_data, out_pdf_path="collision_report.pdf"):
    """
    Generates a mission report using AI and saves it directly to a PDF file.
    Returns: (html_path, pdf_path)
    """
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

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        report_text = response.text

        doc = SimpleDocTemplate(out_pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("AI-Generated Collision Report", styles["Title"]))
        story.append(Spacer(1, 0.25 * inch))

        timestamp = f"Generated at: {datetime.datetime.utcnow():%Y-%m-%d %H:%M:%S} UTC"
        story.append(Paragraph(timestamp, styles["Normal"]))
        story.append(Spacer(1, 0.25 * inch))

        clean_text = report_text.replace("\n", "<br/>")
        story.append(Paragraph(clean_text, styles["Normal"]))

        doc.build(story)
        print(f"✅ PDF saved to {out_pdf_path}")

        return None, out_pdf_path

    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        return None, None
