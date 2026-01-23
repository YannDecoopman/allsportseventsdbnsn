#!/usr/bin/env python3
"""Fetch UFC events from ESPN API."""

import json
from datetime import datetime
from pathlib import Path

import httpx

ESPN_UFC_API = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"
DATA_DIR = Path(__file__).parent
UFC_DATA_FILE = DATA_DIR / "ufc_data.json"


def fetch_ufc_events() -> list[dict]:
    """Fetch UFC events from ESPN API."""
    print("Fetching UFC events from ESPN...")

    response = httpx.get(ESPN_UFC_API, timeout=30)
    response.raise_for_status()
    data = response.json()

    events = []

    # Get calendar events (future events)
    calendar = data.get("leagues", [{}])[0].get("calendar", [])

    for cal_event in calendar:
        label = cal_event.get("label", "")
        start_date = cal_event.get("startDate", "")
        end_date = cal_event.get("endDate", "")

        if not label or not start_date:
            continue

        # Parse dates
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00")) if end_date else start_dt
        except ValueError:
            continue

        # Determine level based on event type
        is_numbered = "UFC " in label and any(c.isdigit() for c in label.split(":")[0])
        level = 1 if is_numbered else 2  # World for numbered UFC, Continental for Fight Nights

        event = {
            "name": f"2026 {label}",
            "date": start_dt.strftime("%Y-%m-%d"),
            "dateTo": end_dt.strftime("%Y-%m-%d"),
            "sport": "MMA",
            "competition": "UFC",
            "level": level,
            "source": "espn",
        }

        events.append(event)

    # Also get current/detailed events if available
    current_events = data.get("events", [])
    for evt in current_events:
        event_id = evt.get("id", "")
        name = evt.get("name", "")
        date_str = evt.get("date", "")

        if not name or not date_str:
            continue

        # Get venue info
        venues = evt.get("venues", [])
        locations = []
        for venue in venues:
            address = venue.get("address", {})
            city = address.get("city", "")
            country = address.get("country", "USA")
            if city:
                locations.append({"country": country, "city": city})

        # Check if already in calendar events
        already_exists = any(e["name"] == f"2026 {name}" for e in events)
        if already_exists:
            # Update with location info
            for e in events:
                if e["name"] == f"2026 {name}" and locations:
                    e["locations"] = locations
                    break
        else:
            try:
                start_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                continue

            is_numbered = "UFC " in name and any(c.isdigit() for c in name.split(":")[0])

            event = {
                "name": f"2026 {name}",
                "date": start_dt.strftime("%Y-%m-%d"),
                "dateTo": start_dt.strftime("%Y-%m-%d"),
                "sport": "MMA",
                "competition": "UFC",
                "level": 1 if is_numbered else 2,
                "source": "espn",
            }
            if locations:
                event["locations"] = locations

            events.append(event)

    # Deduplicate by name
    seen = set()
    unique_events = []
    for e in events:
        if e["name"] not in seen:
            seen.add(e["name"])
            unique_events.append(e)

    return unique_events


def save_ufc_data(events: list[dict]) -> None:
    """Save UFC events to JSON file."""
    with open(UFC_DATA_FILE, "w") as f:
        json.dump({"events": events}, f, indent=2)
    print(f"Saved {len(events)} UFC events to {UFC_DATA_FILE}")


def main():
    events = fetch_ufc_events()
    save_ufc_data(events)

    # Print summary
    print(f"\nUFC Events ({len(events)} total):")
    for e in sorted(events, key=lambda x: x["date"])[:10]:
        print(f"  {e['date']} - {e['name']}")
    if len(events) > 10:
        print(f"  ... and {len(events) - 10} more")


if __name__ == "__main__":
    main()
