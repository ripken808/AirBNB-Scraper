# Core scraper + helpers + email preview text (no SMTP)

import re, time, json, os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Dict, Tuple, List

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService

# Properties
BASE_URL = "https://www.airbnb.com/rooms/"

PROPERTIES: Dict[str, str] = {
    "Unit 1 Maui Ohana Modern Studio": "819453392249281180",
    "Unit 2 Maui Ohana Modern Studio": "837134855123444418",
    "Unit 3 Maui Ohana Modern Studio": "837287812536613417",
    "Unit 4 Maui Ohana Modern Studio": "837807882666931555",
    "Unit 5 Maui Ohana Modern Studio": "839225604600008884",
    "Unit 6 Maui Ohana Modern Studio": "834928764153318041",
    "Unit 7 Maui Ohana Modern Studio": "843628361710698988",
    "Unit 8 Maui Ohana Modern Studio": "843686495184089814",
    "Unit 9 Maui Ohana Modern Studio": "837818923494827841",
    "Unit 10 Maui Ohana Modern Studio": "837824983976858518",
    "Unit 11 Maui Ohana Modern Studio": "837242389710289631",
    "Unit 12 Maui Ohana Modern Studio": "837832037492645038",
    "Unit 13 Maui Ohana Modern Studio": "837841729797836174",
    "Unit 14 Maui Ohana Modern Studio": "837847629327594904",
    "Unit 15 Maui Ohana Modern Studio": "843724944043774069",
    "Unit 16 Maui Ohana Modern Studio": "837853174748563752",
    "Unit 17 Maui Ohana Modern Studio": "841432976860428383",
    "Unit 18 Maui Ohana Modern Studio": "841444949344078443",
    "Unit 19 Maui Ohana Modern Studio": "841459626649520263",
    "Unit 23 Maui Ohana Modern Studio": "1234208300595681725",
    "Unit 24 Maui Ohana Modern Studio": "1477787339981568921",
    "Unit 25 Maui Ohana Modern Studio": "1477799005376636955",
    "Unit 26 Maui Ohana Modern Studio": "1477804151840607052",
    "Unit 27 Maui Ohana Modern Studio": "1477808444041599408",
}


# URL helpers
def build_listing_url(prop_id: str, check_in: str, check_out: str) -> str:
    return f"{BASE_URL}{prop_id}?check_in={check_in}&check_out={check_out}"


def make_listings_dict(properties: Dict[str, str], start_date: str) -> Dict[str, str]:
    end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=2)).strftime(
        "%Y-%m-%d"
    )
    return {
        title: build_listing_url(pid, start_date, end_date)
        for title, pid in properties.items()
    }


def with_dates(url: str, check_in: str, check_out: str) -> str:
    p = urlparse(url)
    q = parse_qs(p.query)
    q["check_in"] = [check_in]
    q["check_out"] = [check_out]
    return urlunparse(p._replace(query=urlencode({k: v[0] for k, v in q.items()})))


def month_label(dstr: str) -> str:
    return datetime.strptime(dstr, "%Y-%m-%d").strftime("%B %Y")


# Parsing helpers
def page_has_month(html: str, month_year: str) -> bool:
    s = BeautifulSoup(html, "html.parser")
    return any(
        month_year in h.get_text(strip=True) for h in s.select('h3[class*="hpipapi"]')
    )


