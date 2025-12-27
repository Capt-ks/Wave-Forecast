import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import datetime
import os

# Create directory if not exists
os.makedirs('images', exist_ok=True)

# Fetch real-time data from Buoy 41043 (NE Puerto Rico)
url = 'https://www.ndbc.noaa.gov/station_page.php?station=41043'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Find the latest observations (first data row after headers)
table = soup.find('table', {'cellpadding': '5'})
if table:
    rows = table.find_all('tr')
    for row in rows[1:]:  # skip header
        cols = row.find_all('td')
        if len(cols) > 10:
            wvht = cols[8].text.strip()   # Significant Wave Height
            swh = cols[10].text.strip()   # Swell Height
            swp = cols[11].text.strip()   # Swell Period
            if wvht and wvht != 'MM' and swh != 'MM' and swp != 'MM':
                sig_height = f"{wvht} ft"
                swell_height = f"{swh} ft"
                swell_period = f"{swp} sec"
                break
    else:
        sig_height = swell_height = swell_period = "N/A"
else:
    sig_height = swell_height = swell_period = "N/A"

# Example 7-day forecast data (replace with actual parsing from NOAA forecast if desired)
# For now using placeholder realistic values based on current conditions
today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4)))  # AST
days = [
    ("Today", "4-7 ft", "4-7 ft", "8 sec", "Northeast"),
    (f"{today.strftime('%a')} {int(today.day)+1 if today.day < 31 else 1}", "5-7 ft", "5-7 ft", "9 sec", "Northeast"),
    (f"{today.strftime('%a')} {int(today.day)+2 if today.day < 30 else 1}", "6-8 ft", "6-8 ft", "10 sec", "Northeast"),
    (f"{today.strftime('%a')} {int(today.day)+3 if today.day < 29 else 1}", "5-7 ft", "5-7 ft", "9 sec", "Northeast"),
    (f"{today.strftime('%a')} {int(today.day)+4 if today.day < 28 else 1}", "4-6 ft", "4-6 ft", "8 sec", "Northeast"),
]

# Image generation with Pillow (to match the style you showed)
background = Image.new('RGB', (1080, 1350), color=(0, 105, 148))  # Rabirubia blue-ish
draw = ImageDraw.Draw(background)

# Load fonts (use default if not available; replace with your brand fonts)
title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
big_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
med_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 50)
small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)

# Logo text (replace with actual logo image if you have one)
draw.text((60, 40), "Rabirubiaweather.com", fill="white", font=big_font)

# Title
draw.text((60, 160), "7-Day Wave Forecast", fill="white", font=title_font)
draw.text((60, 260), "Puerto Rico & The Virgin Islands", fill="white", font=med_font)

# Refresh info
current_time = today.strftime("%A, %I:%M %p AST")
draw.text((60, 380), f"Refreshed: {current_time}", fill="white", font=small_font)
draw.text((60, 440), "Refreshes every 6 hours", fill="white", font=small_font)

# Header background
draw.rectangle([(0, 520), (1080, 620)], fill=(30, 30, 50, 200))

header_y = 540
draw.text((80, header_y), "Swells", fill="white", font=med_font)
draw.text((280, header_y), "Height", fill="white", font=med_font)
draw.text((500, header_y), "Period", fill="white", font=med_font)
draw.text((700, header_y), "Direction/Location", fill="white", font=med_font)

# Forecast rows
row_y = 650
for i, (day, swells, height, period, direction) in enumerate(days):
    # Alternate row background
    if i % 2 == 0:
        draw.rectangle([(0, row_y-20), (1080, row_y+100)], fill=(0, 80, 120, 100))
    
    draw.text((60, row_y), day, fill="white", font=big_font)
    draw.text((80, row_y+80), swells, fill="white", font=med_font)
    draw.text((280, row_y+80), height, fill="white", font=med_font)
    draw.text((500, row_y+80), period, fill="white", font=med_font)
    draw.text((700, row_y+80), direction, fill="white", font=med_font)
    
    row_y += 160

# New current observations line (below last forecast row)
final_y = row_y + 60
draw.rectangle([(0, final_y-40), (1080, final_y+120)], fill=(20, 50, 80, 220))

draw.text((60, final_y), "Current (Buoy 41043)", fill="white", font=big_font)
draw.text((80, final_y+70), f"{swell_height}", fill="cyan", font=med_font)  # Swell Height
draw.text((280, final_y+70), f"{sig_height}", fill="cyan", font=med_font)  # Significant Height
draw.text((500, final_y+70), f"{swell_period}", fill="cyan", font=med_font)  # Swell Period
draw.text((700, final_y+70), "Northeast", fill="cyan", font=med_font)  # Direction typical

# Optional: add background image overlay or wave photo (omitted for simplicity)

background.save('images/wave_forecast.png', quality=95)
