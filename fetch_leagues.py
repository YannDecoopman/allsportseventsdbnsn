#!/usr/bin/env python3
"""Fetch sports leagues/competitions by country from TheSportsDB API."""

import json
import time
from pathlib import Path

import httpx

BASE_URL = "https://www.thesportsdb.com/api/v1/json/3/search_all_leagues.php"

# Countries to fetch
COUNTRIES = [
    "Brazil", "Portugal", "Canada", "United States", "Peru", "Mexico",
    "India", "Bulgaria", "Spain", "Chile", "Morocco", "France", "Senegal",
    "Argentina", "Australia", "Russia", "South Africa", "Belgium", "Japan",
    "Cameroon", "Hungary", "Kazakhstan", "Nigeria", "Ecuador", "Bangladesh",
    "Luxembourg", "Mali",
    # Added batch 2
    "Buenos Aires City", "Singapore", "Venezuela", "Mongolia", "Costa Rica",
    "Poland", "Switzerland", "Netherlands", "Turkey", "Czech Republic",
    "Colombia", "Uzbekistan", "Finland", "Burkina Faso", "Moldova",
    "Papua New Guinea", "El Salvador", "Kyrgyzstan", "Algeria", "Kuwait",
    "Mauritania", "Germany", "Panama", "Gabon", "Sweden", "Guatemala",
    "Cayman Islands", "Azerbaijan", "Nepal", "Bermuda", "Tunisia", "Togo", "Kenya"
]

# UK regions (instead of "United Kingdom")
UK_REGIONS = ["England", "Scotland", "Wales", "Northern Ireland"]

# Countries with variant names to try
VARIANT_COUNTRIES = {
    "Ivory Coast": ["Ivory Coast", "Cote d'Ivoire"],
    "Congo (Kinshasa)": ["Congo (Kinshasa)", "DR Congo", "Democratic Republic of Congo", "Congo"],
}

RATE_LIMIT_DELAY = 1.5  # seconds between requests
MAX_RETRIES = 3


def fetch_leagues(country: str, client: httpx.Client) -> list[dict]:
    """Fetch leagues for a single country with retry on rate limit."""
    for attempt in range(MAX_RETRIES):
        try:
            response = client.get(BASE_URL, params={"c": country})
            response.raise_for_status()
            data = response.json()

            if not data.get("countries"):
                return []

            return [
                {"name": league["strLeague"], "sport": league["strSport"]}
                for league in data["countries"]
            ]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < MAX_RETRIES - 1:
                wait_time = (attempt + 1) * 3  # 3s, 6s, 9s
                print(f"  Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            print(f"  Error fetching {country}: {e}")
            return []
        except httpx.HTTPError as e:
            print(f"  Error fetching {country}: {e}")
            return []
    return []


def main():
    # Load existing data to merge with
    output_path = Path(__file__).parent / "leagues.json"
    if output_path.exists():
        with open(output_path, encoding="utf-8") as f:
            results = json.load(f)
        print(f"Loaded {len(results)} existing countries")
    else:
        results = {}

    with httpx.Client(timeout=30) as client:
        # Regular countries
        all_countries = COUNTRIES + UK_REGIONS

        for country in all_countries:
            if country in results:
                print(f"Skipping {country} (already have {len(results[country])} leagues)")
                continue
            print(f"Fetching {country}...")
            leagues = fetch_leagues(country, client)
            if leagues:
                results[country] = leagues
                print(f"  Found {len(leagues)} leagues")
                # Save after each successful fetch
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
            else:
                print(f"  No leagues found")
            time.sleep(RATE_LIMIT_DELAY)

        # Countries with variant names
        for country_name, variants in VARIANT_COUNTRIES.items():
            if country_name in results:
                print(f"Skipping {country_name} (already have {len(results[country_name])} leagues)")
                continue
            print(f"Fetching {country_name}...")
            for variant in variants:
                leagues = fetch_leagues(variant, client)
                if leagues:
                    results[country_name] = leagues
                    print(f"  Found {len(leagues)} leagues (using '{variant}')")
                    # Save after each successful fetch
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)
                    break
                time.sleep(RATE_LIMIT_DELAY)
            else:
                print(f"  No leagues found")

    # Write output
    output_path = Path(__file__).parent / "leagues.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Saved {len(results)} countries to {output_path}")
    total_leagues = sum(len(leagues) for leagues in results.values())
    print(f"Total leagues: {total_leagues}")


if __name__ == "__main__":
    main()
