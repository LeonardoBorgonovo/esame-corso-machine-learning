# requirements.md — event-service

Base path: `/api/v1/events` · Porta: `5002` · Tipo: obbligatorio

Gestisce conferenze tecniche con ciclo di vita e capienza. Chiama **user-service** per validare l'organizzatore.

---

## Campi della risorsa Event

| Campo | Tipo | Obbligatorio | Vincoli |
|---|---|---|---|
| `id` | uuid | — | generato dal server, read-only |
| `title` | string | Sì | 3–120 caratteri |
| `description` | string | No | max 2000 caratteri |
| `organizer_id` | uuid | Sì | deve esistere in user-service con `role = organizer` |
| `venue` | string | Sì | max 100 caratteri |
| `city` | string | Sì | max 60 caratteri |
| `start_date` | date | Sì | `YYYY-MM-DD` |
| `end_date` | date | Sì | `YYYY-MM-DD`, ≥ `start_date` |
| `capacity` | integer | Sì | 1–10000 |
| `price` | decimal | Sì | ≥ 0.00 |
| `status` | enum | No | `draft` \| `published` \| `cancelled`, default `draft` |
| `created_at` | datetime | — | generato dal server, read-only |
| `updated_at` | datetime | — | generato dal server, read-only |

---

## REQ-EVT-01 — Creazione evento

**User story:** As an organizer, I want to create a new event, so that I can publish it and accept registrations.

**Acceptance criteria**
1. WHEN a POST request to `/api/v1/events` contains valid required fields THE event-service SHALL create the event with `status = draft`, assign a server-generated UUID, set `created_at` and `updated_at` to current UTC time, and respond 201 with a `Location` header
2. IF `status` is not provided THE event-service SHALL default it to `draft`
3. IF the request body is not valid JSON THE event-service SHALL respond 400
4. IF any required field is missing or violates its constraint THE event-service SHALL respond 422 with `VALIDATION_ERROR`
5. IF the client submits `id`, `created_at` or `updated_at` in the body THE event-service SHALL ignore those fields

---

## REQ-EVT-B01 — Validazione organizer_id

**User story:** As the platform, I want every event to have a valid organizer, so that there is always a responsible contact.

**Acceptance criteria**
1. WHEN an event is created or updated with an `organizer_id` THE event-service SHALL call `GET /api/v1/users/{organizer_id}` on user-service
2. IF user-service responds 404 THEN THE event-service SHALL respond 422 with `REFERENCE_NOT_FOUND`
3. IF the user exists but has `role != organizer` THEN THE event-service SHALL respond 422 with `INVALID_ORGANIZER`

---

## REQ-EVT-B02 — Ruolo organizer

**User story:** As the platform, I want only users with role=organizer to be set as event organizers.

**Acceptance criteria**
1. WHEN the `organizer_id` refers to a user with `role` different from `organizer` THE event-service SHALL respond 422 with error code `INVALID_ORGANIZER`

---

## REQ-EVT-B03 — Coerenza date

**User story:** As an organizer, I want the system to reject impossible date ranges.

**Acceptance criteria**
1. WHEN `end_date` is earlier than `start_date` THE event-service SHALL respond 422 with `VALIDATION_ERROR`
2. WHEN `end_date` equals `start_date` THE event-service SHALL accept the event (single-day event)

---

## REQ-EVT-B04 — Transizioni di stato

**User story:** As an organizer, I want controlled state transitions so that published events cannot go back to draft.

**Acceptance criteria**
1. WHEN a PATCH or PUT sets `status = published` on a `draft` event THE event-service SHALL accept the transition
2. WHEN a PATCH or PUT sets `status = cancelled` on a `draft` or `published` event THE event-service SHALL accept the transition
3. IF a PATCH or PUT attempts `published → draft` THEN THE event-service SHALL respond 422 with `INVALID_STATUS_TRANSITION`
4. IF a PATCH or PUT attempts `cancelled → any` THEN THE event-service SHALL respond 422 with `INVALID_STATUS_TRANSITION`

---

## REQ-EVT-B05 — Dipendenza user-service non raggiungibile

**User story:** As the platform, I want graceful degradation when user-service is down.

**Acceptance criteria**
1. WHEN user-service is unreachable (timeout, connection refused, or 5xx) during organizer validation THE event-service SHALL respond 503 with `DEPENDENCY_UNAVAILABLE`

---

## REQ-EVT-B06 — Filtri lista

**User story:** As a client, I want to filter events by status and city.

**Acceptance criteria**
1. WHEN the query string includes `status` THE event-service SHALL return only events matching that status
2. WHEN the query string includes `city` THE event-service SHALL return only events matching that city (case-insensitive)
3. WHEN `page` and `page_size` are provided THE event-service SHALL apply platform-standard pagination

---

## REQ-EVT-02 — Lettura evento

**Acceptance criteria**
1. WHEN GET `/api/v1/events/{id}` and event exists → 200 with full representation
2. IF no event with that id → 404 `NOT_FOUND`

---

## REQ-EVT-03 — Aggiornamento evento (PUT/PATCH)

**Acceptance criteria**
1. WHEN PUT `/api/v1/events/{id}` with valid complete body → 200, `updated_at` refreshed
2. WHEN PATCH `/api/v1/events/{id}` with partial fields → 200, only those fields updated
3. IF event not found → 404
4. IF validation fails → 422; IF dependency down → 503

---

## REQ-EVT-04 — Cancellazione evento

**Acceptance criteria**
1. WHEN DELETE `/api/v1/events/{id}` and event exists → 204
2. IF not found → 404

---

## REQ-EVT-05 — Health check

**Acceptance criteria**
1. WHEN GET `/health` → 200 `{"status": "ok", "service": "event-service"}`

---

## REQ-EVT-06 — Persistenza multi-backend

**Acceptance criteria**
1. WHEN `STORAGE_BACKEND` is `memory` / `json` / `sqlite` THE event-service SHALL work identically, without changes to business logic
