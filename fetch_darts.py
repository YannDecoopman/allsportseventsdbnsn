#!/usr/bin/env python3
"""Fetch PDC darts events."""

import json
from datetime import datetime
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).parent
DARTS_DATA_FILE = DATA_DIR / "darts_data.json"

# PDC Major Events 2026 (static data from PDC calendar)
PDC_EVENTS_2026 = [
    # World Championship (Dec 2025 - Jan 2026)
    {"name": "2026 PDC World Darts Championship", "date": "2025-12-15", "dateTo": "2026-01-03", "country": "United Kingdom", "city": "London", "venue": "Alexandra Palace", "level": 1, "competition": "World Championship"},

    # Premier League
    {"name": "2026 Premier League Darts", "date": "2026-02-05", "dateTo": "2026-05-28", "country": "United Kingdom", "city": "Various", "level": 1, "competition": "Premier League"},

    # Major TV Events
    {"name": "2026 Masters", "date": "2026-01-30", "dateTo": "2026-02-02", "country": "United Kingdom", "city": "Milton Keynes", "level": 1, "competition": "Masters"},
    {"name": "2026 UK Open", "date": "2026-02-28", "dateTo": "2026-03-01", "country": "United Kingdom", "city": "Minehead", "level": 1, "competition": "UK Open"},
    {"name": "2026 World Matchplay", "date": "2026-07-18", "dateTo": "2026-07-26", "country": "United Kingdom", "city": "Blackpool", "venue": "Winter Gardens", "level": 1, "competition": "World Matchplay"},
    {"name": "2026 World Grand Prix", "date": "2026-10-05", "dateTo": "2026-10-11", "country": "Ireland", "city": "Dublin", "level": 1, "competition": "World Grand Prix"},
    {"name": "2026 Grand Slam of Darts", "date": "2026-11-08", "dateTo": "2026-11-16", "country": "United Kingdom", "city": "Wolverhampton", "level": 1, "competition": "Grand Slam"},
    {"name": "2026 Players Championship Finals", "date": "2026-11-27", "dateTo": "2026-11-29", "country": "United Kingdom", "city": "Minehead", "level": 1, "competition": "Players Championship Finals"},

    # European Tour (selection of majors)
    {"name": "2026 European Darts Open", "date": "2026-03-21", "dateTo": "2026-03-23", "country": "Germany", "city": "Leverkusen", "level": 2, "competition": "European Tour"},
    {"name": "2026 German Darts Masters", "date": "2026-05-02", "dateTo": "2026-05-04", "country": "Germany", "city": "Hildesheim", "level": 2, "competition": "European Tour"},
    {"name": "2026 Belgian Darts Open", "date": "2026-04-11", "dateTo": "2026-04-13", "country": "Belgium", "city": "Wieze", "level": 2, "competition": "European Tour"},
    {"name": "2026 Dutch Darts Masters", "date": "2026-05-30", "dateTo": "2026-06-01", "country": "Netherlands", "city": "Zwolle", "level": 2, "competition": "European Tour"},
    {"name": "2026 Czech Darts Open", "date": "2026-06-20", "dateTo": "2026-06-22", "country": "Czech Republic", "city": "Prague", "level": 2, "competition": "European Tour"},
    {"name": "2026 Austrian Darts Open", "date": "2026-09-12", "dateTo": "2026-09-14", "country": "Austria", "city": "Graz", "level": 2, "competition": "European Tour"},
    {"name": "2026 European Championship", "date": "2026-10-29", "dateTo": "2026-11-01", "country": "Germany", "city": "Dortmund", "level": 1, "competition": "European Championship"},

    # World Series
    {"name": "2026 US Darts Masters", "date": "2026-06-06", "dateTo": "2026-06-07", "country": "United States", "city": "New York", "level": 1, "competition": "World Series"},
    {"name": "2026 Nordic Darts Masters", "date": "2026-09-05", "dateTo": "2026-09-06", "country": "Denmark", "city": "Copenhagen", "level": 2, "competition": "World Series"},
    {"name": "2026 World Series of Darts Finals", "date": "2026-09-19", "dateTo": "2026-09-20", "country": "Netherlands", "city": "Amsterdam", "level": 1, "competition": "World Series"},

    # World Cup of Darts
    {"name": "2026 World Cup of Darts", "date": "2026-06-11", "dateTo": "2026-06-14", "country": "Germany", "city": "Frankfurt", "level": 1, "competition": "World Cup"},
]

# BDO/WDF Events (for completeness)
WDF_EVENTS_2026 = [
    {"name": "2026 WDF World Championship", "date": "2026-01-04", "dateTo": "2026-01-12", "country": "United Kingdom", "city": "Lakeside", "level": 1, "competition": "WDF World Championship"},
]


def get_pdc_events() -> list[dict]:
    """Get PDC darts events."""
    events = []
    for event_data in PDC_EVENTS_2026:
        event = {
            "name": event_data["name"],
            "date": event_data["date"],
            "dateTo": event_data.get("dateTo", event_data["date"]),
            "sport": "Darts",
            "competition": event_data.get("competition", "PDC"),
            "level": event_data["level"],
            "source": "pdc",
            "locations": [{"country": event_data["country"], "city": event_data["city"]}],
        }
        if "venue" in event_data:
            event["venue"] = event_data["venue"]
        events.append(event)
    return events


def get_wdf_events() -> list[dict]:
    """Get WDF darts events."""
    events = []
    for event_data in WDF_EVENTS_2026:
        event = {
            "name": event_data["name"],
            "date": event_data["date"],
            "dateTo": event_data.get("dateTo", event_data["date"]),
            "sport": "Darts",
            "competition": event_data.get("competition", "WDF"),
            "level": event_data["level"],
            "source": "wdf",
            "locations": [{"country": event_data["country"], "city": event_data["city"]}],
        }
        events.append(event)
    return events


def fetch_darts_events() -> list[dict]:
    """Fetch all darts events."""
    events = []
    events.extend(get_pdc_events())
    events.extend(get_wdf_events())

    # Sort by date
    return sorted(events, key=lambda x: x["date"])


def save_darts_data(events: list[dict]) -> None:
    """Save darts events to JSON file."""
    with open(DARTS_DATA_FILE, "w") as f:
        json.dump({"events": events}, f, indent=2)
    print(f"Saved {len(events)} darts events to {DARTS_DATA_FILE}")


def main():
    events = fetch_darts_events()
    save_darts_data(events)

    print(f"\nDarts Events ({len(events)} total):")
    for e in events[:15]:
        level_marker = "★" if e["level"] == 1 else " "
        comp = e.get("competition", "")
        print(f"  {level_marker} {e['date']} - {e['name']} ({comp})")
    if len(events) > 15:
        print(f"  ... and {len(events) - 15} more")


if __name__ == "__main__":
    main()