def js_click(driver, el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    driver.execute_script("arguments[0].click();", el)


def classify_day_from_aria(aria: str):
    a = (aria or "").strip().lower()
    a = a.replace("check-out", "checkout").replace("check out", "checkin")
    if "unavailable" in a:
        return "unavailable"
    if (
        "only available for checkout" in a
        or "this day is only available for checkout" in a
    ):
        return "checkout_only"
    if "available" in a and ("checkin" in a or "check-in" in a or "check in" in a):
        return "checkin_available"
    if (
        "selected check-in date" in a
        or "selected checkout date" in a
        or a.endswith("selected.")
    ):
        return "selected"
    return "other"


# Make Selenium use the system chromium + chromedriver explicitly
def _find_chromedriver_path() -> str:
    candidates = [
        "/usr/bin/chromedriver",
        "/usr/lib/chromium/chromedriver",
        "/usr/lib/chromium-browser/chromedriver",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    # fall back to PATH if present
    return "chromedriver"


def _new_chrome(headless: bool):
    opts = Options()
    opts.binary_location = "/usr/bin/chromium"  # Debian chromium binary
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("user-agent=Mozilla/5.0 Chrome/123 Safari/537.36")

    service = ChromeService(executable_path=_find_chromedriver_path())
    return webdriver.Chrome(service=service, options=opts)


def get_calendar_html_with_month(
    url: str, target_month_year: str, keep_open_sec=0, headless=True
) -> str:
    d = _new_chrome(headless=headless)
    try:
        d.get(url)
        for xp in [
            "//button[normalize-space()='Accept']",
            "//button[normalize-space()='OK']",
            "//button[normalize-space()='Got it']",
            "//button[normalize-space()='I agree']",
            "//button[normalize-space()='Dismiss']",
            "//button[@aria-label='Close']",
        ]:
            try:
                WebDriverWait(d, 1).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                ).click()
            except:
                pass
        for css in [
            'div[role="application"][aria-label="Calendar"]',
            '[data-testid="book-it-default"]',
            'button[aria-label*="Dates"]',
            'button[aria-label*="Check in"]',
        ]:
            try:
                js_click(d, d.find_element(By.CSS_SELECTOR, css))
                break
            except:
                pass
        try:
            clear = WebDriverWait(d, 2).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[normalize-space()='Clear dates']")
                )
            )
            js_click(d, clear)
            time.sleep(0.2)
        except:
            pass
        WebDriverWait(d, 15).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, '[role="button"][aria-label]')
            )
        )
        for _ in range(9):
            html = d.page_source
            if page_has_month(html, target_month_year):
                break
            try:
                nxt = WebDriverWait(d, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'button[aria-label^="Move forward"]')
                    )
                )
                js_click(d, nxt)
                time.sleep(0.3)
            except:
                break
        if keep_open_sec > 0:
            time.sleep(keep_open_sec)
        return d.page_source
    finally:
        d.quit()


def iso_from_dtid(val: str):
    try:
        mm, dd, yyyy = val.split("-")[-1].split("/")
        return f"{yyyy}-{mm.zfill(2)}-{dd.zfill(2)}"
    except:
        return None


def iso_from_aria(aria: str):
    m = re.search(r"\b(\d{1,2}),\s+[A-Za-z]+,\s+([A-Za-z]+)\s+(\d{4})", aria or "")
    if not m:
        return None
    d, mon, yr = m.groups()
    return datetime.strptime(f"{d} {mon} {yr}", "%d %B %Y").strftime("%Y-%m-%d")


def extract_states(html: str, start_date: str, days_window: int):
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = start + timedelta(days=days_window - 1)
    s = BeautifulSoup(html, "html.parser")
    states = {}
    for td in s.select('td[role="button"][aria-label]'):
        aria = td.get("aria-label") or ""
        state = classify_day_from_aria(aria)
        if state not in {"checkin_available", "checkout_only"}:
            continue
        iso = None
        div = td.select_one("div[data-testid^='calendar-day-']")
        if div and div.has_attr("data-testid"):
            iso = iso_from_dtid(div["data-testid"])
        if not iso:
            iso = iso_from_aria(aria)
        if not iso:
            continue
        dte = datetime.strptime(iso, "%Y-%m-%d").date()
        if start <= dte <= end:
            states[iso] = state
    return states, start, end


