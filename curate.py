#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
오늘의 발견 — Daily Discovery Newsletter
"""

import os, re, sys, json, smtplib, datetime, time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

import anthropic
from email_template import render_email

# ── Config ────────────────────────────────────────────────────────────────────
HERE       = os.path.dirname(os.path.abspath(__file__))
TASTE_FILE = os.path.join(HERE, "taste_profile.md")
MODEL      = os.environ.get("NEWSLETTER_MODEL", "claude-sonnet-4-6")
MAX_SEARCHES = 3        # rate limit 방지
MAX_TOKENS   = 4000     # 출력 충분히 (rate limit과 무관)
DRY_RUN    = os.environ.get("DRY_RUN", "0") == "1"

CATEGORIES = [
    ("menswear",   "남성복",   "MENSWEAR"),
    ("vintage",    "빈티지",   "VINTAGE"),
    ("music",      "음악",     "MUSIC"),
    ("film",       "영상",     "MOVING IMAGE"),
    ("cars",       "자동차",   "AUTOMOBILE"),
    ("subculture", "서브컬처", "SUBCULTURE"),
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def require_env(name):
    v = os.environ.get(name)
    if not v:
        sys.exit(f"[FATAL] Missing env var: {name}")
    return v

def load_taste_profile():
    if not os.path.exists(TASTE_FILE):
        sys.exit("[FATAL] taste_profile.md not found")
    with open(TASTE_FILE, "r", encoding="utf-8") as f:
        return f.read()[:2000]   # 토큰 절약: 앞부분만

def today_kr():
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    weekday_kr = ["월","화","수","목","금","토","일"][now.weekday()]
    return f"{now.year}년 {now.month}월 {now.day}일 {weekday_kr}요일", now

def extract_text(response):
    return "\n".join(
        b.text for b in response.content
        if getattr(b, "type", None) == "text"
    ).strip()

def extract_json(text):
    """정상 파싱 시도 후, 실패하면 완성된 조각만 건져냄(truncation 안전장치)."""
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(cleaned[start:end + 1])
        except Exception:
            pass

    # ── 살리기: intro + 완성된 discovery 객체들만 ──
    result = {"discoveries": []}
    m = re.search(r'"intro"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned)
    if m:
        result["intro"] = m.group(1)

    didx = cleaned.find('"discoveries"')
    region = cleaned[didx:] if didx != -1 else cleaned
    depth, buf, started = 0, "", False
    for ch in region:
        if ch == "{":
            depth += 1
            started = True
        if started:
            buf += ch
        if ch == "}":
            depth -= 1
            if depth == 0 and started:
                try:
                    obj = json.loads(buf)
                    if "key" in obj:
                        result["discoveries"].append(obj)
                except Exception:
                    pass
                buf, started = "", False

    if not result["discoveries"]:
        raise ValueError("건질 수 있는 JSON이 없습니다.")
    return result

# ── Prompt ────────────────────────────────────────────────────────────────────
def build_prompt(taste_profile, date_str):
    cats = "\n".join(f'  "{k}" → {ko}' for k, ko, en in CATEGORIES)
    return f"""You are a private curator. Today: {date_str}.
Find one NEW discovery per category that fits this reader's taste but they likely don't know yet.

TASTE PROFILE (coordinate system — not a list of answers):
{taste_profile}

CATEGORIES (use these exact keys):
{cats}

RULES:
- Surface the obscure, adjacent, underground — NOT the famous names they already know.
- Each body: 2-3 sentences, specific and interesting.
- Each aside: 1 optional fascinating anecdote (omit if none).
- Each why: 1 sentence connecting to their known tastes.
- Each link: only include if you found a real, working URL. Omit if unsure.
- No womenswear, no formal tailoring.

Return ONLY valid JSON, no fences:
{{
  "intro": "1-2 sentences setting today's mood",
  "discoveries": [
    {{
      "key": "menswear",
      "title": "...",
      "subtitle": "...",
      "body": "2-3 sentences in Korean",
      "aside": "optional anecdote in Korean",
      "why": "1 sentence in Korean",
      "link": "https://...",
      "link_label": "Read / Listen / Watch / Learn more"
    }}
  ]
}}

Write body/aside/why/title/subtitle in Korean. Keep proper nouns in original language."""

# ── Curate ────────────────────────────────────────────────────────────────────
def curate(taste_profile, date_str):
    client = anthropic.Anthropic()
    prompt = build_prompt(taste_profile, date_str)
    print(f"[info] Calling {MODEL} (searches={MAX_SEARCHES}, max_tokens={MAX_TOKENS})…")

    response = None
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": MAX_SEARCHES,
                }],
                messages=[{"role": "user", "content": prompt}],
            )
            break
        except anthropic.RateLimitError:
            wait = 30 * (attempt + 1)
            print(f"[warn] Rate limit. {wait}s 대기 후 재시도…")
            time.sleep(wait)
    if response is None:
        sys.exit("[FATAL] Rate limit: 재시도 실패. 잠시 후 다시 실행하세요.")

    text = extract_text(response)
    if not text:
        sys.exit("[FATAL] 모델이 텍스트를 반환하지 않았습니다.")

    try:
        data = extract_json(text)
    except Exception as e:
        print(f"[warn] JSON 파싱 실패 ({e}). 복구 재시도…")
        repair = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": text},
                {"role": "user", "content":
                    "Return ONLY the corrected, COMPLETE JSON object. No fences, no commentary."},
            ],
        )
        data = extract_json(extract_text(repair))

    by_key = {d.get("key"): d for d in data.get("discoveries", [])}
    ordered = []
    for key, ko, en in CATEGORIES:
        d = by_key.get(key)
        if not d:
            continue
        d["label_ko"], d["label_en"] = ko, en
        ordered.append(d)
    data["discoveries"] = ordered

    if not ordered:
        sys.exit("[FATAL] 발견 항목이 비어 있습니다.")
    print(f"[ok] {len(ordered)}개 항목 큐레이션 완료.")
    return data

# ── Send ──────────────────────────────────────────────────────────────────────
def send_email(html, subject):
    gmail     = require_env("GMAIL_ADDRESS")
    app_pw    = require_env("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("RECIPIENT_EMAIL", gmail)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = formataddr(("오늘의 발견", gmail))
    msg["To"]      = recipient
    msg.attach(MIMEText("오늘의 발견 — HTML 메일입니다.", "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    print(f"[info] Sending to {recipient}…")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail, app_pw)
        server.sendmail(gmail, [recipient], msg.as_string())
    print("[ok] 발송 완료.")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    require_env("ANTHROPIC_API_KEY")
    taste         = load_taste_profile()
    date_str, now = today_kr()

    data             = curate(taste, date_str)
    data["date_str"] = date_str
    html             = render_email(data)

    out = os.path.join(HERE, "last_issue.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[info] 미리보기 저장: {out}")

    subject = f"오늘의 발견 · {now.month}월 {now.day}일"
    if DRY_RUN:
        print("[dry-run] 발송 건너뜀.")
        return
    send_email(html, subject)

if __name__ == "__main__":
    main()
