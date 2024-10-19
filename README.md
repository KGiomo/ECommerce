# Piattaforma di E-commerce

## Introduzione
L’obiettivo del progetto è lo sviluppo di una web application che si interfaccia con un database relazionale. Il progetto è sviluppato in Python, utilizzando le librerie Flask e SQLAlchemy. Il DBMS scelto è PostgreSQL. 
Di seguito sono presenti le specifiche.

## Specifiche
Ho curato il design e l’implementazione di un portale di e-commerce, dove gli utenti possono comprare e vendere i prodotti online. Il sistema include le seguenti funzionalità:
- Gestione degli utenti: Ho implementato funzionalità di autenticazione e autorizzazione degli utenti. Gli utenti possono registrarsi, accedere e gestire i propri profili. Inoltre, sono presenti ruoli utente differenti come acquirenti e venditori, ognuno con il proprio insieme di permessi.
- Gestione dei prodotti: Il database memorizza le informazioni sui prodotti, inclusi nome, descrizione, categoria, prezzo, disponibilità, ecc. I venditori possono aggiungere, modificare ed eliminare i propri prodotti.
- Ricerca e Filtri: Ho implementato una funzionalità di ricerca che permette agli utenti di cercare prodotti basati su parole chiave, categorie e altri attributi. Inoltre, vengono fornite opzioni di filtro per affinare i risultati della ricerca basati su intervallo di prezzo, marca, ecc.
- Carrello: Ho implementare una funzionalità di carrello che permette agli utenti di aggiungere prodotti al proprio carrello, aggiornare le quantità e procedere al pagamento. Il sistema gestisce i livelli di inventario e aggiorna la disponibilità dei prodotti di conseguenza.
- Gestione degli ordini: Ho sviluppato un sistema per gestire gli ordini effettuati dagli utenti. Gli utenti possono visualizzare la loro cronologia degli ordini, monitorare lo stato dei propri ordini e ricevere notifiche sugli aggiornamenti degli ordini. I venditori hanno accesso ai dettagli degli ordini per i prodotti che hanno venduto e posoono aggiornarne lo stato.
- Recensioni e Valutazioni: Gli utenti possono lasciare recensioni e valutazioni per i prodotti che hanno acquistato. Sono presenti le valutazioni medie e vengono fornite opzioni di ordinamento basate sulle valutazioni per aiutare gli utenti a prendere decisioni informate.
