# Dokumentacja techniczna

## Architektura

Projekt Django (`config`) z aplikacjami:

| Aplikacja | Odpowiedzialność |
|---|---|
| `core` | dashboard, ustawienia, middleware |
| `accounts` | użytkownik, role, logowanie, zarządzanie kontami |
| `devices` | rejestr urządzeń, odłączanie, skan nmap, monitoring |
| `logs` | model logów, API ingest, lista/szczegóły z filtrami |
| `alerts` | reguły bezpieczeństwa, alerty, notatki, historia |
| `notifications` | powiadomienia w aplikacji + licznik |
| `audit` | rejestr działań użytkowników (tylko do odczytu) |
| `demo_data` | seeder danych demonstracyjnych |

### Wdrożenie (Docker Compose)

- `web` – gunicorn + whitenoise, port 8000,
- `worker` – `run_monitor` (ping urządzeń w tle),
- `db` – PostgreSQL 16, wolumen `postgres_data`,
- sieć bridge; na Windows: Docker Desktop + WSL2,
- konfiguracja wyłącznie przez `.env` (RNF-14).

## Modele (skrót)

- `User` – role admin/operator, blokada przez `is_active`,
- `Device` – typy, dwa statusy (monitoring / dostęp do sieci),
  ważność, `monitoring_enabled`, `disconnect_blocked`,
- `MonitoringResult` – wynik ping z czasem odpowiedzi,
- `AdminCommand` – historia poleceń odłącz/przyłącz z uzasadnieniem,
- `NetworkScan` – historia skanów nmap,
- `LogEntry` – czas, źródło, poziom, typ, użytkownik, urządzenie, JSON,
- `SecurityRule` / `Alert` / `AlertNote` / `AlertHistory`,
- `Notification`, `ActivityLog`.

## Bezpieczeństwo

- hasła hashowane mechanizmem Django; CSRF na wszystkich formularzach;
- uprawnienia sprawdzane po stronie serwera (dekorator `admin_required`, 403);
- API logów chronione kluczem `X-API-Key` (RNF-15);
- `LoginRateLimitMiddleware` – 5 nieudanych prób na konto / 10 na IP w oknie 5 min (RNF-12);
- `SessionTimeoutMiddleware` – wylogowanie po nieaktywności (konfigurowalne);
- walidacja podsieci skanu nmap po stronie serwera (max /24).

## Monitoring i analiza

- worker pinguje urządzenia z `monitoring_enabled=True`;
- po N kolejnych niepowodzeniach urządzenia **krytycznego** powstaje alert
  (reguła `device_unavailable`);
- `analyze_log_entry` uruchamia aktywne reguły po zapisie logu;
- ochrona przed duplikatami: ten sam reguła+urządzenie w oknie 5 minut.

## Audyt

Sygnały Django zapisują do `ActivityLog`: logowania, nieudane logowania,
wylogowania, CRUD urządzeń, polecenia sieciowe, zmiany statusów alertów,
operacje na kontach. Użytkownik i IP pobierane z żądania przez middleware
`CurrentRequestMiddleware` (thread-local). Historia bez możliwości edycji.

## Wydajność

- indeksy na polach filtrowanych i sortowanych,
- paginacja 50/stronę (logi, alerty, audit),
- filtrowanie po stronie serwera,
- seeder używa `bulk_create`; test na 100 000 logów – listy < 1 s.

## Kopie zapasowe

`backup.sh` / `restore.sh` + `docs/BACKUP_RESTORE.md`.
