# TechConf — Piattaforma microservizi per conferenze tecniche

Cinque microservizi Flask (3 obbligatori + 2 opzionali) per la gestione di utenti, eventi, iscrizioni, feedback e notifiche.

---

## Struttura del repository

```
techconf-exam/
├── contracts/openapi/       # Contratti OpenAPI (non modificabili)
├── tests/integration/       # Suite di collaudo docente (non modificabile)
├── services/
│   ├── user-service/        # porta 5001
│   ├── event-service/       # porta 5002
│   ├── registration-service/ # porta 5003
│   ├── feedback-service/    # porta 5004
│   └── notification-service/ # porta 5005
├── shared/                  # Utilities condivise (errors, config, http_client, pagination)
├── kiro/
│   ├── steering/            # Steering files Kiro
│   └── specs/               # Spec per servizio (requirements, design, tasks)
├── services.yaml            # Manifest per la suite di collaudo
├── BUGS.md                  # Registro bug
└── README.md                # Questo file
```

---

## Prerequisiti

- Python 3.12+
- pip

Installa le dipendenze di tutti i servizi:

```bash
pip install flask requests pytest pytest-cov responses PyYAML jsonschema
```

Oppure per ogni servizio singolarmente:

```bash
pip install -r services/user-service/requirements.txt
```

---

## Avvio manuale dei servizi

Ogni servizio si avvia con `python -m app` dalla sua cartella, leggendo la porta da `PORT`:

```bash
# user-service (porta di default: 5001)
cd services/user-service
PORT=5001 PYTHONPATH=../../shared python -m app

# event-service
cd services/event-service
PORT=5002 USER_SERVICE_URL=http://localhost:5001 PYTHONPATH=../../shared python -m app

# registration-service
cd services/registration-service
PORT=5003 USER_SERVICE_URL=http://localhost:5001 EVENT_SERVICE_URL=http://localhost:5002 PYTHONPATH=../../shared python -m app

# feedback-service
cd services/feedback-service
PORT=5004 REGISTRATION_SERVICE_URL=http://localhost:5003 EVENT_SERVICE_URL=http://localhost:5002 PYTHONPATH=../../shared python -m app

# notification-service
cd services/notification-service
PORT=5005 USER_SERVICE_URL=http://localhost:5001 REGISTRATION_SERVICE_URL=http://localhost:5003 PYTHONPATH=../../shared python -m app
```

---

## Variabili d'ambiente

| Variabile | Descrizione | Default |
|---|---|---|
| `PORT` | Porta di ascolto del servizio | dipende dal servizio |
| `STORAGE_BACKEND` | `memory` \| `json` \| `sqlite` | `memory` |
| `DATA_DIR` | Cartella per i file json/sqlite | `./data` |
| `USER_SERVICE_URL` | URL del user-service | `http://localhost:5001` |
| `EVENT_SERVICE_URL` | URL dell'event-service | `http://localhost:5002` |
| `REGISTRATION_SERVICE_URL` | URL del registration-service | `http://localhost:5003` |
| `FEEDBACK_SERVICE_URL` | URL del feedback-service | `http://localhost:5004` |
| `NOTIFICATION_SERVICE_URL` | URL del notification-service | `http://localhost:5005` |

---

## Test

### Test unitari di un singolo servizio

```bash
# Dalla cartella del servizio
cd services/user-service
PYTHONPATH=../../shared pytest tests/unit --cov=app -v

# Oppure dalla root con path esplicito
PYTHONPATH=shared pytest services/user-service/tests/unit --cov=services/user-service/app -v
```

### Test unitari di tutti i servizi

```bash
# Su Windows PowerShell
foreach ($svc in @("user-service","event-service","registration-service","feedback-service","notification-service")) {
    Write-Host "=== $svc ==="
    $env:PYTHONPATH = "shared"
    pytest "services/$svc/tests/unit" --cov="services/$svc/app" -q
}
```

### Test di integrazione propri

```bash
PYTHONPATH=shared pytest services/event-service/tests/integration -v
PYTHONPATH=shared pytest services/registration-service/tests/integration -v
```

### Suite di collaudo docente (obbligatoria)

```bash
pip install -r tests/integration/requirements.txt

# Tutti i servizi dichiarati in services.yaml
pytest tests/integration -v

# Solo i 3 obbligatori
pytest tests/integration -m mandatory -v

# Un singolo servizio
pytest tests/integration -k registration -v
```

L'output del collaudo è salvato in `collaudo.txt`:

```bash
pytest tests/integration -m mandatory -v > collaudo.txt 2>&1
```

---

## Backend di persistenza

Cambio backend senza modificare il codice applicativo:

```bash
# JSON
STORAGE_BACKEND=json DATA_DIR=./data PORT=5001 PYTHONPATH=../../shared python -m app

# SQLite
STORAGE_BACKEND=sqlite DATA_DIR=./data PORT=5001 PYTHONPATH=../../shared python -m app
```

I file di dati sono in `data/<nome-servizio>/` e sono esclusi da git.

---

## Health check

Ogni servizio espone `GET /health`:

```bash
curl http://localhost:5001/health
# {"status": "ok", "service": "user-service"}
```

---

## Architettura

```
user-service    (5001)  ← chiamato da event, registration, notification
event-service   (5002)  ← chiama user; chiamato da registration, feedback
registration-service (5003) ← chiama user, event; chiamato da feedback, notification
feedback-service (5004) ← chiama registration, event
notification-service (5005) ← chiama user, registration
```

Comunicazione solo via HTTP. Nessun import diretto tra servizi.
