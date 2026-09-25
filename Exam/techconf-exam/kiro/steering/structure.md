# structure.md — Organizzazione del codice TechConf

Questo documento risponde alle domande guida del §7 della traccia e vincola Kiro nella generazione di ogni task: ogni servizio deve rispettare questa struttura.

---

## Repository e confini dei servizi

**Decisione:** repository unico (il fork di `techconf-exam`), ma con una netta separazione a livello di cartelle: ogni microservizio vive isolato sotto `services/<nome-servizio>/`.

```
techconf-exam/
├── contracts/              # NON modificabile (fornito)
├── tests/integration/      # NON modificabile (fornito)
├── .kiro/
│   ├── steering/
│   │   ├── product.md
│   │   ├── tech.md
│   │   ├── structure.md
│   │   └── platform-standards.md
│   └── specs/
│       ├── user-service/
│       │   ├── requirements.md
│       │   ├── design.md
│       │   └── tasks.md
│       ├── event-service/
│       ├── registration-service/
│       ├── feedback-service/        # se implementato
│       └── notification-service/    # se implementato
├── services/
│   ├── user-service/
│   ├── event-service/
│   ├── registration-service/
│   ├── feedback-service/            # se implementato
│   └── notification-service/        # se implementato
├── shared/
├── data/                    # git-ignored
├── services.yaml
├── BUGS.md
└── README.md
```

**Perché repo unico invece di uno per servizio:** la traccia stessa impone un fork unico per partecipante (§6.6, tag `v1.0.0` su un solo `main`), quindi il repo multiplo non è un'opzione qui. Il vantaggio pratico del repo unico è che la suite di collaudo, che legge `services.yaml` nella root, trova tutto con un solo `git clone`. Aggiungere i due servizi opzionali significa solo aggiungere due cartelle sotto `services/` e due righe in `services.yaml`, senza toccare nient'altro.

**Confine tra servizi — reso evidente ed enforced così:**
- Ogni servizio ha la propria sottocartella sotto `services/`, con il proprio `requirements.txt`, i propri test, il proprio entrypoint (`run.py`). Aprire quella cartella isolata equivale a lavorare "come se" fosse un repo a sé.
- **Regola vincolante:** nessun servizio importa codice da `services/<altro-servizio>/`. L'unico canale di comunicazione tra servizi è HTTP (`requests`), mai import Python diretto.
- Enforcement: la regola è strutturale (cartelle separate) più una verifica manuale/hook — nessun import che attraversi `services/` se non tramite gli helper HTTP di `shared/`. Un CI/hook opzionale può fare `grep` sugli import per bloccare eventuali violazioni.

---

## Codice condiviso e duplicazione

**Decisione:** una piccola libreria condivisa in `shared/`, ma limitata a ciò che è **standard di piattaforma vincolante e identico per tutti** (§4). Tutto ciò che è **logica di dominio** resta locale al singolo servizio.

| Cosa | Condiviso o duplicato | Motivo |
|---|---|---|
| Formato errori JSON (`{"error": {...}}`) | Condiviso — `shared/errors.py` | Standard di piattaforma identico ovunque; duplicarlo rischia disallineamenti tra servizi |
| Paginazione (`page`, `page_size`, risposta `{items, page, page_size, total}`) | Condiviso — `shared/pagination.py` | Stessa logica ovunque, zero valore nel duplicare |
| Client HTTP verso altri servizi (timeout 2s, mapping 404→422 `REFERENCE_NOT_FOUND`, timeout/5xx→503 `DEPENDENCY_UNAVAILABLE`) | Condiviso — `shared/http_client.py` | Comportamento vincolante e identico per tutte le chiamate inter-servizio; un fix va applicato in un solo punto |
| Lettura configurazione (`PORT`, `*_SERVICE_URL`, `STORAGE_BACKEND`, `DATA_DIR`) | Condiviso — `shared/config.py` | Evita che ogni servizio legga le env var a modo suo |
| Validazione dei campi specifici di un servizio (es. regole su `email`, `capacity`, transizioni di stato) | **Duplicato/locale** in ogni servizio | È logica di dominio specifica di quel servizio: non ha senso astrarla, e tenerla locale mantiene il servizio autosufficiente |
| Repository/persistenza (memory/json/sqlite) | **Locale** in ogni servizio, ma con la **stessa interfaccia astratta** ripetuta in ciascuno (vedi sotto) | Lo schema dati differisce per servizio |

**Trade-off accettato:** `shared/` introduce un accoppiamento tra i servizi — se un giorno un servizio fosse dato in mano a un altro team, dovrebbe comunque importare/vendorizzare `shared/`. Per l'ambito di questo esame è un compromesso accettabile perché `shared/` contiene solo regole di piattaforma stabili (§4), non logica di business che cambia spesso. In un contesto reale multi-team, `shared/` verrebbe pubblicato come pacchetto Python versionato a parte, per disaccoppiare i deploy dei singoli servizi.

