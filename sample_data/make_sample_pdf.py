"""Generates sample_data/sample_resume.pdf from sample_resume.txt
so Day 1's extraction script has a real PDF to test against.
Not part of the actual product — just test fixture setup.
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

with open("sample_data/sample_resume.txt") as f:
    lines = f.read().split("\n")

doc = SimpleDocTemplate("sample_data/sample_resume.pdf", pagesize=letter,
                         topMargin=0.6*inch, bottomMargin=0.6*inch)
styles = getSampleStyleSheet()
normal = ParagraphStyle('normal', parent=styles['Normal'], fontSize=10, leading=13)
heading = ParagraphStyle('heading', parent=styles['Normal'], fontSize=11, leading=14, spaceBefore=8, spaceAfter=2)
name_style = ParagraphStyle('name', parent=styles['Normal'], fontSize=16, leading=20)

story = []
for i, line in enumerate(lines):
    line = line.strip()
    if not line:
        story.append(Spacer(1, 4))
        continue
    if i == 0:
        story.append(Paragraph(line, name_style))
    elif line.isupper() and len(line.split()) <= 4:
        story.append(Paragraph(f"<b>{line}</b>", heading))
    else:
        story.append(Paragraph(line.replace("&", "&amp;"), normal))

doc.build(story)
print("Generated sample_data/sample_resume.pdf")