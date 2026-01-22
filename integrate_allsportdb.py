#!/usr/bin/env python3
"""Integrate AllSportDB data into merged_sports_data.json."""

import json
from pathlib import Path


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
    """Integrate AllSportDB data."""
    base_path = Path(__file__).parent

    merged_path = base_path / "merged_sports_data.json"
    allsportdb_path = base_path / "allsportdb_data.json"

    merged_data = load_json(merged_path)
    allsportdb_data = load_json(allsportdb_path)

    if not merged_data or not allsportdb_data:
        print("Error: Missing data files")
        return

    # Add sports catalog
    sports_catalog = {}
    for sport in allsportdb_data.get("sports", []):
        sports_catalog[sport["name"]] = {
            "id": sport["id"],
            "season": sport.get("season"),
            "emoji": sport.get("emoji"),
        }
    merged_data["sports_catalog"] = sports_catalog
    print(f"Added {len(sports_catalog)} sports to catalog")

    # Add international competitions by sport and continent
    international_competitions = {}
    for comp in allsportdb_data.get("competitions", []):
        sport = comp.get("sport", "Other")
        if sport not in international_competitions:
            international_competitions[sport] = []

        international_competitions[sport].append({
            "id": comp["id"],
            "name": comp["name"],
            "continent": comp.get("continent"),
            "gender": comp.get("gender"),
            "age_group": comp.get("ageGroup"),
            "logo_url": comp.get("logoThumbnailUrl"),
            "url": comp.get("url"),
        })

    # Sort competitions within each sport
    for sport in international_competitions:
        international_competitions[sport].sort(key=lambda x: x["name"])

    merged_data["international_competitions"] = international_competitions
    print(f"Added {sum(len(c) for c in international_competitions.values())} international competitions")

    # Add countries catalog from AllSportDB (with flags/emoji)
    countries_catalog = {}
    for country in allsportdb_data.get("countries", []):
        countries_catalog[country["name"]] = {
            "code": country.get("code", "").upper(),
            "emoji": country.get("emoji"),
            "continent": country.get("continent"),
            "flag_url": country.get("flagUrl"),
        }
    merged_data["countries_catalog"] = countries_catalog
    print(f"Added {len(countries_catalog)} countries to catalog")

    # Update metadata
    if "_meta" not in merged_data:
        merged_data["_meta"] = {}
    merged_data["_meta"]["allsportdb_integrated"] = True
    merged_data["_meta"]["sports_count"] = len(sports_catalog)
    merged_data["_meta"]["international_competitions_count"] = sum(
        len(c) for c in international_competitions.values()
    )

    # Save
    save_json(merged_data, merged_path)
    print(f"\nSaved to {merged_path}")

    # Summary by sport
    print("\nInternational competitions by sport:")
    for sport, comps in sorted(international_competitions.items(), key=lambda x: -len(x[1])):
        print(f"  {sport}: {len(comps)}")


if __name__ == "__main__":
    main()
