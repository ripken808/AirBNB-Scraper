# AirBNB-Scraper
Scrapes a list of AirBNB rentals for availability

# How to Run:
## *Docker Build:
docker build -t airbnb-scraper .

## *Docker Run (manual run: 14 days):
docker run --rm -it \
-v "$(pwd)/out:/out" \
airbnb-scraper \
/bin/sh -c "python /app/AirBNBScraper.py --start $(date +%F) --days 14 --headless true"

## *Docker Run (manual run: till the end of the month):
docker run --rm -it -v "$(pwd)/out:/out" airbnb-scraper \
/bin/sh -lc 'python - <<PY
from datetime import date
import calendar, os
today = date.today()
days = calendar.monthrange(today.year, today.month)[1] - today.day + 1
os.system(f"python /app/AirBNBScraper.py --start {today.isoformat()} --days {days} --headless true")
PY'

## *Docker Run (automated runs with cron):
docker run -d --name airbnb-scraper \
  -v "$(pwd)/out:/out" \
  airbnb-scraper

# Demo
## Demo Video of Scraping availability of requested AirBNB properties from 10/09/2025 - 10/31/2025
**[https://github.com/user-attachments/assets/1df81f61-c2e7-42a2-9c7d-0ef564d8c13a](https://youtu.be/AyH_GRDKYoY)**

## Output files from the demo can be found in AIRBNBScraper/out/
