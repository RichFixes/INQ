# INQ — UwemMedia Inquiry System

> **A cinematic client intake platform for videographers, built for party promoters, artists, and creatives who move different.**

Live at **[uwem.art](https://uwem.art)**

---

## What It Does

A client submits an inquiry through the form. Behind the scenes, Claude AI instantly generates a full creative brief — storyboard, locations, equipment notes, mood direction — so you walk into every consultation already prepared. The client gets a signed contract PDF and a Calendly link to book their consultation.

```
Client fills out inquiry form
        ↓
Claude AI generates INQ Spot creative brief
        ↓
INQ Spot PDF saved to your admin dashboard
        ↓
Client contract PDF auto-generated
        ↓
Client lands on thank you page + Calendly booking
        ↓
You review everything at /admin
```

---

## Features

**Client-Facing**
- Cinematic dark luxury inquiry form with vertical video background
- Package selection (Basic / Standard / Premium / Custom Quote)
- Auto-generated contract PDF on submission
- Calendly consultation booking on thank you page

**AI-Powered (Claude)**
- Generates a structured INQ Spot creative brief per submission
- Includes: concept summary, storyboard scenes, location recommendations, equipment notes, mood & style direction, pre-production checklist, questions for client
- Brief saved as PDF in `inq_spots/`

**Admin Dashboard (`/admin`)**
- Password-protected backend
- View all submissions newest-first
- Stats: total inquiries, premium packages, custom quotes, AI briefs generated
- Per-submission detail page with storyboard rendered as cards
- Download contract PDF and INQ Spot PDF per client

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python / Flask |
| AI | Anthropic Claude (claude-haiku) |
| PDF Generation | ReportLab |
| Frontend | Vanilla HTML/CSS — Bebas Neue + Cormorant Garamond |
| Hosting | Railway |
| Domain | Squarespace DNS → uwem.art |
| Scheduling | Calendly embed |

---

## Project Structure

```
INQ/
├── run.py                  # App entry point
├── app.py                  # Flask routes (public + admin)
├── ai_generator.py         # Claude API integration
├── contract_generator.py   # Client contract PDF
├── inq_spot_generator.py   # AI brief PDF renderer
├── submission_log.py       # JSON-based submission storage
├── requirements.txt
├── Procfile                # Railway deployment
├── static/
│   ├── Uwem_Logo.png
│   └── hero.mp4            # Video background (not in git)
└── templates/
    ├── inquiry.html         # Main form (cinematic UI)
    ├── thank_you.html       # Post-submission page
    ├── admin_login.html     # Admin auth
    ├── admin_dashboard.html # Submissions overview
    └── admin_detail.html    # Per-client INQ Spot view
```

---

## Environment Variables

Create a `.env` file in the project root:

```
SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=sk-ant-your-key-here
CALENDLY_URL=https://calendly.com/uwemfilms/uwemmedia-consultation
ADMIN_PASSWORD=your-admin-password
```

---

## Running Locally

```zsh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

Visit `http://localhost:5000`
Admin panel at `http://localhost:5000/admin`

---

## Deployment

Deployed on **Railway** via GitHub. Every push to `main` triggers an automatic redeploy.

```
Procfile: web: gunicorn run:app
```

---

## Packages

- `basic` → $100–$250 (1hr shoot, 1 edit)
- `standard` → $300–$500 (3hr shoot, 2 edits)
- `premium` → $600+ (Full production)
- `custom` → Custom quote

---

*Built for UwemMedia — every frame is a choice. We make the ones that last.*
