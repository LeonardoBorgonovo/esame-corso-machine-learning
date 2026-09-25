# platform-standards.md — Standard di piattaforma (vincolanti per tutti i servizi)

Queste regole si applicano identiche a **ogni** microservizio TechConf, obbligatorio o opzionale. Kiro deve rispettarle in ogni task generato, indipendentemente dal servizio.

## Avvio dei servizi

Un file `services.yaml` nella root dichiara, per ogni servizio implementato, la cartella di lavoro (`cwd`) e il comando di avvio (`command`). La suite di collaudo legge questo file e passa a ogni servizio le variabili `PORT` e `*_SERVICE_URL`. Ogni servizio **deve** ascoltare sulla porta indicata da `PORT` (mai una porta hardcoded).

## Base path

`/api/v1/<risorsa>` per tutte le risorse esposte.

## Formato

JSON, campi in `snake_case`.

## Identificativi

`id` è un UUID v4, generato **dal server**. Non è mai accettato in input (un `id` nel body di una POST viene ignorato).

## Timestamp

ISO 8601 UTC, es. `2026-10-15T09:30:00Z`. Ogni risorsa ha `created_at` e `updated_at`, entrambi read-only e gestiti dal server.

## Date e importi

- Date in formato `YYYY-MM-DD`.
- Importi numerici con 2 decimali (es. `149.00`), valuta implicita EUR.

## Paginazione

Query string `?page=1&page_size=20` (`page_size` max 100). Risposta:
```json
{"items": [...], "page": 1, "page_size": 20, "total": 57}
```

## Errori

Formato unico per ogni errore:
```json
{"error": {"code": "UPPER_SNAKE", "message": "...", "details": {...}}}
```

## Status code

| Codice | Uso |
|---|---|
| 201 | creazione (con header `Location`) |
| 200 | lettura/modifica riuscita |
| 204 | cancellazione riuscita |
| 400 | JSON malformato |
| 404 | risorsa non trovata → `NOT_FOUND` |
| 405 | metodo HTTP non previsto sulla risorsa |
| 409 | conflitto (es. duplicato) |
| 422 | `VALIDATION_ERROR` (input non valido) o `REFERENCE_NOT_FOUND` (riferimento a un'altra risorsa inesistente) o violazione di una regola di business specifica |
| 503 | `DEPENDENCY_UNAVAILABLE` (un servizio da cui si dipende non risponde) |

## Chiamate tra servizi

- URL letti **solo** da variabili d'ambiente (`USER_SERVICE_URL`, `EVENT_SERVICE_URL`, `REGISTRATION_SERVICE_URL`), mai scritti nel codice. Default `http://localhost:<porta>`.
- Timeout: **2 secondi** su ogni chiamata.
- Se il servizio chiamato risponde 404 → il chiamante risponde 422 `REFERENCE_NOT_FOUND`.
- Se la chiamata va in timeout, connessione rifiutata, o il servizio chiamato risponde 5xx → il chiamante risponde 503 `DEPENDENCY_UNAVAILABLE`.

## Health check

Ogni servizio espone `GET /health` → `200 {"status": "ok", "service": "<nome-servizio>"}`.

## Persistenza

- Variabile `STORAGE_BACKEND` = `memory` (default) | `json` | `sqlite`.
- Con `json`/`sqlite`, i file vanno in `DATA_DIR` (default `./data`, escluso da git).
- Solo librerie standard (`json`, `sqlite3`): nessun DBMS esterno da installare o configurare.
- Cambiare backend **non deve richiedere modifiche alla logica di business**.

## Dipendenze Python

- Runtime: `flask`, `requests`.
- Test: `pytest`, `pytest-cov`, `responses`.