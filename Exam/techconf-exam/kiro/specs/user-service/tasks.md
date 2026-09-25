# tasks.md — user-service

Ogni task va eseguito da Kiro con "Start task", uno alla volta, con un commit al termine: `feat(user-service): <task> [T-0N]`.

---

- [ ] **T-01 — Scaffolding del servizio**
  Crea la struttura di cartelle `services/user-service/` come da `design.md` (app/, tests/unit/, tests/integration/, requirements.txt, run.py). App factory Flask minima con blueprint vuoto e `GET /health`.
  _Requirements: REQ-USR-06_

- [ ] **T-02 — Modello User e config**
  Implementa `models.py` (dataclass/dict schema User, generazione `id` UUID v4, `created_at`/`updated_at` ISO 8601 UTC) e collega `shared/config.py` per leggere `PORT`, `STORAGE_BACKEND`, `DATA_DIR`.
  _Requirements: REQ-USR-01, REQ-USR-07_

- [ ] **T-03 — Repository: interfaccia + backend memory**
  Implementa l'interfaccia `UserRepository` e `MemoryUserRepository`. Unit test del repository (create/get/list/update/delete/find_by_email) sul backend memory.
  _Requirements: REQ-USR-07_

- [ ] **T-04 — Repository: backend json**
  Implementa `JsonUserRepository` (lettura/scrittura file in `DATA_DIR`, scrittura atomica). Unit test dello stesso set di operazioni usando `tmp_path`.
  _Requirements: REQ-USR-07_

- [ ] **T-05 — Repository: backend sqlite**
  Implementa `SqliteUserRepository` con `sqlite3` standard library (creazione tabella se non esiste). Unit test dello stesso set di operazioni usando `tmp_path`.
  _Requirements: REQ-USR-07_

- [ ] **T-06 — Business logic: creazione utente**
  Implementa in `business.py` la validazione dei campi (`first_name`, `last_name`, `email`, `company`, `role`) e la creazione, inclusa normalizzazione email in minuscolo e default `role=attendee`. Unit test per casi validi e invalidi.
  _Requirements: REQ-USR-01, REQ-USR-B02_

- [ ] **T-07 — Business logic: unicità email**
  Implementa il controllo di unicità case-insensitive su create e update, sollevando `EmailAlreadyExistsError` quando violato. Unit test con email duplicate in casing diverso.
  _Requirements: REQ-USR-B01_

- [ ] **T-08 — Endpoint POST /api/v1/users**
  Implementa la route, collega validazione e persistenza, gestisce 400 (JSON malformato), 422, 409, 201 con header `Location`. Test di contratto per l'endpoint.
  _Requirements: REQ-USR-01, REQ-USR-B01, REQ-USR-B02_

- [ ] **T-09 — Endpoint GET /api/v1/users/{id} e GET /api/v1/users**
  Implementa lettura singola (200/404) e lista paginata con filtri `role`/`email` (200/422). Test di contratto per entrambi.
  _Requirements: REQ-USR-02, REQ-USR-B03_

- [ ] **T-10 — Endpoint PUT/PATCH /api/v1/users/{id}**
  Implementa aggiornamento completo e parziale, `updated_at` aggiornato, gestione 404/422/409, campi read-only ignorati se inviati dal client. Test di contratto.
  _Requirements: REQ-USR-03_

- [ ] **T-11 — Endpoint DELETE /api/v1/users/{id}**
  Implementa cancellazione (204/404) e verifica che una GET successiva risponda 404. Test di contratto.
  _Requirements: REQ-USR-04_

- [ ] **T-12 — Gestione 405 e JSON malformato**
  Verifica/completa la gestione dei metodi non previsti (405) e del body non-JSON su POST/PUT/PATCH (400) a livello di error handler Flask globale.
  _Requirements: REQ-USR-05_

- [ ] **T-13 — Test di integrazione propri**
  Fixture pytest che avvia realmente user-service su una porta libera; test end-to-end del ciclo CRUD completo via HTTP reale (create → get → list → update → delete → get 404).
  _Requirements: REQ-USR-01, REQ-USR-02, REQ-USR-03, REQ-USR-04_

- [ ] **T-14 — Coverage e rifinitura**
  Esegui `pytest --cov=app`, porta la coverage ≥80%, aggiungi eventuali test unit mancanti per rami non coperti (in particolare error handling).
  _Requirements: tutti i precedenti_

- [ ] **T-15 — README del servizio**
  Documenta in `services/user-service/README.md` (o nella sezione dedicata del README root) come avviare il servizio, variabili d'ambiente e comando dei test.
  _Requirements: —_