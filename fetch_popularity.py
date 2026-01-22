#!/usr/bin/env python3
"""Fetch popularity data from Wikipedia pageviews API."""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import httpx

# Wikipedia API for pageviews
WIKI_API_URL = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"

# Major leagues to track popularity for
# Format: {"League Name": "Wikipedia_Article_Title"}
LEAGUES_WIKIPEDIA = {
    # Football - Top European Leagues
    "Ligue 1": "Ligue_1",
    "Premier League": "Premier_League",
    "Bundesliga": "Bundesliga",
    "La Liga": "La_Liga",
    "Serie A": "Serie_A",
    "Eredivisie": "Eredivisie",
    "Primeira Liga": "Primeira_Liga",
    "Belgian Pro League": "Belgian_First_Division_A",
    "Super League Switzerland": "Swiss_Super_League",
    "Austrian Bundesliga": "Austrian_Football_Bundesliga",
    "Superligaen": "Danish_Superliga",
    "Eliteserien": "Eliteserien",
    "Allsvenskan": "Allsvenskan",
    "Super League Greece": "Super_League_Greece",
    "Super Lig": "Süper_Lig",
    "Russian Premier League": "Russian_Premier_League",
    "Ekstraklasa": "Ekstraklasa",
    "League of Ireland Premier Division": "League_of_Ireland_Premier_Division",

    # Football - Americas
    "Major League Soccer": "Major_League_Soccer",
    "Liga MX": "Liga_MX",
    "Brasileirao": "Campeonato_Brasileiro_Série_A",
    "Argentine Primera Division": "Argentine_Primera_División",

    # Football - Asia/Oceania
    "Chinese Super League": "Chinese_Super_League",
    "K League 1": "K_League_1",
    "J1 League": "J1_League",
    "Indian Super League": "Indian_Super_League",
    "A-League Men": "A-League_Men",

    # American Football
    "NFL": "National_Football_League",
    "CFL": "Canadian_Football_League",

    # Basketball
    "NBA": "National_Basketball_Association",
    "EuroLeague": "EuroLeague",
    "Chinese Basketball Association": "Chinese_Basketball_Association",
    "Korean Basketball League": "Korean_Basketball_League",

    # Ice Hockey
    "NHL": "National_Hockey_League",
    "KHL": "Kontinental_Hockey_League",
    "SHL": "Swedish_Hockey_League",

    # Baseball
    "MLB": "Major_League_Baseball",
    "Nippon Professional Baseball": "Nippon_Professional_Baseball",
    "KBO League": "KBO_League",

    # Rugby
    "Top 14": "Top_14",
    "Premiership Rugby": "Premiership_Rugby",
    "Super Rugby": "Super_Rugby",

    # Cricket
    "Indian Premier League": "Indian_Premier_League",
    "The Ashes": "The_Ashes",
    "Big Bash League": "Big_Bash_League",

    # MMA
    "UFC": "Ultimate_Fighting_Championship",

    # Tennis
    "ATP Tour": "ATP_Tour",
    "WTA Tour": "WTA_Tour",

    # Motorsport
    "Formula One": "Formula_One",
    "NASCAR": "NASCAR",
    "MotoGP": "MotoGP",

    # Golf
    "PGA Tour": "PGA_Tour",

    # Cycling
    "Tour de France": "Tour_de_France",
    "Giro d'Italia": "Giro_d%27Italia",

    # Australian Rules
    "AFL": "Australian_Football_League",

    # Handball
    "Handball-Bundesliga": "Handball-Bundesliga",
    "LNH Division 1": "LNH_Division_1_(handball)",

    # Volleyball
    "CEV Champions League": "CEV_Champions_League_Volley",
}

RATE_LIMIT_DELAY = 0.2  # Wikipedia allows 100 req/s, be conservative


def get_pageviews(article: str, client: httpx.Client) -> int | None:
    """Get monthly pageviews for a Wikipedia article (last 6 months average)."""
    # Calculate date range (last 6 months)
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=180)

    url = f"{WIKI_API_URL}/en.wikipedia/all-access/all-agents/{article}/monthly/{start_date.strftime('%Y%m%d')}/{end_date.strftime('%Y%m%d')}"

    try:
        response = client.get(url)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()

        if "items" in data and data["items"]:
            total_views = sum(item["views"] for item in data["items"])
            return total_views // len(data["items"])  # Monthly average
        return None
    except httpx.HTTPError as e:
        print(f"    Error fetching {article}: {e}")
        return None


def calculate_tier(score: int) -> str:
    """Calculate popularity tier based on normalized score."""
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    else:
        return "D"


def main():
    """Fetch Wikipedia pageviews for major leagues."""
    base_path = Path(__file__).parent
    output_path = base_path / "popularity_data.json"

    results = {}
    all_views = []

    print(f"Fetching Wikipedia pageviews for {len(LEAGUES_WIKIPEDIA)} leagues...")

    with httpx.Client(
        timeout=30,
        headers={"User-Agent": "SportsDatabaseBot/1.0 (contact@example.com)"}
    ) as client:
        for league, article in LEAGUES_WIKIPEDIA.items():
            print(f"  {league}...", end=" ")
            views = get_pageviews(article, client)
            if views:
                results[league] = {
                    "wikipedia_monthly_views": views,
                    "wikipedia_article": article,
                }
                all_views.append(views)
                print(f"{views:,} views/month")
            else:
                print("no data")
            time.sleep(RATE_LIMIT_DELAY)

    # Normalize scores (0-100 based on max views)
    if all_views:
        max_views = max(all_views)
        for league, data in results.items():
            views = data["wikipedia_monthly_views"]
            # Log scale normalization for better distribution
            import math
            normalized = int(math.log10(views + 1) / math.log10(max_views + 1) * 100)
            data["score"] = normalized
            data["tier"] = calculate_tier(normalized)

    # Save results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved popularity data for {len(results)} leagues to {output_path}")

    # Top 10 by views
    print("\nTop 10 leagues by Wikipedia pageviews:")
    sorted_leagues = sorted(
        results.items(),
        key=lambda x: x[1]["wikipedia_monthly_views"],
        reverse=True
    )[:10]
    for i, (league, data) in enumerate(sorted_leagues, 1):
        print(f"  {i}. {league}: {data['wikipedia_monthly_views']:,} views (Tier {data['tier']})")


if __name__ == "__main__":
    main()
