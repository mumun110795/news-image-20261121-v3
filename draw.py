#!/usr/bin/env python3
"""news-image-20261121-v3: draw the Saturday 21 Nov 2026 broadsheet.

Fresh from-spec build. Every figure was re-verified against wire reporting
on 21 Nov 2026 before drawing; unverifiable or stale items were dropped
(see NOTES at the bottom of this file). Deterministic: same input -> same
bytes. Stdlib + Pillow for the local render; the shipped entrypoint
(main.py) only copies the finished entry.png.
"""
import hashlib
from collections import Counter
from PIL import Image, ImageDraw, ImageFont

W = H = 1024
M = 14                      # outer margin
CW = W - 2 * M              # 996 content width
CREAM = (244, 236, 216)
PAPER = (250, 244, 228)
INK = (26, 26, 26)
RED = (178, 32, 42)
NAVY = (31, 58, 95)
GOLD = (201, 162, 39)
DARK = (18, 18, 18)
GREY = (96, 90, 76)
TEAL = (18, 110, 110)
GREEN = (28, 120, 60)

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(size, bold=False):
    return ImageFont.truetype(FB if bold else FR, size)


def wrap(text, fnt, width, dr=None):
    """Greedy word wrap; returns list of lines that fit `width` px."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if fnt.getlength(t) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_one(text, fnt, width):
    """Trim words off the end until the single line fits."""
    words = text.split()
    while words and fnt.getlength(" ".join(words)) > width:
        words.pop()
    return " ".join(words)


def text_lines(dr, x, y, lines, fnt, fill=INK, leading=None, align="left",
               box_w=None):
    """Draw lines; returns y just below the last line."""
    lh = leading if leading else int(fnt.size * 1.22)
    for ln in lines:
        if align == "center":
            dr.text((x + (box_w - fnt.getlength(ln)) / 2, y), ln,
                    font=fnt, fill=fill)
        elif align == "right":
            dr.text((x + box_w - fnt.getlength(ln), y), ln, font=fnt, fill=fill)
        else:
            dr.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


# ---------------------------------------------------------------- stories
# regions: Europe, N America, Asia-Pacific, S Asia, Global, Latin America,
# Middle East. Region counts are computed from this table at draw time.
HEROES = [
    dict(n=1, place="ANTALYA", topic="CLIMATE", tag="REPORTED",
         region="Europe", panel="cop",
         headline="COP31 runs into Saturday with no deal",
         body=("Talks in Antalya pass Friday's deadline with no deal. The "
               "draft drops all fossil-fuel mention and the $120bn "
               "adaptation target. France and Panama want a stronger "
               "text. COP32 goes to Addis Ababa.")),
    dict(n=2, place="KRYVYI RIH", topic="WAR", tag="REPORTED",
         region="Europe", panel="night",
         headline="Double-tap strike kills a boy, 7, and a paramedic",
         body=("Two ballistic missiles hit the city centre on Friday "
               "evening; drones then struck the same site as rescuers "
               "worked. A boy of 7 and a paramedic, 20, were killed. "
               "42 were hurt, 27 of them seriously.")),
    dict(n=3, place="NEW YORK", topic="MARKETS", tag="REPORTED",
         region="N America", panel="chart",
         headline="Wall Street's worst week since 2020",
         body=("Friday capped the worst week for US shares since March "
               "2020. The Nasdaq fell 5.3% on the day and 10% in the "
               "week, erasing its 2026 gains. Anthropic slid 8.5% to "
               "$88.91; Nvidia fell 14% in a day.")),
]

CARDS = [
    dict(n=4, place="PARIS", topic="PROTESTS", tag="REPORTED",
         region="Europe", icon="flag",
         headline="France marches again over living costs",
         body=("One authorised Paris march, 14:00 from République to "
               "Nation. 70,000 police deployed across France.")),
    dict(n=5, place="BRUSSELS", topic="AID", tag="REPORTED",
         region="Europe", icon="shield",
         headline="EU adopts €1bn of military aid for Kyiv",
         body=("Council funds joint buying of drones, air defence and "
               "ammo, due by end-2027. Britain adds 1,000 drones, "
               "£260m.")),
    dict(n=6, place="SHENZHEN", topic="SUMMIT", tag="REPORTED",
         region="Asia-Pacific", icon="table",
         headline="Shenzhen summit: warmth, little to show",
         body=("Trump threatens a 'tremendous tax' on US firms building "
               "AI datacentres abroad. The joint text skips Ukraine "
               "and Iran.")),
    dict(n=7, place="THE HAGUE", topic="LAW", tag="REPORTED",
         region="Asia-Pacific", icon="scales",
         headline="Myanmar rejects genocide ruling as 'unfair'",
         body=("The Court found genocide against the Rohingya, 9–6 — a "
               "first against a state. Reparations ordered.")),
    dict(n=8, place="ODISHA", topic="STORM", tag="REPORTED",
         region="S Asia", icon="cyclone",
         headline="Akvan weakens; Odisha counts no deaths",
         body=("No deaths, no major damage. 372,000 evacuated; orange "
               "alert in 14 districts; 39 trains off.")),
    dict(n=9, place="KYIV", topic="WAR", tag="REPORTED",
         region="Europe", icon="burst",
         headline="Barrage by night, blackouts by day",
         body=("110+ missiles and 400+ drones overnight; 9 killed, 28+ "
               "hurt. Three Kyiv bridges hit; two missiles land in "
               "Poland.")),
    dict(n=10, place="MUMBAI", topic="MARKETS", tag="REPORTED",
         region="S Asia", icon="bars",
         headline="India defies the rout as Sensex jumps",
         body=("Sensex rose 898 points to 83,919.71, a nine-month high. "
               "Nifty added 286 to 25,800.60 as banks led.")),
    dict(n=11, place="NEW YORK", topic="CYBER", tag="REPORTED",
         region="N America", icon="lock",
         headline="Cyberattack hits payment giants' vendor",
         body=("JPMorgan, Visa, Mastercard report a vendor breach. "
               "Marketing data only; no card numbers. Payment "
               "networks not hit.")),
    dict(n=12, place="WASHINGTON", topic="CYBER", tag="REPORTED",
         region="N America", icon="bug",
         headline="Hackers breach the US Agriculture Dept",
         body=("Intruders broke into the farmer-payments system, NBC "
               "reports. Staff were told on Thursday. Culprit "
               "unknown.")),
    dict(n=13, place="ROME", topic="FOOD AID", tag="FORECAST",
         region="Global", icon="bowl",
         headline="Food aid faces a funding cliff in 2027",
         body=("The World Food Programme seeks $12bn to help 91m "
               "people, down from 110m. 266m face acute hunger.")),
    dict(n=14, place="COPENHAGEN", topic="SPY ROW", tag="REPORTED",
         region="Europe", icon="dkflag",
         headline="Denmark expels a Russian diplomat",
         body=("The defence attaché has 7 days to leave. Copenhagen "
               "accuses Moscow of plotting to kill a rapper; Russia "
               "denies it.")),
    dict(n=15, place="WELLINGTON", topic="CRICKET", tag="REPORTED",
         region="Asia-Pacific", icon="bat",
         headline="India 159 for 1, still 209 behind",
         body=("NZ made 368; Jaiswal hit 85 and Rahul 52* as India "
               "reached 159 for 1 at stumps on day two.")),
]

BRIEFS = [
    (16, "LA fire accused convicted; Palisades blaze killed 12", "N America"),
    (17, "Berlin students march against rearmament", "Europe"),
    (18, "Paris police guilty in Zecler beating case", "Europe"),
    (19, "Bolsonaro taken to hospital with stomach pain", "Latin America"),
    (20, "Carlsen forfeits a rapid game", "Europe"),
    (21, "US releases more UFO footage", "N America"),
    (22, "Nepal: a test for PM Balendra Shah", "S Asia"),
    (23, "Hong Kong backs Tai Po fire survivors", "Asia-Pacific"),
    (24, "Modi opens first SCO dialogue forum in Delhi", "S Asia"),
    (25, "Top court rejects Cauvery water plea", "S Asia"),
    (26, "Hyundai Elantra 2027 at LA Auto Show", "N America"),
    (27, "Potatoes grow in simulated moon soil", "N America"),
    (28, "First black-hole image validated", "Global"),
    (29, "Gates warns of a major cyberattack", "Global"),
    (30, "Two Salvadoran soldiers die in Haiti", "N America"),
    (31, "Colombia's hippos put pupils at risk", "Latin America"),
    (32, "UN chief: Myanmar must take Rohingya back", "Asia-Pacific"),
    (33, "Estonia to shut road borders with Russia", "Europe"),
    (34, "Ukraine hits Druzhba pipeline in Russia", "Europe"),
    (35, "Poland scrambles jets as missiles land", "Europe"),
    (36, "UNICEF: 1,144 children hurt or killed in Ukraine", "Europe"),
    (37, "Russia hits Europe's biggest substation", "Europe"),
    (38, "Reports: SEC examines Nvidia's accounting", "N America"),
    (39, "Cheetah gives birth at Kuno park", "S Asia"),
    (40, "Fear gauge VIX jumps to 37", "N America"),
    (41, "S&P 500 in correction after 7th straight loss", "N America"),
    (42, "Nasdaq erases its gains for 2026", "N America"),
]

TIMELINE = [
    ("07:30", "ODISHA", "Akvan crosses coast near Gopalpur; 372,000 evacuated"),
    ("14:00", "PARIS", "March sets off from République to Nation"),
    ("16:00", "NEW YORK", "Nasdaq closes down 5.3%; worst week since 2020"),
    ("18:00", "ANTALYA", "Deadline passes with no deal; talks into overtime"),
    ("22:24", "KRYVYI RIH", "Boy, 7, dies in hospital; toll now 2 dead"),
    ("23:00", "KRYVYI RIH", "Toll rises: 42 hurt, 27 of them seriously"),
]

STATS = [
    ("42", "hurt in Kryvyi Rih; 2 dead"),
    ("372,000", "evacuated before Akvan"),
    ("–10%", "Nasdaq's week, worst since 2020"),
    ("+898", "Sensex points on Friday"),
    ("€1bn", "new EU military aid to Kyiv"),
    ("70,000", "police out for Paris march"),
]

MARKETS = [
    ("Nasdaq", "–5.3% Fri · –10% week"),
    ("S&P 500", "–3.7% Fri · –8.6% week"),
    ("Dow", "–1.9% Fri · –8% week"),
    ("Anthropic", "–8.5% · $88.91"),
    ("Nvidia", "–14% · VIX 37"),
    ("Sensex", "+898 · 9-mo high"),
]

REGIONS = ["Europe", "N America", "Asia-Pacific", "S Asia",
           "Global", "Latin America", "Middle East"]

# lon/lat of the 15 numbered stories, for the map pins.
PINS = {1: (27.0, 33.5), 2: (33.0, 43.5), 3: (-74.0, 40.7), 4: (-4.0, 45.5),
        5: (10.0, 49.0), 6: (114.05, 22.55), 7: (0.0, 55.0),
        8: (85.8, 20.3), 9: (38.0, 53.0), 10: (72.9, 19.1),
        11: (-64.0, 45.0), 12: (-86.0, 34.5), 13: (14.0, 39.5),
        14: (18.0, 58.0), 15: (174.78, -41.29)}


# ---------------------------------------------------------------- drawing
def pin_badge(dr, x, y, n, d=17):
    dr.ellipse([x, y, x + d, y + d], fill=RED, outline=INK, width=1)
    t = str(n)
    f = font(10, True)
    dr.text((x + (d - f.getlength(t)) / 2, y + 2), t, font=f, fill=(255, 255, 255))


def tag_chip(dr, x, y, tag):
    f = font(9, True)
    w = f.getlength(tag) + 8
    fill = NAVY if tag == "REPORTED" else (TEAL if tag == "FORECAST"
                                           else (150, 110, 20))
    dr.rectangle([x, y, x + w, y + 13], fill=fill)
    dr.text((x + 4, y + 1), tag, font=f, fill=(255, 255, 255))
    return w


def hero_panel(dr, kind, x, y, w, h):
    """Illustrated panel on top of each hero card."""
    if kind == "cop":
        bands = [(16, 96, 120), (38, 138, 130), (210, 150, 60),
                 (232, 190, 80), (240, 214, 130)]
        bh = h / len(bands)
        for i, c in enumerate(bands):
            dr.rectangle([x, y + i * bh, x + w, y + (i + 1) * bh], fill=c)
        dr.ellipse([x + w - 66, y + 8, x + w - 22, y + 52], fill=(255, 214, 90),
                   outline=(255, 240, 160), width=2)
        cx, cy, r = x + 62, y + h // 2 + 2, 30
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(70, 160, 190),
                   outline=(255, 255, 255), width=2)
        for k in range(-2, 3):
            yy = cy + k * 11
            dr.arc([cx - r, yy - 6, cx + r, yy + 6], 0, 360,
                   fill=(255, 255, 255), width=1)
        for k in (-1, 0, 1):
            dr.arc([cx + k * 15 - 7, cy - r, cx + k * 15 + 7, cy + r], 0, 360,
                   fill=(255, 255, 255), width=1)
        dr.rectangle([x + w - 36, y + h - 48, x + w - 28, y + h - 26],
                     fill=(200, 40, 50))
        dr.ellipse([x + w - 41, y + h - 30, x + w - 23, y + h - 12],
                   fill=(200, 40, 50))
        dr.rectangle([x, y + h - 22, x + w, y + h], fill=DARK)
        f = font(13, True)
        dr.text((x + 10, y + h - 20), "1.5°C", font=f, fill=(255, 255, 255))
        dr.text((x + 78, y + h - 19), "OVERSHOOT ACKNOWLEDGED",
                font=font(10, True), fill=(255, 214, 90))
    elif kind == "night":
        dr.rectangle([x, y, x + w, y + h], fill=(12, 18, 48))
        import random
        rnd = random.Random(7)
        for _ in range(46):
            sx, sy = x + rnd.randint(2, w - 2), y + rnd.randint(2, h - 30)
            dr.point((sx, sy), fill=(255, 255, 220))
        dr.ellipse([x + w - 52, y + 8, x + w - 28, y + 32], fill=(240, 238, 210))
        dr.ellipse([x + w - 46, y + 10, x + w - 30, y + 26], fill=(12, 18, 48))
        base = y + h
        blocks = [(0, 46, 34), (40, 62, 22), (78, 52, 44), (126, 70, 26),
                  (160, 58, 40), (206, 66, 24), (238, 50, 36), (276, 60, 28)]
        for bx, bw, bh in blocks:
            dr.rectangle([x + bx, base - bh, x + bx + bw, base],
                         fill=(22, 26, 56))
            for wy in range(base - bh + 6, base - 6, 10):
                for wx in range(x + bx + 5, x + bx + bw - 5, 10):
                    if (wx + wy) % 20 == 0:
                        dr.rectangle([wx, wy, wx + 4, wy + 5], fill=(255, 205, 80))
        cx, cy = x + w - 92, y + 34
        import math
        outer = [20, 13, 22, 12, 19, 13, 21, 12]
        pts = []
        for k, r in enumerate(outer):
            a = math.radians(k * 45 + 10)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        dr.polygon(pts, fill=(230, 80, 30))
        dr.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(255, 220, 90))
        for sx, sy in ((cx - 34, cy + 16), (cx - 22, cy + 24), (cx + 26, cy + 18)):
            dr.ellipse([sx - 4, sy - 3, sx + 4, sy + 3], fill=(90, 90, 110))
    else:  # chart
        dr.rectangle([x, y, x + w, y + h], fill=(10, 30, 22))
        for gy in range(y + 10, y + h - 8, 14):
            dr.line([(x + 6, gy), (x + w - 6, gy)], fill=(30, 70, 50), width=1)
        pts = [(x + 8, y + 18), (x + 60, y + 26), (x + 110, y + 22),
               (x + 160, y + 40), (x + 210, y + 34), (x + 255, y + 58),
               (x + 300, y + 66)]
        dr.line(pts, fill=(220, 60, 60), width=3, joint="curve")
        for px, py in pts[1:]:
            dr.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 255, 255))
        f = font(15, True)
        dr.text((x + 10, y + h - 24), "NASDAQ –10% IN A WEEK",
                font=f, fill=(255, 255, 255))
        dr.text((x + w - 74, y + 8), "–5.3% FRI", font=font(11, True),
                fill=(255, 90, 90))


def draw_icon(dr, kind, x, y, s=22):
    """Small line icon for a card, drawn in ink/red."""
    if kind == "flag":
        dr.line([(x + 3, y + 2), (x + 3, y + s - 2)], fill=INK, width=2)
        dr.polygon([(x + 3, y + 2), (x + s - 2, y + 6), (x + 3, y + 11)],
                   fill=RED)
    elif kind == "shield":
        dr.polygon([(x + 2, y + 3), (x + s - 2, y + 3), (x + s - 2, y + 12),
                    (x + s // 2, y + s - 2), (x + 2, y + 12)],
                   outline=NAVY, width=2)
        dr.line([(x + 6, y + 11), (x + 10, y + 15), (x + 17, y + 7)],
                fill=NAVY, width=2)
    elif kind == "table":
        dr.line([(x + 2, y + 14), (x + s - 2, y + 14)], fill=INK, width=2)
        for px in (5, 11, 17):
            dr.ellipse([x + px - 2, y + 4, x + px + 2, y + 8], fill=RED)
            dr.line([(x + px, y + 8), (x + px, y + 14)], fill=INK, width=1)
    elif kind == "scales":
        dr.line([(x + s // 2, y + 2), (x + s // 2, y + s - 3)], fill=INK, width=2)
        dr.line([(x + 3, y + 5), (x + s - 3, y + 5)], fill=INK, width=2)
        dr.polygon([(x + 1, y + 13), (x + 8, y + 13), (x + 4, y + 6)],
                   outline=INK, width=1)
        dr.polygon([(x + s - 8, y + 13), (x + s - 1, y + 13),
                    (x + s - 4, y + 6)], outline=INK, width=1)
    elif kind == "cyclone":
        for r in (9, 6, 3):
            dr.arc([x + s // 2 - r, y + s // 2 - r, x + s // 2 + r,
                    y + s // 2 + r], 20, 300, fill=TEAL, width=2)
    elif kind == "burst":
        import math
        cx, cy = x + s // 2, y + s // 2
        for ang in range(0, 360, 30):
            a = math.radians(ang)
            dr.line([(cx + 3 * math.cos(a), cy + 3 * math.sin(a)),
                     (cx + 10 * math.cos(a), cy + 10 * math.sin(a))],
                    fill=RED, width=2)
        dr.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(255, 170, 40))
    elif kind == "bars":
        hs = [6, 10, 14, 18]
        for i, hh in enumerate(hs):
            dr.rectangle([x + 2 + i * 5, y + s - 2 - hh, x + 5 + i * 5,
                          y + s - 2], fill=GREEN)
    elif kind == "lock":
        dr.rectangle([x + 4, y + 10, x + s - 4, y + s - 2], fill=NAVY)
        dr.arc([x + 6, y + 2, x + s - 6, y + 12], 180, 360, fill=NAVY, width=2)
        dr.rectangle([x + s // 2 - 1, y + 14, x + s // 2 + 1, y + 18],
                     fill=(255, 255, 255))
    elif kind == "bug":
        dr.ellipse([x + 7, y + 6, x + s - 7, y + s - 4], fill=INK)
        dr.ellipse([x + 9, y + 2, x + s - 9, y + 8], fill=INK)
        for ly in (9, 13, 17):
            dr.line([(x + 7, y + ly), (x + 1, y + ly - 3)], fill=INK, width=1)
            dr.line([(x + s - 7, y + ly), (x + s - 1, y + ly - 3)],
                    fill=INK, width=1)
    elif kind == "bowl":
        dr.arc([x + 2, y + 8, x + s - 2, y + s - 2], 0, 180, fill=INK, width=2)
        dr.line([(x + 2, y + 8), (x + s - 2, y + 8)], fill=INK, width=2)
        for sx in (7, 11, 15):
            dr.line([(x + sx, y + 6), (x + sx, y + 1)], fill=RED, width=2)
    elif kind == "dkflag":
        dr.rectangle([x + 1, y + 3, x + s - 1, y + s - 3], fill=RED)
        dr.rectangle([x + 7, y + 3, x + 10, y + s - 3], fill=(255, 255, 255))
        dr.rectangle([x + 1, y + 9, x + s - 1, y + 12], fill=(255, 255, 255))
    elif kind == "bat":
        dr.polygon([(x + 4, y + s - 2), (x + 10, y + 8), (x + 14, y + 11),
                    (x + 17, y + 16), (x + 12, y + s - 2)], fill=(205, 165, 110),
                   outline=INK)
        dr.line([(x + 13, y + 11), (x + 18, y + 3)], fill=INK, width=3)


# --- dotted world map: rough land boxes (lon/lat), sampled on a grid ---
LAND_BOXES = [
    (-168, -95, 60, 71), (-168, -55, 45, 60), (-125, -66, 30, 45),
    (-118, -80, 15, 30), (-92, -78, 7, 15), (-58, -20, 60, 83),
    (-80, -35, -55, -30), (-80, -35, -30, -5), (-78, -45, -5, 10),
    (-10, 40, 36, 70), (-5, 2, 50, 58), (-18, 50, -35, 35),
    (-18, 32, 15, 35), (32, 50, -35, 15), (40, 180, 45, 75),
    (40, 135, 25, 45), (60, 100, 5, 25), (95, 140, -10, 10),
    (100, 110, 5, 25), (130, 145, 31, 45), (113, 154, -40, -10),
    (167, 178, -47, -34), (68, 90, 8, 35),
]


def is_land(lon, lat):
    return any(a <= lon <= b and c <= lat <= d for a, b, c, d in LAND_BOXES)


def draw_map(dr, x, y, w, h):
    dr.rectangle([x, y, x + w, y + h], fill=PAPER, outline=INK, width=1)
    lon0, lon1, lat0, lat1 = -170, 190, 78, -56
    step_lon, step_lat = 5.2, 5.0
    lon = lon0
    while lon < lon1:
        lat = lat0
        while lat > lat1:
            if is_land(lon, lat):
                px = x + (lon - lon0) / (lon1 - lon0) * w
                py = y + (lat0 - lat) / (lat0 - lat1) * h
                dr.ellipse([px - 1, py - 1, px + 1, py + 1], fill=TEAL)
            lat -= step_lat
        lon += step_lon
    for n, (lon, lat) in sorted(PINS.items()):
        px = x + (lon - lon0) / (lon1 - lon0) * w
        py = y + (lat0 - lat) / (lat0 - lat1) * h
        r = 5
        dr.ellipse([px - r, py - r, px + r, py + r], fill=RED,
                   outline=(255, 255, 255), width=1)
        t = str(n)
        f = font(8, True)
        dr.text((px - f.getlength(t) / 2, py - 4), t, font=f,
                fill=(255, 255, 255))
    cap = "DOTS: LAND · RED PINS: STORIES 1–15"
    cf = font(9, True)
    dr.rectangle([x + 3, y + h - 16, x + 8 + cf.getlength(cap), y + h - 3],
                 fill=PAPER)
    dr.text((x + 6, y + h - 14), cap, font=cf, fill=GREY)


# ---------------------------------------------------------------- layout
def build():
    img = Image.new("RGB", (W, H), CREAM)
    dr = ImageDraw.Draw(img)
    dr.rectangle([6, 6, W - 7, H - 7], outline=INK, width=2)
    dr.rectangle([10, 10, W - 11, H - 11], outline=INK, width=1)

    # masthead
    f10 = font(10, True)
    dr.text((M, 16), "EST. 2026", font=f10, fill=INK)
    rt = "ONE IMAGE · ONE DAY"
    dr.text((M + CW - f10.getlength(rt), 16), rt, font=f10, fill=INK)
    f44 = font(44, True)
    title = "THE SATURDAY WORLD"
    dr.text(((W - f44.getlength(title)) / 2, 26), title, font=f44, fill=INK)
    dr.line([(M, 78), (M + CW, 78)], fill=INK, width=2)
    f11b = font(11, True)
    dr.text((M, 84), "NO. 325", font=f11b, fill=INK)
    date = "SATURDAY 21 NOVEMBER 2026"
    f20 = font(20, True)
    dr.text(((W - f20.getlength(date)) / 2, 82), date, font=f20, fill=RED)
    wk = "WEEK 47"
    dr.text((M + CW - f11b.getlength(wk), 84), wk, font=f11b, fill=INK)
    dr.line([(M, 104), (M + CW, 104)], fill=INK, width=1)

    # stat strip
    y0, sh = 110, 46
    dr.rectangle([M, y0, M + CW, y0 + sh], fill=DARK)
    cell = CW / 6
    for i, (num, lab) in enumerate(STATS):
        cx = M + i * cell
        if i:
            dr.line([(cx, y0 + 6), (cx, y0 + sh - 6)], fill=(90, 90, 90), width=1)
        fn = font(20, True)
        dr.text((cx + 10, y0 + 4), num, font=fn,
                fill=GOLD if i in (2, 4) else (255, 255, 255))
        fl = font(10)
        lab_lines = wrap(lab, fl, cell - 20)
        yy = y0 + 27 if len(lab_lines) == 1 else y0 + 24
        for ln in lab_lines[:1]:
            dr.text((cx + 10, yy), ln, font=fl, fill=(220, 220, 210))
        if len(lab_lines) > 1:
            dr.text((cx + 10, yy + 11), lab_lines[1], font=fl,
                    fill=(220, 220, 210))

    # timeline
    ty = 164
    dr.text((M, ty), "THE DAY BY HOURS", font=font(11, True), fill=INK)
    sub = "Friday night into Saturday"
    dr.text((M + CW - font(10).getlength(sub), ty + 1), sub, font=font(10),
            fill=RED)
    dr.line([(M, ty + 15), (M + CW, ty + 15)], fill=INK, width=1)
    tcell = CW / 6
    for i, (tm, pl, txt) in enumerate(TIMELINE):
        cx = M + i * tcell
        if i:
            dr.line([(cx - 5, ty + 20), (cx - 5, ty + 56)], fill=(180, 170, 145),
                    width=1)
        dr.text((cx, ty + 20), tm, font=font(11, True), fill=RED)
        dr.text((cx + 42, ty + 20), pl, font=font(10, True), fill=INK)
        for j, ln in enumerate(wrap(txt, font(10), tcell - 10)):
            dr.text((cx, ty + 35 + j * 12), ln, font=font(10), fill=INK)

    # heroes
    hy, hh, pw, gap = 230, 220, 324, 12
    for i, st in enumerate(HEROES):
        hx = M + i * (pw + gap)
        dr.rectangle([hx, hy, hx + pw, hy + hh], fill=PAPER, outline=INK,
                     width=1)
        hero_panel(dr, st["panel"], hx + 1, hy + 1, pw - 2, 82)
        ky = hy + 88
        pin_badge(dr, hx + 8, ky, st["n"])
        dr.text((hx + 30, ky + 2), st["place"] + " · " + st["topic"],
                font=font(11, True), fill=INK)
        tag_chip(dr, hx + pw - 62, ky + 1, st["tag"])
        y = text_lines(dr, hx + 8, ky + 22,
                       wrap(st["headline"], font(21, True), pw - 16),
                       font(21, True), leading=24)
        text_lines(dr, hx + 8, y + 2,
                   wrap(st["body"], font(12), pw - 16), font(12), leading=14)

    # cards: 4 x 3
    cy0, ch, cw, cg = 458, 96, 243, 8
    for i, st in enumerate(CARDS):
        r, c = divmod(i, 4)
        cx = M + c * (cw + cg)
        cy = cy0 + r * (ch + cg)
        dr.rectangle([cx, cy, cx + cw, cy + ch], fill=PAPER, outline=INK,
                     width=1)
        ky = cy + 5
        pin_badge(dr, cx + 6, ky, st["n"], d=15)
        dr.text((cx + 26, ky + 1), st["place"] + " · " + st["topic"],
                font=font(10, True), fill=INK)
        tag_chip(dr, cx + cw - 58, ky, st["tag"])
        hy2 = cy + 24
        draw_icon(dr, st["icon"], cx + 6, hy2, s=22)
        hl = wrap(st["headline"], font(13, True), cw - 40)
        y = text_lines(dr, cx + 32, hy2, hl, font(13, True), leading=15)
        text_lines(dr, cx + 6, max(y + 1, hy2 + 30),
                   wrap(st["body"], font(11), cw - 12), font(11), leading=13)

    # bottom boxes
    by, bh = 768, 62
    boxes = [(M, 330), (M + 338, 336), (M + 682, 314)]
    dr.rectangle([boxes[0][0], by, boxes[0][0] + 330, by + bh], fill=DARK)
    dr.text((boxes[0][0] + 8, by + 4), "MARKETS AT THE CLOSE — FRIDAY",
            font=font(10, True), fill=GOLD)
    for j, (k, v) in enumerate(MARKETS):
        col, row = divmod(j, 3)
        xx = boxes[0][0] + 8 + col * 165
        yy = by + 19 + row * 14
        dr.text((xx, yy), k, font=font(10, True), fill=(255, 255, 255))
        dr.text((xx + font(10, True).getlength(k) + 5, yy), v, font=font(10),
                fill=(220, 220, 210))
    dr.rectangle([boxes[1][0], by, boxes[1][0] + 336, by + bh], fill=PAPER,
                 outline=INK, width=1)
    dr.text((boxes[1][0] + 8, by + 4), "THE VERDICT — THE HAGUE",
            font=font(10, True), fill=RED)
    text_lines(dr, boxes[1][0] + 8, by + 19,
               wrap("The World Court's 9–6 finding of genocide against "
                    "Myanmar — the first against a state — now faces its "
                    "test: reparations and return, which Myanmar rejects.",
                    font(11), 320), font(11), leading=13)
    dr.rectangle([boxes[2][0], by, boxes[2][0] + 314, by + bh], fill=PAPER,
                 outline=INK, width=1)
    dr.text((boxes[2][0] + 8, by + 4), "DATE CHECK", font=font(10, True),
            fill=RED)
    dc = ["Today: Saturday 21 November 2026",
          "Day 325 of 2026 · ISO week 47",
          "Friday news: only with Saturday follow-up"]
    text_lines(dr, boxes[2][0] + 8, by + 19, dc, font(11), leading=13)

    # region bar + map + briefs (counts computed from the story table)
    counts = Counter()
    for st in HEROES + CARDS:
        counts[st["region"]] += 1
    for _, _, rg in BRIEFS:
        counts[rg] += 1
    total = sum(counts.values())
    assert total == 42, total
    ry = 836
    dr.text((M, ry), "WHERE IT HAPPENED", font=font(11, True), fill=INK)
    reg_txt = "  ·  ".join(f"{r} {counts[r]}" for r in REGIONS if counts[r])
    dr.text((M + 150, ry + 1), reg_txt, font=font(10, True), fill=RED)
    dr.text((M + CW - font(10).getlength(f"{total} stories"), ry + 1),
            f"{total} stories", font=font(10, True), fill=INK)
    dr.line([(M, ry + 15), (M + CW, ry + 15)], fill=INK, width=1)
    my = ry + 21
    mh = 140
    draw_map(dr, M, my, 330, mh)
    bx = M + 338
    bw = CW - 338
    col_w = bw / 2
    f10b = font(10)
    for i, (n, txt, _) in enumerate(BRIEFS):
        col, row = divmod(i, 14)
        xx = bx + col * col_w
        yy = my + row * 10
        num = f"{n}. "
        line = fit_one(num + txt, f10b, col_w - 4)
        dr.text((xx, yy), line, font=f10b, fill=INK)
    fy = my + mh + 4
    dr.text((M, fy), "Drawn by an AI agent · Wire reports, 20–21 Nov 2026",
            font=font(10), fill=GREY)
    src = "Sources: Reuters · AP · AFP · BBC · CNN · WSJ · Consilium · IMD"
    dr.text((M + CW - font(10).getlength(src), fy), src, font=font(10),
            fill=GREY)
    return img


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "entry.png"
    im = build()
    im.save(out, optimize=True)
    data = open(out, "rb").read()
    print(out, len(data), "bytes", hashlib.md5(data).hexdigest())


# ---------------------------------------------------------------- NOTES
# Verified 21 Nov 2026 (web sweep, named sources in the build session):
#  COP31: 3rd draft due Sat morning; fossil-fuel mention + $120bn adaptation
#    target dropped (Reuters/AP); 35% electricity by 2035 kept; COP32 Addis
#    Ababa (AsiaToday).  Kryvyi Rih: 2 dead (boy 7, paramedic 20), 42 hurt,
#    27 serious (Kyiv Independent/Ukrinform).  Markets: Nasdaq -5.3% Fri,
#    -10% wk; S&P -3.7%/-8.6%; Dow -1.9%/-8%; >$4tn wiped; Anthropic -8.5%
#    to $88.91; Nvidia -14%; VIX 37 (AP/WSJ/CNN).  Sensex +898 to 83,919.71
#    (PTI).  Akvan: 372,000 evacuated, no deaths, orange alert 14 districts,
#    39 ECR trains off (IMD via Indian press).  Paris: 14:00 République to
#    Nation, 70,000 police nationwide (AFP via Sortiraparis).  EU: €1bn
#    EPF aid, delivery by end-2027; UK 1,000 drones, £260m (Consilium).
#    Myanmar: ICJ 9-6, first state genocide finding; Myanmar calls it
#    "unfair" (AP/CNN).  Barrage: 110+ missiles (27 ballistic), 400+
#    drones, 9 killed, 28+ hurt, 3 Kyiv bridges, 2 Kh-101 in Poland (CNN/
#    Kyiv Independent).  Trump: "tremendous tax" on AI datacentres abroad
#    (Reuters, Fri presser).  Denmark: defence attaché out in 7 days over
#    Kyivstoner plot (Al Jazeera/WSJ).  USDA: farmer-payments system
#    breached (NBC via Reuters).  Vendor breach: JPMorgan/Visa/Mastercard,
#    marketing data only, no card numbers (Reuters, 19 Nov).  WFP: 2027
#    appeal $12bn for 91m (was 110m); 266m face acute hunger (Reuters).
#    Cricket: NZ 368 (Nicholls 175*), India 159/1, trail 209 (Cricinfo).
#    LA: Rinderknecht guilty, 2 arson counts; Palisades fire killed 12,
#    ~6,800 structures (Reuters).
# DROPPED vs the morning brief / v2:
#  - Venezuela "$120bn detained": FALSE. Truth (State Dept/KPMG, 12 Nov):
#    US handled $12.26bn, returned $12.11bn (~99%), $168.6m left in
#    escrow. Story also 9 days old; dropped entirely, $120bn stays only
#    with the COP31 adaptation target where it belongs.
#  - Gaza floods: the big tent-flood event was 6-9 Nov (OCHA/UN News),
#    not 20-21 Nov; dropped as stale.
#  - Myanmar death toll: sources conflict (~10,000 vs ~100,000); no toll
#    printed.
#  - VIX: brief said 35.89; AP reported 37 on Fri close; printed 37.
#  - Unverified numbers dropped: Malaysia 10,000 Rohingya resettlement,
#    Indonesia $30bn fires, Senate 51-48, Pete Rose pardon, $52m
#    schooling, Sweden envoy summons, "foreign inflows record India".
