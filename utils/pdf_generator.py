"""
LoanWise - Professional PDF Loan Evaluation Report Generator
Builds a multi-section underwriting summary report using ReportLab.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from utils.calculator import calculate_emi
from utils.suggestions import generate_underwriting_insights


def generate_loan_report_pdf(record, contributions=None):
    """
    Generates a PDF document stream for a given loan application record.
    Returns bytes of the generated PDF file.
    """
    buffer = io.BytesIO()

    # Document setup: Letter size with 0.5-inch margins
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

    # Custom Typography Styles
    c_navy = colors.HexColor('#101B35')
    c_blue = colors.HexColor('#2563EB')
    c_green = colors.HexColor('#16A34A')
    c_red = colors.HexColor('#DC2626')
    c_slate = colors.HexColor('#64748B')
    c_border = colors.HexColor('#E2E8F0')
    c_light_bg = colors.HexColor('#F8FAFC')

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_navy
    )

    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=c_slate
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=c_navy
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=c_navy
    )

    body_muted = ParagraphStyle(
        'BodyMuted',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=c_slate
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=c_navy
    )

    # 1. HEADER BANNER
    header_data = [
        [
            Paragraph("<b>LOANWISE</b> &bull; <font color='#2563EB'>AI Underwriting Engine</font>", title_style),
            Paragraph(f"<b>Application Ref:</b> {record.get('application_id')}<br/>"
                      f"<b>Date:</b> {record.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M'))}", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[3.8 * inch, 3.4 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_blue, spaceBefore=4, spaceAfter=10))

    # 2. DECISION EXECUTIVE SUMMARY
    is_approved = int(record.get('prediction', 0)) == 1
    status_text = "RECOMMENDED FOR APPROVAL" if is_approved else "RECOMMENDED FOR REJECTION"
    status_color = c_green if is_approved else c_red
    bg_color = colors.HexColor('#ECFDF5') if is_approved else colors.HexColor('#FEF2F2')
    prob_pct = round(float(record.get('probability', 0.5)) * 100, 1)
    risk_level = record.get('risk_level', 'Moderate Risk')

    decision_banner_data = [
        [
            Paragraph(f"<font color='{status_color.hexval()}'><b>{status_text}</b></font><br/>"
                      f"<font size='8' color='{c_slate.hexval()}'>Machine Learning Risk Tier: <b>{risk_level}</b></font>", body_style),
            Paragraph(f"<font size='14'><b>{prob_pct}%</b></font><br/>"
                      f"<font size='7' color='{c_slate.hexval()}'>Approval Probability</font>", ParagraphStyle('Prob', parent=body_style, alignment=TA_CENTER))
        ]
    ]
    decision_table = Table(decision_banner_data, colWidths=[5.6 * inch, 1.6 * inch])
    decision_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('BOX', (0, 0), (-1, -1), 1, status_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(decision_table)
    story.append(Spacer(1, 10))

    # 3. APPLICANT & LOAN DETAILS TABLE
    story.append(Paragraph("1. Applicant & Underwriting Parameters", section_header_style))
    story.append(Spacer(1, 4))

    app_income = float(record.get('applicant_income', 0))
    coapp_income = float(record.get('coapplicant_income', 0))
    loan_k = float(record.get('loan_amount', 0))
    term = float(record.get('loan_amount_term', 360))
    credit_hist = "1.0 - Meets Guidelines" if float(record.get('credit_history', 1)) == 1.0 else "0.0 - Unfavorable"

    profile_data = [
        [
            Paragraph("<b>Applicant Name:</b>", body_muted),
            Paragraph(str(record.get('applicant_name', 'Applicant')), body_style),
            Paragraph("<b>Education:</b>", body_muted),
            Paragraph(str(record.get('education', 'Graduate')), body_style),
        ],
        [
            Paragraph("<b>Gender / Marital:</b>", body_muted),
            Paragraph(f"{record.get('gender')}, {record.get('married')} Married", body_style),
            Paragraph("<b>Employment:</b>", body_muted),
            Paragraph("Self-Employed" if record.get('self_employed') == 'Yes' else "Salaried / Employed", body_style),
        ],
        [
            Paragraph("<b>Monthly Income:</b>", body_muted),
            Paragraph(f"${app_income:,.2f}", body_style),
            Paragraph("<b>Co-Applicant Income:</b>", body_muted),
            Paragraph(f"${coapp_income:,.2f}" if coapp_income > 0 else "None ($0.00)", body_style),
        ],
        [
            Paragraph("<b>Requested Principal:</b>", body_muted),
            Paragraph(f"${loan_k:,.0f},000", body_style),
            Paragraph("<b>Tenure:</b>", body_muted),
            Paragraph(f"{term:.0f} Months ({term/12:.1f} Yrs)", body_style),
        ],
        [
            Paragraph("<b>Credit Bureau History:</b>", body_muted),
            Paragraph(credit_hist, body_style),
            Paragraph("<b>Property Zoning:</b>", body_muted),
            Paragraph(str(record.get('property_area', 'Urban')), body_style),
        ]
    ]

    profile_table = Table(profile_data, colWidths=[1.8 * inch, 1.8 * inch, 1.8 * inch, 1.8 * inch])
    profile_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_light_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(profile_table)
    story.append(Spacer(1, 10))

    # 4. FINANCIAL ESTIMATES & EMI BREAKDOWN
    story.append(Paragraph("2. Financial Amortization & Repayment Summary", section_header_style))
    story.append(Spacer(1, 4))

    # Calculate standard EMI at benchmark 9.5% annual rate
    principal_dollars = loan_k * 1000.0
    emi_calc = calculate_emi(principal_dollars, 9.5, term)

    emi_data = [
        [
            Paragraph("<b>Monthly EMI Estimate:</b><br/><font size='10' color='#2563EB'><b>${:,.2f}</b></font>".format(emi_calc['emi']), body_style),
            Paragraph("<b>Total Interest Payable:</b><br/><font size='10'><b>${:,.2f}</b></font>".format(emi_calc['total_interest']), body_style),
            Paragraph("<b>Total Repayment Amount:</b><br/><font size='10'><b>${:,.2f}</b></font>".format(emi_calc['total_repayment']), body_style),
            Paragraph("<b>Indicative Rate:</b><br/><font size='10'><b>9.50% p.a.</b></font>", body_style)
        ]
    ]
    emi_table = Table(emi_data, colWidths=[1.8 * inch, 1.8 * inch, 1.8 * inch, 1.8 * inch])
    emi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_light_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(emi_table)
    story.append(Spacer(1, 10))

    # 5. EXPLAINABLE AI – WHY THIS DECISION?
    insights = generate_underwriting_insights(record, int(record.get('prediction', 0)), float(record.get('probability', 0.5)))
    story.append(Paragraph("3. Explainable AI (XAI) – Underwriting Factors", section_header_style))
    story.append(Spacer(1, 3))

    xai_rows = []
    # Positive Factors
    if contributions and contributions.get('top_positive'):
        pos_str = ", ".join([f"<b>{c['feature']}</b> (+{c['impact']})" for c in contributions['top_positive'][:3]])
    else:
        pos_str = "Standard income to loan proportionality"
    xai_rows.append([Paragraph("<font color='#16A34A'><b>&bull; Supporting Factors:</b></font>", bullet_style), Paragraph(pos_str, bullet_style)])

    # Negative Factors
    if contributions and contributions.get('top_negative'):
        neg_str = ", ".join([f"<b>{c['feature']}</b> ({c['impact']})" for c in contributions['top_negative'][:3]])
    else:
        neg_str = "None identified"
    xai_rows.append([Paragraph("<font color='#DC2626'><b>&bull; Risk Indicators:</b></font>", bullet_style), Paragraph(neg_str, bullet_style)])

    xai_table = Table(xai_rows, colWidths=[2.0 * inch, 5.2 * inch])
    xai_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(xai_table)
    story.append(Spacer(1, 10))

    # 6. ACTIONABLE IMPROVEMENT SUGGESTIONS
    story.append(Paragraph("4. Actionable Loan Improvement Advisory", section_header_style))
    story.append(Spacer(1, 3))

    sugg_rows = []
    for s in insights['suggestions'][:3]:
        sugg_rows.append([
            Paragraph(f"<b>[{s['category']}] {s['action']}:</b>", bullet_style),
            Paragraph(s['details'], bullet_style)
        ])

    sugg_table = Table(sugg_rows, colWidths=[2.2 * inch, 5.0 * inch])
    sugg_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(sugg_table)
    story.append(Spacer(1, 12))

    # 7. LEGAL & COMPLIANCE DISCLAIMER
    disclaimer_text = (
        "<b>Important Regulatory Disclaimer:</b> This evaluation report is generated by the LoanWise "
        "machine learning predictive model for screening and risk evaluation purposes only. It does not "
        "constitute a legally binding credit commitment or final loan approval. Commercial lending approval "
        "is subject to full institutional underwriting, physical collateral appraisal, debt-to-income verification, "
        "and compliance with statutory lending requirements."
    )
    disclaimer_table = Table([[Paragraph(disclaimer_text, body_muted)]], colWidths=[7.2 * inch])
    disclaimer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF3C7')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#F59E0B')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(disclaimer_table)

    # Build the document
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

