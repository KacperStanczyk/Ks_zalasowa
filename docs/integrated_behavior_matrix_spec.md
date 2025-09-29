# Integrated Specification – Behavior Matrix with ISO 26262 and Event Types

**Data:** Monday, September 29, 2025, 12:23 PM

## 1. Purpose & Scope
### Purpose
Celem projektu jest stworzenie Behavior Matrix – centralnego kontraktu danych wspierającego automatyzację testów w obszarze Functional Safety (FuSa). Artefakt ten stanowi jedno źródło prawdy (single source of truth) dla oczekiwanego zachowania systemu, zastępując rozproszone i ad-hoc definicje testów.

Behavior Matrix umożliwia deterministyczne, audytowalne generowanie kandydatów przypadków testowych (TC) zgodnie z ISO 26262-6:2018, Clause 11, a także zapewnia pełną ścieżkę traceability:

```
safety goal → event type → TC_ID → wynik testu
```

### Users
- **Behavior Authors (FuSa/Validation Engineers):** definiują zachowania w macierzy (fault × component × context → expected behavior, monitor, timing, priority).
- **Test Developers (Automation Engineers):** implementują i rozszerzają moduły testowe oraz pluginy monitorów, które weryfikują konkretne funkcje lub sygnały w środowiskach testowych.
- **Reviewers/Auditors:** korzystają z wizualizacji i raportów (traceability matrix, coverage heatmap, ISO compliance view) do przeglądu spójności danych i oceny zgodności.

### Scope
- Definicja modelu danych i formatów wejściowych (YAML/CSV, JSON Schema).
- Algorytm deterministycznej generacji kandydatów TC (transition + recovery), z unikalnymi TC_ID.
- Reguły walidacji i spójności (schema, unikalność, ISO compliance, mapping event_type).
- Modularna architektura:
  - Behavior Matrix (dane)
  - Generator (algorytm)
  - Monitors (pluginy walidacyjne)
  - Visualizer (grafy przejść, heatmapy pokrycia, pivoty czasowe)
- Integracja z narzędziami zewnętrznymi (RQM/Jira, ECU-TEST, Databricks).
- Obsługa standardowych interfejsów wymiany danych (import/export CSV, YAML, JSON).
- Użycie katalogu eventów wysokopoziomowych (1–15) jako ustandaryzowanego szablonu zachowań systemowych.

### Out of Scope
- Realne wykonanie testów na ECU/HIL/pojazdach oraz obsługa logów runtime.
- Warstwa runtime (I/O sprzętowe, harmonogram w czasie rzeczywistym).
- Interpretacja semantyki monitorów – prototyp traktuje je jako identyfikatory, a logika jest przeniesiona do pluginów.

### Key Constraints
- **Deterministic reproducibility:** identyczny seed → identyczny zestaw TC.
- **Auditability:** dane, generacja i wyniki muszą być śledzalne i zgodne z ISO 26262.
- **Extensibility:** możliwość dodawania nowych event types, monitorów i pluginów bez refaktoryzacji core.
- **Parallelization:** gotowość do pracy w CI/CD pipeline i kolaboracji wielu zespołów.
- **Traceability:** jawne powiązanie Safety Goals ↔ Event Types ↔ TC_ID ↔ wynik testu.

## 2. Data Model
### 2.1. Klucz unikalności
Każdy wiersz macierzy musi być unikalny względem klucza:

```
(fault_id, component_id, context.start_state, context.warm_from_fault_id, event_type, phase)
```

- `event_type = null` nadal wchodzi do klucza.
- Pole `phase` dodane do klucza rozróżnia definicje `transition` vs `recovery`.
- Dodatkowo rekomendowane pole: `event_family` (`FRR | THRESHOLD | MODE | DIAG | PINCH`).

### 2.2. Pola wymagane (MUST)
| Pole | Typ | Opis |
| --- | --- | --- |
| `fault_id` | string | Identyfikator błędu (np. FI.*). |
| `component_id` | string | Id komponentu (np. COMP.*). |
| `asil` | "A" \| "B" \| "C" \| "D" \| "QM" | Poziom ASIL; "QM" dla elementów poza FuSa. |
| `context.start_state` | string | Stan początkowy (z `components.yaml`). |
| `phase` | "transition" \| "recovery" \| "both" | Faza generowanego testu. |
| `expect.end_state` | string | Oczekiwany stan końcowy (z `components.yaml`). |
| `monitors[]` | array | Min. 1 monitor. |
| `priority` | number [0.0–1.0] | Priorytet selekcji. |
| `enabled` | boolean | Flaga aktywacji wiersza. |

