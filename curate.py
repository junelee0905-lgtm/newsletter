#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
오늘의 발견 — Daily Discovery Newsletter
=========================================
Reads a taste profile, asks Claude (with live web search) to find things the
reader doesn't already know but will love, then renders an Apple / Jony Ive /
LoveFrom-styled email and sends it via Gmail.

Run:  python curate.py
Env:  ANTHROPIC_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL
Optional env: NEWSLETTER_MODEL (default below), DRY_RUN ("1" to skip sending)
"""

import os
import re
import sys
import json
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

import anthropic

from email_template import render_email

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
TASTE_FILE = os.path.join(HERE, "taste_profile.md")

# Sonnet = great quality/cost balance and supports web search.
# Switch to "claude-opus-4-8" for the highest-quality curation (slower, pricier).
MODEL = os.environ.get("NEWSLETTER_MODEL", "claude-sonnet-4-6")

MAX_SEARCHES = int(os.environ.get("NEWSLETTER_MAX_SEARCHES", "10"))
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

CATEGORIES = [
    ("menswear",   "남성복",        "MENSWEAR"),
    ("vintage",    "빈티지",        "VINTAGE"),
    ("music",      "음악",          "MUSIC"),
    ("film",       "영상",          "MOVING IMAGE"),
    ("cars",       "자동차",        "AUTOMOBILE"),
    ("subculture", "서브컬처",      "SUBCULTURE"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def require_env(name):
    v = os.environ.get(name)
    if not v:
        sys.exit(f"[FATAL] Missing required environment variable: {name}")
    return v


def load_taste_profile():
    if not os.path.exists(TASTE_FILE):
        sys.exit(f"[FATAL] taste_profile.md not found at {TASTE_FILE}")
    with open(TASTE_FILE, "r", encoding="utf-8") as f:
        return f.read()


def today_kr():
    """Korean-formatted date string, e.g. '2026년 6월 7일 토요일'."""
    # GitHub Actions runs in UTC; shift to KST for a correct 'morning' date.
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][now.weekday()]
    return f"{now.year}년 {now.month}월 {now.day}일 {weekday_kr}요일", now


def extract_text(response):
    """Concatenate all text blocks from an Anthropic response."""
    parts = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts).strip()


def extract_json(text):
    """Pull the first JSON object out of a text blob (handles ``` fences)."""
    # strip code fences
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    # find first { ... last }
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output.")
    candidate = cleaned[start:end + 1]
    return json.loads(candidate)


# ─────────────────────────────────────────────────────────────────────────────
# The curation prompt
# ─────────────────────────────────────────────────────────────────────────────
def build_prompt(taste_profile, date_str):
    cats_desc = "\n".join(
        f'  - "{key}"  →  {ko} / {en}' for key, ko, en in CATEGORIES
    )
    return f"""You are the private curator for a discerning reader. Today is {date_str}.
Your job: each day, find genuinely NEW discoveries across six domains — things this
specific reader most likely does NOT already know, but that fit their taste precisely.

This is the reader's taste profile. Treat it as a coordinate system, not a list of answers:

────────────────────────────────────────
{taste_profile}
────────────────────────────────────────

YOUR TASK
- Use web search to find real, specific, current/верifiable items. Search broadly and
  follow the lineage: precursors, side players, deep cuts, the obscure-but-pivotal.
- Produce ONE discovery for each of these six categories (keys must match exactly):
{cats_desc}
- Each discovery must be something a knowledgeable insider would respect — NOT the
  obvious famous name the reader surely knows already. Surface the thing *behind* the thing.
- For each, explain the lineage: connect it back to something in the profile
  ("if you love X, this is where X came from / what X was reacting to").
- Respect the AVOID list. Bias toward patina, provenance, Japan, the analog, the underground.
- Prefer items with a real, working URL (article, archive, video, listing, profile).
  If you cannot verify a URL, omit the link field rather than inventing one.

IMAGES (important)
- For each discovery, include one or two real image URLs that depict the item
  (the garment, the album cover, a film still, the car, the person, the magazine, etc.).
- Image URLs MUST be direct links to an image file or a hotlinkable image (ending in
  .jpg/.jpeg/.png/.webp, or a stable CDN/Wikimedia/Discogs/archive image URL).
  Wikimedia Commons (upload.wikimedia.org/...) is a reliable source — prefer it when available.
- Only include an image you actually found via search and are confident resolves to a real
  picture of the subject. If you cannot find a trustworthy image URL, omit the image fields
  rather than guessing. A missing image is fine; a broken or wrong image is not.

DEPTH
- "body" should be a richer, more detailed explanation than a one-liner: 3-5 sentences that
  give real context, history, and specifics a curious reader would savour.
- "aside" is an optional "여담" — a single interesting anecdote, trivia, or side note that
  makes the reader feel they learned something most people don't know. Keep it to 1-3 sentences.

OUTPUT FORMAT
Return ONLY a single JSON object, no preamble, no markdown fences. Schema:

{{
  "intro": "one or two elegant sentences setting today's mood — understated, no hype",
  "discoveries": [
    {{
      "key": "menswear",
      "title": "the name of the thing",
      "subtitle": "a short evocative line (designer, year, origin, etc.)",
      "body": "3-5 sentences: what it is, its history/context, and why it's a real discovery",
      "aside": "optional 여담: one fascinating anecdote or piece of trivia (omit if none)",
      "why": "1 sentence lineage hook tying it to the reader's known tastes",
      "image": "https://... direct image URL (omit if not confidently found)",
      "image2": "https://... optional second image URL (omit if none)",
      "link": "https://... (omit this field entirely if not verifiable)",
      "link_label": "short label like 'Read' / 'Listen' / 'Watch' / 'Archive' / 'Learn more'"
    }}
    // ... one object per category, all six, in the order listed above
  ]
}}

Write "title", "subtitle", "body", "aside", "why" in Korean (한국어), keeping proper nouns,
brand names, song/film/model names in their original language. Keep it refined and quiet
in tone — the voice of someone with deep taste who doesn't need to shout."""


# ─────────────────────────────────────────────────────────────────────────────
# Call Claude with web search
# ─────────────────────────────────────────────────────────────────────────────
def curate(taste_profile, date_str):
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    prompt = build_prompt(taste_profile, date_str)

    print(f"[info] Calling {MODEL} with web search (max {MAX_SEARCHES} searches)…")
    response = client.messages.create(
        model=MODEL,
        max_tokens=6000,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": MAX_SEARCHES,
        }],
        messages=[{"role": "user", "content": prompt}],
    )

    text = extract_text(response)
    if not text:
        raise RuntimeError("Model returned no text content.")

    try:
        data = extract_json(text)
    except Exception as e:
        # one corrective retry: ask the model to fix its own JSON
        print(f"[warn] JSON parse failed ({e}); retrying with a repair prompt…")
        repair = client.messages.create(
            model=MODEL,
            max_tokens=6000,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": text},
                {"role": "user", "content":
                    "That was not valid JSON. Reply with ONLY the corrected JSON "
                    "object, no fences, no commentary."},
            ],
        )
        data = extract_json(extract_text(repair))

    # Order discoveries to match CATEGORIES, attach Korean/English labels
    by_key = {d.get("key"): d for d in data.get("discoveries", [])}
    ordered = []
    for key, ko, en in CATEGORIES:
        d = by_key.get(key)
        if not d:
            continue
        d["label_ko"] = ko
        d["label_en"] = en
        ordered.append(d)
    data["discoveries"] = ordered
    return data


# ─────────────────────────────────────────────────────────────────────────────
# Send email via Gmail
# ─────────────────────────────────────────────────────────────────────────────
def send_email(html, subject):
    gmail = require_env("GMAIL_ADDRESS")
    app_pw = require_env("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("RECIPIENT_EMAIL", gmail)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr(("오늘의 발견", gmail))
    msg["To"] = recipient

    # plain-text fallback
    text_fallback = "오늘의 발견 — 이 메일은 HTML로 보는 것을 권장합니다."
    msg.attach(MIMEText(text_fallback, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    print(f"[info] Sending to {recipient} via Gmail SMTP…")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail, app_pw)
        server.sendmail(gmail, [recipient], msg.as_string())
    print("[ok] Sent.")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    require_env("ANTHROPIC_API_KEY")
    taste = load_taste_profile()
    date_str, now = today_kr()

    data = curate(taste, date_str)
    data["date_str"] = date_str

    html = render_email(data)

    # save a local copy every run (useful for debugging / archiving)
    out_path = os.path.join(HERE, "last_issue.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[info] Wrote preview to {out_path}")

    subject = f"오늘의 발견 · {now.month}월 {now.day}일"

    if DRY_RUN:
        print("[dry-run] Skipping send. Set DRY_RUN=0 to send for real.")
        return

    send_email(html, subject)


if __name__ == "__main__":
    main()
