# design.md — event-service

Riferimento contratto: `contracts/openapi/event-service.yaml`
Riferimento requisiti: `.kiro/specs/event-service/requirements.md`

---

## 1. Struttura

```
services/event-service/
├── app/
│   ├── __init__.py       # app factory Flask
│   ├── __main__.py       # entrypoint: python -m app
│   ├── routes.py         # HTTP layer
│   ├── business.py       # regole REQ-EVT-B01..B06
│   ├── repository.py     # interfaccia + memory/json/sqlite
│   ├── clients.py        # chiamata a user-service (isolata per mock nei test)
│   └── models.py         # schema Event, serializzazione
├── tests/unit/
├── tests/integration/
├── requirements.txt
└── pytest.ini
```

## 2. Componenti

- **`routes.py`**: parsing HTTP, delega a `business.py`, mappa eccezioni → status code.
- **`business.py`**: REQ-EVT-B01 (valida organizer via `clients.py`), REQ-EVT-B02 (role=organizer), REQ-EVT-B03 (end_date ≥ start_date), REQ-EVT-B04 (transizioni stato), REQ-EVT-B06 (filtri).
- **`clients.py`**: `get_user(organizer_id)` → chiama `GET USER_SERVICE_URL/api/v1/users/{id}`, usa `shared/http_client.py`. Isolato per mock nei test.
- **`repository.py`**: interfaccia `EventRepository` + MemoryEventRepository / JsonEventRepository / SqliteEventRepository.
- **`models.py`**: `new_event(data)`, `serialize_event(event)`.

## 3. Transizioni di stato ammesse

```
draft      → published, cancelled
published  → cancelled
cancelled  → (nessuna)
```

## 4. Persistenza

Identica a user-service: memory (dict), json (file atomico), sqlite (tabella `events`). `STORAGE_BACKEND` e `DATA_DIR` da `shared/config.py`.

## 5. Strategia di test

- **Unit**: business.py testato con `responses` per mockare chiamate a user-service. Repository testato su tutti e 3 i backend.
- **Contratto**: almeno 1 test per endpoint con `assert_matches_contract`.
- **Integration propri**: avvia realmente user-service + event-service; testa 1 caso positivo, 1 organizer inesistente (422), 1 user-service spento (503).