### 2.3. Pola opcjonalne (SHOULD/MAY)
- `event_type`: integer \| null – powiązanie z checklistą 1–15.
- `context.warm_from_fault_id`: string \| null – poprzedni fault.
- `iso.environments[]`: odwzorowanie środowisk z tab. 13 ISO.
- `iso.methods.test[]`: odwzorowanie metod z tab. 14 ISO.
- `trace.req_ids[]`: identyfikatory wymagań.
- `version`: string (SemVer).
- `row_id` (UUID), `owner`, `created_at`, `updated_at`, `change_note` – pola audytowe.
- `fault.kind`, `fault.profile`, `gate.*`, `transition.*`, `diag.*`, `obstacle.*` – rozszerzenia dla 5 rodzin eventów.

### 2.4. MonitorSpec
| Pole | Typ | Opis |
| --- | --- | --- |
| `id` | string | Id monitora (`MON.*`). |
| `plugin` | string | Powiązany plugin. |
| `params` | object | Parametry specyficzne dla pluginu. |

## 3. Validation & Rules
### 3.1. Źródła Prawdy
- `components.yaml` – komponenty i stany.
- `monitors.yaml` – rejestr monitorów.
- `event_map.yaml` – mapa `event_type` (1–15) → `event_family`.

### 3.2. Reguły Walidacji
1. JSON Schema.
2. Unikalność klucza.
3. Zgodność z rejestrami.
4. ISO compliance: dla ASIL C/D wymagane `iso.environments` i `iso.methods.test`.
5. Coverage: wszystkie typy eventów 1–15 muszą wystąpić ≥1 raz (`enabled=true`).
6. Raport coverage musi rozróżniać `disabled` vs `not present`.

#### Kody błędów
| Exit code | Meaning | Example |
| --- | --- | --- |
| 0 | OK | Poprawna walidacja |
| 2 | Schema error | Brak monitors |
| 3 | Duplicate key | Duplikat (`fault_id`, `component_id`, …) |
| 4 | ISO compliance error | Brak `iso.environments` dla ASIL C |

## 4. ISO 26262-6 Compliance Mapping
| ISO Clause | Behavior Matrix Implementation |
| --- | --- |
| 11.1 Objective | `trace.req_ids` + `expect.*` → dowód spełnienia safety requirements |
| 11.3 Inputs | Plik YAML/CSV + `trace.req_ids` |
| 11.4.1 Environments | `iso.environments[]` (HIL, ECU_NET, VEHICLE) |
| 11.4.2 Methods | `iso.methods.test[]` zgodne z tab. 14 |
| 11.4.3 TC derivation | `iso.methods.derivation[]` + `event_type` |
| 11.4.4 Evaluation | `expect.*`, `monitors[]`, `timing`. |
| 11.5 Work Products | Behavior Matrix = refined SVS |

## 5. High-Level Event Families (Plugins)
### F1. Fault → Reaction → Recovery (FRR)
- Źródło: fault.
- Przebieg: fault → transition → recovery.
- Recovery zależny od polityki (auto/reset/power_cycle).

### F2. Threshold / Gating
- Źródło: warunek progowy.
- TC: poniżej, na progu, powyżej.
- Recovery po zejściu poniżej progu.

### F3. Mode / State Transition
- Źródło: zmiana trybu/stanu.
- TC: wszystkie przejścia `from_state` → `to_state`.
- Recovery = powrót do NORMAL/inna polityka.

### F4. Diagnostics / Service
- Źródło: sesja diagnostyczna.
- TC: `enter_session`, `exit_session`.
- Walidacja: skutki np. DTC cleared.

### F5. Pinch / Obstacle Trigger
- Źródło: trigger bezpieczeństwa.
- Reakcja: immediate inhibit.
- Recovery opcjonalny (po usunięciu przeszkody).

