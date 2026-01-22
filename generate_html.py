"""Generate static HTML calendar from events_data.json."""

import json
from html import escape
from pathlib import Path

DATA_DIR = Path(__file__).parent


def load_events() -> dict:
    """Load events from events_data.json."""
    with open(DATA_DIR / "events_data.json") as f:
        return json.load(f)


def render_event_card(event: dict, for_calendar: bool = False) -> str:
    """Render a single event card."""
    emoji = event.get("emoji", "🏆")
    name = escape(event.get("name", ""))
    competition = escape(event.get("competition", ""))
    sport = escape(event.get("sport", ""))
    date_display = escape(event.get("dateDisplay", event.get("date", "")))
    continent = event.get("continent", "")
    level = event.get("level", 4)
    is_major = event.get("isMajorSport", False)
    web_url = event.get("webUrl", "")
    logo_url = event.get("logoUrl", "")

    # Level badge
    level_class = {1: "world", 2: "continental", 3: "national"}.get(level, "other")
    level_label = {1: "Mondial", 2: "Continental", 3: "National"}.get(level, "")
    level_badge = f'<span class="level-badge {level_class}">{level_label}</span>' if level_label else ""

    # Continent badge
    continent_badge = f'<span class="continent-badge">{escape(continent)}</span>' if continent else ""

    # Logo
    logo_html = f'<img src="{logo_url}" alt="" class="event-logo" loading="lazy">' if logo_url else ""

    # Link
    link_html = f'<a href="{web_url}" target="_blank" class="event-link" title="Site officiel">↗</a>' if web_url else ""

    # Major sport highlight
    major_class = "major-sport" if is_major else ""

    # Calendar-specific class
    calendar_class = "calendar-event" if for_calendar else ""

    return f'''
    <div class="event-card {major_class} {calendar_class}" data-sport="{sport}" data-level="{level}" data-date="{event.get('date', '')}">
        <div class="event-header">
            {logo_html}
            <span class="event-emoji">{emoji}</span>
            <div class="event-title">
                <div class="event-name">{name}{link_html}</div>
                <div class="event-meta">{competition} • {sport}</div>
            </div>
        </div>
        <div class="event-footer">
            <div class="event-date">{date_display}</div>
            <div class="event-badges">{level_badge}{continent_badge}</div>
        </div>
    </div>'''


def group_events_by_month(events: list) -> dict:
    """Group events by month."""
    by_month = {}
    for event in events:
        date = event.get("date", "")
        if not date or len(date) < 7:
            continue
        month = date[:7]  # YYYY-MM
        if month not in by_month:
            by_month[month] = []
        by_month[month].append(event)
    return by_month


