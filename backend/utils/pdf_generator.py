import io
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def clean_markdown_for_paragraph(text: str) -> str:
    """
    Converts simple markdown syntax (headers, bold, lists) into ReportLab Paragraph XML tags.
    """
    if not text:
        return ""
    
    # Replace markdown headers with bold text and line breaks
    text = re.sub(r'^###\s+(.*?)$', r'<br/><b>\1</b><br/>', text, flags=re.MULTILINE)
    text = re.sub(r'^##\s+(.*?)$', r'<br/><b>\1</b><br/>', text, flags=re.MULTILINE)
    text = re.sub(r'^#\s+(.*?)$', r'<br/><font size="14"><b>\1</b></font><br/>', text, flags=re.MULTILINE)
    
    # Replace bold syntax **text** with <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # Replace bullet points
    text = re.sub(r'^\*\s+(.*?)$', r'&bull; \1', text, flags=re.MULTILINE)
    text = re.sub(r'^-\s+(.*?)$', r'&bull; \1', text, flags=re.MULTILINE)
    
    # Clean up any Github callouts like > [!IMPORTANT]
    text = re.sub(r'^>\s+\[!(IMPORTANT|WARNING|CAUTION|NOTE|TIP)\]', r'<b>\1:</b>', text, flags=re.MULTILINE)
    text = re.sub(r'^>\s+(.*?)$', r'<i>\1</i>', text, flags=re.MULTILINE)
    
    # Convert newlines to breaks
    text = text.replace('\n', '<br/>')
    
    # Clean up double line breaks
    text = re.sub(r'(<br/>){3,}', '<br/><br/>', text)
    
    return text

