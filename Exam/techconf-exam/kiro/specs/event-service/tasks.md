# tasks.md — event-service

- [x] **T-01 — Scaffolding + health**
  Struttura cartelle, app factory Flask, `GET /health`.
  _Requirements: REQ-EVT-05_

- [x] **T-02 — Modello Event e config**
  `models.py` (schema, UUID, timestamps), `shared/config.py` per PORT/STORAGE_BACKEND/DATA_DIR.
  _Requirements: REQ-EVT-01, REQ-EVT-06_

- [x] **T-03 — Repository: memory**
  `EventRepository` interfaccia + `MemoryEventRepository`. Unit test CRUD.
  _Requirements: REQ-EVT-06_

- [x] **T-04 — Repository: json e sqlite**
  `JsonEventRepository` e `SqliteEventRepository`. Unit test con `tmp_path`.
  _Requirements: REQ-EVT-06_

- [x] **T-05 — clients.py: get_user**
  `get_user(organizer_id)` che chiama user-service. Unit test mockato con `responses`.
  _Requirements: REQ-EVT-B01, REQ-EVT-B05_

- [x] **T-06 — Business logic: validazioni e CRUD**
  Validazione campi, REQ-EVT-B01/B02/B03/B04/B06, orchestrazione CRUD.
  _Requirements: REQ-EVT-B01..B06_

- [x] **T-07 — Endpoint POST/GET/PUT/PATCH/DELETE**
  Tutte le route con test di contratto.
  _Requirements: REQ-EVT-01..REQ-EVT-04_

- [x] **T-08 — Integration test propri**
  Avvio reale user-service + event-service; casi positivo, 422, 503.
  _Requirements: REQ-EVT-B01, REQ-EVT-B05_

- [x] **T-09 — Coverage ≥ 80%**
  _Requirements: tutti_
