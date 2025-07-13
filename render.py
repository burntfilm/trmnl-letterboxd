#!/usr/bin/env python3
# Renders a 400 × 300 1-bit PNG for a TRMNL panel using only two public pages:
#   • https://letterboxd.com/axisofaction/year/2025/
#   • https://letterboxd.com/axisofaction/rss/
# No API keys, no login required.

USERNAME  = "axisofaction"
YEAR      = 2025
RSS_URL   = f"https://letterboxd.com/{USERNAME}/rss/"
YEAR_URL  = f"https://letterboxd.com/{USERNAME}/year/{YEAR}/"

import io, datetime, re, requests, feedparser
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont


# ---------- scrape “Films logged” & “Average per week” ----------
def get_year_stats():
    html  = requests.get(YEAR_URL, timeout=15).text
    text  = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)

    m_films = re.search(r"([0-9][0-9,]*)\s+Films logged",       text)
    if not m_films:
        raise ValueError("Couldn’t find ‘Films logged’ — is the profile public?")

    films = int(m_films.group(1).replace(",", ""))

    m_avg   = re.search(r"([0-9]*\.?[0-9]+)\s+Average per week", text)
    if m_avg:
        per_week = float(m_avg.group(1))
    else:                     # fall-back: calculate it ourselves
        week_no  = datetime.date.today().isocalendar().week
        per_week = round(films / week_no, 1)

    return films, per_week


# ---------- grab the latest four diary entries ----------
def get_last4():
    feed = feedparser.parse(RSS_URL)
    out  = []
    for e in feed.entries[:4]:
        out.append({
            "title":  e.get("letterboxd_filmTitle",  e.title),
            "year":   e.get("letterboxd_filmYear",   ""),
            "rating": e.get("letterboxd_memberRating", ""),  # ★★★★½ etc — keep the ½
            "like":   "letterboxd_memberLike" in e,
        })
    return out


# ---------- compose the 1-bit PNG ----------
def render_png(stats, recent):
    W, H = 400, 300                      # TRMNL v1 native panel size
    img   = Image.new("1", (W, H), 255)  # white canvas
    d     = ImageDraw.Draw(img)

    f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
    f_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
    f_sm  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",        18)

    films, perwk = stats

    # left column ─ year stats
    d.text((20,  10), str(YEAR),  font=f_big, fill=0)
    d.text((20, 100), str(films), font=f_med, fill=0)
    d.text((20, 140), "FILMS LOGGED", font=f_sm, fill=0)
    d.text((20, 170), f"{perwk}", font=f_med, fill=0)
    d.text((20, 210), "films / week", font=f_sm, fill=0)

    # right column ─ latest watches
    d.text((180, 10), "LAST 4 WATCHED", font=f_sm, fill=0)
    y = 40
    for r in recent:
        d.text((180, y),   r["title"][:18], font=f_sm, fill=0)     # truncate long titles
        d.text((340, y),   str(r["year"]), font=f_sm, fill=0)
        d.text((180, y+18), r["rating"],   font=f_sm, fill=0)      # keeps ★★★★½
        if r["like"]:
            d.text((350, y+18), "♥", font=f_sm, fill=0)
        y += 44

    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    with open("out.png", "wb") as f:
        f.write(buf.getbuffer())


if __name__ == "__main__":
    render_png(get_year_stats(), get_last4())