def generate_pdf_report(user_name: str, date_str: str, symptoms: list[str], predictions: list[dict], risk_score: int, ai_explanation: str) -> io.BytesIO:
    """
    Generates a professional medical recommendation report in PDF format and returns a BytesIO buffer.
    """
    buffer = io.BytesIO()
    
    # Define document layout
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    primary_color = colors.HexColor("#0284c7")  # Light Blue / Sky
    secondary_color = colors.HexColor("#16a34a")  # Soft Green
    text_color = colors.HexColor("#1f2937")  # Charcoal
    
    # Update default styles
    styles['Normal'].textColor = text_color
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 14
    
    # Define custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=15
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=15,
        spaceAfter=8,
        keepWithNext=True
    )
    
    meta_label_style = ParagraphStyle(
        'MetaLabel',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#4b5563")
    )
    
    meta_val_style = ParagraphStyle(
        'MetaVal',
        fontName='Helvetica',
        fontSize=10,
        leading=12,
        textColor=text_color
    )
    
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#9ca3af"),
        alignment=1  # Centered
    )
    
    story = []
    
    # 1. Header Banner
    banner_data = [
        [
            Paragraph("HealthSenseAI", title_style),
            Paragraph("Health Recommendation Report", ParagraphStyle('SubTitle', fontName='Helvetica-Bold', fontSize=10, leading=12, textColor=colors.HexColor("#6b7280"), alignment=2))
        ]
    ]
    banner_table = Table(banner_data, colWidths=[3.5*inch, 3.5*inch])
    banner_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, -1), 1, primary_color)
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 15))
    
    # 2. Metadata Section (Patient Name, Date)
    meta_data = [
        [Paragraph("Patient Name:", meta_label_style), Paragraph(user_name, meta_val_style), 
         Paragraph("Report Date:", meta_label_style), Paragraph(date_str, meta_val_style)],
        [Paragraph("Report ID:", meta_label_style), Paragraph(f"HS-{datetime.now().strftime('%Y%m%d%H%M%S')}", meta_val_style), 
         Paragraph("Access:", meta_label_style), Paragraph("Confidential / Educational Only", meta_val_style)]
    ]
    meta_table = Table(meta_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 2.3*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0"))
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # 3. Symptoms Entered
    story.append(Paragraph("Symptoms Evaluated", section_heading))
    symptoms_text = ", ".join([s.replace('_', ' ').title() for s in symptoms])
    story.append(Paragraph(symptoms_text, styles['Normal']))
    story.append(Spacer(1, 15))
    
    # 4. Predictions & Confidence Scores
    story.append(Paragraph("Machine Learning Disease Predictions", section_heading))
    
    table_content = [[
        Paragraph("<b>Probable Condition</b>", ParagraphStyle('Th', fontName='Helvetica-Bold', fontSize=10, leading=12)),
        Paragraph("<b>Confidence Level</b>", ParagraphStyle('Th', fontName='Helvetica-Bold', fontSize=10, leading=12, alignment=1))
    ]]
    
    for idx, pred in enumerate(predictions):
        disease = pred["disease"]
        conf = f"{pred['confidence']}%"
        # Color top prediction
        bg_col = colors.HexColor("#f0fdf4") if idx == 0 else colors.white
        table_content.append([
            Paragraph(f"<b>{idx+1}. {disease}</b>" if idx == 0 else f"{idx+1}. {disease}", styles['Normal']),
            Paragraph(conf, ParagraphStyle('Tc', fontName='Helvetica-Bold' if idx == 0 else 'Helvetica', fontSize=10, leading=12, alignment=1))
        ])
        
    pred_table = Table(table_content, colWidths=[4.5*inch, 2.5*inch])
    pred_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#eff6ff")), # Top prediction highlighted in soft blue
    ]))
    story.append(pred_table)
    story.append(Spacer(1, 15))
    
    # 5. Risk Score
    story.append(Paragraph("Calculated Health Risk Level", section_heading))
    
    if risk_score <= 30:
        risk_label = "LOW RISK"
        risk_color_hex = "#16a34a" # Green
        risk_explanation = f"Your score of {risk_score}/100 indicates a low likelihood of a severe or urgent medical condition. Home care and standard precautions are likely appropriate."
    elif risk_score <= 70:
        risk_label = "MODERATE RISK"
        risk_color_hex = "#ea580c" # Orange
        risk_explanation = f"Your score of {risk_score}/100 suggests moderate symptoms or risk factors. You should monitor your symptoms closely and consider contacting a health professional for advice."
    else:
        risk_label = "HIGH RISK"
        risk_color_hex = "#dc2626" # Red
        risk_explanation = f"Your score of {risk_score}/100 indicates high symptom severity or potential warning signs. It is strongly recommended that you seek professional medical evaluation promptly."
        
    risk_data = [
        [
            Paragraph(f"<font color='white'><b>{risk_label} ({risk_score}/100)</b></font>", ParagraphStyle('RiskBadge', fontName='Helvetica-Bold', fontSize=12, leading=14, alignment=1)),
            Paragraph(risk_explanation, styles['Normal'])
        ]
    ]
    
    risk_table = Table(risk_data, colWidths=[2.2*inch, 4.8*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor(risk_color_hex)),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#fdf2f8") if risk_score > 70 else colors.HexColor("#f8fafc")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0, 0), (-1, -1), 10)
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 15))
    
    # 6. AI Explanation
    story.append(Paragraph("AI Educational Recommendations & Precautions", section_heading))
    cleaned_ai_explanation = clean_markdown_for_paragraph(ai_explanation)
    story.append(Paragraph(cleaned_ai_explanation, styles['Normal']))
    
    # Keep together disclaimer
    disclaimer_block = []
    disclaimer_block.append(Spacer(1, 30))
    disclaimer_block.append(Paragraph("<b>Disclaimer:</b> This tool is for educational purposes only and does not replace professional medical advice, diagnosis, or treatment. Always consult with a qualified healthcare provider regarding any medical condition. If you are experiencing a medical emergency, immediately contact emergency services.", disclaimer_style))
    story.append(KeepTogether(disclaimer_block))
    
    # Build Document
    doc.build(story)
    buffer.seek(0)
    return buffer
