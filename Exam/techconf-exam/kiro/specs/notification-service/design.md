# design.md — notification-service

Riferimento contratto: `contracts/openapi/notification-service.yaml`

---

## 1. Struttura

```
services/notification-service/
├── app/
│   ├── __init__.py
│   ├── __main__.py
│   ├── routes.py
│   ├── business.py       # REQ-NTF-B01..B04
│   ├── repository.py     # interfaccia + 3 backend
│   ├── clients.py        # get_user(), get_confirmed_registrations()
│   └── models.py
├── tests/unit/
├── requirements.txt
└── pytest.ini
```

## 2. clients.py

- `get_user(user_id)`: `GET USER_SERVICE_URL/api/v1/users/{id}`.
- `get_confirmed_registrations(event_id)`: `GET REGISTRATION_SERVICE_URL/api/v1/registrations?event_id=&status=confirmed&page_size=100`. Restituisce la lista di tutti gli item (gestisce paginazione semplice: usa page_size=100 per il collaudo).

## 3. Broadcast

`POST /api/v1/notifications/broadcast` registrata come route letterale prima di `/{id}` per evitare conflitti.

## 4. sent_at

Valorizzato solo quando `status` passa a `sent`; nelle altre transizioni rimane `null`.
