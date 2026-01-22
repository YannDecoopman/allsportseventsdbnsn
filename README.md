# All Sports Events DB

Script Python pour récupérer les compétitions sportives par pays via l'API TheSportsDB.

## Installation

```bash
uv sync
```

## Usage

```bash
uv run python fetch_leagues.py
```

Génère un fichier `leagues.json` avec la structure :

```json
{
  "France": [
    {"name": "Ligue 1", "sport": "Soccer"},
    {"name": "Top 14", "sport": "Rugby"}
  ],
  "Brazil": [...]
}
```

## Pays couverts

29 pays + UK décomposé en 4 régions (England, Scotland, Wales, Northern Ireland).

## API

- Source : [TheSportsDB](https://www.thesportsdb.com/)
- Endpoint : `search_all_leagues.php?c={country}`
- Rate limit : 0.5s entre requêtes
