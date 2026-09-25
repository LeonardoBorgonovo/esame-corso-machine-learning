# BUGS.md — Registro dei bug TechConf

Formato: BUG-ID | Issue | Trovato da | Tipo | Requisito | Causa radice | Test di regressione | Commit

---

## BUG-01

| Campo | Valore |
|---|---|
| **ID** | BUG-01 |
| **Issue** | #1 |
| **Trovato da** | IT-R06 (collaudo manuale) |
| **Tipo** | implementazione |
| **Requisito** | REQ-REG-B05 |
| **Causa radice** | `count_confirmed()` contava anche le iscrizioni con `status = cancelled`, gonfiando il contatore e rifiutando iscrizioni valide dopo una cancellazione. |
| **Test di regressione** | `test_cancel_frees_slot` in `services/registration-service/tests/unit/test_business.py` |
| **Commit** | fix(registration-service): count only confirmed regs for capacity (closes #1) |

**Descrizione:** Quando un utente cancellava un'iscrizione e un altro utente tentava di iscriversi a un evento con capienza 1, riceveva `409 EVENT_FULL` anche se il posto era stato liberato. La query `count_confirmed` includeva erroneamente le iscrizioni `cancelled`.

**Fix applicato:** La query SQL e il loop in-memory ora filtrano `AND status = 'confirmed'` esplicitamente.

---

## BUG-02

| Campo | Valore |
|---|---|
| **ID** | BUG-02 |
| **Issue** | #2 |
| **Trovato da** | IT-E03 (test manuale) |
| **Tipo** | implementazione |
| **Requisito** | REQ-EVT-B02 |
| **Causa radice** | `business.py` di event-service sollevava `ValidationError` generica invece di `ValidationError` con `code = "INVALID_ORGANIZER"`, causando il fallimento della validazione del contratto OpenAPI che si aspettava il codice specifico. |
| **Test di regressione** | `test_create_organizer_wrong_role` in `services/event-service/tests/unit/test_business.py` |
| **Commit** | fix(event-service): use INVALID_ORGANIZER code for wrong role (closes #2) |

**Descrizione:** Creare un evento con `organizer_id` che punta a un utente con `role = attendee` restituiva `422 VALIDATION_ERROR` con `code = "VALIDATION_ERROR"` invece di `"INVALID_ORGANIZER"`, facendo fallire il test IT-E03 nella suite di collaudo.

**Fix applicato:** Introdotta `InvalidOrganizerError` con `code = "INVALID_ORGANIZER"` in `business.py` di event-service; la classe estende `ValidationError` (422) ma sovrascrive il codice.

---

## Note

- Entrambi i bug sono stati corretti in Vibe session su branch `fix/registration-service-1` e `fix/event-service-2`.
- Nessun file in `contracts/` o `tests/integration/` è stato modificato.
