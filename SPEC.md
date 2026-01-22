# SPEC - Calendrier Événements Sportifs NSN

## Objectif

Outil de planification éditoriale pour l'équipe NSN : vision globale des événements sportifs majeurs à venir pour savoir quoi couvrir.

## Problème résolu

- Suivi manuel fastidieux des dates de compétitions
- Infos éparpillées sur plusieurs sources
- Pas de vue consolidée pour l'équipe édito

## Utilisateurs

- **Qui** : Équipe éditoriale NSN
- **Fréquence** : Consultation régulière pour planifier le contenu
- **Auth** : Aucune (page accessible directement)

## Définition d'un "événement"

Tout ce qui mérite une couverture éditoriale :
- **Compétition entière** : Roland Garros, Coupe du Monde, Euro
- **GP / Étape / Round** : GP de Monaco, Étape 15 Tour de France
- **Journée de championnat** (post-MVP) : Ligue 1 J25

## Sports couverts

Tous les sports majeurs, pondérés par importance dans chaque pays :
- Football (ligues majeures + coupes internationales)
- Tennis (Grand Slam, Masters)
- Formule 1 (GPs)
- Rugby (Tournoi, Coupe du Monde)
- Basketball (NBA playoffs, EuroLeague)
- Cyclisme (Grands Tours)
- Hockey, MMA, Cricket, etc.

## Source de données

**AllSportDB uniquement** (pour le MVP)
- API : `https://allsportdb.com/api/`
- Récupérer TOUS les événements disponibles (pas juste les 23 actuels)
- Filtres :
  - Événements Senior uniquement
  - Sports majeurs prioritaires par pays
  - Niveau de compétition (Mondial > Continental > National)

Post-MVP : scraping si besoin de compléter

## Fonctionnalités MVP

### Data
- [ ] Fetch complet AllSportDB (tous les événements, pas juste calendar)
- [ ] Filtrage Senior + sports majeurs
- [ ] Stockage dans `events_data.json`

### UI
- [ ] Vue liste chronologique (actuelle, améliorée)
- [ ] Vue calendrier mensuel (grille)
- [ ] Toggle entre les 2 vues
- [ ] Filtres : par sport, par période (7j/30j/saison/custom)
- [ ] Recherche textuelle
- [ ] Distinction visuelle par type (tournoi vs GP vs journée)

### UX
- [ ] Période configurable par l'utilisateur
- [ ] Indicateur de niveau de compétition (badge)
- [ ] Emoji par sport (déjà fait)

## Hors scope MVP

- Matchs individuels (PSG vs Lyon)
- Authentification
- Intégrations (Slack, Google Calendar, API)
- Notifications
- Marquage "couvert" / assignation rédacteur
- Scraping sources externes

## Stack technique

- **Data** : Python + AllSportDB API
- **UI** : HTML statique généré (pas de framework JS)
- **Hosting** : Serveur local / static file server
- **Refresh** : Manuel (script à lancer)

## Structure fichiers

```
allsportseventsdbnsn/
├── fetch_allsportdb.py      # Fetch complet AllSportDB
├── events_data.json         # Données consolidées
├── generate_html.py         # Génération HTML
├── index.html               # Page calendrier
├── SPEC.md                  # Ce fichier
└── ...
```

## Critères de succès

1. **Exhaustivité** : Tous les événements majeurs AllSportDB sont récupérés
2. **Lisibilité** : Vue claire et filtrable par l'équipe
3. **Multi-sport** : Tennis, F1, Rugby... pas que football
4. **Rapidité** : Chargement < 2s, filtres instantanés

## Estimation

**Budget** : Demi-journée

| Tâche | Temps estimé |
|-------|--------------|
| Fix fetch AllSportDB (tous events) | 1h |
| UI améliorée (filtres, vues) | 2h |
| Tests et ajustements | 30min |

## Résolu

- [x] AllSportDB expose 1176 events avec les paramètres `dateFrom` et `dateTo` (vs 23 sans)
- [x] Endpoint `/calendar?dateFrom=YYYY-MM-DD&dateTo=YYYY-MM-DD` avec pagination (100 items/page)
