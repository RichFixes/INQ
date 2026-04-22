# INQ

UwemFilms Inquiry Form

Architecture:
User submits form
↓
AI generates production plan
↓
PDF is created (AI brief)
↓
Email sent to YOU (attachment)
↓
User only sees thank you page (no AI output)

# INQ Project (Refactored)

This project has been refactored for clarity, testing, and Deta Micro deployment.

Run locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Deploy to Deta Micro:

```bash
curl -fsSL https://get.deta.dev/cli.sh | sh
deta login
deta new --python
deta deploy
```