def group_maximal_ranges(states: Dict[str, str], window_start, window_end):
    checkins = sorted([d for d, s in states.items() if s == "checkin_available"])
    checkouts = sorted([d for d, s in states.items() if s == "checkout_only"])

    all_days = []
    cur = window_start
    while cur <= window_end:
        all_days.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=1)

    if checkins and not checkouts:
        if all(d in states and states[d] == "checkin_available" for d in all_days):
            return (
                checkins,
                checkouts,
                [(window_start.strftime("%Y-%m-%d"), window_end.strftime("%Y-%m-%d"))],
                True,
                (all_days[-1] in checkins),
            )

    ci_dates = list(map(lambda x: datetime.strptime(x, "%Y-%m-%d").date(), checkins))
    co_dates = list(map(lambda x: datetime.strptime(x, "%Y-%m-%d").date(), checkouts))
    ranges: List[Tuple[str, str]] = []
    i = j = 0
    while i < len(ci_dates):
        ci = ci_dates[i]
        while j < len(co_dates) and co_dates[j] < ci:
            j += 1
        if j < len(co_dates):
            co = co_dates[j]
            ranges.append((ci.strftime("%Y-%m-%d"), co.strftime("%Y-%m-%d")))
            i += 1
            while i < len(ci_dates) and ci_dates[i] <= co:
                i += 1
            j += 1
        else:
            end_str = window_end.strftime("%Y-%m-%d")
            if end_str in checkins:
                ranges.append((ci.strftime("%Y-%m-%d"), end_str))
            break

    end_day_available = window_end.strftime("%Y-%m-%d") in checkins
    return checkins, checkouts, ranges, False, end_day_available


# ---------- One listing & multi listing ----------
def scrape_listing_window(
    url: str, start_date: str, window_days: int = 14, headless: bool = True
):
    tgt_month = month_label(start_date)
    url_w = with_dates(
        url,
        start_date,
        (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=2)).strftime(
            "%Y-%m-%d"
        ),
    )
    html = get_calendar_html_with_month(
        url_w, tgt_month, keep_open_sec=0, headless=headless
    )
    states, win_start, win_end = extract_states(html, start_date, window_days)
    checkins, checkouts, ranges, all_move_in, end_day_available = group_maximal_ranges(
        states, win_start, win_end
    )
    return {
        "url": url,
        "start": win_start.strftime("%Y-%m-%d"),
        "end": win_end.strftime("%Y-%m-%d"),
        "states": states,
        "checkins": checkins,
        "checkouts": checkouts,
        "ranges": ranges,
        "all_move_in": all_move_in,
        "end_day_available": end_day_available,
    }


def scrape_all(
    listings: Dict[str, str],
    start_date: str,
    window_days: int = 14,
    headless: bool = True,
):
    results = {}
    for name, url in listings.items():
        try:
            res = scrape_listing_window(url, start_date, window_days, headless=headless)
            results[name] = res
            print(f"✓ {name}: {len(res['ranges'])} range(s)")
        except Exception as e:
            print(f"✗ {name}: {e}")
    return results


# Email preview
def build_email_preview(results: Dict[str, dict]) -> str:
    lines = []
    lines.append("===== EMAIL PREVIEW =====")
    lines.append("")
    lines.append("Dear Client,")
    lines.append("")
    lines.append("We have availabilities on the following properties:")
    lines.append("")
    for name, res in results.items():
        lines.append(f"{name} ({res['start']} → {res['end']}):")
        if res["all_move_in"]:
            lines.append(
                f"  • {res['start']} → {res['end']}  ({with_dates(res['url'], res['start'], res['end'])})"
            )
        elif res["ranges"]:
            for ci, co in res["ranges"]:
                lines.append(f"  • {ci} → {co}  ({with_dates(res['url'], ci, co)})")
            if res.get("end_day_available"):
                lines.append(f"  • End date available to start: {res['end']}")
        else:
            if res["checkins"]:
                lines.append("  • Ready for move-in on: " + ", ".join(res["checkins"]))
                if res.get("end_day_available"):
                    lines.append(f"  • End date available to start: {res['end']}")
            else:
                lines.append("  • No qualifying availability in this window.")
        lines.append("")
    lines.append("Best,")
    lines.append("Your Availability Bot")
    return "\n".join(lines)
