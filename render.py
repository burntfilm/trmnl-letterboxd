#!/usr/bin/env python3
# axisofaction · letterboxd · TRMNL 800×480 e-ink

USERNAME = "axisofaction"
YEAR     = 2025

import io, datetime, re, requests, textwrap, feedparser
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

RSS_URL  = f"https://letterboxd.com/{USERNAME}/rss/"
YEAR_URL = f"https://letterboxd.com/{USERNAME}/year/{YEAR}/"

# ---------- scrape stats ----------
def year_stats():
    txt = BeautifulSoup(requests.get(YEAR_URL, timeout=15).text,
                        "html.parser").get_text(" ", strip=True).lower()
    films = int(re.search(r"([0-9][0-9,]*)\s+films logged", txt)
                .group(1).replace(",", ""))
    m_avg = re.search(r"([0-9]*\.?[0-9]+)\s+average per week", txt)
    if m_avg: perwk = float(m_avg.group(1))
    else:     perwk = round(films / datetime.date.today().isocalendar().week, 1)
    return films, perwk

# ---------- last four ----------
def last4():
    f = feedparser.parse(RSS_URL).entries[:4]
    return [{"title":e.get("letterboxd_filmTitle",e.title),
             "year": e.get("letterboxd_filmYear",""),
             "rate": e.get("letterboxd_memberRating",""),
             "like": "letterboxd_memberLike" in e} for e in f]

# ---------- draw PNG ----------
def render(stats, recent):
    W,H = 800,480; L = 260             # left column width
    img = Image.new("1",(W,H),255); d  = ImageDraw.Draw(img)

    font_path = "Inter-Regular.ttf"    # put this TTF in repo root
    big = ImageFont.truetype(font_path,140)
    num = ImageFont.truetype(font_path,90)
    sm  = ImageFont.truetype(font_path,34)

    films,perwk = stats
    # LEFT COLUMN
    d.text((40,10), str(YEAR),  font=big, fill=0)
    d.text((40,200), str(films), font=num, fill=0)
    d.text((40,290), "FILMS LOGGED", font=sm, fill=0)
    d.text((40,340), f"{perwk}", font=num, fill=0)
    d.text((40,430), "films / week", font=sm, fill=0)

    # RIGHT COLUMN HEADER
    d.text((L+20,20), "LAST 4 WATCHED", font=sm, fill=0)

    # helper: ellipsis that really fits
    def clip(txt,max_px,fnt):
        while fnt.getlength(txt+"…")>max_px and len(txt):
            txt=txt[:-1]
        return txt+"…" if len(txt)<len(r["title"]) else txt

    y = 70
    for r in recent:
        title = clip(r["title"], 340, sm)
        d.text((L+20,y),    title,           font=sm, fill=0)
        d.text((L+370,y),   str(r["year"]),  font=sm, fill=0)
        d.text((L+20,y+36), r["rate"],       font=sm, fill=0)
        if r["like"]: d.text((L+200,y+36),"♥",font=sm,fill=0)
        y += 90

    buf=io.BytesIO(); img.save(buf,"PNG",optimize=True)
    open("out.png","wb").write(buf.getbuffer())

if __name__=="__main__":
    render(year_stats(), last4())
