#!/usr/bin/env python3
"""Fetch season information from TheSportsDB API."""

import json
import time
from pathlib import Path

import httpx

BASE_URL = "https://www.thesportsdb.com/api/v1/json/3"

# Major leagues to fetch seasons for (league name -> TheSportsDB search term)
LEAGUES_TO_FETCH = {
    # Football - Europe
    "French Ligue 1": "French Ligue 1",
    "English Premier League": "English Premier League",
    "German Bundesliga": "German Bundesliga",
    "Spanish La Liga": "Spanish La Liga",
    "Italian Serie A": "Italian Serie A",
    "Dutch Eredivisie": "Dutch Eredivisie",
    "Portuguese Primeira Liga": "Portuguese Primeira Liga",
    "Belgian First Division A": "Belgian First Division A",
    "Swiss Super League": "Swiss Super League",
    "Austrian Bundesliga": "Austrian Football Bundesliga",
    "Danish Superliga": "Danish Superliga",
    "Norwegian Eliteserien": "Norwegian Eliteserien",
    "Swedish Allsvenskan": "Swedish Allsvenskan",
    "Greek Super League": "Greek Super League",
    "Turkish Super Lig": "Turkish Super Lig",
    "Russian Premier League": "Russian Premier League",
    "Polish Ekstraklasa": "Polish Ekstraklasa",
    "League of Ireland": "League of Ireland Premier Division",

    # Football - Americas
    "American Major League Soccer": "American Major League Soccer",
    "Mexican Liga MX": "Mexican Primera League",
    "Brazilian Serie A": "Brazilian Serie A",
    "Argentine Primera Division": "Argentine Primera Division",

    # Football - Asia
    "Chinese Super League": "Chinese Super League",
    "Japanese J League": "Japanese J League",
    "Korean K League": "Korean K League",
    "Indian Super League": "Indian Super League",
    "Australian A-League": "Australian A-League",

    # American Football
    "NFL": "NFL",
    "CFL": "CFL",

    # Basketball
    "NBA": "NBA",
    "EuroLeague": "EuroLeague Basketball",

    # Ice Hockey
    "NHL": "NHL",
    "KHL": "KHL",

    # Baseball
    "MLB": "MLB",
    "Japanese NPB": "NPB",
    "Korean KBO": "KBO League",

    # Rugby
    "French Top 14": "French Top 14",
    "English Premiership Rugby": "English Premiership Rugby",

    # Cricket
    "Indian Premier League": "Indian Premier League",
    "Big Bash League": "Big Bash League",

    # MMA
    "UFC": "UFC",

    # Motorsport
    "Formula 1": "Formula 1",
    "NASCAR Cup Series": "NASCAR Cup Series",
    "MotoGP": "MotoGP",

    # Cycling
    "Tour de France": "Tour de France",

    # Australian Rules
    "AFL": "AFL",
}

RATE_LIMIT_DELAY = 1.5


def fetch_league_info(search_term: str, client: httpx.Client) -> dict | None:
    """Fetch league info including current season."""
    try:
        response = client.get(
            f"{BASE_URL}/search_all_leagues.php",
            params={"l": search_term}
        )
        response.raise_for_status()
        data = response.json()

        # API returns nested list: [[{league_info}]]
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], list) and len(data[0]) > 0:
                return data[0][0]
            elif isinstance(data[0], dict):
                return data[0]

        # Try dict format
        if isinstance(data, dict):
            if data.get("leagues"):
                return data["leagues"][0]
            elif data.get("countries"):
                for league in data["countries"]:
                    if search_term.lower() in league.get("strLeague", "").lower():
                        return league

        return None
    except httpx.HTTPError as e:
        print(f"error: {e}")
        return None


def fetch_season_events(league_id: str, season: str, client: httpx.Client) -> dict:
    """Fetch events for a specific season to get start/end dates."""
    try:
        response = client.get(
            f"{BASE_URL}/eventsseason.php",
            params={"id": league_id, "s": season}
        )
        response.raise_for_status()
        data = response.json()

        events = data.get("events") or []
        if not events:
            return {}

        # Get first and last event dates
        dates = [e.get("dateEvent") for e in events if e.get("dateEvent")]
        if not dates:
            return {}

        dates.sort()
        return {
            "start_date": dates[0],
            "end_date": dates[-1],
            "events_count": len(events),
        }
    except httpx.HTTPError as e:
        print(f"events error: {e}")
        return {}


def main():
    """Fetch season information for major leagues."""
    base_path = Path(__file__).parent
    output_path = base_path / "seasons_data.json"

    print(f"Fetching seasons for {len(LEAGUES_TO_FETCH)} major leagues...")

    results = {}

    with httpx.Client(timeout=30) as client:
        for league_name, search_term in LEAGUES_TO_FETCH.items():
            print(f"  {league_name}...", end=" ", flush=True)

            league_info = fetch_league_info(search_term, client)

            if not league_info:
                print("not found")
                time.sleep(RATE_LIMIT_DELAY)
                continue

            league_id = league_info.get("idLeague")
            current_season = league_info.get("strCurrentSeason")
            formed_year = league_info.get("intFormedYear")

            if not league_id:
                print("no ID")
                time.sleep(RATE_LIMIT_DELAY)
                continue

            # Get event dates for current season
            season_info = {}
            if current_season:
                time.sleep(RATE_LIMIT_DELAY)
                season_info = fetch_season_events(league_id, current_season, client)

            results[league_name] = {
                "league_id": league_id,
                "league_name": league_info.get("strLeague"),
                "sport": league_info.get("strSport"),
                "country": league_info.get("strCountry"),
                "current_season": current_season,
                "formed_year": formed_year,
                **season_info,
            }

            events = season_info.get("events_count", 0)
            start = season_info.get("start_date", "?")
            end = season_info.get("end_date", "?")
            print(f"✓ {current_season} ({start} → {end}, {events} events)")

            time.sleep(RATE_LIMIT_DELAY)

    # Save results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved season data for {len(results)} leagues to {output_path}")

    # Summary
    with_dates = sum(1 for r in results.values() if r.get("start_date"))
    print(f"Leagues with season dates: {with_dates}/{len(results)}")


if __name__ == "__main__":
    main()
