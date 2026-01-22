"""Merge leagues.json with major_sports_by_country.json reference data."""

import json
from pathlib import Path
from collections import defaultdict

# Sport mapping: TheSportsDB → Reference
SPORT_MAPPING = {
    "Soccer": "Football",
    "Fighting": ["MMA", "Boxing", "Wrestling", "Lucha Libre"],
    "American Football": "American Football",
    "Ice Hockey": "Ice Hockey",
    "Motorsport": "Motorsport",
    "Rugby": "Rugby",
    "Basketball": "Basketball",
    "Baseball": "Baseball",
    "Cricket": "Cricket",
    "Tennis": "Tennis",
    "Golf": "Golf",
    "Cycling": "Cycling",
    "Volleyball": "Volleyball",
    "Handball": "Handball",
    "Australian Rules": "Australian Rules Football",
    "Esports": None,  # Ignore
}

# UK aggregation mapping
UK_COUNTRIES = ["England", "Scotland", "Wales", "Northern Ireland"]


def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict, path: Path) -> None:
    """Save JSON file with pretty formatting."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def normalize_sport(sport: str) -> str | list | None:
    """Map TheSportsDB sport to reference sport(s)."""
    return SPORT_MAPPING.get(sport, sport)


def aggregate_uk_leagues(leagues_data: dict) -> dict:
    """Aggregate UK countries into United Kingdom."""
    uk_leagues = []
    for country in UK_COUNTRIES:
        if country in leagues_data:
            uk_leagues.extend(leagues_data[country])
            del leagues_data[country]

    if uk_leagues:
        leagues_data["United Kingdom"] = uk_leagues

    return leagues_data


def get_matching_sport(league_sport: str, major_sports: list[str]) -> str | None:
    """Check if a league sport matches any major sport."""
    normalized = normalize_sport(league_sport)

    if normalized is None:
        return None

    if isinstance(normalized, list):
        # Fighting maps to multiple sports
        for sport in normalized:
            if sport in major_sports:
                return sport
        return normalized[0] if normalized else None

    return normalized if normalized in major_sports else normalized


def process_country(country: str, leagues: list, reference: dict) -> dict:
    """Process a single country and compute coverage."""
    ref_data = reference.get(country, {})
    major_sports = ref_data.get("major_sports", [])

    # Group leagues by normalized sport
    leagues_by_sport = defaultdict(list)
    for league in leagues:
        sport = league.get("sport", "Unknown")
        normalized = normalize_sport(sport)

        if normalized is None:
            continue

        if isinstance(normalized, list):
            # For Fighting, try to match to a major sport
            matched = False
            for s in normalized:
                if s in major_sports:
                    leagues_by_sport[s].append({"name": league["name"]})
                    matched = True
                    break
            if not matched:
                # Default to first option if no match
                leagues_by_sport[normalized[0]].append({"name": league["name"]})
        else:
            leagues_by_sport[normalized].append({"name": league["name"]})

    # Calculate coverage
    found_sports = set(leagues_by_sport.keys())
    major_set = set(major_sports)

    matched = sorted(found_sports & major_set)
    missing = sorted(major_set - found_sports)
    extra = sorted(found_sports - major_set)

    # Stats
    total_leagues = len(leagues)
    matched_leagues = sum(
        len(leagues_by_sport[s]) for s in matched
    )
    coverage_percent = round(len(matched) / len(major_sports) * 100) if major_sports else 0

    return {
        "code": ref_data.get("code", ""),
        "major_sports": major_sports,
        "leagues_by_sport": dict(sorted(leagues_by_sport.items())),
        "coverage": {
            "matched": matched,
            "missing": missing,
            "extra_sports": extra,
        },
        "stats": {
            "total_leagues": total_leagues,
            "matched_leagues": matched_leagues,
            "coverage_percent": coverage_percent,
        },
        "notes": ref_data.get("notes", ""),
    }


def main():
    """Main merge function."""
    base_path = Path(__file__).parent

    # Load data
    leagues_data = load_json(base_path / "leagues.json")
    reference_data = load_json(base_path / "major_sports_by_country.json")

    print(f"Loaded {len(leagues_data)} countries from leagues.json")
    print(f"Loaded {len(reference_data)} countries from reference")

    # Aggregate UK
    leagues_data = aggregate_uk_leagues(leagues_data)
    print(f"After UK aggregation: {len(leagues_data)} countries")

    # Identify countries
    leagues_countries = set(leagues_data.keys())
    reference_countries = set(reference_data.keys())

    missing_in_leagues = reference_countries - leagues_countries
    unreferenced = leagues_countries - reference_countries

    if missing_in_leagues:
        print(f"\nCountries in reference but NOT in leagues.json:")
        for c in sorted(missing_in_leagues):
            print(f"  - {c}")

    # Process each country in reference
    merged = {}
    for country in reference_data:
        leagues = leagues_data.get(country, [])
        merged[country] = process_country(country, leagues, reference_data)

        # Debug output
        stats = merged[country]["stats"]
        coverage = merged[country]["coverage"]
        print(
            f"  {country}: {stats['total_leagues']} leagues, "
            f"{stats['coverage_percent']}% coverage, "
            f"missing: {coverage['missing']}"
        )

    # Add metadata
    output = {
        "_meta": {
            "generated": True,
            "countries_in_reference": len(reference_data),
            "countries_with_data": len(reference_countries - missing_in_leagues),
            "unreferenced_countries": sorted(unreferenced),
        },
        "countries": merged,
    }

    # Save output
    output_path = base_path / "merged_sports_data.json"
    save_json(output, output_path)
    print(f"\nSaved merged data to {output_path}")

    # Summary
    total_matched = sum(m["stats"]["matched_leagues"] for m in merged.values())
    total_leagues = sum(m["stats"]["total_leagues"] for m in merged.values())
    countries_with_data = len([m for m in merged.values() if m["stats"]["total_leagues"] > 0])
    avg_coverage = sum(m["stats"]["coverage_percent"] for m in merged.values()) / len(merged)

    print(f"\nSummary:")
    print(f"  Countries in reference: {len(merged)}")
    print(f"  Countries with league data: {countries_with_data}")
    print(f"  Total leagues: {total_leagues}")
    print(f"  Matched leagues: {total_matched}")
    print(f"  Average coverage: {avg_coverage:.1f}%")
    print(f"  Unreferenced countries: {len(unreferenced)}")


if __name__ == "__main__":
    main()
