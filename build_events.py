#!/usr/bin/env python3
"""Build events_data.json from AllSportDB data with filtering."""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent

# Sports majeurs par priorité
MAJOR_SPORTS = {
    "Football", "Tennis", "Rugby", "Basketball", "Ice Hockey",
    "Cycling", "Athletics", "Swimming", "Handball", "Volleyball",
    "Baseball", "Cricket", "Golf", "Motorsport", "Boxing", "MMA",
    "Skiing", "Figure Skating", "Gymnastics", "Water Polo",
}

# Niveaux de compétition
COMPETITION_LEVELS = {
    "World": 1,      # Coupe du Monde, Championnats du Monde
    "Continental": 2, # Euro, Copa America, Champions League
    "National": 3,    # Championnats nationaux
    "Other": 4,
}


def get_competition_level(event: dict) -> int:
    """Determine competition level from event data."""
    name = event.get("name", "").lower()
    competition = event.get("competition", "").lower()

    if any(w in name or w in competition for w in ["world", "mondial", "olympics", "olympic"]):
        return COMPETITION_LEVELS["World"]
    if any(w in name or w in competition for w in ["european", "euro ", "asian", "african", "copa america", "champions league"]):
        return COMPETITION_LEVELS["Continental"]
    if any(w in name or w in competition for w in ["national", "championship", "cup"]):
        return COMPETITION_LEVELS["National"]
    return COMPETITION_LEVELS["Other"]


def load_allsportdb_data() -> dict:
    """Load AllSportDB data."""
    path = DATA_DIR / "allsportdb_data.json"
    with open(path) as f:
        return json.load(f)


def build_events() -> dict:
    """Build unified events data."""
    data = load_allsportdb_data()

    # Build competition lookup for ageGroup filtering
    comp_lookup = {c["id"]: c for c in data.get("competitions", [])}

    events = []
    sports_count = {}

    for event in data.get("events", []):
        comp_id = event.get("competitionId")
        comp_info = comp_lookup.get(comp_id, {})
        age_group = comp_info.get("ageGroup", "")

        # Filter: only Senior or unknown
        if age_group and age_group not in ("Senior", ""):
            continue

        sport = event.get("sport", "Unknown")
        sports_count[sport] = sports_count.get(sport, 0) + 1

        # Parse dates
        date_from = event.get("dateFrom", "")[:10] if event.get("dateFrom") else ""
        date_to = event.get("dateTo", "")[:10] if event.get("dateTo") else ""

        events.append({
            "id": event.get("id"),
            "name": event.get("name", ""),
            "date": date_from,
            "dateTo": date_to,
            "dateDisplay": event.get("date", ""),
            "sport": sport,
            "sportId": event.get("sportId"),
            "competition": event.get("competition", ""),
            "competitionId": comp_id,
            "continent": event.get("continent", ""),
            "emoji": event.get("emoji", "🏆"),
            "level": get_competition_level(event),
            "isMajorSport": sport in MAJOR_SPORTS,
            "webUrl": event.get("webUrl", ""),
            "wikiUrl": event.get("wikiUrl", ""),
            "logoUrl": event.get("logoThumbnailUrl", ""),
            "locations": [
                {"country": loc.get("name"), "city": loc.get("locations", [{}])[0].get("name")}
                for loc in event.get("location", [])
            ],
        })

    # Sort by date
    events.sort(key=lambda e: e.get("date", ""))

    # Build metadata
    sports_list = sorted(sports_count.items(), key=lambda x: -x[1])

    return {
        "events": events,
        "metadata": {
            "total_count": len(events),
            "sports": {s: c for s, c in sports_list},
            "major_sports_count": sum(1 for e in events if e["isMajorSport"]),
            "generated_at": datetime.now().isoformat(),
        }
    }


def main():
    print("Building events data...")
    data = build_events()

    output_path = DATA_DIR / "events_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved {data['metadata']['total_count']} events to {output_path}")
    print(f"Sports breakdown:")
    for sport, count in list(data["metadata"]["sports"].items())[:15]:
        marker = "★" if sport in MAJOR_SPORTS else " "
        print(f"  {marker} {sport}: {count}")


if __name__ == "__main__":
    main()
