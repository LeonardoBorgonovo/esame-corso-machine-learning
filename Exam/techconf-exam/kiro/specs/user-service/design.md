# design.md — user-service

Riferimento contratto: `contracts/openapi/user-service.yaml`
Riferimento requisiti: `.kiro/specs/user-service/requirements.md`
Riferimento standard di piattaforma: `.kiro/steering/platform-standards.md`

---

## 1. Struttura del servizio

```
services/user-service/
├── app/
│   ├── __init__.py       # app factory Flask, registra blueprint e error handler
│   ├── routes.py         # endpoint HTTP: parsing, chiamata a business.py, formattazione risposta
│   ├── business.py       # regole REQ-USR-B01, REQ-USR-B02, REQ-USR-B03 + orchestrazione CRUD
│   ├── repository.py     # interfaccia Repository + MemoryUserRepository / JsonUserRepository / SqliteUserRepository
│   ├── models.py         # dataclass User, serializzazione a/da dict JSON
│   └── errors.py         # (re-export da shared/errors.py) eccezioni di dominio → status code
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── run.py
```

Nessuna dipendenza da altri servizi: user-service non chiama nessun altro microservizio (vedi tabella architettura, §2 della traccia).

## 2. Componenti e responsabilità

- **`routes.py`** — unico punto che parla HTTP. Non contiene logica di business: valida che il body sia JSON (400 se malformato), estrae i parametri di query, chiama `business.py`, mappa le eccezioni di dominio sui codici di errore standard, serializza la risposta.
- **`business.py`** — contiene le regole `REQ-USR-B01` (unicità email case-insensitive), `REQ-USR-B02` (normalizzazione email in minuscolo), `REQ-USR-B03` (filtri lista). Riceve dati già deserializzati da `routes.py`, non conosce Flask.
- **`repository.py`** — espone un'interfaccia astratta comune:
  ```python
  class UserRepository(Protocol):
      def create(self, user: dict) -> dict: ...
      def get(self, user_id: str) -> dict | None: ...
      def list(self, filters: dict, page: int, page_size: int) -> tuple[list[dict], int]: ...
      def update(self, user_id: str, changes: dict) -> dict | None: ...
      def delete(self, user_id: str) -> bool: ...
      def find_by_email(self, email_lower: str, exclude_id: str | None = None) -> dict | None: ...
  ```
  Tre implementazioni (`memory`, `json`, `sqlite`) selezionate all'avvio in base a `STORAGE_BACKEND` (letto da `shared/config.py`). `business.py` dipende solo da questa interfaccia.
- **`models.py`** — definisce la forma della risorsa User e le funzioni di (de)serializzazione JSON, incluso il calcolo di `id` (UUID v4) e `created_at`/`updated_at` (UTC ISO 8601) alla creazione.

## 3. Gestione della persistenza

- **`memory`**: dizionario Python `{id: user_dict}` in un singleton a livello di modulo/app.
- **`json`**: un file `DATA_DIR/user-service/users.json` contenente una lista di user dict; lettura/scrittura completa del file a ogni operazione (accettabile per i volumi di un esame). Scrittura atomica: scrivi su file temporaneo poi `os.replace`.
- **`sqlite`**: un database `DATA_DIR/user-service/users.db`, tabella `users` con colonne corrispondenti ai campi della risorsa; solo libreria standard `sqlite3`.
- Tutte e tre le implementazioni rispettano la stessa interfaccia `UserRepository`, quindi `business.py` non cambia mai al variare del backend (soddisfa REQ-USR-07).

## 4. Gestione errori

Mapping centralizzato in `errors.py` (eccezioni di dominio → risposta HTTP), condiviso nella forma con `shared/errors.py`:

| Eccezione di dominio | Status | error.code |
|---|---|---|
| `ValidationError` | 422 | `VALIDATION_ERROR` |
| `EmailAlreadyExistsError` | 409 | `EMAIL_ALREADY_EXISTS` |
| `NotFoundError` | 404 | `NOT_FOUND` |
| JSON malformato (catturato in `routes.py`) | 400 | — |
| Metodo non previsto (routing Flask) | 405 | — |

## 5. Strategia di test

- **Unit (`tests/unit/`)**: testano `business.py` e `repository.py` in isolamento. `repository.py` è testato con tutti e tre i backend, usando `tmp_path` di pytest per `json`/`sqlite`. Nessuna chiamata di rete (user-service non ne fa comunque).
- **Contratto**: almeno un test per endpoint che chiama l'app Flask in-process (`app.test_client()`) e valida la risposta con `contracts/validator.py::assert_matches_contract("user-service", method, path, response)`.
- **Integration propri (`tests/integration/`)**: user-service non dipende da altri servizi, quindi qui bastano test end-to-end contro l'app avviata realmente su una porta libera (nessun caso 503/dipendenza da testare per questo servizio — a differenza di event-service e registration-service).
- Ogni test riporta l'ID del requisito coperto, via `@pytest.mark.req("REQ-USR-B01")` o nel nome/docstring.

## 6. Configurazione

Legge da `shared/config.py`: `PORT` (default 5001), `STORAGE_BACKEND` (default `memory`), `DATA_DIR` (default `./data`). Nessuna variabile `*_SERVICE_URL` necessaria per questo servizio.