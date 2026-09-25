# requirements.md — feedback-service

Base path: `/api/v1/feedbacks` · Porta: `5004` · Tipo: opzionale

Valutazioni degli eventi da parte degli iscritti. Chiama **registration-service** ed **event-service**.

---

## Campi della risorsa Feedback

| Campo | Tipo | Obbligatorio | Vincoli |
|---|---|---|---|
| `id` | uuid | — | read-only |
| `user_id` | uuid | Sì | deve avere iscrizione `confirmed` all'evento |
| `event_id` | uuid | Sì | — |
| `rating` | integer | Sì | 1–5 |
| `comment` | string | No | max 500 caratteri |
| `created_at` | datetime | — | read-only |
| `updated_at` | datetime | — | read-only |

---

## REQ-FBK-01 — Creazione feedback

**Acceptance criteria**
1. WHEN POST `/api/v1/feedbacks` with valid fields → 201 con `Location`
2. IF JSON malformato → 400
3. IF campo obbligatorio mancante o `rating` fuori 1–5 → 422 `VALIDATION_ERROR`

---

## REQ-FBK-B01 — Iscrizione confirmed richiesta

**User story:** As the platform, I want only registered attendees to leave feedback.

**Acceptance criteria**
1. WHEN creating feedback THE feedback-service SHALL call `GET /api/v1/registrations?user_id=&event_id=&status=confirmed` on registration-service
2. IF no confirmed registration exists for `(user_id, event_id)` THEN respond 422 with `NOT_REGISTERED`

---

## REQ-FBK-B02 — Un solo feedback per (user_id, event_id)

**Acceptance criteria**
1. IF a feedback already exists for `(user_id, event_id)` THEN respond 409 with `FEEDBACK_ALREADY_EXISTS`

---

## REQ-FBK-B03 — Summary

**User story:** As an organizer, I want a summary of ratings for my event.

**Acceptance criteria**
1. WHEN GET `/api/v1/feedbacks/summary?event_id=` THE feedback-service SHALL return `{event_id, count, average_rating}` (media a 2 decimali, `null` se count = 0)
2. IF the event does not exist (event-service returns 404) → 404 `NOT_FOUND`

---

## REQ-FBK-B04 — Dipendenza non raggiungibile

**Acceptance criteria**
1. WHEN registration-service or event-service is unreachable → 503 `DEPENDENCY_UNAVAILABLE`

---

## REQ-FBK-02 — Lettura, lista, aggiornamento, cancellazione

**Acceptance criteria**
1. GET `/api/v1/feedbacks/{id}` → 200 / 404
2. GET `/api/v1/feedbacks?event_id=&user_id=` → 200 paginated
3. PATCH `/api/v1/feedbacks/{id}` (`rating`, `comment`) → 200 / 404 / 422
4. DELETE `/api/v1/feedbacks/{id}` → 204 / 404

---

## REQ-FBK-03 — Health check

**Acceptance criteria**
1. GET `/health` → 200 `{"status": "ok", "service": "feedback-service"}`
