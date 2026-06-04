# Workspace (uproszczony)

## Układ

| Kolumna | Rola |
|---------|------|
| Lewa | Tickety ze **statusem kolorem** (kolejka → przypisany → w toku → zrobiony / błąd) |
| Środek | Chat + szkic ticketu |
| Prawa | Artefakt ticketu: **URL**, **URI**, akcje |

## Statusy (kolor)

| Status | Znaczenie |
|--------|-----------|
| Szkic (fiolet) | Propozycja — nie kliknięto „Utwórz” |
| Kolejka (szary) | `pending` — czeka |
| Przypisany (niebieski) | `assigned` |
| W toku (żółty, puls) | `running` |
| Zrobiony (zielony) | `completed` |
| Błąd (czerwony) | `failed` |
| Archiwum (ciemny) | Oznaczony w UI jako zarchiwizowany |

## Adresowanie ticketów

- **URL:** `http://localhost:3003/t/{task_id}`
- **URI:** `mullm://ticket/{task_id}` — do scope, logów, integracji z Access Fabric

Pliki: upload w panelu „Pliki · kontekst” — URI pliku (`mullm://localfs/...`) osobno od URI ticketu.

## Wykonanie

- **Utwórz** — ticket w kolejce (bez shell agent nic nie uruchomi).
- **Utwórz + shell** — wymaga `run …` w wiadomości lub pola Shell w formularzu.

## API

- `GET /api/tickets?view=active|archived`
- `GET /api/tickets/{id}`
- `POST /api/tickets/{id}/archive`
- `POST /api/tickets/{id}/link`
