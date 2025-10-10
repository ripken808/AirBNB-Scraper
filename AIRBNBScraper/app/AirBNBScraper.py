# CLI runner: multi-scrape + email text preview + file outputs

import argparse, json, os
from datetime import datetime, timedelta

from modules import (
    BASE_URL,
    PROPERTIES,
    make_listings_dict,
    with_dates,
    scrape_all,
    build_email_preview,
)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--start",
        required=False,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Start date (YYYY-MM-DD)",
    )
    p.add_argument("--days", type=int, default=14, help="Window size in days")
    p.add_argument("--headless", default="true", help="true|false for headless browser")
    return p.parse_args()


def main():
    args = parse_args()
    start = args.start
    days = int(args.days)
    headless = str(args.headless).lower() in {"1", "true", "yes", "y"}

    listings = make_listings_dict(PROPERTIES, start)

    print(f"Start date: {start}  |  Window: {days} days  |  Headless: {headless}")
    print("\nGenerated listings for scraping:")
    for name, url in listings.items():
        print(f"- {name}: {url}")

    results = scrape_all(listings, start, days, headless=headless)

    win_end = (
        datetime.strptime(start, "%Y-%m-%d") + timedelta(days=days - 1)
    ).strftime("%Y-%m-%d")
    print("\nWindow:", start, "→", win_end)
    for name, res in results.items():
        print(f"\n{name} ({res['start']} → {res['end']})")
        if res["all_move_in"]:
            print(
                "  All days are check-in (ready for move-in):",
                f"{res['start']} → {res['end']}",
            )
        elif res["ranges"]:
            for ci, co in res["ranges"]:
                print("  ", f"{ci} → {co}", with_dates(res["url"], ci, co))
            if res.get("end_day_available"):
                print("  End date is also available for move-in:", res["end"])
        else:
            if res["checkins"]:
                print("  Ready for move-in on:", ", ".join(res["checkins"]))
                if res.get("end_day_available"):
                    print("  End date is also available for move-in:", res["end"])
            else:
                print("  (no ranges and no check-in days found)")

    # Build email preview text (no sending)
    email_text = build_email_preview(results)
    print("\n" + email_text)

    # Persist artifacts
    os.makedirs("/out", exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    json_path = f"/out/results_{ts}.json"
    txt_path = f"/out/email_{ts}.txt"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(email_text)

    print(f"\nSaved results  → {json_path}")
    print(f"Saved email    → {txt_path}")


if __name__ == "__main__":
    main()
