import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# set page size vars once
width, height = letter

def generate_contract(name, service, date, budget, budget_display, details, package):
    # Ensure contracts folder exists
    os.makedirs("contracts", exist_ok=True)

    # Output file path
    filename = f"contracts/{name.replace(' ', '_')}_contract.pdf"

    # Path to logo
    logo_path = os.path.join(os.path.dirname(__file__), "static", "Uwem_Logo.png")

    # Add logo on a separate canvas (optional pre-pass)
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    try:
        if os.path.exists(logo_path):
            c.drawImage(
                logo_path,
                50, height - 100,
                width=120,
                preserveAspectRatio=True,
                mask="auto"
            )
    except Exception as e:
        print(f"[WARN] Could not load logo: {e}")
    c.save()

    # Now build styled PDF content
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)

    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("<b>UwemMedia Service Agreement & Invoice</b>", styles["Title"]))
    story.append(Spacer(1, 0.25 * inch))

    # Client & Project Info
    client_info = f"""
    <b>Client Information</b><br/>
    Name: {name}<br/>
    Service: {service}<br/>
    Package: {package.title()}<br/>
    Project Date: {date}<br/>
    Budget: {budget if isinstance(budget, str) else f"${budget:,}"}<br/>
    """   
    story.append(Paragraph(client_info, styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    # Project Details
    story.append(Paragraph("<b>Project Details</b>", styles["Heading2"]))
    story.append(Paragraph(details, styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    # Scope of Services
    scope = """
    <b>Scope of Services</b><br/>
    ☐ 30min Pre-production consultation<br/>
    ☐ Filming (up to 6 hours)<br/>
    ☐ Editing (2 revisions included)<br/>
    ☐ Delivery of final product (MP4 format)<br/>
    """
    story.append(Paragraph(scope, styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    # Payment Terms
    payment = f"""
    <b>Payment Terms</b><br/>
    Package: {package.title()}<br/>
    Price Range: {budget_display}<br/>
    Deposit (30% due by end of consultation): ${budget * 0.3:,.2f}<br/>
    Balance due on delivery.<br/>
    """
    story.append(Paragraph(payment, styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    # Rights & Responsibilities
    rights = """
    <b>Rights & Responsibilities</b><br/>
    - The Videographer retains copyright to all raw footage.<br/>
    - The Client is granted rights for personal and promotional use.<br/>
    - Client must provide access, permissions, and meals (if applicable).<br/>
    - Cancellations within 5 days of event incur NO REFUND of deposit fee.<br/>
    """
    story.append(Paragraph(rights, styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    # Liability
    liability = """
    <b>Liability</b><br/>
    The Videographer is not responsible for circumstances beyond control 
    (weather, venue restrictions, technical failures, acts of God).
    """
    story.append(Paragraph(liability, styles["Normal"]))
    story.append(Spacer(1, 0.5 * inch))

    # Signatures
    story.append(Paragraph("<b>Agreement & Signatures</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Client Signature: ___________________________________   Date: ___________", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Videographer Signature: ______________________________   Date: ___________", styles["Normal"]))

    # Build PDF
    doc.build(story)

    return filename
