import os
import re
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
from dotenv import load_dotenv

load_dotenv()

from contract_generator import generate_contract
from ai_generator import generate_inq_spot
from inq_spot_generator import generate_inq_spot_pdf
from submission_log import save_submission, load_submissions, get_submission_by_id
# from email_utils import send_inq_spot_email  # Uncomment when ready

PRICING = {
    "basic":    {"amount": 150, "display": "$100–$250", "label": "Basic"},
    "standard": {"amount": 300, "display": "$300–$500", "label": "Standard"},
    "premium":  {"amount": 600, "display": "$600+",     "label": "Premium"},
    "custom":   {"amount": 0,   "display": "Custom Quote", "label": "Custom"}
}

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

 # Database
from models import db
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///inq.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

@app.before_request
def create_tables():
    db.create_all()

# with app.app_context():
#     db.create_all()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "uwemmedia2024")


# ─── Auth helper ─────────────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ─── Public Routes ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("inquiry.html")


@app.route("/submit", methods=["POST"])
def submit():
    name    = request.form.get("name", "").strip()
    email   = request.form.get("email", "").strip()
    service = request.form.get("service", "").strip()
    date    = request.form.get("date", "").strip()
    package = request.form.get("package", "").strip()
    details = request.form.get("details", "").strip()

    # Validate required fields
    if not all([name, email, service, date, details]):
        flash("All fields are required.")
        return redirect(url_for("index"))

    # Validate package
    if package not in PRICING:
        flash("Invalid package selected.")
        return redirect(url_for("index"))

    package_info   = PRICING[package]
    budget         = package_info["amount"]
    budget_display = package_info["display"]

    # 1. Generate INQ Spot creative brief (Claude AI)
    ai_text = generate_inq_spot(details, client_name=name, service=service)

    # 2. Create INQ Spot PDF
    inq_pdf_path = generate_inq_spot_pdf(name, ai_text)

    # 3. Email it (uncomment when email_utils is configured)
    # send_inq_spot_email(inq_pdf_path)

    # 4. Generate client-facing contract PDF
    pdf_path = generate_contract(name, service, date, budget, budget_display, details, package)

    # 5. Save submission to log
    entry = save_submission(
        name=name,
        email=email,
        service=service,
        date=date,
        package=package_info["label"],
        budget_display=budget_display,
        details=details,
        ai_text=ai_text,
        contract_path=pdf_path,
        inq_spot_path=inq_pdf_path
    )

    return render_template(
        "thank_you.html",
        name=name,
        pdf_path=pdf_path,
        token=entry.token
    )


@app.route("/download_contract/<client_name>")
def download_contract(client_name):
    safe_name = client_name.replace(" ", "_")
    filepath = os.path.join("contracts", f"{safe_name}_contract.pdf")
    if not os.path.exists(filepath):
        return f"Contract for {client_name} not found.", 404
    return send_file(filepath, as_attachment=True)

@app.route("/inquiry/<token>")
def inquiry_status(token):
    from models import Inquiry
    inquiry = Inquiry.query.filter_by(token=token).first()
    if not inquiry:
        return render_template("404.html"), 404
    return render_template("inquiry_status.html", s=inquiry)
@app.route("/sign/<token>", methods=["GET", "POST"])
def sign_contract(token):
    from models import Inquiry
    inquiry = Inquiry.query.filter_by(token=token).first()
    if not inquiry:
        return "Inquiry not found.", 404
    if inquiry.contract_signed:
        return redirect(url_for("inquiry_status", token=token))
    return render_template("sign_contract.html", s=inquiry)


