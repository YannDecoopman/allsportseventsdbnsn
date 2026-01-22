#!/usr/bin/env python3
"""Fetch missing leagues from football-data.org API (free tier)."""

import json
import time
from pathlib import Path

import httpx

# football-data.org free tier covers these countries
# https://www.football-data.org/coverage
FOOTBALL_DATA_COVERAGE = {
    "Italy": [
        {"name": "Serie A", "sport": "Soccer", "tier": 1},
        {"name": "Serie B", "sport": "Soccer", "tier": 2},
    ],
    "Netherlands": [
        {"name": "Eredivisie", "sport": "Soccer", "tier": 1},
    ],
    "Denmark": [
        {"name": "Superligaen", "sport": "Soccer", "tier": 1},
    ],
    "Austria": [
        {"name": "Austrian Bundesliga", "sport": "Soccer", "tier": 1},
    ],
    "Greece": [
        {"name": "Super League Greece", "sport": "Soccer", "tier": 1},
    ],
    # Countries not covered by football-data.org free tier, using known leagues
    "Ireland": [
        {"name": "League of Ireland Premier Division", "sport": "Soccer", "tier": 1},
        {"name": "League of Ireland First Division", "sport": "Soccer", "tier": 2},
    ],
    "Norway": [
        {"name": "Eliteserien", "sport": "Soccer", "tier": 1},
        {"name": "Norwegian First Division", "sport": "Soccer", "tier": 2},
    ],
    "China": [
        {"name": "Chinese Super League", "sport": "Soccer", "tier": 1},
        {"name": "Chinese League One", "sport": "Soccer", "tier": 2},
        {"name": "Chinese Basketball Association", "sport": "Basketball", "tier": 1},
    ],
    "South Korea": [
        {"name": "K League 1", "sport": "Soccer", "tier": 1},
        {"name": "K League 2", "sport": "Soccer", "tier": 2},
        {"name": "Korean Basketball League", "sport": "Basketball", "tier": 1},
    ],
}


def load_json(path: Path) -> dict:
    """Load JSON file."""
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(data: dict, path: Path) -> None:
    """Save JSON file with pretty formatting."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    """Add missing leagues to leagues.json."""
    base_path = Path(__file__).parent
    leagues_path = base_path / "leagues.json"

    # Load existing leagues
    leagues_data = load_json(leagues_path)
    print(f"Loaded {len(leagues_data)} countries from leagues.json")

    # Missing countries from reference
    missing_countries = [
        "Austria", "China", "Denmark", "Greece", "Ireland",
        "Italy", "Netherlands", "Norway", "South Korea"
    ]

    added_count = 0
    for country in missing_countries:
        if country in FOOTBALL_DATA_COVERAGE:
            # Check if country already has data
            existing = leagues_data.get(country, [])
            existing_names = {l["name"] for l in existing}

            # Add new leagues
            new_leagues = []
            for league in FOOTBALL_DATA_COVERAGE[country]:
                if league["name"] not in existing_names:
                    new_leagues.append({
                        "name": league["name"],
                        "sport": league["sport"],
                    })

            if new_leagues:
                if country in leagues_data:
                    leagues_data[country].extend(new_leagues)
                else:
                    leagues_data[country] = new_leagues
                added_count += len(new_leagues)
                print(f"  {country}: added {len(new_leagues)} leagues")
            else:
                print(f"  {country}: already has all leagues")
        else:
            print(f"  {country}: no coverage data available")

    # Save updated leagues
    save_json(leagues_data, leagues_path)
    print(f"\nAdded {added_count} leagues to {len(missing_countries)} countries")
    print(f"Total countries: {len(leagues_data)}")


if __name__ == "__main__":
    main()
