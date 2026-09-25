# product.md — Dominio TechConf

## Cos'è TechConf

TechConf è la piattaforma di una società che organizza conferenze tecniche (cloud, AI, security). Gestisce l'intero ciclo: anagrafica delle persone coinvolte, creazione e pubblicazione degli eventi, iscrizioni dei partecipanti, e — nella parte opzionale — raccolta di feedback e invio di notifiche.

La piattaforma è composta da microservizi indipendenti che comunicano tra loro via HTTP, mai tramite accesso diretto ai dati di un altro servizio.

## Chi la usa

- **Attendee (partecipante):** si registra come utente, si iscrive agli eventi pubblicati, eventualmente lascia un feedback dopo aver partecipato.
- **Speaker:** utente con ruolo speciale, non ha permessi differenti nei servizi obbligatori ma è distinto nel dominio.
- **Organizer (organizzatore):** utente con ruolo `organizer`; solo un utente con questo ruolo può essere associato come organizzatore di un evento (`organizer_id`).

## I concetti chiave del dominio

- **Utente:** persona registrata sulla piattaforma, con un ruolo (`attendee`, `speaker`, `organizer`) che determina cosa può fare nel dominio (es. solo un `organizer` può creare eventi).
- **Evento:** una conferenza con un ciclo di vita (`draft → published → cancelled`), una capienza massima e un prezzo. Solo un evento `published` accetta iscrizioni.
- **Iscrizione (registration):** il legame tra un utente e un evento pubblicato. Ha uno stato (`confirmed`/`cancelled`) e un importo copiato dal prezzo dell'evento al momento dell'iscrizione. Non può superare la capienza dell'evento, né duplicarsi per lo stesso utente/evento.
- **Feedback** *(opzionale)*: valutazione (1–5) che solo chi ha un'iscrizione confermata a un evento può lasciare, una sola volta.
- **Notifica** *(opzionale)*: comunicazione verso un utente (email/sms/push), anche inviata in massa (`broadcast`) a tutti gli iscritti confermati a un evento.

## Perché l'architettura è a microservizi

Ogni concetto del dominio (utenti, eventi, iscrizioni, feedback, notifiche) è di competenza di un servizio distinto, con la propria persistenza. I servizi collaborano solo via HTTP e solo quando un dato di dominio richiede una verifica esterna (es. registration-service verifica che l'utente e l'evento esistano davvero, chiamando rispettivamente user-service ed event-service). Questo riflette una scelta realistica: ogni servizio potrebbe, in un contesto reale, essere sviluppato e rilasciato da un team diverso.