@app.route("/sign/<token>/submit", methods=["POST"])
def submit_signature(token):
    from models import Inquiry
    import base64
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from io import BytesIO

    inquiry = Inquiry.query.filter_by(token=token).first()
    if not inquiry:
        return "Inquiry not found.", 404

    signature_data = request.form.get("signature_data", "")
    if not signature_data or "," not in signature_data:
        flash("Signature is required.")
        return redirect(url_for("sign_contract", token=token))

    # Decode signature image
    sig_bytes = base64.b64decode(signature_data.split(",")[1])

    # Save signature as temp PNG
    os.makedirs("contracts", exist_ok=True)
    sig_path = f"contracts/{inquiry.name.replace(' ', '_')}_sig.png"
    with open(sig_path, "wb") as f:
        f.write(sig_bytes)

    # Generate signed PDF with ReportLab
    signed_path = f"contracts/{inquiry.name.replace(' ', '_')}_signed.pdf"
    c = canvas.Canvas(signed_path, pagesize=letter)
    w, h = letter

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(1*inch, h - 1*inch, "UwemMedia Service Agreement")
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(1*inch, h - 1.3*inch, f"Generated {inquiry.submitted_at}")

    # Section helper
    def section(title, y):
        c.setFont("Helvetica-Bold", 11)
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.drawString(1*inch, y, title)
        c.setLineWidth(0.5)
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.line(1*inch, y - 4, 7.5*inch, y - 4)
        return y - 20

    def field(label, value, y):
        c.setFont("Helvetica-Bold", 9)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawString(1*inch, y, label + ":")
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.drawString(2.5*inch, y, str(value))
        return y - 16

    def body(text, y):
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        # Simple word wrap
        words = text.split()
        line = ""
        for word in words:
            if c.stringWidth(line + " " + word, "Helvetica", 9) < 5.5*inch:
                line += " " + word
            else:
                c.drawString(1*inch, y, line.strip())
                y -= 14
                line = word
        if line:
            c.drawString(1*inch, y, line.strip())
            y -= 14
        return y - 6

    y = h - 1.6*inch
    y = section("Client & Project Details", y)
    y = field("Client", inquiry.name, y)
    y = field("Email", inquiry.email, y)
    y = field("Service", inquiry.service, y)
    y = field("Package", inquiry.package, y)
    y = field("Event Date", inquiry.event_date, y)
    y = field("Budget Range", inquiry.budget_display, y)

    y -= 10
    y = section("Project Description", y)
    y = body(inquiry.details, y)

    y -= 6
    y = section("Scope of Services", y)
    for item in [
        "30-minute pre-production consultation",
        "Filming per package duration",
        "Professional editing with revisions per package tier",
        "Final delivery in MP4 format within 2 weeks of shoot date"
    ]:
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawString(1.1*inch, y, f"• {item}")
        y -= 14
    y -= 6

    y = section("Payment Terms", y)
    y = body("A 30% deposit is due upon signing to confirm your booking. Remaining balance due on delivery. Cancellations within 5 days forfeit the deposit.", y)

    y -= 6
    y = section("Rights & Responsibilities", y)
    for item in [
        "UwemMedia retains copyright to all raw footage.",
        "Client is granted rights for personal and promotional use.",
        "Client must provide necessary access and permissions.",
        "UwemMedia is not liable for circumstances beyond control."
    ]:
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawString(1.1*inch, y, f"• {item}")
        y -= 14
    y -= 16

    # Signature
    y = section("Client Signature", y)
    y -= 8
    try:
        c.drawImage(sig_path, 1*inch, y - 60, width=200, height=60,
                   preserveAspectRatio=True, mask='auto')
    except Exception:
        c.drawString(1*inch, y - 30, "[Signature on file]")
    y -= 70
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(1*inch, y, f"{inquiry.name} — digitally signed")
    y -= 12
    c.drawString(1*inch, y, f"Date: {inquiry.submitted_at}")

    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    c.drawString(1*inch, 0.5*inch,
        "UwemMedia · uwem.art · This document constitutes a binding service agreement.")

    c.save()

    # Clean up temp sig file
    try:
        os.remove(sig_path)
    except Exception:
        pass

    # Update DB
    inquiry.contract_signed = True
    inquiry.contract_path = signed_path
    db.session.commit()

    return redirect(url_for("inquiry_status", token=token))