#### Porównanie rodzin
| Rodzina | Źródło | Typowy przebieg | Kluczowe parametry | Recovery |
| --- | --- | --- | --- | --- |
| F1 FRR | Fault | Fault → Reaction → Recovery | `fault.kind`, `timing` | Tak |
| F2 Threshold | Próg sygnału | Below/At/Above threshold → Reaction | `gate.signal_id`, `gate.value` | Tak |
| F3 Mode | Zmiana trybu | Transition (NORMAL→DEGRADED) | `transition.from/to`, `trigger` | Tak |
| F4 Diagnostics | Sesja serwisowa | Enter → Reaction → Exit | `diag.session`, `command` | Tak |
| F5 Pinch | Trigger bezpieczeństwa | Obstacle → Inhibit | `obstacle.direction`, `reaction_time` | Opcjonalnie |

✅ Dokument jest spójny, zawiera wszystkie wcześniejsze treści, a struktura jest klarowna: Purpose → Data Model → Validation → ISO Compliance → Event Families.

Czy chcesz, żebym przygotował teraz pełne JSON Schema v2 (obsługujące wszystkie 5 rodzin eventów) jako załącznik do tego dokumentu?

## 6. Wymagania dotyczące wizualizacji
### 6.1. Cel i Użytkownicy
Moduł Visualizer ma na celu transformację surowych danych z Behavior Matrix w interaktywne, intuicyjne widoki graficzne. Umożliwia to szybką weryfikację poprawności logiki, analizę pokrycia testowego oraz wsparcie procesów audytowych.

Główni użytkownicy wizualizacji:
- **Behavior Authors (Testerzy):** Używają wizualizacji do bieżącej weryfikacji zdefiniowanych zachowań, aby upewnić się, że logika przejść między stanami jest zgodna z ich intencją.
- **Reviewers/Auditors (Recenzenci, Audytorzy):** Wykorzystują widoki wysokopoziomowe (mapy pokrycia, macierze traceability) do oceny kompletności, spójności i zgodności z wymaganiami oraz normą ISO 26262.
- **Project/FuSa Managers:** Monitorują postęp prac i identyfikują "białe plamy" w pokryciu testowym na poziomie całego projektu.

### 6.2. Kluczowe Widoki Wizualizacji
Visualizer musi dostarczać co najmniej cztery kluczowe, interaktywne widoki:

#### 6.2.1. Graf Przejść Stanów (State Transition Graph)
Jest to podstawowe narzędzie dla testera, które dynamicznie generuje graf na podstawie danych z matrycy.

- **Opis:** Wizualna reprezentacja cyklu życia komponentu. Węzły grafu reprezentują stany (`context.start_state`, `expect.end_state`), a krawędzie reprezentują przejścia (fazy transition i recovery) wyzwalane przez określone błędy (`fault_id`) lub zdarzenia.
- **Wymagania funkcjonalne:**
  - **Filtrowanie:** Możliwość wygenerowania grafu dla wybranego `component_id` lub grupy komponentów.
  - **Interaktywność:** Po najechaniu na krawędź (przejście) powinny wyświetlić się kluczowe informacje: `fault_id`, `event_type`, lista monitorów (`monitors[]`).
  - **Kodowanie kolorami:** Różne kolory dla fazy transition (np. czerwony) i recovery (np. zielony), aby łatwo odróżnić cykl błędu.
  - **Czytelność:** Automatyczne układanie grafu w celu minimalizacji przecięć i poprawy przejrzystości.

#### 6.2.2. Mapa Pokrycia (Coverage Heatmap)
Narzędzie do szybkiej identyfikacji luk w pokryciu testowym.

- **Opis:** Tabela (heatmapa), w której wiersze odpowiadają identyfikatorom komponentów (`component_id`), a kolumny – standardowym typom zdarzeń (`event_type` 1–15). Komórka na przecięciu wskazuje status pokrycia.
- **Wymagania funkcjonalne:**
  - **Statusy kodowane kolorami:**
    - Zielony (Pokryty): Istnieje co najmniej jedna aktywna (`enabled: true`) definicja dla danej pary (komponent, event).
    - Żółty (Wyłączony): Wszystkie definicje dla danej pary są nieaktywne (`enabled: false`).
    - Czerwony (Brakujący): Brak jakiejkolwiek definicji.
  - **Drill-down:** Kliknięcie komórki powinno filtrować i wyświetlać wszystkie wiersze z Behavior Matrix, które jej dotyczą.
  - **Statystyki:** Wyświetlanie procentowego pokrycia dla każdego komponentu oraz dla całego projektu.

#### 6.2.3. Macierz Identyfikowalności (Traceability Matrix)
Widok kluczowy dla audytów i dowodzenia zgodności z wymaganiami (ISO 26262).

