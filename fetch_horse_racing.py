#!/usr/bin/env python3
"""Fetch major horse racing events."""

import json
import os
from datetime import datetime
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).parent
HORSE_RACING_DATA_FILE = DATA_DIR / "horse_racing_data.json"

# The Racing API (requires API key from https://www.theracingapi.com/)
RACING_API_KEY = os.environ.get("RACING_API_KEY", "")
RACING_API_BASE = "https://api.theracingapi.com/v1"

# Major horse racing events (static fallback)
MAJOR_RACING_EVENTS_2026 = [
    # UK
    {"name": "2026 Grand National", "date": "2026-04-04", "country": "United Kingdom", "city": "Liverpool", "level": 1},
    {"name": "2026 Cheltenham Festival", "date": "2026-03-10", "dateTo": "2026-03-13", "country": "United Kingdom", "city": "Cheltenham", "level": 1},
    {"name": "2026 Royal Ascot", "date": "2026-06-16", "dateTo": "2026-06-20", "country": "United Kingdom", "city": "Ascot", "level": 1},
    {"name": "2026 Epsom Derby", "date": "2026-06-06", "country": "United Kingdom", "city": "Epsom", "level": 1},
    {"name": "2026 King George VI and Queen Elizabeth Stakes", "date": "2026-07-25", "country": "United Kingdom", "city": "Ascot", "level": 1},
    {"name": "2026 Glorious Goodwood", "date": "2026-07-28", "dateTo": "2026-08-01", "country": "United Kingdom", "city": "Goodwood", "level": 2},
    {"name": "2026 St Leger", "date": "2026-09-12", "country": "United Kingdom", "city": "Doncaster", "level": 1},
    {"name": "2026 Champions Day", "date": "2026-10-17", "country": "United Kingdom", "city": "Ascot", "level": 1},

    # Ireland
    {"name": "2026 Irish Derby", "date": "2026-06-28", "country": "Ireland", "city": "Curragh", "level": 1},
    {"name": "2026 Galway Races", "date": "2026-07-27", "dateTo": "2026-08-02", "country": "Ireland", "city": "Galway", "level": 2},
    {"name": "2026 Leopardstown Christmas Festival", "date": "2026-12-26", "dateTo": "2026-12-29", "country": "Ireland", "city": "Dublin", "level": 2},

    # USA
    {"name": "2026 Kentucky Derby", "date": "2026-05-02", "country": "United States", "city": "Louisville", "level": 1},
    {"name": "2026 Preakness Stakes", "date": "2026-05-16", "country": "United States", "city": "Baltimore", "level": 1},
    {"name": "2026 Belmont Stakes", "date": "2026-06-06", "country": "United States", "city": "Elmont", "level": 1},
    {"name": "2026 Breeders' Cup", "date": "2026-11-06", "dateTo": "2026-11-07", "country": "United States", "city": "TBD", "level": 1},
    {"name": "2026 Pegasus World Cup", "date": "2026-01-24", "country": "United States", "city": "Hallandale Beach", "level": 1},

    # France
    {"name": "2026 Prix de l'Arc de Triomphe", "date": "2026-10-04", "country": "France", "city": "Paris", "level": 1},
    {"name": "2026 Prix du Jockey Club", "date": "2026-06-07", "country": "France", "city": "Chantilly", "level": 1},

    # Australia
    {"name": "2026 Melbourne Cup", "date": "2026-11-03", "country": "Australia", "city": "Melbourne", "level": 1},
    {"name": "2026 Cox Plate", "date": "2026-10-24", "country": "Australia", "city": "Melbourne", "level": 1},
    {"name": "2026 The Everest", "date": "2026-10-17", "country": "Australia", "city": "Sydney", "level": 1},

    # Dubai
    {"name": "2026 Dubai World Cup", "date": "2026-03-28", "country": "United Arab Emirates", "city": "Dubai", "level": 1},

    # Japan
    {"name": "2026 Japan Cup", "date": "2026-11-29", "country": "Japan", "city": "Tokyo", "level": 1},

    # Hong Kong
    {"name": "2026 Hong Kong International Races", "date": "2026-12-13", "country": "Hong Kong", "city": "Sha Tin", "level": 1},
]


def fetch_racing_api_events() -> list[dict]:
    """Fetch events from The Racing API (if API key available)."""
    if not RACING_API_KEY:
        print("No RACING_API_KEY set, using static events only")
        return []

    print("Fetching horse racing events from The Racing API...")
    headers = {"Authorization": f"Bearer {RACING_API_KEY}"}

    try:
        # Get upcoming race meetings
        response = httpx.get(
            f"{RACING_API_BASE}/racecards",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        events = []
        for meeting in data.get("meetings", []):
            event = {
                "name": f"2026 {meeting.get('course', 'Unknown')} Races",
                "date": meeting.get("date", ""),
                "country": meeting.get("region", "United Kingdom"),
                "city": meeting.get("course", ""),
                "level": 3,  # Daily races are National level
                "source": "theracingapi",
            }
            events.append(event)

        return events
    except httpx.HTTPError as e:
        print(f"Error fetching from Racing API: {e}")
        return []


def get_static_events() -> list[dict]:
    """Get major horse racing events (static data)."""
    events = []
    for event_data in MAJOR_RACING_EVENTS_2026:
        event = {
            "name": event_data["name"],
            "date": event_data["date"],
            "dateTo": event_data.get("dateTo", event_data["date"]),
            "sport": "Horse Racing",
            "competition": "Major Racing",
            "level": event_data["level"],
            "source": "static",
            "locations": [{"country": event_data["country"], "city": event_data["city"]}],
        }
        events.append(event)
    return events


def fetch_horse_racing_events() -> list[dict]:
    """Fetch all horse racing events."""
    events = get_static_events()

    # Add API events if available
    api_events = fetch_racing_api_events()
    events.extend(api_events)

    # Deduplicate by name
    seen = set()
    unique_events = []
    for e in events:
        if e["name"] not in seen:
            seen.add(e["name"])
            unique_events.append(e)

    return sorted(unique_events, key=lambda x: x["date"])


def save_horse_racing_data(events: list[dict]) -> None:
    """Save horse racing events to JSON file."""
    with open(HORSE_RACING_DATA_FILE, "w") as f:
        json.dump({"events": events}, f, indent=2)
    print(f"Saved {len(events)} horse racing events to {HORSE_RACING_DATA_FILE}")


def main():
    events = fetch_horse_racing_events()
    save_horse_racing_data(events)

    print(f"\nHorse Racing Events ({len(events)} total):")
    for e in events[:10]:
        level_marker = "★" if e["level"] == 1 else " "
        print(f"  {level_marker} {e['date']} - {e['name']}")
    if len(events) > 10:
        print(f"  ... and {len(events) - 10} more")


if __name__ == "__main__":
    main()
