from models import db, Inquiry


def save_submission(name, email, service, date, package, budget_display,
                    details, ai_text, contract_path, inq_spot_path):
    """Saves a new client submission to SQLite."""
    entry = Inquiry(
        name=name,
        email=email,
        service=service,
        event_date=date,
        package=package,
        budget_display=budget_display,
        details=details,
        ai_brief=ai_text,
        contract_path=contract_path,
        inq_spot_path=inq_spot_path
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def load_submissions():
    """Returns all submissions ordered by most recent first."""
    return Inquiry.query.order_by(Inquiry.id.desc()).all()


def get_submission_by_id(submission_id: int):
    """Returns a single submission by ID."""
    return Inquiry.query.get(submission_id)