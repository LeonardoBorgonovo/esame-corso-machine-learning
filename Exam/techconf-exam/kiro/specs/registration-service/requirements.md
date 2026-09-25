# requirements.md — registration-service

Base path: `/api/v1/registrations` · Porta: `5003` · Tipo: obbligatorio

Gestisce le iscrizioni degli utenti agli eventi. Chiama **user-service** ed **event-service**.

---

## Campi della risorsa Registration

| Campo | Tipo | Obbligatorio | Vincoli |
|---|---|---|---|
| `id` | uuid | — | generato dal server, read-only |
| `user_id` | uuid | Sì | deve esistere in user-service |
| `event_id` | uuid | Sì | deve esistere in event-service con `status = published` |
| `amount` | decimal | Read-only | copiato da `event.price` al momento dell'iscrizione, mai dal client |
| `status` | enum | Read-only in POST | `confirmed` \| `cancelled`, alla creazione sempre `confirmed` |
| `created_at` | datetime | — | read-only |
| `updated_at` | datetime | — | read-only |

---

## REQ-REG-01 — Creazione iscrizione

**User story:** As an attendee, I want to register for a published event, so that I can attend it.

**Acceptance criteria**
1. WHEN a POST to `/api/v1/registrations` with valid `user_id` and `event_id` THE registration-service SHALL create it with `status = confirmed`, `amount = event.price`, and respond 201 with `Location`
2. IF the request body is not valid JSON THE registration-service SHALL respond 400
3. IF `user_id` or `event_id` is missing THE registration-service SHALL respond 422 with `VALIDATION_ERROR`
4. IF the client includes `amount` or `status` in the body THE registration-service SHALL ignore them

---

## REQ-REG-B01 — user_id deve esistere

**Acceptance criteria**
1. WHEN `user_id` does not exist in user-service THE registration-service SHALL respond 422 with `REFERENCE_NOT_FOUND`

---

## REQ-REG-B02 — event_id deve esistere

**Acceptance criteria**
1. WHEN `event_id` does not exist in event-service THE registration-service SHALL respond 422 with `REFERENCE_NOT_FOUND`

---

## REQ-REG-B03 — Evento deve essere published

**User story:** As the platform, I want registrations only for published events.

**Acceptance criteria**
1. IF the event exists but has `status != published` THEN THE registration-service SHALL respond 422 with `EVENT_NOT_OPEN`

---

## REQ-REG-B04 — Nessuna doppia iscrizione confirmed

**User story:** As the platform, I want to prevent a user from registering twice for the same event.

**Acceptance criteria**
1. IF a `confirmed` registration already exists for `(user_id, event_id)` THEN THE registration-service SHALL respond 409 with `ALREADY_REGISTERED`

---

## REQ-REG-B05 — Capienza evento

**User story:** As an organizer, I want registrations to stop when the event is full.

**Acceptance criteria**
1. WHEN a registration is requested AND confirmed registrations for the event are fewer than `event.capacity` THE registration-service SHALL create it with `status = confirmed`
2. IF confirmed registrations equal `event.capacity` THEN THE registration-service SHALL respond 409 with `EVENT_FULL`
3. WHEN a confirmed registration is cancelled THE registration-service SHALL free one seat

---

## REQ-REG-B06 — amount = event.price

**Acceptance criteria**
1. WHEN a registration is created THE registration-service SHALL set `amount` equal to `event.price` read from event-service, regardless of any client-submitted value

---

## REQ-REG-B07 — Transizione stato

**User story:** As an attendee, I want to cancel my registration.

**Acceptance criteria**
1. WHEN a PATCH sets `status = cancelled` on a `confirmed` registration THE registration-service SHALL accept it
2. IF a PATCH attempts `cancelled → confirmed` THEN THE registration-service SHALL respond 422 with `INVALID_STATUS_TRANSITION`
3. WHEN a confirmed registration is cancelled THE registration-service SHALL free one slot towards capacity

---

## REQ-REG-B08 — Stats

**User story:** As an organizer, I want to see confirmed registrations and available seats.

**Acceptance criteria**
1. WHEN GET `/api/v1/registrations/stats?event_id=` THE registration-service SHALL return `{event_id, capacity, confirmed, available}`
2. IF the event does not exist (event-service returns 404) THEN THE registration-service SHALL respond 404 with `NOT_FOUND`
3. `available = capacity - confirmed` (never negative)

---

## REQ-REG-B09 — Dipendenza non raggiungibile

**Acceptance criteria**
1. WHEN user-service or event-service is unreachable THE registration-service SHALL respond 503 with `DEPENDENCY_UNAVAILABLE`

---

## REQ-REG-02 — Lettura e lista

**Acceptance criteria**
1. GET `/api/v1/registrations/{id}` → 200 / 404
2. GET `/api/v1/registrations?user_id=&event_id=&status=` → 200 paginated
3. Filtri: `user_id`, `event_id`, `status`

---

## REQ-REG-03 — PUT non consentito

**Acceptance criteria**
1. PUT `/api/v1/registrations/{id}` → 405 `METHOD_NOT_ALLOWED`

---

## REQ-REG-04 — Cancellazione

**Acceptance criteria**
1. DELETE `/api/v1/registrations/{id}` → 204 / 404

---

## REQ-REG-05 — Health check

**Acceptance criteria**
1. GET `/health` → 200 `{"status": "ok", "service": "registration-service"}`
