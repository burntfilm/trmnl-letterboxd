#!/usr/bin/env python3
# --- Letterboxd → TRMNL scraper | axisofaction | 2025 ---

USERNAME = "axisofaction"
YEAR     = 2025

import io, datetime, re, textwrap, requests, feedparser
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

RSS_URL  = f"https://letterboxd.com/{USERNAME}/rss/"
YEAR_URL = f"https://letterboxd.com/{USERNAME}/year/{YEAR}/"

# ---------- helper: scrape year page ----------
def year_stats():
    html  = requests.get(YEAR_URL, timeout=15).text
    txt   = BeautifulSoup(html, "html.parser").get_text(" ", strip=True).lower()

    m_films = re.search(r"([0-9][0-9,]*)\s+films logged", txt)
    if not m_films:
        raise RuntimeError("Couldn’t find ‘Films logged’ – is profile public?")
    films = int(m_films.group(1).replace(",", ""))

    m_avg = re.search(r"([0-9]*\.?[0-9]+)\s+average per week", txt)
    if m_avg:
        per_week = float(m_avg.group(1))
    else:                                     # fallback calculation
        wk      = datetime.date.today().isocalendar().week
        per_week = round(films / wk, 1)
    return films, per_week

# ---------- helper: latest 4 diary entries ----------
def last_four():
    feed = feedparser.parse(RSS_URL)
    out  = []
    for e in feed.entries[:4]:
        out.append({
            "title":  e.get("letterboxd_filmTitle",  e.title),
            "year":   e.get("letterboxd_filmYear",   ""),
            "rating": e.get("letterboxd_memberRating", ""),
            "like":   "letterboxd_memberLike" in e,
        })
    return out

# ---------- render 1-bit PNG ----------
def render(stats, recent):
    # ---- panel & font sizes ----
    W, H   = 800, 480                    # change if your TRMNL is different
    L_PAD  = 40                          # left margin
    COL2_X = 420                         # x-start of right column
    ROW_H  = 100                         # per-film row height

    img  = Image.new("1", (W, H), 255)   # white canvas
    draw = ImageDraw.Draw(img)

    big  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 160)
    med  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  80)
    sm   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",        36)

    films, perwk = stats

    # ---- left column ----
    draw.text((L_PAD,  10), str(YEAR),  font=big, fill=0)
    draw.text((L_PAD, 190), str(films), font=med, fill=0)
    draw.text((L_PAD, 280), "FILMS LOGGED", font=sm, fill=0)
    draw.text((L_PAD, 330), f"{perwk}", font=med, fill=0)
    draw.text((L_PAD, 410), "films / week", font=sm, fill=0)

    # ---- right column header ----
    draw.text((COL2_X,  10), "LAST 4 WATCHED", font=sm, fill=0)

    # ---- film rows ----
    y =  60
    for r in recent:
        # truncate long titles to fit within 26 chars (roughly 340px at this font)
        title = textwrap.shorten(r["title"], width=26, placeholder="…")
        draw.text((COL2_X, y), title, font=sm, fill=0)
        draw.text((COL2_X, y + 38), f"{r['year']}  {r['rating']}", font=sm, fill=0)
        if r["like"]:
            draw.text((COL2_X + 330, y + 38), "♥", font=sm, fill=0)
        y += ROW_H

    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    with open("out.png", "wb") as f:
        f.write(buf.getbuffer())

if __name__ == "__main__":
    render(year_stats(), last_four())
