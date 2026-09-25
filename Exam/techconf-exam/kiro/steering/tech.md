# tech.md — Stack tecnico TechConf

## Linguaggio e framework

- **Python 3.12**
- **Flask** per esporre le API REST di ogni servizio
- **requests** per le chiamate HTTP tra servizi

## Testing

- **pytest** come test runner, per unit e integration test
- **pytest-cov** per la coverage (`pytest --cov=app`), soglia minima richiesta: **80%** per servizio
- **responses** per mockare le chiamate HTTP in uscita nei test unitari (mai colpire una rete reale nei test unit)

## Persistenza

- Backend selezionabile a runtime tramite la variabile `STORAGE_BACKEND`:
  - `memory` (default) — dati tenuti in un dizionario/lista in RAM, persi al riavvio
  - `json` — un file JSON per risorsa/servizio dentro `DATA_DIR`
  - `sqlite` — un database SQLite dentro `DATA_DIR`
- **Solo librerie standard**: `json` e `sqlite3` dal Python standard library. Nessun DBMS esterno da installare o configurare (vietato dalla traccia, penalità −5).
- Il cambio di backend è **trasparente alla business logic**: ogni servizio espone un'interfaccia di repository comune (`get`, `list`, `create`, `update`, `delete`) con tre implementazioni intercambiabili; la business logic dipende solo dall'interfaccia, mai dall'implementazione concreta.
- `DATA_DIR` di default è `./data`, escluso da git.

## Comunicazione tra servizi

- Solo HTTP con `requests`, mai import diretto di codice tra servizi.
- URL degli altri servizi **sempre** letti da variabili d'ambiente (`USER_SERVICE_URL`, `EVENT_SERVICE_URL`, `REGISTRATION_SERVICE_URL`), mai hardcoded (vietato dalla traccia, penalità −5). Default `http://localhost:<porta standard del servizio>`.
- Timeout fisso di **2 secondi** su ogni chiamata verso un altro servizio.

## Configurazione

Ogni servizio legge da variabili d'ambiente, in un unico punto (`shared/config.py`):

| Variabile | Scopo | Default |
|---|---|---|
| `PORT` | porta su cui il servizio ascolta | dipende dal servizio (5001–5005) |
| `STORAGE_BACKEND` | `memory` \| `json` \| `sqlite` | `memory` |
| `DATA_DIR` | cartella per i file di persistenza | `./data` |
| `USER_SERVICE_URL`, `EVENT_SERVICE_URL`, `REGISTRATION_SERVICE_URL` | URL dei servizi da cui si dipende | `http://localhost:<porta>` |

## Dipendenze dichiarate per servizio

Ogni servizio ha il proprio `requirements.txt`:

```
flask
requests

# test (opzionalmente in requirements-dev.txt separato)
pytest
pytest-cov
responses
```

## Cosa NON si usa

- Nessun ORM (SQLAlchemy, ecc.) — con solo `sqlite3` standard l'accesso ai dati resta esplicito e leggero.
- Nessun framework di validazione esterno (es. Pydantic, Marshmallow) a meno che non serva davvero: la validazione dei campi può essere scritta a mano nella business logic, mantenendo zero dipendenze extra oltre a `flask` e `requests`.
- Nessun DBMS esterno (Postgres, MySQL, MongoDB, ecc.): esplicitamente vietato dalla traccia.