def generate_html(data: dict) -> str:
    """Generate complete HTML page."""
    events = data.get("events", [])
    metadata = data.get("metadata", {})
    sports = metadata.get("sports", {})

    # Build sports filter options
    sports_options = "\n".join(
        f'<option value="{escape(sport)}">{escape(sport)} ({count})</option>'
        for sport, count in sorted(sports.items(), key=lambda x: -x[1])
    )

    # Render all events for grid view
    events_html = "".join(render_event_card(e) for e in events)

    # Render calendar view (pre-rendered by month)
    months_sorted = sorted(group_events_by_month(events).items())
    month_names = ['Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin',
                   'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre']

    calendar_html = ""
    for month, month_events in months_sorted:
        year, m = month.split('-')
        month_name = month_names[int(m) - 1]
        month_cards = "".join(render_event_card(e, for_calendar=True) for e in month_events)
        calendar_html += f'''
        <div class="calendar-month" data-month="{month}">
            <div class="calendar-month-header">{month_name} {year} ({len(month_events)})</div>
            <div class="calendar-month-events">{month_cards}</div>
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calendrier Sportif NSN</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            color: #1a1a2e;
            line-height: 1.5;
        }}

        /* Header */
        .header {{
            background: #1a1a2e;
            color: white;
            padding: 1.5rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        .header h1 {{
            font-size: 1.4rem;
            font-weight: 600;
        }}
        .header-stats {{
            display: flex;
            gap: 1.5rem;
            font-size: 0.9rem;
            opacity: 0.8;
        }}
        .header-stats strong {{
            color: #4fd1c5;
        }}

        /* Filters */
        .filters {{
            background: white;
            padding: 1rem 2rem;
            border-bottom: 1px solid #e2e8f0;
            position: sticky;
            top: 64px;
            z-index: 99;
        }}
        .filters-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            align-items: center;
        }}
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .filter-group label {{
            font-size: 0.85rem;
            color: #64748b;
            font-weight: 500;
        }}
        select, input[type="text"] {{
            padding: 0.5rem 0.75rem;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            font-size: 0.9rem;
            background: white;
            min-width: 150px;
        }}
        select:focus, input:focus {{
            outline: none;
            border-color: #4fd1c5;
        }}
        .view-toggle {{
            display: flex;
            gap: 0.25rem;
            margin-left: auto;
        }}
        .view-btn {{
            padding: 0.5rem 1rem;
            border: 1px solid #e2e8f0;
            background: white;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s;
        }}
        .view-btn:first-child {{ border-radius: 6px 0 0 6px; }}
        .view-btn:last-child {{ border-radius: 0 6px 6px 0; }}
        .view-btn.active {{
            background: #1a1a2e;
            color: white;
            border-color: #1a1a2e;
        }}
        .filter-count {{
            font-size: 0.85rem;
            color: #64748b;
            padding: 0.5rem 1rem;
            background: #f1f5f9;
            border-radius: 20px;
        }}

        /* Container */
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 1.5rem 2rem;
        }}

        /* Grid View */
        .events-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1rem;
        }}

        /* Calendar View */
        .events-calendar {{
            display: none;
        }}
        .events-calendar.active {{
            display: block;
        }}
        .events-grid.active {{
            display: grid;
        }}
        .events-grid:not(.active) {{
            display: none;
        }}

        .calendar-month {{
            margin-bottom: 2rem;
        }}
        .calendar-month.hidden {{
            display: none;
        }}
        .calendar-month-header {{
            font-size: 1.2rem;
            font-weight: 600;
            padding: 0.75rem 1rem;
            background: #1a1a2e;
            color: white;
            border-radius: 8px 8px 0 0;
            position: sticky;
            top: 130px;
            z-index: 10;
        }}
        .calendar-month-events {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            padding: 1rem;
            background: white;
            border-radius: 0 0 8px 8px;
        }}

        /* Event Card */
        .event-card {{
            background: white;
            border-radius: 8px;
            padding: 1rem;
            border: 1px solid #e2e8f0;
            transition: all 0.2s;
        }}
        .event-card:hover {{
            border-color: #4fd1c5;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }}
        .event-card.major-sport {{
            border-left: 3px solid #4fd1c5;
        }}
        .event-card.hidden {{
            display: none;
        }}
        .event-header {{
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            margin-bottom: 0.75rem;
        }}
        .event-logo {{
            width: 40px;
            height: 40px;
            object-fit: contain;
            border-radius: 4px;
        }}
        .event-emoji {{
            font-size: 1.5rem;
            line-height: 1;
        }}
        .event-title {{
            flex: 1;
            min-width: 0;
        }}
        .event-name {{
            font-weight: 600;
            font-size: 0.95rem;
            color: #1a1a2e;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .event-link {{
            color: #4fd1c5;
            text-decoration: none;
            font-size: 0.85rem;
        }}
        .event-link:hover {{
            text-decoration: underline;
        }}
        .event-meta {{
            font-size: 0.8rem;
            color: #64748b;
            margin-top: 0.2rem;
        }}
        .event-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        .event-date {{
            font-size: 0.85rem;
            color: #1a1a2e;
            background: #f1f5f9;
            padding: 0.3rem 0.6rem;
            border-radius: 4px;
        }}
        .event-badges {{
            display: flex;
            gap: 0.4rem;
        }}
        .level-badge {{
            font-size: 0.7rem;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-weight: 500;
            text-transform: uppercase;
        }}
        .level-badge.world {{
            background: #fef3c7;
            color: #92400e;
        }}
        .level-badge.continental {{
            background: #dbeafe;
            color: #1e40af;
        }}
        .level-badge.national {{
            background: #dcfce7;
            color: #166534;
        }}
        .continent-badge {{
            font-size: 0.7rem;
            background: #f1f5f9;
            color: #64748b;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
        }}

        /* Calendar-specific event styling */
        .calendar-event {{
            display: flex;
            flex-direction: row;
            align-items: center;
            padding: 0.75rem 1rem;
        }}
        .calendar-event .event-header {{
            flex: 1;
            margin-bottom: 0;
        }}
        .calendar-event .event-footer {{
            flex-shrink: 0;
        }}
        .calendar-event .event-date {{
            min-width: 140px;
            text-align: center;
        }}

        /* Empty state */
        .empty-state {{
            text-align: center;
            padding: 4rem 2rem;
            color: #64748b;
        }}
        .empty-state h3 {{
            font-size: 1.2rem;
            margin-bottom: 0.5rem;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .header-content {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .filters-content {{
                flex-direction: column;
                align-items: stretch;
            }}
            .view-toggle {{
                margin-left: 0;
            }}
            .events-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <h1>Calendrier Sportif NSN</h1>
            <div class="header-stats">
                <span><strong>{metadata.get('total_count', 0)}</strong> evenements</span>
                <span><strong>{len(sports)}</strong> sports</span>
            </div>
        </div>
    </header>

    <div class="filters">
        <div class="filters-content">
            <div class="filter-group">
                <label for="sport-filter">Sport</label>
                <select id="sport-filter">
                    <option value="">Tous les sports</option>
                    {sports_options}
                </select>
            </div>
            <div class="filter-group">
                <label for="level-filter">Niveau</label>
                <select id="level-filter">
                    <option value="">Tous les niveaux</option>
                    <option value="1">Mondial</option>
                    <option value="2">Continental</option>
                    <option value="3">National</option>
                </select>
            </div>
            <div class="filter-group">
                <label for="search-filter">Recherche</label>
                <input type="text" id="search-filter" placeholder="Nom, competition...">
            </div>
            <span class="filter-count" id="filter-count">{metadata.get('total_count', 0)} evenements</span>
            <div class="view-toggle">
                <button class="view-btn active" data-view="grid">Liste</button>
                <button class="view-btn" data-view="calendar">Calendrier</button>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="events-grid active" id="events-grid">
            {events_html}
        </div>
        <div class="events-calendar" id="events-calendar">
            {calendar_html}
        </div>
        <div class="empty-state" id="empty-state" style="display: none;">
            <h3>Aucun evenement trouve</h3>
            <p>Essayez de modifier vos filtres</p>
        </div>
    </div>

    <script>
        (function() {{
            const sportFilter = document.getElementById('sport-filter');
            const levelFilter = document.getElementById('level-filter');
            const searchFilter = document.getElementById('search-filter');
            const filterCount = document.getElementById('filter-count');
            const eventsGrid = document.getElementById('events-grid');
            const eventsCalendar = document.getElementById('events-calendar');
            const emptyState = document.getElementById('empty-state');
            const viewBtns = document.querySelectorAll('.view-btn');

            const gridEvents = eventsGrid.querySelectorAll('.event-card');
            const calendarEvents = eventsCalendar.querySelectorAll('.event-card');
            const calendarMonths = eventsCalendar.querySelectorAll('.calendar-month');

            function filterEvents() {{
                const sport = sportFilter.value.toLowerCase();
                const level = levelFilter.value;
                const search = searchFilter.value.toLowerCase();

                let visibleCount = 0;

                // Filter grid events
                gridEvents.forEach(function(card) {{
                    const cardSport = card.dataset.sport.toLowerCase();
                    const cardLevel = card.dataset.level;
                    const cardText = card.textContent.toLowerCase();

                    const match = (!sport || cardSport === sport) &&
                                  (!level || cardLevel === level) &&
                                  (!search || cardText.indexOf(search) >= 0);

                    if (match) {{
                        card.classList.remove('hidden');
                        visibleCount++;
                    }} else {{
                        card.classList.add('hidden');
                    }}
                }});

                // Filter calendar events
                calendarEvents.forEach(function(card) {{
                    const cardSport = card.dataset.sport.toLowerCase();
                    const cardLevel = card.dataset.level;
                    const cardText = card.textContent.toLowerCase();

                    const match = (!sport || cardSport === sport) &&
                                  (!level || cardLevel === level) &&
                                  (!search || cardText.indexOf(search) >= 0);

                    if (match) {{
                        card.classList.remove('hidden');
                    }} else {{
                        card.classList.add('hidden');
                    }}
                }});

                // Hide empty months
                calendarMonths.forEach(function(month) {{
                    const visible = month.querySelectorAll('.event-card:not(.hidden)').length;
                    if (visible === 0) {{
                        month.classList.add('hidden');
                    }} else {{
                        month.classList.remove('hidden');
                    }}
                }});

                filterCount.textContent = visibleCount + ' evenements';
                emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
            }}

            function switchView(view) {{
                viewBtns.forEach(function(btn) {{
                    btn.classList.toggle('active', btn.dataset.view === view);
                }});
                eventsGrid.classList.toggle('active', view === 'grid');
                eventsCalendar.classList.toggle('active', view === 'calendar');
            }}

            sportFilter.addEventListener('change', filterEvents);
            levelFilter.addEventListener('change', filterEvents);
            searchFilter.addEventListener('input', filterEvents);
            viewBtns.forEach(function(btn) {{
                btn.addEventListener('click', function() {{ switchView(btn.dataset.view); }});
            }});
        }})();
    </script>
</body>
</html>'''


def main():
    data = load_events()
    html = generate_html(data)

    output_path = DATA_DIR / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated {output_path}")
    print(f"  {data['metadata']['total_count']} events")


if __name__ == "__main__":
    main()
