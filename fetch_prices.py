"""Autonox fuel price feed.

Reads the Government of India's daily "Retail Selling Price of Petrol / Diesel" sheet published by
PPAC (Petroleum Planning & Analysis Cell, Ministry of Petroleum and Natural Gas) and writes
fuel-prices.json, which the Autonox app downloads.

PPAC publishes the four metros only: Delhi, Mumbai, Chennai and Kolkata. Prices elsewhere differ
because of state VAT, so the app labels the price with its city and date and lets the user edit it.

If anything looks wrong (page changed, numbers missing or out of range) the script exits with an
error and leaves the previous fuel-prices.json untouched, so the app never gets a bad price.

Run:  python fetch_prices.py            (writes fuel-prices.json next to this file)
      python fetch_prices.py --pdf X    (parse a PDF you already downloaded, for testing)
"""

import datetime as dt
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

from pypdf import PdfReader

PAGE_URL = ("https://ppac.gov.in/retail-selling-price-rsp-of-petrol-diesel-and-domestic-lpg/"
            "rsp-of-petrol-and-diesel-in-metro-cities-since-16-6-2017")
CITIES = ["Delhi", "Mumbai", "Chennai", "Kolkata"]   # column order in the PPAC sheet
OUT = Path(__file__).with_name("fuel-prices.json")
HEADERS = {"User-Agent": "AutonoxFuelPrices/1.0 (+https://github.com/aryanlakra2306)"}

DATE = r"(\d{1,2}-[A-Za-z]{3}-\d{2})"
NUM = r"(\d{2,3}\.\d{2})"
# One table row: date, petrol x4, date, diesel x4 (newest row comes first in the sheet).
ROW = re.compile(DATE + r"\s+" + r"\s+".join([NUM] * 4) + r"\s+" + DATE + r"\s+" + r"\s+".join([NUM] * 4))


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def find_pdf_url():
    html = get(PAGE_URL).decode("utf-8", errors="ignore")
    links = re.findall(r'href="([^"]*PP_9_a_DailyPriceMSHSD_Metro[^"]*\.pdf)"', html)
    if not links:
        fail("daily metro price PDF link not found on the PPAC page (page layout changed?)")
    url = links[0]
    return url if url.startswith("http") else "https://ppac.gov.in/" + url.lstrip("/")


def parse(pdf_bytes):
    text = PdfReader(io.BytesIO(pdf_bytes)).pages[0].extract_text()
    if not re.search(r"Delhi\s+Mumbai\s+Chennai\s+Kolkata\s+Delhi\s+Mumbai\s+Chennai\s+Kolkata", text):
        fail("city header row not found (sheet layout changed?)")
    m = ROW.search(text)
    if not m:
        fail("no price row found")
    g = m.groups()
    if g[0] != g[5]:
        fail(f"petrol and diesel rows have different dates ({g[0]} / {g[5]})")
    date = dt.datetime.strptime(g[0], "%d-%b-%y").date()
    petrol = [float(x) for x in g[1:5]]
    diesel = [float(x) for x in g[6:10]]
    for v in petrol + diesel:
        if not 50 <= v <= 250:
            fail(f"price {v} outside the sane range")
    # Guard against the two blocks being swapped: petrol has cost more than diesel in every metro.
    if not all(p > d for p, d in zip(petrol, diesel)):
        fail("petrol not above diesel in every city (columns swapped?)")
    cities = {c: {"petrol": p, "diesel": d} for c, p, d in zip(CITIES, petrol, diesel)}
    return date, cities


def main():
    args = sys.argv[1:]
    if args[:1] == ["--pdf"]:
        pdf_url, pdf = "local file", Path(args[1]).read_bytes()
    else:
        pdf_url = find_pdf_url()
        pdf = get(pdf_url)
    date, cities = parse(pdf)
    feed = {
        "version": 1,
        "source": "Petroleum Planning & Analysis Cell (PPAC), Ministry of Petroleum and Natural Gas, Government of India",
        "sourceURL": pdf_url,
        "unit": "INR per litre",
        "effectiveDate": date.isoformat(),
        "fetchedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "cities": cities,
    }
    OUT.write_text(json.dumps(feed, indent=2) + "\n")
    print(json.dumps(feed, indent=2))


if __name__ == "__main__":
    main()
