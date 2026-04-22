import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors


def generate_inq_spot_pdf(name: str, ai_text: str) -> str:
    """
    Generates a styled INQ Spot PDF from Claude's creative brief text.
    Saves to inq_spots/ folder and returns the file path.
    """

    os.makedirs("inq_spots", exist_ok=True)
    safe_name = name.replace(" ", "_")
    filename = f"inq_spots/{safe_name}_inq_spot.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=60, leftMargin=60,
        topMargin=60, bottomMargin=60
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "INQTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "INQSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#4a4a6a"),
        spaceAfter=20
    )
    section_style = ParagraphStyle(
        "INQSection",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#2d4059"),
        spaceBefore=16,
        spaceAfter=6,
        borderPad=4
    )
    body_style = ParagraphStyle(
        "INQBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=16
    )

    story = []
    story.append(Paragraph("UwemMedia 🎬", title_style))
    story.append(Paragraph(f"INQ Spot — Creative Brief for {name}", subtitle_style))
    story.append(Spacer(1, 0.1 * inch))

    # Parse the AI text into sections
    lines = ai_text.split("\n")
    buffer = []

    SECTION_KEYWORDS = [
        "CONCEPT SUMMARY", "RECOMMENDED LOCATIONS", "EQUIPMENT",
        "STORYBOARD", "MOOD", "PRE-PRODUCTION", "QUESTIONS FOR CLIENT"
    ]

    def flush_buffer(buf):
        if buf:
            content = "<br/>".join(line for line in buf if line.strip())
            if content:
                story.append(Paragraph(content, body_style))
            buf.clear()

    for line in lines:
        stripped = line.strip()

        # Skip decorative lines
        if stripped.startswith("==="):
            continue

        # Detect section headers
        is_header = any(stripped.upper().startswith(kw) for kw in SECTION_KEYWORDS)

        if is_header:
            flush_buffer(buffer)
            story.append(Paragraph(stripped.title(), section_style))
        elif stripped:
            buffer.append(stripped)

    flush_buffer(buffer)

    doc.build(story)
    return filename
