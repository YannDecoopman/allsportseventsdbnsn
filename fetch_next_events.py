"""Fetch upcoming events from TheSportsDB using eventsround endpoint."""

import json
import time
from datetime import datetime
from pathlib import Path

import httpx

BASE_URL = "https://www.thesportsdb.com/api/v1/json/3"
DATA_DIR = Path(__file__).parent

# Leagues with TheSportsDB IDs (from all_leagues endpoint)
# Format: (id, name, season_format)
LEAGUES = [
    ("4328", "English Premier League", "2025-2026"),
    ("4331", "German Bundesliga", "2025-2026"),
    ("4332", "Italian Serie A", "2025-2026"),
    ("4334", "French Ligue 1", "2025-2026"),
    ("4335", "Spanish La Liga", "2025-2026"),
    ("4337", "Dutch Eredivisie", "2025-2026"),
    ("4339", "Turkish Super Lig", "2025-2026"),
    ("4344", "Portuguese Primeira Liga", "2025-2026"),
    ("4346", "Major League Soccer", "2026"),
    ("4347", "Swedish Allsvenskan", "2026"),
    ("4350", "Liga MX", "2025-2026"),
    ("4351", "Brazilian Serie A", "2026"),
    ("4358", "Norwegian Eliteserien", "2026"),
    ("4359", "English Championship", "2025-2026"),
    ("4380", "Russian Premier League", "2025-2026"),
    ("4422", "Polish Ekstraklasa", "2025-2026"),
    ("4675", "Swiss Super League", "2025-2026"),
]


def load_allsportdb_events() -> list:
    """Load existing events from AllSportDB data."""
    path = DATA_DIR / "allsportdb_data.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)

    comp_age = {c["id"]: c.get("ageGroup", "") for c in data.get("competitions", [])}

    events = []
    for event in data.get("events", []):
        comp_id = event.get("competitionId")
        age_group = comp_age.get(comp_id, "")
        if age_group in ("Senior", ""):
            events.append({
                "source": "allsportdb",
                "id": event.get("id"),
                "name": event.get("name", ""),
                "date": event.get("dateFrom", ""),
                "time": None,
                "homeTeam": None,
                "awayTeam": None,
                "league": event.get("competition", ""),
                "sport": event.get("sport", ""),
                "emoji": event.get("emoji", "🏆"),
                "webUrl": event.get("webUrl", ""),
                "eventType": "tournament",
            })
    return events


def get_current_round(league_id: str, season: str, client: httpx.Client) -> int:
    """Get current round by checking standings (games played)."""
    try:
        resp = client.get(
            f"{BASE_URL}/lookuptable.php",
            params={"l": league_id, "s": season}
        )
        resp.raise_for_status()
        data = resp.json()

        if data and data.get("table"):
            played = int(data["table"][0].get("intPlayed", 0))
            return played + 1  # Next round is played + 1
        return 1
    except (httpx.HTTPError, ValueError, IndexError):
        return 1


def fetch_events_for_round(
    league_id: str,
    round_num: int,
    season: str,
    client: httpx.Client
) -> list:
    """Fetch events for a specific round."""
    try:
        resp = client.get(
            f"{BASE_URL}/eventsround.php",
            params={"id": league_id, "r": round_num, "s": season}
        )
        resp.raise_for_status()
        data = resp.json()

        if not data or not data.get("events"):
            return []

        today = datetime.now().strftime("%Y-%m-%d")
        events = []

        for e in data["events"]:
            date_str = e.get("dateEvent", "")
            # Only include future events
            if date_str >= today:
                time_str = e.get("strTime", "")
                events.append({
                    "source": "thesportsdb",
                    "id": e.get("idEvent"),
                    "name": f'{e.get("strHomeTeam", "")} vs {e.get("strAwayTeam", "")}',
                    "date": date_str,
                    "time": time_str[:5] if time_str and len(time_str) >= 5 else None,
                    "homeTeam": e.get("strHomeTeam"),
                    "awayTeam": e.get("strAwayTeam"),
                    "league": e.get("strLeague", ""),
                    "sport": e.get("strSport", "Soccer"),
                    "emoji": get_sport_emoji(e.get("strSport", "Soccer")),
                    "webUrl": None,
                    "eventType": "match",
                    "venue": e.get("strVenue"),
                    "round": str(round_num),
                })
        return events

    except httpx.HTTPError:
        return []


def get_sport_emoji(sport: str) -> str:
    """Get emoji for a sport."""
    emojis = {
        "Soccer": "⚽",
        "American Football": "🏈",
        "Basketball": "🏀",
        "Ice Hockey": "🏒",
        "Baseball": "⚾",
        "Cricket": "🏏",
        "Rugby": "🏉",
        "Tennis": "🎾",
        "Golf": "⛳",
        "Motorsport": "🏎️",
        "MMA": "🥊",
        "Boxing": "🥊",
        "Cycling": "🚴",
        "Australian Rules": "🏈",
    }
    return emojis.get(sport, "🏆")


def main():
    print("Fetching upcoming events from TheSportsDB...")

    all_events = []

    with httpx.Client(timeout=30) as client:
        for league_id, league_name, season in LEAGUES:
            print(f"Processing {league_name}...")

            # Get current round
            current_round = get_current_round(league_id, season, client)
            print(f"  Current round: {current_round}")

            # Fetch next 3 rounds
            league_events = []
            for round_offset in range(3):
                round_num = current_round + round_offset
                events = fetch_events_for_round(league_id, round_num, season, client)
                league_events.extend(events)
                time.sleep(0.3)

            print(f"  -> {len(league_events)} upcoming events")
            all_events.extend(league_events)
            time.sleep(0.3)

    print(f"\nTotal TheSportsDB events: {len(all_events)}")

    # Load AllSportDB events
    print("Loading AllSportDB events...")
    allsportdb_events = load_allsportdb_events()
    print(f"AllSportDB events: {len(allsportdb_events)}")

    # Remove duplicates by event ID
    seen_ids = set()
    unique_events = []
    for e in all_events:
        if e["id"] not in seen_ids:
            seen_ids.add(e["id"])
            unique_events.append(e)

    # Combine and save
    combined_data = {
        "thesportsdb_events": unique_events,
        "allsportdb_events": allsportdb_events,
        "metadata": {
            "thesportsdb_count": len(unique_events),
            "allsportdb_count": len(allsportdb_events),
            "total_count": len(unique_events) + len(allsportdb_events),
            "leagues_fetched": len(LEAGUES),
            "generated_at": datetime.now().isoformat(),
        }
    }

    output_path = DATA_DIR / "events_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {output_path}")
    print(f"Total events: {combined_data['metadata']['total_count']}")


if __name__ == "__main__":
    main()
