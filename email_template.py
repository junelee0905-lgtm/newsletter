# -*- coding: utf-8 -*-
"""
Email template — Apple.com / Keynote aesthetic.

Design language:
  · Stark white ground, large confident imagery
  · SF Pro via the -apple-system stack (true SF on Apple Mail; graceful fallback elsewhere)
  · Big light-weight headlines, tight tracking, generous air
  · Apple-blue links, hairline dividers, product-page rhythm
"""

import html as _html

# ── palette (Apple) ──────────────────────────────────────────────────────────
WHITE     = "#FFFFFF"   # page ground
PANEL     = "#FBFBFD"   # section panel (Apple's off-white)
INK       = "#1D1D1F"   # Apple near-black text
GREY      = "#86868B"   # Apple secondary grey
GREY2     = "#6E6E73"   # slightly darker secondary
HAIRLINE  = "#D2D2D7"   # Apple divider grey
BLUE      = "#0066CC"   # Apple link blue
NUMERAL   = "#E8E8ED"   # quiet large numerals

# ── font stacks ──────────────────────────────────────────────────────────────
# This is exactly how apple.com specifies its type. On Apple Mail it renders as SF Pro.
SF_DISPLAY = ("-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', "
              "'Helvetica Neue', 'Apple SD Gothic Neo', 'Pretendard', Arial, sans-serif")
SF_TEXT    = ("-apple-system, BlinkMacSystemFont, 'SF Pro Text', "
              "'Helvetica Neue', 'Apple SD Gothic Neo', 'Pretendard', Arial, sans-serif")


def _esc(s):
    return _html.escape(s or "", quote=True)


def _discovery_block(d, index, total):
    num      = f"{index:02d}"
    label_en = _esc(d.get("label_en", ""))
    label_ko = _esc(d.get("label_ko", ""))
    title    = _esc(d.get("title", ""))
    subtitle = _esc(d.get("subtitle", ""))
    body     = _esc(d.get("body", ""))
    aside    = _esc(d.get("aside", ""))      # 여담 / anecdote
    why      = _esc(d.get("why", ""))
    link     = d.get("link")
    link_lbl = _esc(d.get("link_label", "Learn more"))
    image    = d.get("image")                # hero image url
    image2   = d.get("image2")               # optional second image

    # ── hero image ──
    image_html = ""
    if image:
        image_html = f"""
        <tr><td style="padding:0 0 30px 0;">
          <img src="{_esc(image)}" width="504" alt="{title}"
               style="display:block;width:100%;max-width:504px;height:auto;border:0;
                      border-radius:18px;background:{PANEL};" />
        </td></tr>"""

    # ── eyebrow (category) ──
    eyebrow = f"""
        <div style="font-family:{SF_TEXT};font-size:12px;font-weight:600;
                    letter-spacing:0.06em;color:{GREY};text-transform:uppercase;">
          {label_en}<span style="color:{HAIRLINE};">&nbsp;·&nbsp;</span>{label_ko}
        </div>"""

    # ── subtitle ──
    subtitle_html = ""
    if subtitle:
        subtitle_html = f"""
        <div style="font-family:{SF_DISPLAY};font-size:19px;font-weight:400;
                    color:{GREY2};line-height:1.4;margin:8px 0 0 0;">{subtitle}</div>"""

    # ── body ──
    body_html = f"""
        <div style="font-family:{SF_TEXT};font-size:17px;font-weight:400;
                    color:{INK};line-height:1.6;margin:22px 0 0 0;">{body}</div>"""

    # ── second image (between body and aside) ──
    image2_html = ""
    if image2:
        image2_html = f"""
        <div style="margin:24px 0 0 0;">
          <img src="{_esc(image2)}" width="504" alt="{title}"
               style="display:block;width:100%;max-width:504px;height:auto;border:0;
                      border-radius:14px;background:{PANEL};" />
        </div>"""

    # ── aside (여담) — boxed, lighter ──
    aside_html = ""
    if aside:
        aside_html = f"""
        <div style="margin:24px 0 0 0;padding:18px 20px;background:{PANEL};border-radius:14px;">
          <div style="font-family:{SF_TEXT};font-size:11px;font-weight:600;letter-spacing:0.08em;
                      text-transform:uppercase;color:{GREY};margin:0 0 8px 0;">여담</div>
          <div style="font-family:{SF_TEXT};font-size:15px;font-weight:400;color:{GREY2};
                      line-height:1.6;">{aside}</div>
        </div>"""

    # ── why (lineage hook) ──
    why_html = ""
    if why:
        why_html = f"""
        <div style="font-family:{SF_TEXT};font-size:15px;font-weight:500;color:{INK};
                    line-height:1.55;margin:22px 0 0 0;">
          <span style="color:{GREY};">왜 당신에게 —</span> {why}</div>"""

    # ── link (Apple blue, chevron) ──
    link_html = ""
    if link:
        link_html = f"""
        <div style="margin:20px 0 0 0;">
          <a href="{_esc(link)}" target="_blank"
             style="font-family:{SF_TEXT};font-size:17px;font-weight:400;color:{BLUE};
                    text-decoration:none;">{link_lbl}&nbsp;&#8250;</a>
        </div>"""

    # divider above every block except the first
    divider = ""
    if index > 1:
        divider = f"""
        <tr><td style="padding:0;">
          <div style="border-top:1px solid {HAIRLINE};margin:0 0 56px 0;"></div>
        </td></tr>"""

    return f"""
    {divider}
    <tr><td style="padding:0 0 56px 0;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr><td>
          <div style="font-family:{SF_DISPLAY};font-size:54px;font-weight:700;
                      line-height:1;color:{NUMERAL};letter-spacing:-0.02em;margin:0 0 6px 0;">{num}</div>
          {eyebrow}
          <div style="font-family:{SF_DISPLAY};font-size:32px;font-weight:600;line-height:1.15;
                      color:{INK};letter-spacing:-0.02em;margin:10px 0 0 0;">{title}</div>
          {subtitle_html}
        </td></tr>
        {image_html}
        <tr><td>
          {body_html}
          {image2_html}
          {aside_html}
          {why_html}
          {link_html}
        </td></tr>
      </table>
    </td></tr>"""


