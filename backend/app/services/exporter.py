import io
from datetime import datetime
import pandas as pd
from typing import List, Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf_report(record: Dict[str, Any]) -> io.BytesIO:
    """
    Generates a beautifully styled, professional academic report card PDF.
    Streamed directly via memory buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#1e293b")  # Slate 800
    c_secondary = colors.HexColor("#3b82f6")  # Blue 500
    c_accent = colors.HexColor("#f1f5f9")  # Slate 100
    c_text = colors.HexColor("#334155")  # Slate 700
    c_white = colors.white
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=c_primary,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=25
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=c_primary,
        spaceBefore=15,
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=c_text
    )
    
    body_bold_style = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    roadmap_week_style = ParagraphStyle(
        'RoadmapWeek',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_secondary
    )
    
    story = []
    
    # Title & Metadata
    story.append(Paragraph("Student Performance Prediction Report", title_style))
    created_date = record.get("created_at")
    if isinstance(created_date, datetime):
        date_str = created_date.strftime("%Y-%m-%d %H:%M:%S")
    else:
        date_str = str(created_date)[:19]
        
    story.append(Paragraph(f"Generated on {date_str} | Student Performance Prediction Engine v2.0", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Core Student & Prediction Info Table
    info_data = [
        [
            Paragraph("Student Name:", body_bold_style),
            Paragraph(record.get("student_name", "N/A"), body_style),
            Paragraph("Predicted Score:", body_bold_style),
            Paragraph(f"{record.get('predicted_score', 0.0):.2f}%", body_bold_style)
        ],
        [
            Paragraph("Performance level:", body_bold_style),
            Paragraph(record.get("performance_level", "N/A"), body_style),
            Paragraph("Risk level:", body_bold_style),
            Paragraph(record.get("risk_level", "N/A"), body_style)
        ],
        [
            Paragraph("Confidence Score:", body_bold_style),
            Paragraph(f"{record.get('confidence_score', 0.0):.1f}%", body_style),
            Paragraph("Assessment Date:", body_bold_style),
            Paragraph(date_str[:10], body_style)
        ]
    ]
    
    info_table = Table(info_data, colWidths=[120, 140, 120, 140])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_accent),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.HexColor("#e2e8f0")),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Input Feature Parameters Table
    story.append(Paragraph("Academic & Lifestyle Parameters", h2_style))
    
    features_headers = [
        Paragraph("Parameter", body_bold_style), 
        Paragraph("Value", body_bold_style),
        Paragraph("Parameter", body_bold_style), 
        Paragraph("Value", body_bold_style)
    ]
    
    features_data = [
        features_headers,
        [
            Paragraph("Attendance Rate", body_style), Paragraph(f"{record.get('attendance', 0.0):.1f}%", body_style),
            Paragraph("Previous GPA", body_style), Paragraph(f"{record.get('previous_gpa', 0.0):.2f}/10.0", body_style)
        ],
        [
            Paragraph("Weekly Study Hours", body_style), Paragraph(f"{record.get('study_hours', 0.0):.1f} hrs/wk", body_style),
            Paragraph("Assignment Completion Rate", body_style), Paragraph(f"{record.get('assignment_completion', 0.0):.1f}%", body_style)
        ],
        [
            Paragraph("Class Participation Score", body_style), Paragraph(f"{record.get('participation_score', 0.0):.1f}/10.0", body_style),
            Paragraph("Daily Sleep Hours", body_style), Paragraph(f"{record.get('sleep_hours', 0.0):.1f} hrs/day", body_style)
        ],
        [
            Paragraph("Practice Test Score", body_style), Paragraph(f"{record.get('practice_test_score', 0.0):.1f}%", body_style),
            Paragraph("Practice Problems Completed", body_style), Paragraph(f"{record.get('practice_problems', 0)} solved", body_style)
        ]
    ]
    
    features_table = Table(features_data, colWidths=[160, 100, 160, 100])
    features_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.HexColor("#e2e8f0")),
    ]))
    story.append(features_table)
    story.append(Spacer(1, 20))
    
    # Strengths / Weaknesses / Summary Section
    story.append(Paragraph("Performance Analysis Summary", h2_style))
    story.append(Paragraph(record.get("summary", "No summary report available."), body_style))
    story.append(Spacer(1, 15))
    
    # Strengths & Weaknesses Grids
    strengths_list = record.get("strengths", []) or []
    weaknesses_list = record.get("weaknesses", []) or []
    
    strengths_html = "<br/>".join([f"• {s}" for s in strengths_list]) or "No major strengths identified."
    weaknesses_html = "<br/>".join([f"• {w}" for w in weaknesses_list]) or "No major weaknesses identified."
    
    sw_data = [
        [Paragraph("Identified Strengths", body_bold_style), Paragraph("Areas for Improvement", body_bold_style)],
        [Paragraph(strengths_html, body_style), Paragraph(weaknesses_html, body_style)]
    ]
    
    sw_table = Table(sw_data, colWidths=[260, 260])
    sw_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#dcfce7")),  # Green 100
        ('BACKGROUND', (1,0), (1,0), colors.HexColor("#fee2e2")),  # Red 100
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.HexColor("#e2e8f0")),
    ]))
    story.append(sw_table)
    story.append(Spacer(1, 20))
    
    # Page Break for Learning Roadmap (ensures it is on Page 2 for neatness)
    story.append(PageBreak())
    
    # AI Personalized Learning Roadmap
    story.append(Paragraph("Personalized 4-Week Study Roadmap", title_style))
    story.append(Paragraph("This custom milestone checklist targets features below reference levels.", subtitle_style))
    story.append(Spacer(1, 10))
    
    roadmap_list = record.get("learning_roadmap", []) or []
    for week_info in roadmap_list:
        week_num = week_info.get("week", 1)
        title = week_info.get("title", f"Week {week_num}")
        focus = week_info.get("focus", "")
        tasks = week_info.get("tasks", [])
        
        story.append(Paragraph(f"Week {week_num}: {title}", roadmap_week_style))
        story.append(Paragraph(f"<b>Weekly Focus:</b> {focus}", body_style))
        story.append(Spacer(1, 4))
        
        tasks_html = "<br/>".join([f"✔ {t}" for t in tasks])
        story.append(Paragraph(tasks_html, body_style))
        story.append(Spacer(1, 12))
        
    # Build Document
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_excel_report(records: List[Dict[str, Any]]) -> io.BytesIO:
    """
    Exports prediction history list to Excel format.
    """
    buffer = io.BytesIO()
    
    # Flatten records for tabular report
    rows = []
    for r in records:
        rows.append({
            "Record ID": r.get("id"),
            "Student Name": r.get("student_name"),
            "Predicted Score": r.get("predicted_score"),
            "Performance Level": r.get("performance_level"),
            "Confidence Score (%)": r.get("confidence_score"),
            "Risk Level": r.get("risk_level"),
            "Attendance (%)": r.get("attendance"),
            "Previous GPA": r.get("previous_gpa"),
            "Study Hours (hrs/wk)": r.get("study_hours"),
            "Assignment Completion (%)": r.get("assignment_completion"),
            "Class Participation (/10)": r.get("participation_score"),
            "Sleep Hours (hrs/day)": r.get("sleep_hours"),
            "Practice Test Score (%)": r.get("practice_test_score"),
            "Practice Problems Solved": r.get("practice_problems"),
            "Record Created At": str(r.get("created_at"))[:19]
        })
        
    df = pd.DataFrame(rows)
    
    # Write to Excel with formatting
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Prediction History', index=False)
        
        # Style sheet
        workbook = writer.book
        worksheet = writer.sheets['Prediction History']
        
        # Auto-adjust column widths
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 3, 10)
            
    buffer.seek(0)
    return buffer
