# requirements.md — notification-service

Base path: `/api/v1/notifications` · Porta: `5005` · Tipo: opzionale

Notifiche agli utenti, anche broadcast verso iscritti confermati. Chiama **user-service** e **registration-service**.

---

## Campi della risorsa Notification

| Campo | Tipo | Obbligatorio | Vincoli |
|---|---|---|---|
| `id` | uuid | — | read-only |
| `user_id` | uuid | Sì | deve esistere in user-service |
| `channel` | enum | Sì | `email` \| `sms` \| `push` |
| `subject` | string | Sì | 1–150 caratteri |
| `body` | string | Sì | 1–5000 caratteri |
| `status` | enum | No | `queued` \| `sent` \| `failed`, default `queued` |
| `sent_at` | datetime | Read-only | valorizzato quando `status → sent` |
| `created_at` | datetime | — | read-only |
| `updated_at` | datetime | — | read-only |

---

## REQ-NTF-01 — Creazione notifica

**Acceptance criteria**
1. WHEN POST `/api/v1/notifications` con campi validi → 201 con `Location`, `status = queued`, `sent_at = null`
2. IF JSON malformato → 400
3. IF campo obbligatorio mancante o constraint violato → 422 `VALIDATION_ERROR`

---

## REQ-NTF-B01 — user_id deve esistere

**Acceptance criteria**
1. IF `user_id` non esiste in user-service → 422 `REFERENCE_NOT_FOUND`

---

## REQ-NTF-B02 — Transizioni di stato

**User story:** As the platform, I want notification status to follow a defined lifecycle.

**Acceptance criteria**
1. WHEN PATCH `status = sent` su `queued` → 200, `sent_at` valorizzato al momento della transizione
2. WHEN PATCH `status = failed` su `queued` → 200
3. IF PATCH tenta `sent → qualsiasi` o `failed → qualsiasi` → 422 `INVALID_STATUS_TRANSITION`
4. IF PATCH tenta `queued → queued` → 422 `INVALID_STATUS_TRANSITION`

---

## REQ-NTF-B03 — Broadcast

**User story:** As an organizer, I want to notify all confirmed registrants at once.

**Acceptance criteria**
1. WHEN POST `/api/v1/notifications/broadcast` con `{event_id, channel, subject, body}` THE notification-service SHALL call `GET /api/v1/registrations?event_id=&status=confirmed` su registration-service
2. THE notification-service SHALL create one notification per `user_id` in the confirmed registrations and respond 201 with `{event_id, created: n}`
3. Le registrazioni `cancelled` sono escluse

---

## REQ-NTF-B04 — Dipendenza non raggiungibile

**Acceptance criteria**
1. IF user-service o registration-service non raggiungibili → 503 `DEPENDENCY_UNAVAILABLE`

---

## REQ-NTF-02 — Lettura, lista, cancellazione

**Acceptance criteria**
1. GET `/api/v1/notifications/{id}` → 200 / 404
2. GET `/api/v1/notifications?user_id=&status=` → 200 paginated
3. DELETE `/api/v1/notifications/{id}` → 204 / 404

---

## REQ-NTF-03 — Health check

**Acceptance criteria**
1. GET `/health` → 200 `{"status": "ok", "service": "notification-service"}`
