# Instrukcja użytkownika

## Logowanie

Wejdź na adres panelu, podaj login i hasło otrzymane od administratora.
Po 30 minutach nieaktywności sesja wygasa. Motyw (jasny/ciemny/systemowy)
przełączysz selectem przy nazwie użytkownika – wybór jest zapamiętywany.

## Dashboard

Liczby urządzeń i alertów, wykres zdarzeń z 7 dni, ostatnie zdarzenia
i alerty. Kliknięcie alertu prowadzi do jego szczegółów.

## Urządzenia

- **Lista** – wyszukiwarka i filtry u góry; kliknięcie nazwy = szczegóły.
- **Dodaj/Edytuj** – formularz; pola z `*` są wymagane.
- **Usuń** – wymaga potwierdzenia.
- **Odłącz od sieci** – tylko administrator; wymaga uzasadnienia;
  operacja trafia do historii poleceń.
- **Skanuj sieć** – tylko administrator; podaj podsieć (np. 192.168.1.0/24),
  zaznacz wykryte hosty i dodaj je do rejestru.
- **Szczegóły** – dane, statusy, historia monitoringu, ostatnie logi,
  powiązane alerty, historia poleceń.

## Logi

Lista z wyszukiwaniem, filtrami (poziom, źródło, typ, urządzenie, daty)
i paginacją. Kliknięcie treści = szczegóły z pełnymi danymi JSON.

## Alerty

- filtry: status, poziom, urządzenie, reguła, daty;
- szczegóły: opis, powiązane logi, zmiana statusu, przypisanie osoby,
  notatki i pełna historia obsługi.

## Powiadomienia

Czerwony licznik w menu = nieprzeczytane. „Zobacz alert” przechodzi do
alertu, „Oznacz jako przeczytane” zdejmuje licznik.

## Konta (tylko administrator)

Dodawanie, edycja danych i roli, blokowanie/odblokowanie, reset hasła
(przycisk „Hasło”). Zablokowane konto nie może się zalogować.

## Zmiana własnego hasła

„Zmień hasło” przy nazwie użytkownika; wymagane obecne hasło.
