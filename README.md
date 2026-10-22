# Autonox fuel prices (free, official)

A tiny "personal API" for the Autonox app. Every morning a GitHub Action reads the Government of
India's daily petrol and diesel price sheet from **PPAC** (Petroleum Planning & Analysis Cell,
Ministry of Petroleum and Natural Gas) and saves it as `fuel-prices.json`. The app downloads:

    https://raw.githubusercontent.com/aryanlakra2306/autonox-fuel-prices/main/fuel-prices.json

Cost: ₹0. No server, no API key, no user data sent anywhere.

## What it covers

PPAC publishes **Delhi, Mumbai, Chennai and Kolkata**, petrol and diesel, in ₹ per litre. Other
cities differ by a few rupees because of state VAT, so the app always shows which city and date
the price is for, and the user can change it.

## One-time setup (about 5 minutes)

1. On github.com, create a new **public** repository named `autonox-fuel-prices`
   (no README, no licence — leave it empty).
2. Copy the contents of this `FuelPriceAPI` folder (including the hidden `.github` folder) into it
   and push. (Claude can do this step for you once the empty repo exists.)
3. In the repo on GitHub: **Settings → Actions → General → Workflow permissions** → choose
   **Read and write permissions** → Save.
4. **Actions** tab → **Update fuel prices** → **Run workflow** once to check it works.

After that it runs by itself every day at 07:00 IST.

## If it ever breaks

PPAC may change their page. The script refuses to publish anything that looks wrong (missing
cities, odd numbers, swapped columns), so the last good file stays online and the app keeps
working with it. GitHub emails you when the Action fails; fix `fetch_prices.py` and run it again.

Test locally:

    pip install -r requirements.txt
    python fetch_prices.py
