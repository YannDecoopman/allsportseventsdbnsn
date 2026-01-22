#!/usr/bin/env python3
"""Fetch Google Trends data for sports leagues using pytrends."""

import json
import time
from pathlib import Path

from pytrends.request import TrendReq

# Leagues to track with their search terms
# Format: {"League Name": "search_term"}
LEAGUES_TRENDS = {
    # Football - Top European
    "Ligue 1": "Ligue 1",
    "Premier League": "Premier League football",
    "Bundesliga": "Bundesliga",
    "La Liga": "La Liga",
    "Serie A": "Serie A",
    "Eredivisie": "Eredivisie",
    "Primeira Liga": "Primeira Liga",
    "Belgian Pro League": "Belgian Pro League",
    "Super League Switzerland": "Swiss Super League",
    "Austrian Bundesliga": "Austrian Bundesliga",
    "Superligaen": "Danish Superliga",
    "Eliteserien": "Eliteserien",
    "Allsvenskan": "Allsvenskan",
    "Super League Greece": "Super League Greece",
    "Super Lig": "Süper Lig",
    "Russian Premier League": "Russian Premier League",
    "Ekstraklasa": "Ekstraklasa",
    "League of Ireland Premier Division": "League of Ireland",

    # Football - Americas
    "Major League Soccer": "MLS soccer",
    "Liga MX": "Liga MX",
    "Brasileirao": "Brasileirão",
    "Argentine Primera Division": "Argentine Primera División",

    # Football - Asia
    "Chinese Super League": "Chinese Super League",
    "K League 1": "K League",
    "J1 League": "J League",
    "Indian Super League": "Indian Super League",
    "A-League Men": "A-League",

    # American Football
    "NFL": "NFL",
    "CFL": "CFL football",

    # Basketball
    "NBA": "NBA",
    "EuroLeague": "EuroLeague basketball",
    "Chinese Basketball Association": "CBA basketball",

    # Ice Hockey
    "NHL": "NHL",
    "KHL": "KHL hockey",

    # Baseball
    "MLB": "MLB",
    "Nippon Professional Baseball": "NPB baseball",
    "KBO League": "KBO",

    # Rugby
    "Top 14": "Top 14 rugby",
    "Premiership Rugby": "Premiership Rugby",
    "Super Rugby": "Super Rugby",

    # Cricket
    "Indian Premier League": "IPL cricket",
    "The Ashes": "The Ashes cricket",
    "Big Bash League": "Big Bash League",

    # MMA
    "UFC": "UFC",

    # Tennis
    "ATP Tour": "ATP tennis",
    "WTA Tour": "WTA tennis",

    # Motorsport
    "Formula One": "Formula 1",
    "NASCAR": "NASCAR",
    "MotoGP": "MotoGP",

    # Golf
    "PGA Tour": "PGA Tour",

    # Cycling
    "Tour de France": "Tour de France",
    "Giro d'Italia": "Giro d'Italia",

    # Australian Rules
    "AFL": "AFL football",

    # Handball
    "Handball-Bundesliga": "Handball Bundesliga",
}

# Batch size for pytrends (max 5 terms per request)
BATCH_SIZE = 5
RATE_LIMIT_DELAY = 2  # seconds between batches


def fetch_trends_batch(pytrends: TrendReq, terms: list[str]) -> dict[str, int]:
    """Fetch Google Trends interest for a batch of terms."""
    results = {}
    try:
        pytrends.build_payload(terms, timeframe="today 12-m", geo="")
        interest = pytrends.interest_over_time()

        if interest.empty:
            return {term: 0 for term in terms}

        # Get average interest over the period
        for term in terms:
            if term in interest.columns:
                results[term] = int(interest[term].mean())
            else:
                results[term] = 0
    except Exception as e:
        print(f"    Error: {e}")
        return {term: 0 for term in terms}

    return results


def main():
    """Fetch Google Trends data for leagues."""
    base_path = Path(__file__).parent
    output_path = base_path / "google_trends_data.json"

    print(f"Fetching Google Trends for {len(LEAGUES_TRENDS)} leagues...")

    # Initialize pytrends
    pytrends = TrendReq(hl="en-US", tz=360)

    # Prepare batches
    leagues = list(LEAGUES_TRENDS.items())
    results = {}

    for i in range(0, len(leagues), BATCH_SIZE):
        batch = leagues[i:i + BATCH_SIZE]
        terms = [term for _, term in batch]
        names = [name for name, _ in batch]

        print(f"  Batch {i // BATCH_SIZE + 1}: {', '.join(names[:3])}...")

        trends = fetch_trends_batch(pytrends, terms)

        # Map results back to league names
        for name, term in batch:
            results[name] = {
                "google_trends_index": trends.get(term, 0),
                "search_term": term,
            }

        time.sleep(RATE_LIMIT_DELAY)

    # Save results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved Google Trends data for {len(results)} leagues to {output_path}")

    # Top 10 by trends
    sorted_leagues = sorted(
        results.items(),
        key=lambda x: x[1]["google_trends_index"],
        reverse=True
    )[:10]

    print("\nTop 10 leagues by Google Trends interest:")
    for i, (league, data) in enumerate(sorted_leagues, 1):
        print(f"  {i}. {league}: {data['google_trends_index']}")


if __name__ == "__main__":
    main()