- **Opis:** Tabela łącząca wymagania wyższego rzędu z konkretnymi artefaktami testowymi.
- **Struktura:**
  - **Wiersze:** Identyfikatory wymagań (`trace.req_ids[]`).
  - **Kolumny:** Wygenerowane unikalne identyfikatory przypadków testowych (`TC_ID`).
  - **Zawartość:** Oznaczenie na przecięciu wskazuje, że dany `TC_ID` weryfikuje dane wymaganie (`req_id`).
- **Wymagania funkcjonalne:**
  - **Dwukierunkowość:** Możliwość filtrowania zarówno po `req_id` (aby zobaczyć wszystkie TC), jak i po `TC_ID` (aby zobaczyć, jakie wymagania pokrywa).
  - **Eksport:** Możliwość wygenerowania raportu w formacie CSV lub HTML.

#### 6.2.4. Widok Zgodności z ISO 26262 (ISO Compliance View)
Dashboard analityczny dla menedżerów FuSa i audytorów.

- **Opis:** Zestaw wykresów i wskaźników podsumowujących, jak definicje w matrycy spełniają zalecenia normy ISO 26262-6 (Tabele 13 i 14).
- **Wymagania funkcjonalne:**
  - **Wykres pokrycia metod:** Wykres kołowy lub słupkowy pokazujący, jakie metody testowe (`iso.methods.test[]`) są używane i z jaką częstotliwością, zwłaszcza dla ASIL C/D.
  - **Wykres pokrycia środowisk:** Podobny wykres dla środowisk testowych (`iso.environments[]`).
  - **Filtrowanie po ASIL:** Możliwość wyświetlenia statystyk wyłącznie dla definicji o określonym poziomie ASIL.

### 6.3. Wymagania Niefunkcjonalne
- **Wydajność:** Wizualizacje muszą być generowane w akceptowalnym czasie (< 5 sekund) nawet dla matrycy zawierającej tysiące wierszy.
- **Integracja:** Moduł Visualizer powinien być dostępny jako samodzielna aplikacja webowa lub jako plugin zintegrowany z narzędziami CI/CD (np. Jenkins, GitLab) lub systemami do zarządzania dokumentacją (np. Confluence).
- **Eksport:** Wszystkie widoki (grafy, tabele) muszą być eksportowalne do popularnych formatów (PNG, SVG dla grafiki; CSV, HTML dla tabel) w celu łatwego dołączania do raportów.

✅ Dokument został zaktualizowany o kompleksowe wymagania dotyczące wizualizacji, które bezpośrednio wspierają Twój model pracy, ułatwiając weryfikację i zapewniając przejrzystość na każdym etapie.

## 7. Pytest MVP & Visualization Prototype
A minimal vertical slice is available in `src/behavior_matrix` with executable pytest coverage. The sample YAML under `tests/data/behavior_matrix_sample.yaml` demonstrates two FRR and two MODE behaviors, including disabled entries to exercise coverage logic.

### Key Artifacts
- **Loader (`behavior_matrix.loader`)** – normalizes YAML into strongly-typed rows.
- **Generator (`behavior_matrix.generator`)** – produces deterministic `TC_ID`s and exposes mock monitor plugins.
- **Plugins (`behavior_matrix.plugins.mock_monitors`)** – placeholder implementations returning deterministic pass/fail envelopes for range, state, and timing checks.
- **Visualizer (`behavior_matrix.visualizer`)** – generates in-memory data for state graphs, coverage heatmaps, traceability matrices, and ISO summaries with optional Matplotlib exports.

### Running the MVP
```bash
pip install -r requirements.txt
pytest tests/behavior_matrix/test_generated_cases.py -vv
```
The parametrized tests execute the generated test cases end-to-end, invoking the mock monitors and returning structured `TestResult` payloads for inspection.

### Generating Prototype Visuals
To produce quick-look artefacts, call the helper functions with an output path (Matplotlib optional):
```python
from pathlib import Path
from behavior_matrix import build_state_transition_graph, load_behavior_matrix

matrix = load_behavior_matrix("tests/data/behavior_matrix_sample.yaml")
build_state_transition_graph(matrix["rows"], component_id="COMP.BMS", output_path=Path("artifacts/state_graph.png"))
```
If Matplotlib is unavailable the functions still return structured dictionaries for downstream rendering.
