import os
import json
from datetime import datetime


LOG_FILE = "submissions.json"


def save_submission(name, email, service, date, package, budget_display, details, ai_text, contract_path, inq_spot_path):
    """Appends a new client submission to the JSON log file."""

    submissions = load_submissions()

    entry = {
        "id": len(submissions) + 1,
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "name": name,
        "email": email,
        "service": service,
        "event_date": date,
        "package": package,
        "budget_display": budget_display,
        "details": details,
        "ai_brief": ai_text,
        "contract_path": contract_path,
        "inq_spot_path": inq_spot_path
    }

    submissions.append(entry)

    with open(LOG_FILE, "w") as f:
        json.dump(submissions, f, indent=2)

    return entry


def load_submissions():
    """Loads all submissions from the JSON log file."""
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def get_submission_by_id(submission_id: int):
    """Returns a single submission by ID."""
    submissions = load_submissions()
    for s in submissions:
        if s.get("id") == submission_id:
            return s
    return None
