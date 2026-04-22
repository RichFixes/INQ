import os
import json
import requests


def generate_inq_spot(details: str, client_name: str = "", service: str = "") -> str:
    """
    Calls Claude API to generate a structured INQ Spot creative brief.
    Returns a formatted string (not JSON) ready for PDF rendering.
    """

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "[ERROR] ANTHROPIC_API_KEY not set. Add it to your .env file."

    system_prompt = """You are a creative director assistant for UwemMedia, a professional videography company.
Read the client's project inquiry and generate a structured creative brief called an INQ Spot.
Be specific, professional, and practical. Output ONLY the brief — no extra commentary.

Use this exact format:

=== INQ SPOT: CREATIVE BRIEF ===

CONCEPT SUMMARY
[2-3 sentences on the core vision and emotional tone]

RECOMMENDED LOCATIONS
- [Location 1]
- [Location 2]
- [Location 3]

EQUIPMENT & TECHNICAL NOTES
- [Item 1]
- [Item 2]
- [Item 3]

STORYBOARD
Scene 1: [description]
Scene 2: [description]
Scene 3: [description]
Scene 4: [description]
Scene 5: [description]

MOOD & STYLE
[Color palette, editing pace, music vibe, visual tone]

PRE-PRODUCTION CHECKLIST
- [Action item 1]
- [Action item 2]
- [Action item 3]
- [Action item 4]

QUESTIONS FOR CLIENT
- [Question 1]
- [Question 2]
- [Question 3]

================================"""

    user_message = f"""Client Name: {client_name or 'Not provided'}
Service Type: {service or 'Not specified'}
Project Details: {details}"""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 1000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}]
            },
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        if data.get("content"):
            return data["content"][0]["text"]
        return "[ERROR] Empty response from Claude."

    except requests.exceptions.Timeout:
        return "[ERROR] Claude API timed out. Try again."
    except requests.exceptions.HTTPError as e:
        return f"[ERROR] Claude API error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"[ERROR] Unexpected error: {str(e)}"
