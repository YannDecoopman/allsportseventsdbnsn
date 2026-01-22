#!/usr/bin/env python3
"""Enrich merged_sports_data.json with popularity scores from multiple sources."""

import json
import math
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


def normalize_league_name(name: str) -> str:
    """Normalize league name for matching."""
    return name.lower().replace("-", " ").replace("_", " ").strip()


def calculate_tier(score: int) -> str:
    """Calculate popularity tier based on normalized score."""
    if score >= 75:
        return "A"
    elif score >= 50:
        return "B"
    elif score >= 25:
        return "C"
    else:
        return "D"


def normalize_log_scale(value: float, max_value: float) -> int:
    """Normalize value using log scale (0-100)."""
    if value <= 0 or max_value <= 0:
        return 0
    return int(math.log10(value + 1) / math.log10(max_value + 1) * 100)


def main():
    """Enrich merged sports data with popularity scores and season info."""
    base_path = Path(__file__).parent

    # Load all data sources
    merged_path = base_path / "merged_sports_data.json"
    wikipedia_path = base_path / "popularity_data.json"
    trends_path = base_path / "google_trends_data.json"
    seasons_path = base_path / "seasons_data.json"

    merged_data = load_json(merged_path)
    wikipedia_data = load_json(wikipedia_path)
    trends_data = load_json(trends_path)
    seasons_data = load_json(seasons_path)

    if not merged_data:
        print("Error: merged_sports_data.json not found. Run merge_data.py first.")
        return

    print(f"Loaded {len(merged_data.get('countries', {}))} countries")
    print(f"Wikipedia data: {len(wikipedia_data)} leagues")
    print(f"Google Trends data: {len(trends_data)} leagues")
    print(f"Seasons data: {len(seasons_data)} leagues")

    # Find max values for normalization
    wiki_max = max(
        (d.get("wikipedia_monthly_views", 0) for d in wikipedia_data.values()),
        default=1
    )
    trends_max = max(
        (d.get("google_trends_index", 0) for d in trends_data.values()),
        default=1
    )

    print(f"\nMax Wikipedia views: {wiki_max:,}")
    print(f"Max Google Trends index: {trends_max}")

    # Create normalized lookups
    def create_lookup(data: dict) -> dict:
        lookup = {}
        for league_name, league_data in data.items():
            normalized = normalize_league_name(league_name)
            lookup[normalized] = league_data
            # Add without common suffixes
            for suffix in [" league", " division", " liga", " tour"]:
                if normalized.endswith(suffix):
                    lookup[normalized[:-len(suffix)].strip()] = league_data
        return lookup

    wiki_lookup = create_lookup(wikipedia_data)
    trends_lookup = create_lookup(trends_data)
    seasons_lookup = create_lookup(seasons_data)

    # Weights for combined score (normalized to 100%)
    # Original plan: wiki 30%, trends 25%, social 25%, attendance 20%
    # With only 2 sources: wiki 55%, trends 45%
    WIKI_WEIGHT = 0.55
    TRENDS_WEIGHT = 0.45

    # Enrich leagues with popularity
    enriched_count = 0
    for country, country_data in merged_data.get("countries", {}).items():
        leagues_by_sport = country_data.get("leagues_by_sport", {})

        for sport, leagues in leagues_by_sport.items():
            for league in leagues:
                league_name = league.get("name", "")
                normalized = normalize_league_name(league_name)

                # Try to find data from each source
                wiki_data = None
                trends_data_item = None

                # Exact match first
                if normalized in wiki_lookup:
                    wiki_data = wiki_lookup[normalized]
                if normalized in trends_lookup:
                    trends_data_item = trends_lookup[normalized]

                # Partial matching if no exact match
                if not wiki_data:
                    for pop_name, data in wiki_lookup.items():
                        if pop_name in normalized or normalized in pop_name:
                            wiki_data = data
                            break

                if not trends_data_item:
                    for pop_name, data in trends_lookup.items():
                        if pop_name in normalized or normalized in pop_name:
                            trends_data_item = data
                            break

                # Calculate combined score if we have any data
                if wiki_data or trends_data_item:
                    wiki_views = wiki_data.get("wikipedia_monthly_views", 0) if wiki_data else 0
                    trends_index = trends_data_item.get("google_trends_index", 0) if trends_data_item else 0

                    # Normalize each metric
                    wiki_norm = normalize_log_scale(wiki_views, wiki_max)
                    trends_norm = int(trends_index / trends_max * 100) if trends_max > 0 else 0

                    # Calculate weighted score
                    sources_used = []
                    total_weight = 0

                    if wiki_data:
                        sources_used.append("wikipedia")
                        total_weight += WIKI_WEIGHT

                    if trends_data_item:
                        sources_used.append("google_trends")
                        total_weight += TRENDS_WEIGHT

                    # Normalize weights if only one source
                    if total_weight > 0:
                        wiki_contrib = (wiki_norm * WIKI_WEIGHT) / total_weight if wiki_data else 0
                        trends_contrib = (trends_norm * TRENDS_WEIGHT) / total_weight if trends_data_item else 0
                        combined_score = int(wiki_contrib + trends_contrib)
                    else:
                        combined_score = 0

                    league["popularity"] = {
                        "score": combined_score,
                        "tier": calculate_tier(combined_score),
                        "sources": sources_used,
                    }

                    if wiki_data:
                        league["popularity"]["wikipedia_monthly_views"] = wiki_views
                        league["popularity"]["wikipedia_score"] = wiki_norm

                    if trends_data_item:
                        league["popularity"]["google_trends_index"] = trends_index
                        league["popularity"]["google_trends_score"] = trends_norm

                    enriched_count += 1

                # Add season data
                season_data_item = None
                if normalized in seasons_lookup:
                    season_data_item = seasons_lookup[normalized]
                else:
                    # Partial matching
                    for season_name, data in seasons_lookup.items():
                        if season_name in normalized or normalized in season_name:
                            season_data_item = data
                            break

                if season_data_item:
                    league["season"] = {
                        "current": season_data_item.get("current_season"),
                        "start_date": season_data_item.get("start_date"),
                        "end_date": season_data_item.get("end_date"),
                        "events_count": season_data_item.get("events_count"),
                    }

    # Count leagues with season data
    season_count = 0
    for country_data in merged_data.get("countries", {}).values():
        for leagues in country_data.get("leagues_by_sport", {}).values():
            for league in leagues:
                if "season" in league:
                    season_count += 1

    # Update metadata
    if "_meta" not in merged_data:
        merged_data["_meta"] = {}
    merged_data["_meta"]["enriched_with_popularity"] = True
    merged_data["_meta"]["leagues_with_popularity"] = enriched_count
    merged_data["_meta"]["leagues_with_season"] = season_count
    merged_data["_meta"]["popularity_sources"] = ["wikipedia", "google_trends"]
    merged_data["_meta"]["popularity_weights"] = {
        "wikipedia": WIKI_WEIGHT,
        "google_trends": TRENDS_WEIGHT,
    }

    # Save enriched data
    save_json(merged_data, merged_path)
    print(f"\nEnriched {enriched_count} leagues with popularity data")
    print(f"Enriched {season_count} leagues with season data")
    print(f"Saved to {merged_path}")

    # Summary by tier
    tier_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    for country_data in merged_data.get("countries", {}).values():
        for leagues in country_data.get("leagues_by_sport", {}).values():
            for league in leagues:
                if "popularity" in league:
                    tier = league["popularity"].get("tier", "D")
                    tier_counts[tier] = tier_counts.get(tier, 0) + 1

    print("\nLeagues by popularity tier:")
    for tier in ["A", "B", "C", "D"]:
        print(f"  Tier {tier}: {tier_counts[tier]} leagues")

    # Show some examples
    print("\nSample enriched leagues:")
    count = 0
    for country_data in merged_data.get("countries", {}).values():
        for leagues in country_data.get("leagues_by_sport", {}).values():
            for league in leagues:
                if "popularity" in league and len(league["popularity"].get("sources", [])) == 2:
                    pop = league["popularity"]
                    print(f"  {league['name']}: score={pop['score']} tier={pop['tier']} "
                          f"(wiki={pop.get('wikipedia_score', 0)}, trends={pop.get('google_trends_score', 0)})")
                    count += 1
                    if count >= 5:
                        break
            if count >= 5:
                break
        if count >= 5:
            break


if __name__ == "__main__":
    main()
