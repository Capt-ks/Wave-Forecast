import requests
import re
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# PART 1: Original AMZ726 Forecast (unchanged)
# ─────────────────────────────────────────────────────────────
URL = "https://www.ndbc.noaa.gov/data/Forecasts/FZCA52.TJSJ.html"
ZONE = "726"
FALLBACK = "Wave forecast temporarily unavailable."

forecast_text = FALLBACK

try:
    r = requests.get(URL, timeout=20)
    r.raise_for_status()
    html = r.text
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n")

    pattern = rf"({ZONE}.*?)(\\d{{3}}|$)"
    m = re.search(pattern, text, re.DOTALL)
    if m:
        block = m.group(1).replace("feet", "ft")
        lines = block.splitlines()
        periods = []
        current_label = None
        current_text = []

        for line in lines:
            line = line.strip()
            if re.match(r"^(REST OF TONIGHT|TODAY|MON|TUE|WED|THU|FRI|SAT|SUN)", line):
                if current_label and current_text:
                    periods.append((current_label, " ".join(current_text)))
                current_label = line
                current_text = []
            else:
                if current_label:
                    current_text.append(line)

        if current_label and current_text:
            periods.append((current_label, " ".join(current_text)))

        cleaned = [(lbl if lbl != "REST OF TONIGHT" else "TODAY", txt) for lbl, txt in periods][:6]

        final_lines = []
        first = True
        for label, txt in cleaned:
            if first:
                label = "Currently"
                first = False

            m = re.search(r"Wave Detail:\s*([A-Za-z]+)\s*(\d+)\s*ft\s*at\s*(\d+)\s*seconds?", txt, re.I)
            if m:
                dir_ = m.group(1).upper()
                h = int(m.group(2))
                p = m.group(3)
                height_str = f"{h-1}–{h+1} ft"
                final_lines.append(f"{label}: {height_str} @ {p}s {dir_}")

        if final_lines:
            forecast_text = "\n".join(final_lines)
except Exception as e:
    forecast_text = f"Forecast error: {str(e)}"

# ─────────────────────────────────────────────────────────────
# PART 2: FIXED & ROBUST Buoy 41043 parsing (current 2025 structure)
# ─────────────────────────────────────────────────────────────
sig_height = swell_height = swell_period = buoy_dir = "N/A"

try:
    buoy_url = "https://www.ndbc.noaa.gov/station_page.php?station=41043"
    buoy_r = requests.get(buoy_url, timeout=12)
    buoy_r.raise_for_status()
    buoy_soup = BeautifulSoup(buoy_r.text, "html.parser")

    # Find wave table by searching for WVHT marker
    table = None
    for t in buoy_soup.find_all("table"):
        if "WVHT" in t.get_text():
            table = t
            break

    if table:
        rows = table.find_all("tr")
        if len(rows) >= 2:
            # Latest row = index 1 (after header)
            cols = rows[1].find_all("td")
            if len(cols) >= 5:
                # Current column order (0-based):
                # 0: TIME, 1: WVHT ft, 2: SwH ft, 3: SwP sec, 4: SwD
                wvht = cols[1].get_text(strip=True)
                swh  = cols[2].get_text(strip=True)
                swp  = cols[3].get_text(strip=True)
                swd  = cols[4].get_text(strip=True)

                if wvht not in ["MM", "-", ""]: sig_height     = f"{wvht} ft"
                if swh  not in ["MM", "-", ""]: swell_height   = f"{swh} ft"
                if swp  not in ["MM", "-", ""]: swell_period   = f"{swp} sec"
                if swd  not in ["MM", "-", ""]: buoy_dir       = swd
except Exception as e:
    sig_height = swell_height = swell_period = buoy_dir = f"Fetch error: {str(e)}"

# ─────────────────────────────────────────────────────────────
# PART 3: Image Generation + Bottom Section
# ─────────────────────────────────────────────────────────────
bg = None
try:
    bg_data = requests.get("https://images.unsplash.com/photo-1507525428034-b723cf961d3e", timeout=20).content
    bg = Image.open(io.BytesIO(bg_data)).convert("RGB")
except:
    bg = Image.new("RGB", (800, 950), "#004488")

bg = bg.resize((800, 950))
enhancer = ImageEnhance.Brightness(bg)
bg = enhancer.enhance(1.12)

overlay = Image.new("RGBA", bg.size, (255, 255, 255, 40))
card = Image.alpha_composite(bg.convert("RGBA"), overlay)
draw = ImageDraw.Draw(card)

# Logo (optional)
try:
    logo_data = requests.get("https://static.wixstatic.com/media/80c250_b1146919dfe046429a96648c59e2c413~mv2.png", timeout=20).content
    logo = Image.open(io.BytesIO(logo_data)).convert("RGBA").resize((120, 120))
    card.paste(logo, (40, 40), logo)
except:
    pass

# Fonts
try:
    font_title    = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
    font_sub      = ImageFont.truetype("DejaVuSans.ttf", 40)
    font_location = ImageFont.truetype("DejaVuSans.ttf", 26)
    font_body     = ImageFont.truetype("DejaVuSans.ttf", 28)
    font_footer   = ImageFont.truetype("DejaVuSans.ttf", 18)
    font_buoy     = ImageFont.truetype("DejaVuSans.ttf", 22)
except:
    font_title = font_sub = font_location = font_body = font_footer = font_buoy = ImageFont.load_default()

TEXT = "#0a1a2f"

draw.text((200, 80), datetime.now().strftime("%b %d, %Y"), fill=TEXT, font=font_title)
draw.text((400, 180), "Wave Forecast", fill=TEXT, font=font_sub, anchor="mm")
draw.text((400, 240), "Coastal waters east of Puerto Rico (AMZ726)", fill=TEXT, font=font_location, anchor="mm")

draw.multiline_text((80, 300), forecast_text, fill=TEXT, font=font_body, align="left", spacing=10)

# Current buoy section
buoy_y = 700  # ← increase to 740+ if overlaps with forecast text
draw.rectangle([(60, buoy_y-20), (740, buoy_y+80)], fill=(0, 20, 60, 140))

draw.text((80, buoy_y), "Current (Buoy 41043 – NE Puerto Rico)", fill="white", font=font_buoy)
buoy_text = f"Sig: {sig_height} | Swell: {swell_height} | {swell_period} | {buoy_dir}"
draw.text((80, buoy_y+35), buoy_text, fill="#a0d0ff", font=font_buoy)

draw.text((400, 880), "NDBC Marine Forecast | RabirubiaWeather.com | Updated every 6 hours", fill=TEXT, font=font_footer, anchor="mm")

card.convert("RGB").save("wave_card.png", optimize=True)
