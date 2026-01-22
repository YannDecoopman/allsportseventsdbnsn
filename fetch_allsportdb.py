#!/usr/bin/env python3
"""Fetch sports data from AllSportDB API."""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import httpx

BASE_URL = "https://api.allsportdb.com/v3"
API_TOKEN = "78f69663-2698-45cf-ac2b-97945ed5f0b9"

RATE_LIMIT_DELAY = 0.5
MAX_RETRIES = 3


def fetch_paginated(client: httpx.Client, endpoint: str, params: dict = None) -> list:
    """Fetch all pages from a paginated endpoint."""
    all_items = []
    page = 1
    params = params or {}

    while True:
        params["page"] = page

        # Retry logic for rate limiting
        for retry in range(MAX_RETRIES):
            response = client.get(f"{BASE_URL}/{endpoint}", params=params)

            if response.status_code == 429:
                wait_time = (2 ** retry) * 2  # Exponential backoff: 2, 4, 8 seconds
                print(f"  Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            break

        if response.status_code != 200:
            print(f"  Error {response.status_code}: {response.text[:200]}")
            break

        data = response.json()
        items = data if isinstance(data, list) else data.get("data", data.get("items", []))

        if not items:
            break

        all_items.extend(items)
        print(f"  Page {page}: {len(items)} items (total: {len(all_items)})")

        # API returns up to 100 items per page, stop if less
        if len(items) < 100:
            break

        page += 1
        time.sleep(RATE_LIMIT_DELAY)

    return all_items


def fetch_sports(client: httpx.Client) -> list:
    """Fetch all sports."""
    print("Fetching sports...")
    response = client.get(f"{BASE_URL}/sports")
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return []
    return response.json()


def fetch_competitions(client: httpx.Client, sport: str = None) -> list:
    """Fetch competitions, optionally filtered by sport."""
    print(f"Fetching competitions{' for ' + sport if sport else ''}...")
    params = {"sport": sport} if sport else {}
    return fetch_paginated(client, "competitions", params)


def fetch_countries(client: httpx.Client) -> list:
    """Fetch all countries."""
    print("Fetching countries...")
    return fetch_paginated(client, "countries")


def fetch_calendar(
    client: httpx.Client,
    date_from: str = None,
    date_to: str = None,
    competition_id: str = None,
) -> list:
    """Fetch calendar/events with date range."""
    params = {}
    if date_from:
        params["dateFrom"] = date_from
    if date_to:
        params["dateTo"] = date_to
    if competition_id:
        params["competitionId"] = competition_id
    return fetch_paginated(client, "calendar", params)


def main():
    """Fetch and save AllSportDB data."""
    base_path = Path(__file__).parent
    output_path = base_path / "allsportdb_data.json"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json",
    }

    results = {
        "sports": [],
        "competitions": [],
        "countries": [],
        "events": [],
    }

    with httpx.Client(timeout=30, headers=headers) as client:
        # Fetch sports
        results["sports"] = fetch_sports(client)
        print(f"Got {len(results['sports'])} sports")
        time.sleep(RATE_LIMIT_DELAY)

        # Fetch countries
        results["countries"] = fetch_countries(client)
        print(f"Got {len(results['countries'])} countries")
        time.sleep(RATE_LIMIT_DELAY)

        # Fetch competitions for major sports
        major_sports = ["Football", "Basketball", "Ice Hockey", "Baseball", "Tennis",
                       "Rugby", "Cricket", "Motorsport", "Cycling", "MMA"]

        for sport in major_sports:
            competitions = fetch_competitions(client, sport)
            results["competitions"].extend(competitions)
            print(f"Got {len(competitions)} {sport} competitions")
            time.sleep(RATE_LIMIT_DELAY)

    # Remove duplicates
    seen_ids = set()
    unique_competitions = []
    for comp in results["competitions"]:
        comp_id = comp.get("id") or comp.get("competitionId")
        if comp_id and comp_id not in seen_ids:
            seen_ids.add(comp_id)
            unique_competitions.append(comp)
    results["competitions"] = unique_competitions

    # Fetch calendar for the next 12 months
    print("\nFetching calendar (next 12 months)...")
    today = datetime.now()
    date_from = today.strftime("%Y-%m-%d")
    date_to = (today + timedelta(days=365)).strftime("%Y-%m-%d")

    with httpx.Client(timeout=30, headers=headers) as client:
        results["events"] = fetch_calendar(client, date_from=date_from, date_to=date_to)
        print(f"Got {len(results['events'])} events")

    # Save results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {output_path}")
    print(f"  Sports: {len(results['sports'])}")
    print(f"  Countries: {len(results['countries'])}")
    print(f"  Competitions: {len(results['competitions'])}")


if __name__ == "__main__":
    main()