import stripe

@app.route("/checkout/<token>")
def checkout(token):
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    from models import Inquiry
    inquiry = Inquiry.query.filter_by(token=token).first()
    if not inquiry:
        return "Inquiry not found.", 404

    package_amounts = {
        "Basic": 150, "Standard": 300, "Premium": 600, "Custom": 0
    }
    base_amount = package_amounts.get(inquiry.package, 0)

    if base_amount == 0:
        return render_template("inquiry_status.html",
            s=inquiry, custom_quote=True)

    deposit_amount = int(base_amount * 0.30 * 100)
    full_amount = int(base_amount * 100)

    return render_template("payment_choice.html",
        s=inquiry,
        deposit_amount=deposit_amount,
        full_amount=full_amount,
        deposit_display=f"${base_amount * 0.30:,.0f}",
        full_display=f"${base_amount:,}"
    )


@app.route("/checkout/<token>/pay/<payment_type>")
def checkout_pay(token, payment_type):
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    from models import Inquiry
    inquiry = Inquiry.query.filter_by(token=token).first()
    if not inquiry:
        return "Inquiry not found.", 404

    package_amounts = {
        "Basic": 150, "Standard": 300, "Premium": 600, "Custom": 0
    }
    base_amount = package_amounts.get(inquiry.package, 0)

    if payment_type == "deposit":
        amount = int(base_amount * 0.30 * 100)
        label = "30% Deposit"
    else:
        amount = int(base_amount * 100)
        label = "Full Payment"

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"UwemMedia — {inquiry.service}",
                    "description": f"{inquiry.package} package · {label}"
                },
                "unit_amount": amount,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=url_for("checkout_success", token=token,
            payment_type=payment_type, _external=True),
        cancel_url=url_for("inquiry_status", token=token, _external=True),
        metadata={"token": token, "payment_type": payment_type}
    )
    return redirect(session.url, code=303)


@app.route("/checkout/success/<token>")
def checkout_success(token):
    from models import Inquiry
    payment_type = request.args.get("payment_type", "deposit")
    inquiry = Inquiry.query.filter_by(token=token).first()
    if inquiry:
        inquiry.deposit_paid = True
        if payment_type == "full":
            inquiry.stage = "shoot_scheduled"
        else:
            inquiry.stage = "deposit_paid"
        db.session.commit()
    return render_template("deposit_success.html", s=inquiry,
        payment_type=payment_type)


# ─── Admin Routes ─────────────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Incorrect password.")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    submissions = load_submissions()
    submissions = list(reversed(submissions))
    return render_template("admin_dashboard.html", submissions=submissions)


@app.route("/admin/submission/<int:submission_id>")
@admin_required
def admin_submission_detail(submission_id):
    submission = get_submission_by_id(submission_id)
    if not submission:
        return "Submission not found.", 404
    return render_template("admin_detail.html", s=submission)


@app.route("/admin/download/contract/<int:submission_id>")
@admin_required
def admin_download_contract(submission_id):
    submission = get_submission_by_id(submission_id)
    if not submission or not os.path.exists(submission["contract_path"]):
        return "Contract not found.", 404
    return send_file(submission["contract_path"], as_attachment=True)


@app.route("/admin/download/inq_spot/<int:submission_id>")
@admin_required
def admin_download_inq_spot(submission_id):
    submission = get_submission_by_id(submission_id)
    if not submission or not os.path.exists(submission["inq_spot_path"]):
        return "INQ Spot not found.", 404
    return send_file(submission["inq_spot_path"], as_attachment=True)


def is_safe_input(text):
    pattern = re.compile(r'^[a-zA-Z0-9\s.,!?-]+$')
    return bool(pattern.match(text))


if __name__ == "__main__":
    app.run(debug=True)
