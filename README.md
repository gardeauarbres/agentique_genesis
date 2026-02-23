# agentique_genesis
Agent autonome genesis

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -r requirements.txt
python scripts/smoke_test.py
pytest -q
```

The smoke test validates the baseline runtime (Python 3.10+) and checks the core imports used by the app.
If you run Python 3.14, this same smoke test is valid and should pass once dependencies are installed.

## Optimisations recommandées

- Ajouter des timeouts/retries et un budget d'exécution (`max_iterations`, `max_tool_calls`, `max_seconds`).
- Ajouter des sorties structurées par outil (objets Pydantic) pour fiabiliser le pipeline.
- Ajouter un cache simple (TTL) pour éviter les appels web redondants.
- Journaliser les étapes/outils (latence, erreurs, nombre d'appels).

## Outils gratuits proposés (MVP)

- `search_web(query)`: recherche DuckDuckGo.
- `fetch_url_text(url)`: extraction de texte lisible depuis une URL.
- `fact_check(claim)`: verdict léger basé sur diversité de sources.
