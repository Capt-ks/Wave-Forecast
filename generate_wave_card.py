import requests
import re
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io

# ─────────────────────────────────────────────────────────────
# PART 1: Fetch & Parse AMZ726 Forecast (FIXED REGEX)
# ─────────────────────────────────────────────────────────────
URL = "https://www.ndbc.noaa.gov/data/Forecasts/FZCA52.TJSJ.html"
ZONE = "726"
FALLBACK = "Wave forecast temporarily unavailable."

forecast_text = FALLBACK

try:
    r = requests.get(URL, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text("\n")

    pattern = rf"({ZONE}.*?)(\d{{3}}|$)"
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

    if m:
        block = m.group(1).replace("feet", "ft")
        lines = [l.strip() for l in block.splitlines() if l.strip()]

        periods = []
        current_label = None
        current_text = []

        for line in lines:
            if re.match(
                r"^(REST OF TONIGHT|TODAY|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)",
                line, re.I
            ):
                if current_label:
                    periods.append((current_label, " ".join(current_text)))
                current_label = line.upper()
                current_text = []
            else:
                current_text.append(line)

        if current_label:
            periods.append((current_label, " ".join(current_text)))

        final_lines = []
        for label, txt in periods[:7]:
            wave = re.search(
                r"Wave Detail:\s*(.+?)(?=\.|$|Scattered|Isolated)",
                txt, re.I
            )
            seas = re.search(r"Seas\s*(\d+)\s*to\s*(\d+)\s*ft", txt, re.I)

            if wave:
                final_lines.append(f"{label}: {wave.group(1)}")
            elif seas:
                final_lines.append(f"{label}: Seas {seas.group(1)}–{seas.group(2)} ft")
            else:
                final_lines.append(f"{label}: {txt[:90]}...")

        if final_lines:
            forecast_text = "\n".join(final_lines)

except Exception as e:
    print("FORECAST ERROR:", e)

# ─────────────────────────────────────────────────────────────
# PART 2: Fetch Current Buoy 41043 Data (STABLE REALTIME FEED)
# ─────────────────────────────────────────────────────────────
sig_height = swell_height = swell_period = buoy_dir = "N/A"

try:
    buoy_url = "https://www.ndbc.noaa.gov/data/realtime2/41043.txt"
    r = requests.get(buoy_url, timeout=15)
    r.raise_for_status()

    lines = r.text.strip().splitlines()
    header = lines[0].split()
    data = lines[1].split()

    def val(k):
        return data[header.index(k)] if k in header else None

    wvht = val("WVHT")
    swh = val("SwH")
    swp = val("SwP")
    swd = val("SwD")

    if wvht and wvht != "MM":
        sig_height = f"{round(float(wvht) * 3.28084, 1)} ft"

    if swh and swh != "MM":
        swell_height = f"{round(float(swh) * 3.28084, 1)} ft"

    if swp and swp != "MM":
        swell_period = f"{swp} sec"

    if swd and swd != "MM":
        buoy_dir = f"{swd}°"

except Exception as e:
    print("BUOY ERROR:", e)

# ─────────────────────────────────────────────────────────────
# PART 3: Image Generation (FULLY SAFE)
# ─────────────────────────────────────────────────────────────
try:
    try:
        bg_data = requests.get(
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e",
            timeout=20
        ).content
        bg = Image.open(io.BytesIO(bg_data)).convert("RGB")
    except Exception:
        bg = Image.new("RGB", (800, 950), "#004488")

    bg = bg.resize((800, 950))
    bg = ImageEnhance.Brightness(bg).enhance(1.12)

    overlay = Image.new("RGBA", bg.size, (255, 255, 255, 40))
    card = Image.alpha_composite(bg.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(card)

    # Logo
    try:
        logo_data = requests.get(
            "https://static.wixstatic.com/media/80c250_b1146919dfe046429a96648c59e2c413~mv2.png",
            timeout=20
        ).content
        logo = Image.open(io.BytesIO(logo_data)).convert("RGBA").resize((120, 120))
        card.paste(logo, (40, 40), logo)
    except Exception:
        pass

    # Fonts
    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_sub = ImageFont.truetype("DejaVuSans.ttf", 40)
        font_location = ImageFont.truetype("DejaVuSans.ttf", 26)
        font_body = ImageFont.truetype("DejaVuSans.ttf", 28)
        font_footer = ImageFont.truetype("DejaVuSans.ttf", 18)
        font_buoy = ImageFont.truetype("DejaVuSans.ttf", 22)
    except Exception:
        font_title = font_sub = font_location = font_body = font_footer = font_buoy = ImageFont.load_default()

    TEXT = "#0a1a2f"
    GRAY = "#aaaaaa"

    draw.text((400, 180), "7-Day Wave Forecast", fill=TEXT, font=font_sub, anchor="mm")
    draw.text((400, 220), "(Forecast starting from TODAY - Real-time current below)",
              fill=GRAY, font=font_footer, anchor="mm")
    draw.text((400, 240),
              "Coastal waters east of Puerto Rico (AMZ726)",
              fill=TEXT, font=font_location, anchor="mm")

    draw.multiline_text((80, 300), forecast_text,
                        fill=TEXT, font=font_body, spacing=12)

    buoy_y = 700
    draw.rectangle([(60, buoy_y - 20), (740, buoy_y + 55)],
                   fill=(0, 20, 60, 140))
    draw.text((80, buoy_y),
              "Current (Buoy 41043 – NE Puerto Rico)",
              fill="white", font=font_buoy)

    buoy_text = f"Sig: {sig_height} | Swell: {swell_height} | {swell_period} | {buoy_dir}"
    draw.text((80, buoy_y + 30),
              buoy_text, fill="#a0d0ff", font=font_buoy)

    draw.text((400, 880),
              "NDBC Marine Forecast | RabirubiaWeather.com | Updated every 6 hours",
              fill=TEXT, font=font_footer, anchor="mm")

    card.convert("RGB").save("wave_card.png", optimize=True)

except Exception as e:
    print("IMAGE ERROR:", e)
