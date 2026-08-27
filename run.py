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

import stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@app.route("/checkout/<token>")
def checkout(token):
    from models import Inquiry
    inquiry = Inquiry.query.filter_by(token=token).first()
    if not inquiry:
        return "Inquiry not found.", 404

    # Calculate 30% deposit
    package_amounts = {
        "Basic": 150, "Standard": 300, "Premium": 600, "Custom": 0
    }
    base_amount = package_amounts.get(inquiry.package, 0)
    deposit_amount = int(base_amount * 0.30 * 100)  # Stripe uses cents

    if deposit_amount == 0:
        flash("Custom quote — contact us to arrange payment.")
        return redirect(url_for("inquiry_status", token=token))

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"UwemMedia Deposit — {inquiry.service}",
                    "description": f"{inquiry.package} package · 30% deposit"
                },
                "unit_amount": deposit_amount,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=url_for("checkout_success", token=token, _external=True),
        cancel_url=url_for("inquiry_status", token=token, _external=True),
        metadata={"token": token}
    )
    return redirect(session.url, code=303)


@app.route("/checkout/success/<token>")
def checkout_success(token):
    from models import Inquiry
    inquiry = Inquiry.query.filter_by(token=token).first()
    if inquiry:
        inquiry.deposit_paid = True
        inquiry.stage = "deposit_paid"
        db.session.commit()
    return render_template("deposit_success.html", s=inquiry)
@app.route("/schedule", methods=["GET", "POST"])
def schedule():
    if request.method == "POST":
        time_slot = request.form.get("time_slot")
        contact   = request.form.get("contact_method")
        print(f"Booking: {time_slot}, via {contact}")
        flash("Your consultation request has been received!")
        return redirect(url_for("index"))
    return render_template("schedule.html")


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