---

## Struttura interna di un servizio

Ogni servizio sotto `services/<nome>/` segue lo stesso schema a strati, per separare le responsabilità:

```
services/user-service/
├── app/
│   ├── __init__.py       # app factory Flask
│   ├── routes.py         # solo gestione HTTP: parsing richiesta, chiamata alla business logic, formattazione risposta
│   ├── business.py       # regole REQ-*-B* (es. REQ-USR-B01 email univoca)
│   ├── repository.py     # persistenza: interfaccia comune + implementazioni memory/json/sqlite
│   ├── clients.py        # chiamate HTTP verso altri servizi (usa shared/http_client.py), isolate qui
│   └── models.py         # schema/serializzazione della risorsa
├── tests/
│   ├── unit/              # business logic e repository, HTTP mockato con `responses`
│   └── integration/       # i TUOI test §6.3: avviano davvero i servizi coinvolti
├── requirements.txt
└── run.py                 # entrypoint, legge PORT da shared/config.py
```

- **Le regole `REQ-*-B*` vivono in `business.py`**, mai in `routes.py`: `routes.py` non deve contenere logica di business, solo traduzione HTTP ↔ funzioni Python.
- **Memory/json/sqlite non tocca la business logic:** `repository.py` espone un'interfaccia comune (es. `get(id)`, `list(filters)`, `create(data)`, `update(id, data)`, `delete(id)`) con tre implementazioni intercambiabili, selezionate a runtime da `STORAGE_BACKEND`. `business.py` dipende solo dall'interfaccia, mai da una implementazione specifica.
- **Le chiamate agli altri servizi sono isolate in `clients.py`**, così nei test unitari si può mockare facilmente con `responses` senza toccare la business logic.

---

## Configurazione e avvio

- `PORT`, `*_SERVICE_URL`, `STORAGE_BACKEND`, `DATA_DIR` si leggono in **un solo punto**: `shared/config.py`, importato da ogni servizio all'avvio. Nessun servizio legge `os.environ` direttamente altrove.
- Comando di avvio in `services.yaml`: identico per pattern in tutti i servizi, es. `python run.py`, con `cwd` puntato alla cartella del servizio.
- Dipendenze Python: **un `requirements.txt` per servizio**, non un unico ambiente condiviso. Se due servizi richiedessero versioni diverse della stessa libreria, l'isolamento per-servizio evita conflitti; il costo è installare le dipendenze più volte, accettabile per 3-5 servizi Flask leggeri.

---

## Test

- Test unitari e i test di integrazione "propri" (§6.3) vivono **dentro la cartella del servizio** (`services/<nome>/tests/unit` e `.../tests/integration`), non in una cartella centrale: restano vicini al codice che testano, coerente con l'isolamento per servizio.
- I test di integrazione propri avviano i servizi reali coinvolti tramite una fixture pytest che li lancia come sottoprocesso su una porta libera, e li spegne a fine sessione (teardown della fixture).
- Comando singolo per un servizio: `pytest services/<nome>/tests --cov=app` (lanciato con `cwd` nella cartella del servizio, o con path esplicito dalla root).
- Comando per l'intera piattaforma: uno script/Makefile alla root (`make test`) che itera su tutte le cartelle in `services/` ed esegue il comando sopra per ciascuna.

---

## Spec e tracciabilità

- **Una spec Kiro per servizio** (non per funzionalità o per singola regola): coerente con l'architettura a microservizi e con `.kiro/specs/<servizio>/` richiesto dalla traccia.
- Da `REQ-REG-B05` al codice: l'ID compare (a) nell'acceptance criteria in `requirements.md`, (b) nel commento/docstring della funzione in `business.py` che lo implementa, (c) nel marker `@pytest.mark.req("REQ-REG-B05")` del test corrispondente. Una `grep -r "REQ-REG-B05"` sul repo porta a tutti e tre i punti in pochi secondi.
- **`structure.md`** contiene le regole valide per **tutto il repository** (questo file). **`design.md`** di ciascun servizio contiene le decisioni **specifiche di quel servizio** (es. come registration-service gestisce la lettura di `event.price`, quali endpoint interni espone `clients.py`).

---

## Dati e Git

- I file di dati `json`/`sqlite` vanno in `data/<nome-servizio>/` alla root del repo (path da `DATA_DIR`), **esclusi da git** (`.gitignore` contiene `data/`).
- I commit seguono la sequenza spec → task → codice, con prefissi convenzionali: `spec(<svc>): requirements|design|tasks`, poi `feat(<svc>): <task> [T-0N]` uno per task, `test(<svc>): ...` se un test viene aggiunto separatamente, `fix(<svc>): ... (closes #N)` per i bug, `docs(...)`, `chore(...)`. Questo rende leggibile, per ogni servizio, l'intera storia dalla specifica al codice.