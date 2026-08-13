"""
Report utility for HepatoX.
Generates PDF and CSV clinical reports for patients and predictions.
"""
import os
import io
import csv
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_patient_pdf_report(patient, predictions=None, logo_path=None):
    """
    Generate a professional clinical PDF report for a patient and return bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=colors.HexColor('#1e3c72'),
        alignment=TA_LEFT,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_LEFT,
        spaceAfter=15
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#2a5298'),
        spaceBefore=15,
        spaceAfter=8
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        leading=14
    )
    
    header_data = []
    
    # Brand Header
    if logo_path and os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=48, height=48)
            header_text = Paragraph(
                "<b>HEPATOX CLINICAL DIAGNOSTIC REPORT</b><br/>"
                "<font size=9 color='#666666'>AI-Powered Hepatic Disease Risk Assessment System</font>",
                title_style
            )
            header_table = Table([[img, header_text]], colWidths=[60, 480])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (0,0), 'LEFT'),
            ]))
            story.append(header_table)
        except Exception:
            story.append(Paragraph("HEPATOX CLINICAL DIAGNOSTIC REPORT", title_style))
    else:
        story.append(Paragraph("HEPATOX CLINICAL DIAGNOSTIC REPORT", title_style))
        story.append(Paragraph("AI-Powered Hepatic Disease Risk Assessment System", subtitle_style))
        
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#30cfd0'), spaceAfter=15))
    
    # Report Metadata & Patient Info
    created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_data = [
        [
            Paragraph("<b>Patient Name:</b> " + str(patient.name), body_style),
            Paragraph("<b>Patient ID:</b> #" + str(patient.id), body_style)
        ],
        [
            Paragraph("<b>Age:</b> " + str(patient.age) + " yrs | <b>Gender:</b> " + str(patient.gender), body_style),
            Paragraph("<b>BMI:</b> " + f"{patient.bmi:.1f}", body_style)
        ],
        [
            Paragraph("<b>Registration Date:</b> " + (patient.created_at.strftime("%Y-%m-%d") if patient.created_at else "N/A"), body_style),
            Paragraph("<b>Report Generated:</b> " + created_date, body_style)
        ]
    ]
    
    info_table = Table(info_data, colWidths=[270, 270])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e9ecef')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))
    
    # Section 1: Biometrics & Lab Biomarkers
    story.append(Paragraph("Clinical Biometrics & Laboratory Telemetry", section_heading))
    
    activity_levels = ["Low", "Moderate", "High"]
    act_str = activity_levels[patient.physical_activity] if 0 <= patient.physical_activity < len(activity_levels) else "N/A"
    
    bio_data = [
        ["Biomarker / Factor", "Measured Value", "Reference Status"],
        ["Liver Function Test (LFT)", f"{patient.liver_function_test:.2f}", "Elevated" if patient.liver_function_test > 2.5 else "Normal"],
        ["Body Mass Index (BMI)", f"{patient.bmi:.1f}", "Overweight" if patient.bmi >= 25 else "Normal"],
        ["Diabetes History", "Yes" if patient.diabetes else "No", "Risk Factor" if patient.diabetes else "Normal"],
        ["Hypertension", "Yes" if patient.hypertension else "No", "Risk Factor" if patient.hypertension else "Normal"],
        ["Genetic Preposition", "Yes" if patient.genetic_risk else "No", "Family History" if patient.genetic_risk else "None"],
        ["Alcohol Consumption", "Yes" if patient.alcohol_consumption else "No", "Lifestyle Factor" if patient.alcohol_consumption else "None"],
        ["Smoking History", "Yes" if patient.smoking else "No", "Lifestyle Factor" if patient.smoking else "None"],
        ["Physical Activity Level", act_str, "Optimal" if patient.physical_activity >= 1 else "Sedentary"]
    ]
    
    bio_table = Table(bio_data, colWidths=[200, 160, 180])
    bio_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a5298')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    story.append(bio_table)
    story.append(Spacer(1, 15))
    
    # Section 2: AI Predictions History
    story.append(Paragraph("AI Diagnostic Risk Predictions", section_heading))
    
    if predictions and len(predictions) > 0:
        pred_data = [["ID", "Date", "Model Used", "Prediction", "Probability", "Risk Level"]]
        for p in predictions[:5]:
            pred_label = "Liver Disease" if p.prediction == 1 else "Healthy"
            prob_str = f"{p.probability * 100:.1f}%"
            date_str = p.created_at.strftime("%Y-%m-%d") if p.created_at else "N/A"
            pred_data.append([
                f"#{p.id}",
                date_str,
                str(p.model_used or "Standard Ensembles"),
                pred_label,
                prob_str,
                str(p.risk_level or "N/A")
            ])
            
        pred_table = Table(pred_data, colWidths=[40, 85, 145, 100, 80, 90])
        pred_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#11998e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        story.append(pred_table)
    else:
        story.append(Paragraph("<i>No previous machine learning prediction scans recorded for this patient.</i>", body_style))
        
    story.append(Spacer(1, 20))
    
    # Disclaimer Footer
    disclaimer = (
        "<b>Medical Disclaimer:</b> HepatoX is an AI-assisted diagnostic clinical decision support tool. "
        "Predictions generated by this system are designed to complement, not replace, clinical evaluation by "
        "a board-certified physician or hepatologist."
    )
    story.append(Paragraph(disclaimer, ParagraphStyle('Disc', parent=body_style, fontSize=8, textColor=colors.HexColor('#777777'))))
    story.append(Spacer(1, 10))
    
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_patient_csv_report(patient, predictions=None):
    """
    Generate CSV report data for a patient.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["HEPATOX CLINICAL DIAGNOSTIC REPORT"])
    writer.writerow(["Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])
    
    writer.writerow(["PATIENT INFORMATION"])
    writer.writerow(["Patient ID", patient.id])
    writer.writerow(["Name", patient.name])
    writer.writerow(["Age", patient.age])
    writer.writerow(["Gender", patient.gender])
    writer.writerow(["BMI", patient.bmi])
    writer.writerow(["Liver Function Test (LFT)", patient.liver_function_test])
    writer.writerow(["Diabetes", "Yes" if patient.diabetes else "No"])
    writer.writerow(["Hypertension", "Yes" if patient.hypertension else "No"])
    writer.writerow(["Genetic Risk", "Yes" if patient.genetic_risk else "No"])
    writer.writerow(["Smoking", "Yes" if patient.smoking else "No"])
    writer.writerow(["Alcohol Consumption", "Yes" if patient.alcohol_consumption else "No"])
    writer.writerow(["Physical Activity", ["Low", "Moderate", "High"][patient.physical_activity] if 0 <= patient.physical_activity < 3 else "N/A"])
    writer.writerow([])
    
    if predictions:
        writer.writerow(["PREDICTION HISTORY"])
        writer.writerow(["Prediction ID", "Date", "Model Used", "Prediction", "Probability", "Confidence Score", "Risk Level"])
        for p in predictions:
            writer.writerow([
                p.id,
                p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
                p.model_used,
                "Liver Disease" if p.prediction == 1 else "Healthy",
                f"{p.probability:.4f}",
                f"{p.confidence_score:.4f}" if hasattr(p, 'confidence_score') and p.confidence_score else "N/A",
                p.risk_level
            ])
            
    return output.getvalue()


def generate_prediction_pdf_report(prediction, patient=None, logo_path=None):
    """
    Generate a focused single-scan PDF diagnostic report for a specific prediction.
    """
    if patient is None and hasattr(prediction, 'patient'):
        patient = prediction.patient

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#1e3c72'),
        alignment=TA_LEFT,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_LEFT,
        spaceAfter=12
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=colors.HexColor('#2a5298'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        textColor=colors.HexColor('#333333'),
        leading=13
    )
    
    story.append(Paragraph("HEPATOX AI DIAGNOSTIC ASSESSMENT REPORT", title_style))
    story.append(Paragraph(f"Single Telemetry Prediction Scan #{prediction.id} | Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#30cfd0'), spaceAfter=12))
    
    # Patient Info & Prediction Overview Box
    pred_label = "LIVER DISEASE RISK DETECTED" if prediction.prediction == 1 else "HEALTHY LIVER INDICATOR"
    risk_color = '#d9534f' if prediction.prediction == 1 else '#28a745'
    
    info_data = [
        [
            Paragraph("<b>Patient Name:</b> " + (patient.name if patient else "N/A"), body_style),
            Paragraph("<b>Patient ID:</b> #" + str(patient.id if patient else "N/A"), body_style)
        ],
        [
            Paragraph("<b>Diagnostic Status:</b> <font color='" + risk_color + "'><b>" + pred_label + "</b></font>", body_style),
            Paragraph("<b>Risk Category:</b> <b>" + str(prediction.risk_level or "N/A") + " Risk</b>", body_style)
        ],
        [
            Paragraph("<b>Model Probability:</b> " + f"{prediction.probability * 100:.2f}%", body_style),
            Paragraph("<b>AI Model Architecture:</b> " + str(prediction.model_used or "Stacking Ensemble"), body_style)
        ]
    ]
    
    info_table = Table(info_data, colWidths=[270, 270])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f4f8')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2a5298')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12))
    
    # Biomarkers
    if patient:
        story.append(Paragraph("Patient Clinical Telemetry", section_heading))
        activity_levels = ["Low", "Moderate", "High"]
        act_str = activity_levels[patient.physical_activity] if 0 <= patient.physical_activity < len(activity_levels) else "N/A"
        
        bio_data = [
            ["Feature Name", "Value Recorded", "Clinical Classification"],
            ["Age", f"{patient.age} yrs", "Demographic"],
            ["Gender", str(patient.gender), "Demographic"],
            ["BMI", f"{patient.bmi:.1f}", "Overweight" if patient.bmi >= 25 else "Normal Range"],
            ["Liver Function Test (LFT)", f"{patient.liver_function_test:.2f}", "Elevated" if patient.liver_function_test > 2.5 else "Normal"],
            ["Diabetes History", "Yes" if patient.diabetes else "No", "Metabolic Marker"],
            ["Hypertension", "Yes" if patient.hypertension else "No", "Cardiovascular Marker"],
            ["Genetic Risk Factor", "Yes" if patient.genetic_risk else "No", "Hereditary Risk"],
            ["Alcohol Consumption", "Yes" if patient.alcohol_consumption else "No", "Lifestyle Factor"],
            ["Smoking History", "Yes" if patient.smoking else "No", "Lifestyle Factor"],
            ["Physical Activity", act_str, "Lifestyle Factor"],
        ]
        bio_table = Table(bio_data, colWidths=[200, 160, 180])
        bio_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3c72')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        story.append(bio_table)
        story.append(Spacer(1, 12))
    
    # Recommendation Section
    story.append(Paragraph("Clinical Recommendations", section_heading))
    if prediction.prediction == 1:
        rec_text = (
            "• <b>Immediate Hepatology Consultation:</b> Follow-up blood panel (ALT, AST, ALP, Bilirubin) recommended.<br/>"
            "• <b>Abdominal Ultrasound / Imaging:</b> Assess hepatic steatosis or fibrosis grade.<br/>"
            "• <b>Lifestyle Intervention:</b> Alcohol cessation, dietary modifications, and glycemic monitoring."
        )
    else:
        rec_text = (
            "• <b>Routine Preventive Monitoring:</b> Annual liver panel checks recommended.<br/>"
            "• <b>Healthy Lifestyle Maintenance:</b> Maintain balanced physical activity and optimal BMI."
        )
    story.append(Paragraph(rec_text, body_style))
    story.append(Spacer(1, 15))
    
    # Disclaimer Footer
    disclaimer = (
        "<b>Notice:</b> HepatoX AI Diagnostic System is an assistive clinical decision tool powered by peer-reviewed machine learning algorithms. "
        "It is designed to support medical professionals and should be verified alongside standard laboratory assays."
    )
    story.append(Paragraph(disclaimer, ParagraphStyle('Disc2', parent=body_style, fontSize=8, textColor=colors.HexColor('#777777'))))
    
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