def render_email(data):
    date_str = _esc(data.get("date_str", ""))
    intro    = _esc(data.get("intro", ""))
    discoveries = data.get("discoveries", [])
    total = len(discoveries)

    blocks = "".join(_discovery_block(d, i + 1, total) for i, d in enumerate(discoveries))

    intro_html = ""
    if intro:
        intro_html = f"""
        <div style="font-family:{SF_DISPLAY};font-size:21px;font-weight:400;line-height:1.5;
                    color:{GREY2};margin:0 auto;max-width:480px;">{intro}</div>"""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="x-apple-disable-message-reformatting">
<meta name="color-scheme" content="light only">
<meta name="supported-color-schemes" content="light">
<title>오늘의 발견</title>
<style>
  body {{ margin:0; padding:0; background:{WHITE}; -webkit-text-size-adjust:100%; }}
  a {{ color:{BLUE}; }}
  img {{ -ms-interpolation-mode:bicubic; }}
  @media only screen and (max-width:620px) {{
    .container {{ width:100% !important; }}
    .pad {{ padding-left:24px !important; padding-right:24px !important; }}
    .hero-title {{ font-size:40px !important; }}
  }}
</style>
</head>
<body style="margin:0;padding:0;background:{WHITE};">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;">
    오늘, 당신이 아직 모르는 여섯 가지. {intro}
  </div>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{WHITE};">
    <tr><td align="center" style="padding:0;">

      <table role="presentation" class="container" width="600" cellpadding="0" cellspacing="0" border="0"
             style="width:600px;max-width:600px;background:{WHITE};">

        <!-- ─── HERO (Keynote title slide) ─────────────────────────── -->
        <tr><td class="pad" style="padding:80px 48px 64px 48px;text-align:center;">
          <div style="font-family:{SF_TEXT};font-size:13px;font-weight:600;letter-spacing:0.04em;
                      color:{GREY};text-transform:uppercase;">Daily Discoveries</div>
          <div class="hero-title"
               style="font-family:{SF_DISPLAY};font-size:56px;font-weight:700;line-height:1.05;
                      color:{INK};letter-spacing:-0.03em;margin:14px 0 0 0;">오늘의 발견</div>
          <div style="font-family:{SF_TEXT};font-size:17px;font-weight:400;color:{GREY};
                      margin:16px 0 0 0;">{date_str}</div>
          <div style="margin:36px 0 0 0;">{intro_html}</div>
        </td></tr>

        <!-- ─── DISCOVERIES ────────────────────────────────────────── -->
        <tr><td class="pad" style="padding:8px 48px 0 48px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
            {blocks}
          </table>
        </td></tr>

        <!-- ─── FOOTER ─────────────────────────────────────────────── -->
        <tr><td class="pad" style="padding:20px 48px 72px 48px;text-align:center;">
          <div style="border-top:1px solid {HAIRLINE};margin:0 0 36px 0;"></div>
          <div style="font-family:{SF_DISPLAY};font-size:17px;font-weight:500;color:{INK};
                      line-height:1.5;">트렌드가 아니라, 트렌드가 참조하는 것.</div>
          <div style="font-family:{SF_TEXT};font-size:12px;font-weight:400;letter-spacing:0.02em;
                      color:{GREY};margin:14px 0 0 0;">Curated for you · 매일 아침</div>
        </td></tr>

      </table>

    </td></tr>
  </table>
</body>
</html>"""
