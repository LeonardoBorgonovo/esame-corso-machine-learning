# design.md — feedback-service

Riferimento contratto: `contracts/openapi/feedback-service.yaml`

---

## 1. Struttura

```
services/feedback-service/
├── app/
│   ├── __init__.py
│   ├── __main__.py
│   ├── routes.py
│   ├── business.py       # REQ-FBK-B01..B04
│   ├── repository.py     # interfaccia + 3 backend
│   ├── clients.py        # check_confirmed_registration(), get_event()
│   └── models.py
├── tests/unit/
├── requirements.txt
└── pytest.ini
```

## 2. clients.py

- `check_confirmed_registration(user_id, event_id)`: chiama `GET REGISTRATION_SERVICE_URL/api/v1/registrations?user_id=&event_id=&status=confirmed`, verifica `items` non vuoto.
- `get_event(event_id)`: chiama `GET EVENT_SERVICE_URL/api/v1/events/{id}`, usato per summary.

## 3. Endpoint summary

`GET /api/v1/feedbacks/summary?event_id=` registrato prima di `/{id}` per evitare conflitti di routing.

## 4. average_rating

Calcolata in business.py: `round(sum(ratings)/len(ratings), 2)` oppure `null` se `count = 0`.
