import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def generate_token():
    return str(uuid.uuid4())[:12]

class Inquiry(db.Model):
    __tablename__ = "inquiries"

    id                = db.Column(db.Integer, primary_key=True)
    token             = db.Column(db.String(12), unique=True, default=generate_token)
    submitted_at      = db.Column(db.String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Client info
    name              = db.Column(db.String(128))
    email             = db.Column(db.String(128))
    service           = db.Column(db.String(128))
    event_date        = db.Column(db.String(32))
    package           = db.Column(db.String(64))
    budget_display    = db.Column(db.String(32))
    details           = db.Column(db.Text)

    # AI + docs
    ai_brief          = db.Column(db.Text)
    contract_path     = db.Column(db.String(256))
    inq_spot_path     = db.Column(db.String(256))

    # Contract + payment
    contract_signed   = db.Column(db.Boolean, default=False)
    deposit_paid      = db.Column(db.Boolean, default=False)
    stripe_payment_id = db.Column(db.String(128))

    # Scheduling
    shoot_date        = db.Column(db.String(32))
    consultation_date = db.Column(db.String(32))

    # Pipeline stage
    stage             = db.Column(db.String(64), default="inq_submitted")

    # Delivery