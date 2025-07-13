#!/usr/bin/env python3
# Scrapes Letterboxd /year/<YYYY>/ page + RSS feed and renders out.png

USERNAME  = "axisofaction"
YEAR      = 2025                    # change when the calendar flips
RSS_URL   = f"https://letterboxd.com/axisofaction/rss/"
YEAR_URL  = f"https://letterboxd.com/axisofaction/year/2025/"

import io, re, requests, datetime, feedparser
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

# ---------- helpers ----------
def get_year_stats():
    """Return (films_logged:int, avg_per_week:float)"""
    html = requests.get(YEAR_URL, timeout=15).text
    soup = BeautifulSoup(html, "html.parser")
    banner = soup.find(text=re.compile(r"Films logged"))
    m1 = re.search(r"(\d[\d,]*)\s+Films logged", banner)
    m2 = re.search(r"([\d.]+)\s+Average per week", banner)
    films = int(m1.group(1).replace(",", ""))
    perwk = float(m2.group(1))
    return films, perwk

def get_last4():
    feed = feedparser.parse(RSS_URL)
    out = []
    for e in feed.entries[:4]:
        out.append({
            "title": e.get("letterboxd_filmTitle", e.title),
            "year":  e.get("letterboxd_filmYear", ""),
            "rating": e.get("letterboxd_memberRating", ""),
            "like":   "letterboxd_memberLike" in e,
        })
    return out

def stars(s):                # ★★★½ → remove the ½ for simplicity
    return s.replace("½", "")

# ---------- compose PNG ----------
def render_png(stats, recent):
    W, H = 400, 300      # TRMNL v1 panel
    img = Image.new("1", (W, H), 255)
    d   = ImageDraw.Draw(img)
    f_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 70)
    f_med = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
    f_sm  = ImageFont.truetype("DejaVuSans.ttf", 18)

    films, perwk = stats
    d.text((20, 10), str(YEAR), font=f_big, fill=0)
    d.text((20, 100), str(films), font=f_med, fill=0)
    d.text((20, 140), "FILMS LOGGED", font=f_sm, fill=0)
    d.text((20, 170), f"{perwk}", font=f_med, fill=0)
    d.text((20, 210), "films / week", font=f_sm, fill=0)

    d.text((180, 10), "LAST 4 WATCHED", font=f_sm, fill=0)
    y = 40
    for r in recent:
        d.text((180, y), f"{r['title'][:18]}", font=f_sm, fill=0)
        d.text((340, y), str(r['year']), font=f_sm, fill=0)
        d.text((180, y+18), stars(r['rating']), font=f_sm, fill=0)
        if r['like']:
            d.text((350, y+18), "♥", font=f_sm, fill=0)
        y += 44

    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    open("out.png", "wb").write(buf.getbuffer())

if __name__ == "__main__":
    render_png(get_year_stats(), get_last4())
