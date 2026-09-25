# requirements.md — user-service

Base path: `/api/v1/users` · Porta: `5001` · Tipo: obbligatorio

Questo servizio gestisce l'anagrafica degli utenti della piattaforma (partecipanti, speaker, organizzatori). Non dipende da nessun altro servizio.

---

## Campi della risorsa User

| Campo | Tipo | Obbligatorio | Vincoli |
|---|---|---|---|
| `id` | uuid | — | generato dal server, read-only |
| `first_name` | string | Sì | 1–50 caratteri |
| `last_name` | string | Sì | 1–50 caratteri |
| `email` | string | Sì | formato email valido, univoca case-insensitive, salvata in minuscolo |
| `company` | string | No | max 100 caratteri |
| `role` | enum | No | `attendee` \| `speaker` \| `organizer`, default `attendee` |
| `created_at` | datetime | — | generato dal server, read-only |
| `updated_at` | datetime | — | generato dal server, read-only |

---

## REQ-USR-01 — Creazione utente

**User story:** As a client application, I want to register a new user, so that they can use the TechConf platform.

**Acceptance criteria**
1. WHEN a POST request to `/api/v1/users` contains a valid `first_name`, `last_name` and `email` THE user-service SHALL create the user, assign a server-generated UUID v4 as `id`, set `created_at` and `updated_at` to the current UTC time, and respond 201 with a `Location` header pointing to the new resource
2. IF `role` is not provided in the request THEN THE user-service SHALL default it to `attendee`
3. IF the request body is not valid JSON THEN THE user-service SHALL respond 400
4. IF `first_name`, `last_name` or `email` is missing, or any field violates its length/format constraint, or `role` is not one of the allowed values THEN THE user-service SHALL respond 422 with error code `VALIDATION_ERROR`
5. IF the client submits an `id` in the request body THEN THE user-service SHALL ignore it and generate its own

---

## REQ-USR-B01 — Email univoca

**User story:** As the platform, I want to prevent duplicate accounts, so that each person maps to a single user record.

**Acceptance criteria**
1. WHEN a POST or PUT/PATCH request would result in an `email` that already exists for another user, compared case-insensitively, THE user-service SHALL respond 409 with error code `EMAIL_ALREADY_EXISTS`
2. WHEN comparing emails for uniqueness THE user-service SHALL treat `Jane@Example.com` and `jane@example.com` as the same email

---

## REQ-USR-B02 — Normalizzazione email

**User story:** As the platform, I want emails stored consistently, so that lookups and uniqueness checks are reliable.

**Acceptance criteria**
1. WHEN a user is created or its `email` is updated THE user-service SHALL store the `email` value in lowercase, regardless of the casing submitted by the client

---

## REQ-USR-02 — Lettura di un utente

**User story:** As a client application, I want to fetch a single user by id, so that I can display or verify their details.

**Acceptance criteria**
1. WHEN a GET request is made to `/api/v1/users/{id}` and a user with that `id` exists THE user-service SHALL respond 200 with the full user representation
2. IF no user with the given `id` exists THEN THE user-service SHALL respond 404 with error code `NOT_FOUND`

---

## REQ-USR-B03 — Lista utenti con filtri e paginazione

**User story:** As a client application, I want to list and filter users, so that I can find the ones I need without fetching everyone.

**Acceptance criteria**
1. WHEN a GET request is made to `/api/v1/users` THE user-service SHALL respond 200 with a paginated envelope `{"items": [...], "page": ..., "page_size": ..., "total": ...}`
2. WHEN the query string includes `page` and/or `page_size` THE user-service SHALL apply them, with `page_size` capped at 100
3. WHEN the query string includes `role` THE user-service SHALL return only users whose `role` matches exactly
4. WHEN the query string includes `email` THE user-service SHALL return only users whose `email` matches (case-insensitive)
5. IF `page`, `page_size` or `role` in the query string is invalid (e.g. non-numeric page, `role` outside the allowed enum) THEN THE user-service SHALL respond 422 with error code `VALIDATION_ERROR`

---

## REQ-USR-03 — Aggiornamento utente (PUT/PATCH)

**User story:** As a client application, I want to update a user's details, so that their record stays accurate.

**Acceptance criteria**
1. WHEN a PUT request to `/api/v1/users/{id}` contains a complete, valid representation of an existing user THE user-service SHALL replace the user's fields, update `updated_at` to the current UTC time, and respond 200 with the updated resource
2. WHEN a PATCH request to `/api/v1/users/{id}` contains one or more valid fields THE user-service SHALL update only those fields, update `updated_at`, and respond 200 with the updated resource
3. IF no user with the given `id` exists THEN THE user-service SHALL respond 404 with error code `NOT_FOUND`
4. IF the submitted fields violate any validation constraint THEN THE user-service SHALL respond 422 with error code `VALIDATION_ERROR`
5. IF the update would set `email` to a value already used by another user (case-insensitive) THEN THE user-service SHALL respond 409 with error code `EMAIL_ALREADY_EXISTS`
6. IF the client submits `id`, `created_at` or `updated_at` in the body THEN THE user-service SHALL ignore those fields

---

## REQ-USR-04 — Cancellazione utente

**User story:** As a client application, I want to delete a user, so that their record is removed from the platform.

**Acceptance criteria**
1. WHEN a DELETE request is made to `/api/v1/users/{id}` and a user with that `id` exists THE user-service SHALL delete the user and respond 204 with an empty body
2. IF no user with the given `id` exists THEN THE user-service SHALL respond 404 with error code `NOT_FOUND`
3. WHEN a GET request is made to `/api/v1/users/{id}` after that user has been deleted THE user-service SHALL respond 404 with error code `NOT_FOUND`

---

## REQ-USR-05 — Metodi non previsti

**User story:** As the platform, I want unsupported HTTP methods to be rejected clearly, so that clients get an unambiguous error instead of unexpected behavior.

**Acceptance criteria**
1. IF a request uses an HTTP method not defined for a given path (e.g. PATCH on `/api/v1/users` without an id) THEN THE user-service SHALL respond 405

---

## REQ-USR-06 — Health check

**User story:** As the operations tooling, I want to check whether user-service is alive, so that I can monitor and orchestrate it.

**Acceptance criteria**
1. WHEN a GET request is made to `/api/v1/../health` — i.e. `GET /health` — THE user-service SHALL respond 200 with `{"status": "ok", "service": "user-service"}`

---

## REQ-USR-07 — Persistenza multi-backend

**User story:** As the developer, I want user-service to work with any of the three storage backends, so that it satisfies the platform's persistence standard without code changes to business rules.

**Acceptance criteria**
1. WHEN `STORAGE_BACKEND` is `memory` THE user-service SHALL store users in memory, with no data surviving a restart
2. WHEN `STORAGE_BACKEND` is `json` THE user-service SHALL persist users to a JSON file inside `DATA_DIR`
3. WHEN `STORAGE_BACKEND` is `sqlite` THE user-service SHALL persist users to a SQLite database inside `DATA_DIR`, using only the standard library `sqlite3`
4. WHEN the storage backend changes THE user-service SHALL NOT require any change to the business-rule logic (REQ-USR-B01, REQ-USR-B02, REQ-USR-B03)

---

## Copertura contratto OpenAPI

Ogni endpoint sopra deve rispettare esattamente lo schema definito in `contracts/openapi/user-service.yaml` (nomi campi, tipi, enum, codici di stato). Ogni test unitario per un endpoint valida la risposta con `contracts/validator.py::assert_matches_contract`.