# design.md — registration-service

Riferimento contratto: `contracts/openapi/registration-service.yaml`

---

## 1. Struttura

```
services/registration-service/
├── app/
│   ├── __init__.py
│   ├── __main__.py
│   ├── routes.py
│   ├── business.py       # REQ-REG-B01..B09
│   ├── repository.py     # interfaccia + 3 backend
│   ├── clients.py        # get_user(), get_event()
│   └── models.py
├── tests/unit/
├── tests/integration/
├── requirements.txt
└── pytest.ini
```

## 2. Componenti chiave

- **`clients.py`**: `get_user(user_id)` e `get_event(event_id)`. Usa `shared/http_client.py`. Il 404 di http_client diventa `ReferenceNotFoundError` (422). Il 503 passa direttamente.
- **`business.py`**: verifica sequenziale — prima `user_id` (REQ-REG-B01), poi `event_id` (REQ-REG-B02), poi status=published (REQ-REG-B03), poi duplicato (REQ-REG-B04), poi capienza (REQ-REG-B05). `amount` copiato da `event.price` (REQ-REG-B06). Transizioni (REQ-REG-B07). Stats (REQ-REG-B08).
- **`repository.py`**: interfaccia `RegistrationRepository` + 3 backend. In più, `count_confirmed(event_id)` per il controllo capienza.

## 3. Endpoint speciale: stats

`GET /api/v1/registrations/stats?event_id=` deve essere registrato prima del pattern `/{id}` per evitare che Flask interpreti "stats" come un ID. La route è dichiarata nella blueprint come path letterale.

## 4. PUT 405

Flask risponde 405 automaticamente se il metodo PUT non è registrato per quella route. Lo gestiamo aggiungendo esplicitamente la route con `methods=["PUT"]` che restituisce 405.

## 5. Strategia di test

- **Unit**: `business.py` con `responses` per mockare user-service ed event-service.
- **Integration propri**: avvia user-service + event-service + registration-service; testa caso positivo, utente inesistente (422), evento non published (422), dipendenza spenta (503).
