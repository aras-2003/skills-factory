# Rozbudowa Arek AI Skills — propozycja i backlog

Data: 5 października 2026. Status: propozycja do wdrożenia, nie deklaracja gotowości ani wykonany release.

> Aktualizacja bazowa: 5 października 2026. Weryfikacja z checkoutu: `origin/main` = `eeae820badaa2c8f9c853a1801df8b08178a077a`, z 54 źródłowymi skills i 17 workflowami. Zainstalowany Lab = 0.32.0, zbudowany ze źródła 8d200a3bd9ee675687de85f11ca7b4f6cbf8ba3f (przodek bieżącego main). Katalog zawiera 70 entrypointów skillowych: 54 skille oraz 16 workflowów udostępnionych przez adapters; metadane: 55 production, 12 candidate, 3 draft. Pełny source → build → pakiet nadal weryfikuje release gate, a zgodność liczby entrypointów sama jej nie dowodzi. Nie traktuj historycznych ustaleń jako automatycznie otwartych defektów. Statusy zadań pozostają w BACKLOG.json.

## Rekomendacja

Najpierw domknąć i usprawnić istniejący system Skill Engineering, następnie sprawdzić go na dwóch użytecznych pionowych flow: zakupach i artykułach. Dopiero ich realne użycie powinno uzasadnić wspólne abstrakcje i następne domeny. Nie budować najpierw rozbudowanego frameworka do produkowania skills.

Największa wartość dla Twojego stylu pracy: mniej czasu na definiowanie zadania i ręczne porządkowanie wyników; mocniejsze decyzje oparte na dowodach; realistyczne trade-offs; gotowy materiał do działania; zachowanie kontroli nad publikacją i wydatkami. To lepsza miara sukcesu niż liczba komponentów.

## Co jest potwierdzone, a co jest założeniem

- Źródło `aras-2003/ai-skills`: weryfikowany `main` = **eeae820badaa2c8f9c853a1801df8b08178a077a**; drzewo zawiera **54 źródłowe SKILL.md i 17 WORKFLOW.md**. Sama obecność źródła nie dowodzi dostępności w runtime.
- Zainstalowany **Lab 0.32.0** został odświeżony ze źródła **8d200a3bd9ee675687de85f11ca7b4f6cbf8ba3f**, przodka bieżącego `main`. Zawiera 70 entrypointów skillowych: 54 skille oraz 16 workflowów wystawionych jako adapters; metadane to 55 production, 12 candidate i 3 draft. To osobny pakiet runtime, a jego readiness nadal wymaga pełnego manifestu/digestu i exact-version receipts.
- Meta w `main`: `skill-test-design` 0.2.0 draft, `skill-evaluation` 0.2.0 draft i `skill-release-review` 0.2.2 draft. Wszystkie trzy są też obecne w Lab 0.32.0 w tych wersjach. To istniejące cele rozwoju, nie nowe skille.
- Obecne domeny implementacji: Career, Commerce, OAF, Meta, Investing. Core, Learning, Tender i Web Design mają już plany w README. Historyczne Product Research/Ecommerce częściowo pokrywają obecne Commerce; nie są osobnym powodem do tworzenia tych samych metod.
- Istnieją: szablon skilla i testów, registry workflowów, walidatory i mutation tests, builders dla kanałów, manifesty/provenance, repozytoryjny eval protocol, katalog i `docs/processes.json`.
- Lokalny audit zawiera automatyczny controller/runner, kolejkę, izolację i osobny evaluator. Nie ustalono jeszcze, które elementy są już zintegrowane upstream; ENG-08 zaczyna od tej kontroli. Historyczny stan kolejki R6 nie jest bieżącym stanem całego pakietu.
- Lab udostępnia 16 z 17 workflowów jako skill entrypoints; brakujący workflow należy rozliczyć po registry i packaging rules. Różnica reprezentacji nie jest sama w sobie błędem provenance. Historyczne rozbieżności README i polityki release należy zamykać na podstawie aktualnych plików i evidence, nie samych snapshotów.
- `report-composer` i `visual-output-design` są candidates: main i zainstalowany Lab mają odpowiednio 0.11.0 i 0.12.0. Propozycja używa istniejącego rozdziału kompozycja/rendering, bez drugiego report engine.
- Masz skill artykułowy w aplikacji — informacja od Ciebie. Nazwa i kontrakt nie zostały potwierdzone w udostępnionym katalogu; WRI-01 jest zależnością, a nie sugestią wymiany tego skilla.
- Projekty Amoura, Tender Pilot, Simple website, Houses, Malaga, Foodie Assistant, Meeting Summarizer, Career i Investing uzasadniają rozważenie tych flow. Same nazwy projektów nie dowodzą częstotliwości użycia ani ich obecnego etapu. Nie analizowano ich prywatnych plików.

## Architektura, którą zachowujemy

`Project/context → intent/runtime → najmniejszy właściwy skill lub workflow → istniejące narzędzia → kontrola dowodów → wynik`

| Warstwa | Co tutaj należy | Przykład rozszerzenia |
|---|---|---|
| Project/context | Profil, cele, prywatne dane, bieżący stan | Purchase preferences, voice samples, learning log |
| Skill | Jedna powtarzalna metoda rozumowania/kontroli | Product evidence review, editorial argument review |
| Workflow | Gałęzie, sekwencja, zależności, gates, stop | Purchase decision, article development |
| Script | Obliczenia, parsowanie, agregacja, walidacja | TCO, scaffolder, dependency/test selection |
| Connector/tool | Wyszukiwanie, dane, rzeczywiste działania | Existing search, browser, Drive, scheduler |
| Report Composer | Struktura skończonego raportu | Profil porównania zakupowego lub technical memo |
| Visual Output Design | Kodowanie i rendering sprawdzonych danych | Macierz lub wykres, tylko gdy pomaga |
| Eval/release | Obserwowane zachowanie i tożsamość wersji | Independent receipts, candidate review |

Zasady rozszerzeń:

1. **Reuse przed build.** Native narzędzie rozwiązuje wykonanie, skill dodaje tylko metodę, której brakuje. Nowa nazwa nie jest dowodem nowej odpowiedzialności.
2. **Wąskie granice.** Consumer kupuje do własnego użytku; Commerce ocenia biznes. Software decision dotyczy systemu; OAF architecture-review dotyczy organizacji. Article critique dotyczy argumentu; evidence review wiarygodności claims.
3. **Bez globalnego Life OS i mega-routera.** Domena `consumer` ma konkretny decision object. Codzienne zastosowania zaczynają od flow i kontekstu, zamiast worka przypadkowych skills.
4. **Core po udowodnionym re-use.** Plan Core już istnieje. Rozbudować początkowo trzy metody, dopiero po pilotach. Nie tworzyć naraz całego zestawu ośmiu ogólnych kontrolerów. `decision-brief` można realizować profilem composer, `quality-gate` w istniejących kontrolach, `red-team-review` jako reference zanim ma niezależny recurring use case.
5. **Progressive disclosure.** Opis skilla routuje, body zawiera metodę, reference zawiera szczegóły kategorii. Nie ładować całej biblioteki ani pełnego profilu do każdego pytania.
6. **Obliczenia i integralność w kodzie.** Nie przenosić deterministycznej arytmetyki do instrukcji modelu.
7. **Zależności jawne.** Rejestrować kanały i required/optional dependencies; brak capability skutkuje zawężeniem albo zatrzymaniem właściwej gałęzi. Nie udawać wywołania brakującego writera/specjalisty.
8. **Użyteczny fallback.** Dla nowych flow optional presentation nie blokuje analizy. Gdy istniejący kontrakt wymaga konkretnego renderera, brak renderera nadal ma uczciwy status blocked; zmiana tego kontraktu wymaga odrębnego review.
9. **Stan domenowy ma właściciela.** Investment OS store pozostaje inwestycyjny. Zakupy/artykuły na początek korzystają z private context; nowy persistence dopiero przy realnej potrzebie historii i synchronizacji.
10. **Zgody wynikają z bieżącego zlecenia.** Przygotowanie rekomendacji/tekstu nie wykonuje zakupu ani publikacji. Dawne zgody z konkretnego audytu nie są częścią portable skilla.

## System tworzenia skills: docelowy flow

`Powtarzalna potrzeba → reuse-or-build → skill-specification + wstępne eval cases → skill-authoring z istniejącego template → skill-validation → skill-test-design → isolated execution + independent skill-evaluation → poprawka najmniejszego komponentu → real-use pilot → skill-release-review → autoryzowana promocja → regresje i utrzymanie`

Nie każdy etap musi być osobną sesją ani ręcznym przekazaniem. Jeden controller może przygotować artefakty i uruchomić dozwolone etapy; nadal nie może podać rubryk wykonawcy ani sam zadeklarować runtime PASS. Independent evaluator ma osobny kontekst, nie tylko etykietę roli w tej samej rozmowie.

Przyspieszenie bierze się z: dobrego kontraktu od początku, testów przed obserwacją wyniku, małego scaffoldera, automatycznego zbierania dowodów, wyboru dotkniętych testów, krótkich PR i re-use. Nie z pomijania kontroli ani automatycznej promocji. Nie wymaga webowej platformy, custom DB ani nowego agent frameworka.

Proponowana macierz zmian: DOCS → statyczna kontrola/freshness; ROUTING → negatives i routing neighbors; BEHAVIOR → zmieniony kontrakt + affected workflows; RESOURCE → direct helper tests + dependents; NEW → cały właściwy lifecycle. Builder/registry/shared-contract change wymaga szerszych kontroli integralności. Cosmetic edits nie potrzebują pełnego model eval.

Gate kończący pierwszą falę: jedna reprezentatywna zmiana existing skill przechodzi proces bez ręcznego kopiowania wejść/wyników, z prawidłowym evidence receipt i minimalnym handoff. Nowe Consumer/Writing można specyfikować równolegle; dopiero ich promocja potrzebuje właściwych gates. Nie trzeba naprawić całej biblioteki przed pierwszym pilotem.

## Proponowane flow i granice

### 1. Zakup produktu — najwyższy priorytet użytkowy

**Wejście:** „Potrzebuję monitora do pracy, laptop z USB-C, do 2500 zł” albo „Porównaj te trzy odkurzacze”. Potrzeba i budżet/constraints; brak krytycznej informacji to jedno ukierunkowane pytanie, bez formularza do prostego porównania.

**Flow:** krótki brief → 3–5 modeli → odrzucenie niespełniających must-have → `product-evidence-review` → `product-fit-comparison` → `purchase-offer-review` → rekomendacja. Dla supplied shortlist pomijamy discovery. Dla znanego modelu i pytania „gdzie kupić?” wystarczy offer review.

**Output:** najlepszy wybór i dlaczego, najmocniejsza alternatywa, macierz istotnych różnic, ograniczenia, konkretne oferty z datą, co zmieni rekomendację. Możliwe wyniki: kupić, zbadać jedną niewiadomą, poczekać, zachować obecny produkt. Search kończy się, gdy istnieje opcja spełniająca constraints, a dalsze informacje nie zmieniają decyzji; braku dowodu nie maskować.

**Dlaczego warto:** regularny research oszczędzający czas i realne pieniądze. **Boundary:** brak biznesowego CAC, MOQ i go-to-market. **Ryzyka:** SKU/revision mismatch, affiliate bias, stare ceny, marketing zamiast testów, pozorna precyzja score. TCO ma jednostki, horyzont i known inputs; brak danych nie daje fałszywej dokładności.

### 2. Artykuł — rozszerzenie istniejącego skilla

**Wejście:** temat/teza, odbiorca, kanał; opcjonalnie własny draft i source pack. Voice samples jako private context.

**Flow:** brief → teza i reader value → tylko potrzebny research → argument outline → istniejący writer → `editorial-argument-review` → article claim check → poprawa. Własny tekst do redakcji zaczyna od review, nie od nowego researchu.

**Output:** jeden gotowy tekst, źródła do material claims, niewielka lista unresolved facts tylko gdy blokują. Adaptacje LinkedIn/newsletter/site są późniejszą gałęzią, nie obowiązkowym content bundle.

**Dlaczego warto:** wzmacnia Twój analityczny, konkretny styl; nie wymienia sprawnego writera. **Ryzyka:** płynna pustka, unsupported causal claims, fikcyjne doświadczenia, zbyt ogólny tone, publikacja prywatnych case. Jeśli istniejący skill robi już argument/evidence review, nowe specialists nie powstają — integrujemy jego kontrakt.

### 3. Decyzja technologiczna / vendor

**Flow:** wymagania z repo/context → buy/build/defer → `technical-option-review` → trial/evidence → TCO/operational risk → krótki ADR/memo. `structured-comparison` po jego sprawdzeniu w drugim use case. Security/legal bez danych ma gaps, nie clearance.

**Dlaczego warto:** pasuje do Staff Engineer/Solution Architect i AI-enabled products. **Boundary:** nie zastępuje OAF. **Output:** wybór, strongest alternative, coupling/data ownership, koszt operacji, exit/reversibility, warunek zmiany decyzji. Nie rekomendować vendor wyłącznie na feature table.

### 4. Spotkanie → decyzje i działania

**Flow:** transcript/notes → `meeting-decision-extraction` → decisions/actions/open questions → opcjonalny memo lub istniejący tracker. Najpierw oddzielać „proponujemy” od „postanawiamy”.

**Dlaczego warto:** masz taki kontekst i zawodowo potrzebujesz wiarygodnych ustaleń. **Boundary:** nie zakłada dostępu do nagrania, nie przypisuje zgody, nie wysyła wiadomości. Owner/deadline bez evidence pozostają unknown.

### 5. AI use case → mały pilot

**Flow:** problem i baseline → `ai-use-case-review` → prostsza alternatywa → dane i failure cost → eval task → pilot boundaries → ewentualny automation brief.

**Dlaczego warto:** wspiera Twoje prototypy i ogranicza agent-first overengineering. **Boundary:** workflow ocenia i projektuje, native tooling implementuje. Jeśli problem jest organizacyjny, kieruje do odpowiedniego existing OAF specialist.

### 6. Tender — istniejący plan, mały wycinek

**Flow:** RFP → `rfp-extraction` → `eligibility-check` → `capability-evidence-match` → `go-no-go`. Po przejściu kwalifikacji dopiero rozszerzenia delivery/commercial risk i traceability.

**Dlaczego warto:** pasuje do Tender Pilot. **Boundary:** nie realizować od razu całych 11 zaplanowanych metod; deterministic parsing/calculation do kodu. Kwalifikacja bez dowodu nie staje się zgodnością.

### 7. Learning Session — aktualny Learning OS

**Flow:** cel → minimum theory → `practice-generator` → wykonanie użytkownika → `competence-check` → najmniejszy next step. Diagnose/explain początkowo w workflow. `retention-review` tylko przy potrzebie.

**Dlaczego warto:** przenosi obecny sposób uczenia do powtarzalnego działania. **Boundary:** quick question nie uruchamia lekcji; exposure nie daje mastery. Zbyt wiele pedagogicznych kontrolerów zwiększy koszt bez capability gain.

### 8. Web quality — review zamiast nowego buildera

**Flow:** brief/approved design + rendered page → `design-critique` → `visual-regression-review` → judgment accessibility review → najmniejsze poprawki. Reuse Figma/Sites/browser/CI.

**Dlaczego warto:** Twoje web properties wymagają jakości kompozycji i realnego renderu. **Boundary:** nie drugi website builder ani własny zestaw checkerów, które już wykonuje CI.

### 9. Podróże / dom / usługi / jedzenie — kolejka discovery

- **Trip decision:** shortlist → aktualne koszty → `itinerary-feasibility` → plan z buffers. Jedna powtarzalna metoda logistyczna, pozostałe etapy reużywają Consumer/Core.
- **Property shortlist:** must-have → oferty → dojazdy i known costs → shortlist → pytania na viewing i due diligence. Brak legal/technical clearance; wartość high, ale wymaga więcej danych i kontroli.
- **Local services:** porównywalny scope ofert → koszt/termin → evidence → wybór i pytania. Reviews nie są gwarancją jakości.
- **Meal plan:** preferencje i pantry → realistyczne posiłki → deterministic shopping list. Bez Nutrition/Health OS.
- **Subscriptions:** known payments/usage → value overlap → keep/downgrade/cancel candidates. Nie potrzebuje Investment store.
- **Document to action:** supplied dokument → obowiązek/termin/source location → checklist/draft. Nie wysyła automatycznie.

Te pomysły mają status DISCOVERY, bo kontekst projektów nie dowodzi nawyku. Zaczynać od jednego rzeczywistego zastosowania; jeśli metoda nie powtarza się, pozostawić jako project flow/template.

## Kolejność realizacji i granice WIP

| Fala | Co wykonujemy | Warunek zakończenia |
|---|---|---|
| 0 — reconcile | ENG-01/02, WRI-01, EXI-01 | Aktualny stan i polityka; znamy writera i bieżące high blockers |
| 1 — minimum engineering | ENG-03/04/06/08; następnie ENG-05; mały ENG-07 | Jeden pełny proces z dowodami bez ręcznego kopiowania |
| 2 — dwa pionowe pilots | CON-01…06 i WRI-02…05; maks. dwa flow naraz | Każdy daje wartość w realnych użyciach; negatives nie psują sąsiadów |
| 3 — reuse i utrwalenie | CORE-01…03, ENG-09…12, EXI-04 | Wspólne metody mają dowód re-use, a affected tests obniżają koszt |
| 4 — następna potrzeba | Jedno z Technical/Meeting/AI/Tender/Learning/Web/Career | Wybór na podstawie aktualnej pracy; nie cała fala jednocześnie |
| 5 — daily life i maintenance | Jedno LIF flow + ENG-13/14 | Regularne użycie, brak zbędnego catalog growth |

WIP: jeden engineering increment i najwyżej dwa domenowe pilots. Każdy zakończyć decyzją: utrwalić, poprawić, zostawić jako template, odrzucić. Priorytety są rekomendacją: P0 = warunki wiarygodnego i wydajnego rozwoju; P1 = pierwszy zlecony przyrost użytkowy; P2 = następne dopasowane użycie; P3 = po potwierdzeniu częstotliwości. P0 nie oznacza, że wszystkie prace blokują każdą specyfikację.

Szacunki S/M/L oznaczają wielkość zadania względem innych, bez wiarygodnej obietnicy dni. Runtime pilots, brakujące narzędzia i dostęp do writera mogą zmienić nakład. Owner UNASSIGNED jest do przydzielenia przy realizacji. PROPOSED/DISCOVERY nie oznacza rozpoczętej implementacji. Nowe IDs nie zastępują AIS/RT; zadania historyczne należy rozliczyć na obecnym źródle.

## Definition of Done dla nowego przyrostu

- Potwierdzona powtarzalna potrzeba i reuse-or-build; właściwa warstwa architektury.
- Testowalny scope, triggers/near-misses, inputs/outputs, dependencies, stop/failure handling.
- Static/helper checks właściwe dla zmiany; routing i observed behavior nie są utożsamiane z parsingiem YAML.
- Evals bez leakage, powiązane z konkretną wersją/model/runtime; baseline/previous version gdy sensowny; brak danych pozostaje NOT_RUN.
- Real-use pilot zgodny z lifecycle i brak nierozliczonego high severity; mierzone poprawki/effort.
- Output użyteczny i proporcjonalny; brak zbędnego researchu, formularzy, score i obowiązkowych wizualizacji.
- Catalog/registry/channel manifests zgodne ze źródłem; new personal-beta ograniczony polityką, owner i expiry.
- Krótka reviewable zmiana i autoryzacja do promotion/publication, gdy potrzebna; bez merge/deploy w ramach samego backlogu.

## Co celowo odłożyć lub odrzucić

- Nowa platforma „Skill Factory” z dashboardem, bazą, kolejkami i własnym frameworkiem agentów: na razie nadmierna infrastruktura względem istniejących scripts i controller.
- Duplikat article-writer, generic researcher, generic report generator, website builder, stock screener: najpierw reuse capabilities już dostępnych.
- Monolityczne Life OS, globalny record-store i uniwersalny router wszystkich projektów: rozszerzają coupling i privacy scope bez udowodnionej potrzeby.
- Wszystkie pomysły z dawnych README jednocześnie: wiele jest rozpisaną intencją lub aliasem nowego Commerce.
- Generic critic/red-team/quality-gate jako obowiązkowy etap każdej odpowiedzi: ryzyko procesowego narzutu; konkretna kontrola tylko gdy zmienia wynik.
- Health/legal/tax OS: bez konkretnej potrzeby i odpowiedniego evidence/scope nie są dobrym pierwszym przyrostem.
- Autonomiczne kupowanie, publikowanie, kontaktowanie sprzedawców lub wdrażanie zmian: odrębny action scope, nie domyślna konsekwencja research flow.

## Backlog wykonawczy

Każdy wpis ma uzasadnienie, zakres, kryteria ukończenia, dependencies, wielkość i status. CSV służy do importu; JSON zachowuje pełny kontrakt. Sekwencja zależności jest acykliczna; nie ma obowiązku realizacji wszystkich wpisów.


### Skill Engineering


#### ENG-01 · P0 · Uzgodnić stan źródła, runtime i dotychczasowych backlogów

Typ: documentation/control. Status: PROPOSED. Wielkość: S. Zależności: brak.

Powiązania historyczne do rozliczenia: AIS-16, AIS-21.

**Dlaczego:** Stare README i historyczne snapshoty zaniżają lub mylą zakres; można zlecić ponownie już wykonane prace.

**Zakres:** Zestawić main, manifest Lab, katalog, AIS i RT; skorygować liczbę skills, opis Investing, R6/R7 i wersje. Wskazać rozbieżności, bez automatycznego zamykania historycznych ustaleń.

**Ukończone, gdy:**

- 54 źródłowe skills i 17 workflowów wynikają z przypiętego drzewa

- Manifest Lab 0.29.0 jest osobnym stanem

- Każde powiązanie AIS/RT ma evidence i status do potwierdzenia


#### ENG-02 · P0 · Ujednolicić pełne release gates i personal-beta

Typ: policy/control. Status: PROPOSED. Wielkość: S. Zależności: ENG-01.

Powiązania historyczne do rozliczenia: AIS-21.

**Dlaczego:** Aktualne dokumenty opisują jednocześnie pełną walidację i czasowe wyjątki personal-beta.

**Zakres:** Zaktualizować istniejące lifecycle, skill-development i release-review; jedna polityka dla strict release i ograniczonego personal-beta. Zachować bezwzględny zakaz wyjątku dla znanego high-severity failure.

**Ukończone, gdy:**

- Te same warunki w dokumentach i readiness

- Wyjątek ma owner, zakres, expiry i widoczne NOT_RUN

- Rekomendacja gotowości nie jest autoryzacją publikacji


#### ENG-03 · P0 · Doprowadzić skill-test-design do candidate

Typ: existing skill. Status: PROPOSED. Wielkość: M. Zależności: ENG-01.

**Dlaczego:** Skill istnieje w main jako draft 0.2.0; nie wymaga tworzenia od nowa.

**Zakres:** Pilot na meta, zakupach i artykułach; coverage map kontrakt → obserwowalne asercje; pozytywne i konkurujące intencje PL/EN.

**Ukończone, gdy:**

- Testy odróżniają dobry wynik od wiarygodnego błędu

- Brak testowania ukrytego toku rozumowania

- Runtime evidence dla dokładnej wersji; brak dowodu pozostaje NOT_RUN


#### ENG-04 · P0 · Doprowadzić skill-evaluation do candidate

Typ: existing skill. Status: PROPOSED. Wielkość: M. Zależności: ENG-03.

Powiązania historyczne do rozliczenia: AIS-05, AIS-20.

**Dlaczego:** Draft 0.2.0 ma już zamrożony plan, comparator i analizę wariancji.

**Zakres:** Zweryfikować na baseline bez skill i poprzedniej wersji; zachować niezależność wykonawcy i evaluatora; podać wyniki per case i severity.

**Ukończone, gdy:**

- Wykonawca nie widzi rubryk

- Runtime/model/input/tool budget są porównywalne

- FAIL i brak evidence nie zamieniają się w PASS

- Udokumentowana korzyść lub decyzja ITERATE/REJECT


#### ENG-05 · P0 · Doprowadzić skill-release-review do candidate

Typ: existing skill. Status: PROPOSED. Wielkość: M. Zależności: ENG-02, ENG-04.

**Dlaczego:** Końcowy review już istnieje jako draft 0.2.0; trzeba powiązać go z realną polityką.

**Zakres:** Pilot decyzji dla jednego zdrowego candidate, jednego brakującego dowodu i jednego high failure. Sprawdzić tożsamość źródła, paczki i kanału.

**Ukończone, gdy:**

- Wynik zgodny z ENG-02

- Nieaktualny dowód nie potwierdza zmienionej wersji

- APPROVE nie uruchamia merge/release

- Znany high failure blokuje także personal-beta


#### ENG-06 · P0 · Usprawnić istniejący skill-development

Typ: workflow. Status: PROPOSED. Wielkość: M. Zależności: ENG-02, ENG-03.

**Dlaczego:** Masz proces, lecz wiele ręcznych przejść i niejednolite dokumenty; nowy meta-workflow zdublowałby odpowiedzialność.

**Zakres:** Dodać krótki intake, reuse-or-build, profil zmiany, kontrakt, testy i handoff. Rozpocząć projektowanie testów przy specyfikacji; sfinalizować po draft.

**Ukończone, gdy:**

- DOCS nie uruchamia pełnej kampanii

- NEW/ROUTING/BEHAVIOR/RESOURCE mają jawną macierz kontroli

- Output obejmuje implementację, evidence i najmniejszy następny krok


#### ENG-07 · P1 · Dodać mały scaffolder oparty na istniejącym template

Typ: script/template. Status: PROPOSED. Wielkość: S. Zależności: ENG-06.

**Dlaczego:** Szablony SKILL.md i cases.yaml już są; ręczne kopiowanie zwiększa liczbę niespójności.

**Zakres:** Skrypt tworzy pakiet z kontraktu, korzystając z templates/skill-template; nie generuje pustych katalogów i nie nadpisuje istniejącego skill.

**Ukończone, gdy:**

- Powtarzalny output

- Brak overwrite i path traversal

- Poprawne nazwy oraz walidacja

- Referencje powstają tylko gdy potrzebne


#### ENG-08 · P0 · Zintegrować lokalny runner z repozytoryjnym eval protocol

Typ: runtime tooling. Status: PROPOSED. Wielkość: L. Zależności: ENG-01, ENG-04.

Powiązania historyczne do rozliczenia: AIS-05, AIS-20.

**Dlaczego:** Runner poza repo już obsługuje izolację, smoke, kolejkę i evidence; odbudowa od zera nie ma sensu.

**Zakres:** Najpierw ustalić co jest już upstream. Przenieść potrzebne elementy controller-only do scripts/eval, zachowując receipt.py/campaign.py jako kontrakt. Bez danych prywatnych i historycznej autoryzacji do Drive.

**Ukończone, gdy:**

- Jedna komenda przygotowuje, wykonuje i archiwizuje przypadek

- Wznowienie nie duplikuje run

- Unassisted executor nie widzi rubric

- CLI i Desktop mają oddzielne dowody

- Dawne external-write authorization nie jest kopiowane do biblioteki


#### ENG-09 · P1 · Dodać analizę wpływu zmiany i wybór testów

Typ: script/control. Status: PROPOSED. Wielkość: M. Zależności: ENG-06, ENG-08.

**Dlaczego:** Każde rozszerzenie nie powinno odpalać całej kosztownej kampanii, ale wspólne komponenty mają szeroki wpływ.

**Zakres:** Rozszerzyć istniejące walidatory o affected skills/workflows z grafu dependencies i zasobów; pełny suite przy zmianach registry, buildera lub wspólnego kontraktu.

**Ukończone, gdy:**

- Zmiana specialist wybiera dependents i routing neighbors

- Zmiana wspólnego pliku nie pomija dotkniętych flow

- Dobór jest deterministyczny i ma uzasadnienie


#### ENG-10 · P1 · Utrzymywać granice routingu i zestaw przypadków konkurujących

Typ: catalog/evals. Status: PROPOSED. Wielkość: M. Zależności: ENG-03.

Powiązania historyczne do rozliczenia: AIS-06.

**Dlaczego:** Wzrost biblioteki szczególnie grozi kolizją consumer/commerce, research/article i OAF/software.

**Zakres:** Dodać lekką macierz sąsiadów i routing cases; nie tworzyć centralnego mega-routera ani drugiego ręcznego katalogu procedur.

**Ukończone, gdy:**

- Consumer purchase nie uruchamia Commerce

- Tekst użytkownika do redakcji nie uruchamia pełnego research

- Software ADR nie udaje OAF diagnozy

- Przypadki obejmują PL/EN i pośrednią intencję


#### ENG-11 · P1 · Mierzyć użyteczność i koszt procesu

Typ: metrics/control. Status: PROPOSED. Wielkość: S. Zależności: ENG-04, ENG-08.

**Dlaczego:** Liczba skills i zielony YAML nie dowodzą oszczędności czasu ani jakości.

**Zakres:** Dodać do istniejących receipts opcjonalne metryki czasu, dostępnych tokens/tool calls, kosztu jeśli faktycznie znany, interwencji i poprawek. Trzymać benchmark na tych samych wejściach.

**Ukończone, gdy:**

- Brak kosztu jest unknown

- Wynik zawiera medianę/range i denominator

- Odsetek ciężkich błędów nie ginie w średniej

- Porównanie do pracy bez skill lub accepted version


#### ENG-12 · P1 · Dodawać regresje z realnych poprawek użytkownika

Typ: control/evals. Status: PROPOSED. Wielkość: S. Zależności: ENG-03, ENG-08.

**Dlaczego:** Najbardziej wartościowe testy pochodzą z przypadków, gdzie realny wynik zawiódł.

**Zakres:** Rozszerzyć istniejący revision/post-release loop; anonimizować wejście, zachować błąd i kontrakt, dodać regresję przed poprawką.

**Ukończone, gdy:**

- Pierwotny failure pozostaje w historii

- Dane prywatne nie trafiają do publicznego fixture

- Test nie jest osłabiony, by naprawa wyglądała dobrze


#### ENG-13 · P2 · Wprowadzić przegląd użycia, scalanie i deprecację

Typ: maintenance/control. Status: PROPOSED. Wielkość: S. Zależności: ENG-11.

**Dlaczego:** Duży katalog zwiększa koszt kontekstu i utrzymania, także gdy poszczególne skills są dobre.

**Zakres:** Okresowy review tylko na danych o użyciu/incydentach; wskazać komponenty nieużywane, pokrywające się i wyparte przez native tools.

**Ukończone, gdy:**

- Każde merge/deprecate ma dowód i migration path

- Rzadko używany skill o dużej wartości nie jest automatycznie usuwany

- Brak telemetry nie udaje braku użycia


#### ENG-14 · P2 · Dodać do katalogu flow i jawny stan dostępności

Typ: catalog/release. Status: PROPOSED. Wielkość: M. Zależności: ENG-01, ENG-10.

**Dlaczego:** Katalog i docs/processes.json już istnieją; nowe flow powinny korzystać z tej samej prezentacji.

**Zakres:** Rozszerzyć generator o nowe domains, flow, kanały i readiness; odróżnić suggested path od registered runtime workflow.

**Ukończone, gdy:**

- Brak ręcznie zdublowanych definicji

- Candidate/draft nie wyglądają jak dostępna produkcja

- Stan installed, main i evidence jest rozróżnialny


### Shared methods


#### CORE-01 · P1 · Zrealizować minimalny research-brief

Typ: planned skill. Status: PROPOSED. Wielkość: M. Zależności: CON-02, WRI-02.

**Dlaczego:** Jest zaplanowany w skills/core/README; zakupy, artykuły i vendor research mają podobny etap definiowania pytania.

**Zakres:** Cel decyzji, odbiorca, must-have, ograniczenia, zakres źródeł i stop condition. Pilot z Consumer i Writing przed utrwaleniem abstrakcji.

**Ukończone, gdy:**

- 2–3 realne zastosowania pokazują tę samą metodę

- Krótkie pytanie nie wymaga intake

- Brak profilu użytkownika w skill

- Kontrakt pasuje do obu flow


#### CORE-02 · P1 · Zrealizować evidence-validator bez drugiej analizy domenowej

Typ: planned skill/reference. Status: PROPOSED. Wielkość: M. Zależności: CON-03, WRI-02.

**Dlaczego:** Już jest zaplanowany; istnieje też evidence contract w report-composer.

**Zakres:** Reużyć definicje pochodzenia i niepewności. Kontrola źródeł, daty, sprzeczności i adekwatności wniosku; bez wybierania produktu lub pisania artykułu.

**Ukończone, gdy:**

- Nie kopiuje ledger z composer

- Fakt, user claim, inference i unknown są rozróżnione

- Testuje sprzeczne, stare i marketingowe dane

- Nie analizuje ponownie domeny


#### CORE-03 · P1 · Zrealizować structured-comparison

Typ: planned skill. Status: PROPOSED. Wielkość: M. Zależności: CON-04, PRO-01.

**Dlaczego:** Już jest zaplanowany; porównanie zakupów i rozwiązań technicznych ma wspólne kryteria i trade-offs.

**Zakres:** Metoda porównania z hard constraints przed preferencjami; brak danych to unknown. Wagi tylko jawnie uzgodnione; obliczenia w skrypcie.

**Ukończone, gdy:**

- Niespełnienie must-have nie jest kompensowane ceną

- Brak specyfikacji nie staje się niskim score

- Zmiana priorytetu pokazuje warunek zmiany rekomendacji


#### CORE-04 · P2 · Sprawdzić potrzebę handoff-generator

Typ: planned skill/reference. Status: DISCOVERY. Wielkość: S. Zależności: ENG-06.

**Dlaczego:** Zaplanowany core skill może pomóc w pracy między modelami, ale najpierw wystarczy template w workflow.

**Zakres:** Minimalny handoff: cel, źródła, ustalenia, decyzje, unknowns, authority, next action. Skill dopiero gdy niezależny handoff powtarza się w kilku domenach.

**Ukończone, gdy:**

- Przeniesienie nie dopisuje zgód

- Odbiorca dostaje potrzebny kontekst i nie dostaje rubryk

- Da się wznowić zadanie bez odtwarzania całej rozmowy


### Consumer decisions


#### CON-01 · P1 · Zdefiniować granice Consumer i prywatny purchase profile

Typ: specification/context. Status: PROPOSED. Wielkość: S. Zależności: ENG-01.

**Dlaczego:** Zakup dla siebie to inny cel niż wejście na rynek e-commerce.

**Zakres:** Nowa domena skills/consumer; kraj/rynek, waluta, budżet, zastosowanie i posiadany sprzęt w kontekście. Nazwy i boundaries przechodzą skill-specification.

**Ukończone, gdy:**

- Minimum 3 przykłady: sprzęt, dom/AGD, software subscription

- Osobno must-have i nice-to-have

- Kupno do użytku własnego nie uruchamia Commerce


#### CON-02 · P1 · Zbudować purchase-decision jako pierwszy pionowy pilot

Typ: workflow. Status: PROPOSED. Wielkość: L. Zależności: CON-01, ENG-06.

**Dlaczego:** Realizuje dokładnie prośbę: mówię potrzebę, otrzymuję uporządkowany research i rekomendację.

**Zakres:** Need → constraints → shortlist → hard-filter → evidence → comparison → offer check → recommendation. Zacząć od lekkich reference stages; specialists wyodrębniać gdy są niezależnie użyteczni.

**Ukończone, gdy:**

- 3–5 dopasowanych opcji jako default

- Najlepszy wybór, alternatywa i warunek niewybierania

- Odpowiedź rozróżnia model i ofertę

- Brak zakupu/zamówienia

- Ma stop condition i obsługę niedostępnego narzędzia


#### CON-03 · P1 · Zbudować product-evidence-review

Typ: new skill. Status: PROPOSED. Wielkość: M. Zależności: CON-01, ENG-03.

**Dlaczego:** Karty marketingowe i rankingi afiliacyjne nie wystarczają do rekomendacji.

**Zakres:** Ocena znanego modelu: exact SKU, region/revision, official specs/manual, niezależne pomiary, awarie/limitations; popularność nie jest dowodem jakości.

**Ukończone, gdy:**

- Źródło przy decydującej claim

- Wariant modelu rozpoznany

- Konflikt spec/test jest widoczny

- Brak testu nie oznacza potwierdzonej jakości

- Produkt niekompatybilny nie trafia do zwycięzców


#### CON-04 · P1 · Zbudować product-fit-comparison

Typ: new skill. Status: PROPOSED. Wielkość: M. Zależności: CON-03.

**Dlaczego:** Najlepszy produkt dla Twojej sytuacji nie musi wygrać ogólnego rankingu.

**Zakres:** Porównać model do scenariuszy użytkowania, hard constraints, jakości dowodów i trade-offs. Na start własny mały kontrakt; po pilocie wykorzystać CORE-03.

**Ukończone, gdy:**

- Jawne kryteria i dowody

- Brak nieuzasadnionego aggregate score

- Wskazany kompromis zwycięzcy i strongest alternative

- Aktualny produkt/odroczenie może wygrać


#### CON-05 · P1 · Zbudować purchase-offer-review i prosty kalkulator TCO

Typ: new skill + script. Status: PROPOSED. Wielkość: M. Zależności: CON-01.

**Dlaczego:** Wybór modelu i wybór konkretnej oferty mają inne dane i failure modes.

**Zakres:** Dla known SKU sprawdzić sprzedawcę, cenę, dostępność, dostawę, gwarancję/zwroty i warunki. TCO na znanym okresie: zakup, eksploatacja, abonament, opłaty; nie estymować nieznanych kosztów bez etykiety.

**Ukończone, gdy:**

- Oferta ma exact SKU, walutę, rynek, URL i checked_at

- Nieudokumentowane stock/seller quality są unknown

- Arytmetyka ma testy i jednostki

- Brak danych prawnych nie daje legal clearance


#### CON-06 · P1 · Sprawdzić purchase-decision w realnych przypadkach

Typ: evals/pilot. Status: PROPOSED. Wielkość: M. Zależności: CON-02, CON-03, CON-04, CON-05, ENG-04.

**Dlaczego:** Flow musi oszczędzać pracę, a nie produkować długi research do każdego zakupu.

**Zakres:** Pilot sprzętu, AGD/domu i subskrypcji oraz przypadki: brak must-have, podobne warianty, stare ceny, konflikt testów, zakup biznesowy, bardzo tania rzecz.

**Ukończone, gdy:**

- Około 3–5 realnych użyć zgodnie z lifecycle

- Zestaw realistycznych negatives i failure cases

- Wynik skraca czas i poprawki vs baseline

- Brak nieautoryzowanej transakcji


#### CON-07 · P2 · Dodać price/availability watch na wyraźne zlecenie

Typ: context + automation. Status: PROPOSED. Wielkość: S. Zależności: CON-05, CON-06.

**Dlaczego:** Monitoring ma sens po wyborze produktu i określeniu ceny docelowej.

**Zakres:** Reużyć automation hosta; zachować exact SKU, warunek alertu, cadence, expiry i quiet-on-unchanged. Nie budować crawlera/daemonu.

**Ukończone, gdy:**

- Powiadomienie tylko o znaczącej zmianie

- Dane odświeżone przed alertem

- Wygaszenie/stop są jawne

- Watch nie kupuje produktu


#### CON-08 · P2 · Rozszerzyć decyzję o repair / keep / replace

Typ: workflow branch. Status: PROPOSED. Wielkość: M. Zależności: CON-06.

**Dlaczego:** Największa oszczędność może polegać na niewymienianiu sprawnej rzeczy.

**Zakres:** Gałąź purchase-decision: obecny problem, naprawa/serwis, koszt wymiany, przewidywane ograniczenia i trade-off. Osobny skill tylko przy powtarzalnej analizie.

**Ukończone, gdy:**

- Odroczenie i naprawa są realnymi opcjami

- Brak diagnozy technicznej jest unknown

- Nie wydaje niebezpiecznych instrukcji naprawczych


### Writing / publishing


#### WRI-01 · P1 · Zidentyfikować istniejący skill artykułowy

Typ: inventory/adapter. Status: DISCOVERY. Wielkość: S. Zależności: brak.

**Dlaczego:** Użytkownik deklaruje skill w aplikacji, ale nie ma go w udostępnionym katalogu ani w drzewie ai-skills.

**Zakres:** Odczytać name/version/contract/dependencies, rozróżnić zewnętrzny plugin i repo source; zachować portable boundary. Bez kopiowania cudzej implementacji.

**Ukończone, gdy:**

- Znana funkcja, wejście i wyjście

- Legalny sposób użycia/adapter

- Brak zależności oznacza unavailable, a nie udawane wywołanie


#### WRI-02 · P1 · Zbudować article-development wokół obecnego writera

Typ: workflow. Status: PROPOSED. Wielkość: L. Zależności: WRI-01, ENG-06.

**Dlaczego:** Potrzebujesz opiniotwórczych i analitycznych tekstów; największa wartość jest w tezie i dowodach.

**Zakres:** Brief → teza/odbiorca → potrzebny research → argument structure → existing writer → critique → evidence check → revision. Dla własnego draft pomijać wcześniejsze etapy.

**Ukończone, gdy:**

- Jeden spójny tekst gotowy do redakcji

- Odrębny factual/research gate

- Research kończy się gdy wspiera główne claims

- Nie tworzy nowego article-writer

- Znany kontrakt fallback przy braku adaptera


#### WRI-03 · P1 · Zbudować editorial-argument-review

Typ: new skill. Status: PROPOSED. Wielkość: M. Zależności: WRI-01.

**Dlaczego:** Płynny język nie gwarantuje tezy, logiki ani wartości dla odbiorcy.

**Zakres:** Kontrola centralnej tezy, wnioskowania, weakest premise, strongest counterargument, struktury, powtórzeń i konkretności. Nie researchuje i nie przepisywuje całości bez potrzeby.

**Ukończone, gdy:**

- Rozróżnia błąd logiczny i preferencję stylistyczną

- Wskazuje minimalną poprawkę

- Nie usuwa zastrzeżeń wzmacniających uczciwość

- Nie narzuca generycznego AI tonu


#### WRI-04 · P1 · Zdefiniować article-claim-check

Typ: reference → conditional skill. Status: PROPOSED. Wielkość: M. Zależności: WRI-02.

**Dlaczego:** Faktografia, cytowania i przypisy muszą zgadzać się z faktycznym źródłem.

**Zakres:** Lista claims do kontroli: fakty/cytaty/liczby/causal claims; sprawdzić źródła i daty, oznaczyć opinion/inference. Najpierw reference w flow; po re-use delegować ogólną kontrolę do CORE-02.

**Ukończone, gdy:**

- Nieistniejący link/cytat jest blokowany

- Cytowanie wspiera konkretną claim

- Prywatny case nie trafia do publikacji bez świadomej decyzji

- Własne doświadczenie nie jest dopisywane


#### WRI-05 · P1 · Zbudować prywatny voice profile i sprawdzić flow

Typ: project context + pilot. Status: PROPOSED. Wielkość: M. Zależności: WRI-02, WRI-03, WRI-04, ENG-04.

**Dlaczego:** Twój styl powinien wynikać z autentycznych próbek, a nie z ogólnych przymiotników.

**Zakres:** 3–5 tekstów/próbek, reguły struktury, słownictwo i antyprzykłady w kontekście projektu. Pilot: techniczny artykuł, executive opinion, poprawa własnego tekstu.

**Ukończone, gdy:**

- Profil nie jest zaszyty w publiczny skill

- Tekst nie wymyśla doświadczeń

- Blind A/B ogranicza wpływ atrakcyjnego formatowania

- Mierzony zakres Twoich poprawek


#### WRI-06 · P2 · Dodać adaptacje i publication handoff

Typ: workflow branch / external tools. Status: PROPOSED. Wielkość: M. Zależności: WRI-05.

**Dlaczego:** Jeden zatwierdzony tekst może zasilać LinkedIn, newsletter i stronę.

**Zakres:** Adaptacja odbiorcy i formatu dopiero z ukończonego tekstu; SEO tylko dla właściwego kanału. Reużyć istniejące narzędzia strony/Docs; publikacja na wyraźne polecenie.

**Ukończone, gdy:**

- Brak nowych niezweryfikowanych tez

- Wersje mają źródłowy tekst i approved state

- Przygotowanie nie publikuje automatycznie

- Nie generuje niepotrzebnych treści kanałowych


### Professional work


#### PRO-01 · P2 · Zbudować technical-option-review

Typ: new skill. Status: PROPOSED. Wielkość: M. Zależności: ENG-10.

**Dlaczego:** Twoja praca Staff/Solution Architect wymaga oceny decyzji o systemie; OAF jest oceną architektury organizacyjnej.

**Zakres:** Alternatywy techniczne, constraints, integration/data ownership, operacje, koszt, lock-in i reversibility. Output: krótki ADR lub input do decyzji; repo/tool docs są source of truth.

**Ukończone, gdy:**

- Oddzielna granica od OAF architecture-review

- Co najmniej strongest viable alternative

- Nie wynajduje infrastruktury i API

- Wskazuje co zmieniłoby decyzję


#### PRO-02 · P2 · Zbudować technology-selection dla buy/build/vendor

Typ: workflow. Status: PROPOSED. Wielkość: L. Zależności: PRO-01, CORE-03.

**Dlaczego:** Możesz reużyć porównanie Consumer/Core, ale vendor decision wymaga innych kryteriów.

**Zakres:** Requirements → buy/build/defer → shortlist → evidence → trial → TCO/risk → recommendation. Dodawać tylko security/data/SLA/exit criteria właściwe dla organizacji.

**Ukończone, gdy:**

- Nie myli produktu z enterprise offer

- Vendor marketing nie jest dowodem SLA poza umową

- Decyzja uwzględnia trial i exit cost

- Brak automatycznego zakupu


#### PRO-03 · P2 · Zbudować meeting-decision-extraction

Typ: new skill. Status: PROPOSED. Wielkość: M. Zależności: brak.

**Dlaczego:** Masz kontekst Meeting Summarizer; przydatny wynik to decyzje, zobowiązania i otwarte pytania.

**Zakres:** Z supplied transcript/notes wydobyć decisions/actions z cytatem/time marker; właściciel i termin tylko gdy padły. Rozróżnić propozycję, zgodę i decyzję.

**Ukończone, gdy:**

- Brak wymyślonych właścicieli i dat

- Brak przypisania decyzji z luźnej dyskusji

- Sporne ustalenia są oznaczone

- Nie nagrywa i nie wysyła wiadomości


#### PRO-04 · P2 · Dodać executive-decision-memo jako profil

Typ: workflow branch/template. Status: PROPOSED. Wielkość: S. Zależności: PRO-01.

**Dlaczego:** Masz report-composer; osobny generic memo writer łatwo zdubluje kompozycję.

**Zakres:** Profil: decision, evidence, options, risk, unknowns, owner/next action. Composer tylko jeśli dostępny; jasny lokalny text fallback dla nowego flow.

**Ukończone, gdy:**

- Nie analizuje ponownie tematu

- Zwarta rekomendacja i trade-offs

- Format nie wzmacnia pewności

- Brak zależności composer nie blokuje opcjonalnej prezentacji


#### PRO-05 · P2 · Zbudować ai-use-case-review

Typ: new skill. Status: PROPOSED. Wielkość: M. Zależności: PRO-01.

**Dlaczego:** AI-enabled products są w Twoim kontekście, ale nie każdy problem wymaga LLM/agenta.

**Zakres:** Problem → deterministic/no-AI alternative → data readiness → eval task → failure cost → pilot boundary. OAF specialists tylko dla problemu organizacyjnego.

**Ukończone, gdy:**

- Porównanie do prostszej automatyzacji

- Mierzalny pilot i quality/cost threshold

- Explicit human/action authority

- Brak AI ROI opartego na nieznanych liczbach


#### PRO-06 · P2 · Zbudować automation-opportunity-review

Typ: new skill + workflow. Status: PROPOSED. Wielkość: M. Zależności: PRO-05.

**Dlaczego:** Zanim automatyzować, warto sprawdzić częstotliwość, wyjątki, dostęp i koszt błędu.

**Zakres:** Intake procesu, źródła, deterministyczne kroki, judgement steps, właściciel, retry/idempotency, observability, stop. Output: mały automation brief; implementację wykonują właściwe narzędzia.

**Ukończone, gdy:**

- Rzeczywista powtarzalność

- Prosty script/native automation oceniony przed agentem

- Error/rollback path

- Brak automatycznego provisioningu


#### PRO-07 · P2 · Uruchomić tender-screening na istniejącym planie Tender

Typ: reuse planned domain. Status: PROPOSED. Wielkość: L. Zależności: ENG-06.

**Dlaczego:** Tender Pilot jest Twoim projektem; skills/tender zawiera już plan 11 metod.

**Zakres:** Pierwszy wycinek: rfp-extraction → eligibility-check → capability-evidence-match → go-no-go. Parsery do kodu; requirements mają source location. Nie implementować od razu wszystkich 11 skills.

**Ukończone, gdy:**

- Mandatory fail zatrzymuje dalszy research

- Każda claim ma evidence

- Braki nie stają się deklarowaną zgodnością

- Pilotaż na rzeczywistym lub anonimizowanym RFP


#### PRO-08 · P2 · Uruchomić website-quality-review zamiast kolejnego buildera

Typ: reuse planned domain + native tools. Status: PROPOSED. Wielkość: M. Zależności: ENG-06.

**Dlaczego:** Masz projekty webowe i narzędzia Figma/Sites; domena web-design jest już rozpisana.

**Zakres:** Najpierw design-critique i visual-regression-review; accessibility-gate dla judgement poza automatycznymi testami. Responsive, links i a11y scans w kodzie/CI.

**Ukończone, gdy:**

- Sprawdzony realny render desktop/mobile

- Uwagi z lokalizacją i impact

- Brak duplikacji native builder

- Ruch i wygląd wspierają funkcję


### Learning OS


#### LEA-01 · P2 · Uruchomić learning-session zgodny z obecnym Learning OS

Typ: workflow + project context. Status: PROPOSED. Wielkość: M. Zależności: brak.

**Dlaczego:** Instrukcje projektu już określają router i learning loop; nie trzeba ich przepisywać w pięć obowiązkowych skills.

**Zakres:** Quick question pozostaje quick; dla sesji: cel → minimum theory → practice → feedback → next. knowledge-diagnosis/concept-explainer początkowo jako gałęzie, nie automatyczny pipeline.

**Ukończone, gdy:**

- Brak przymusowego quizu do definicji

- Po wystarczającym rozumieniu przejście do zastosowania

- Profil i prywatny log w kontekście

- Nie dopisuje osiągniętej kompetencji


#### LEA-02 · P2 · Zrealizować practice-generator

Typ: planned skill. Status: PROPOSED. Wielkość: M. Zależności: LEA-01.

**Dlaczego:** Zaplanowany skill daje wysoką wartość przez realistyczne zadania zamiast dalszej teorii.

**Zakres:** Scenariusze decyzji/design/diagnosis z progresywną trudnością i kryterium sukcesu. Dostosować do demonstrated level; nie zdradzać rozwiązania w zadaniu.

**Ukończone, gdy:**

- Ćwiczenie mierzy cel

- Realne trade-offs i edge cases

- Wskazówki oddzielone od zadania

- Difficulty wynika z evidence


#### LEA-03 · P2 · Zrealizować competence-check

Typ: planned skill. Status: PROPOSED. Wielkość: M. Zależności: LEA-02.

**Dlaczego:** Własne poczucie zrozumienia nie jest dowodem kompetencji.

**Zakres:** Ocenić supplied performance: correctness, independence, transfer, trade-offs, error correction; feedback i najmniejszy następny krok. Bez obowiązkowej skali poza checkpoints.

**Ukończone, gdy:**

- Uzasadnienie oceny zachowuje evidence

- Brak wykonania pozostaje nieocenione

- Nie traktuje completion jako mastery

- Nie zatrzymuje nauki dla nieistotnego perfekcjonizmu


#### LEA-04 · P3 · Dodać retention-review i learning log dopiero gdy potrzebne

Typ: planned skill + optional automation. Status: PROPOSED. Wielkość: S. Zależności: LEA-03.

**Dlaczego:** Retencja i wielosesyjna ciągłość są już w instrukcjach; nie każdy temat wymaga śledzenia.

**Zakres:** Review na demonstrated gaps; log na prośbę lub dla ciągłości. Automatyczne przypomnienia tylko zlecone przez użytkownika.

**Ukończone, gdy:**

- Recall/application zamiast streszczania

- Log nie zawiera fikcyjnego postępu

- Plan review ma stop/expiry

- Brak niezamówionych powiadomień


### Daily life


#### LIF-01 · P2 · Zaprojektować trip-decision i itinerary-feasibility

Typ: workflow + narrow skill. Status: DISCOVERY. Wielkość: M. Zależności: CON-06, CORE-03.

**Dlaczego:** Projekt Malaga wskazuje kontekst podróży, ale nie dowodzi częstotliwości.

**Zakres:** Wybór lokalizacji/noclegu/transportu reużywa Consumer/Core; osobna metoda sprawdza czasy, dystanse, godziny, buffer i feasibility. Preferencje w projekcie.

**Ukończone, gdy:**

- Koszty/datę/dostępność odświeżono

- Plan uwzględnia buffers

- Brak fikcyjnych reservations

- Opcje odpadające na constraints nie są rekomendowane


#### LIF-02 · P2 · Zaprojektować property-shortlist-review

Typ: workflow. Status: DISCOVERY. Wielkość: L. Zależności: CORE-02, CORE-03.

**Dlaczego:** Projekt Houses uzasadnia rozpoznanie potrzeby; zakup nieruchomości ma inną wagę niż AGD.

**Zakres:** Oferty → hard constraints → dojazdy/okolica → koszty znane/scenariusze → shortlist → pytania na viewing. Dokładny adres, budżet i stan w private context.

**Ukończone, gdy:**

- Fakty z ofert odróżnione od zweryfikowanych

- Nie wykonuje legal/technical clearance

- Wskazuje dokumenty i due-diligence gaps

- Brak automatycznego kontaktu z agentem


#### LIF-03 · P3 · Zaprojektować meal-planning / pantry-to-list

Typ: workflow + script. Status: DISCOVERY. Wielkość: M. Zależności: brak.

**Dlaczego:** Projekty Foodie Assistant i Jedzenie wskazują użyteczny kontekst, lecz częstotliwość trzeba potwierdzić.

**Zakres:** Budżet/czas/składniki → kilka posiłków → wspólna lista zakupów → batch prep. Agregacja jednostek i ilości w kodzie; preferencje/alergeny w kontekście.

**Ukończone, gdy:**

- Lista nie duplikuje składników

- Uwzględnia supplied restrictions

- Brak twierdzeń medycznych

- Koszt i wartości odżywcze bez źródła są unknown


#### LIF-04 · P3 · Zaprojektować local-service-selection

Typ: workflow. Status: DISCOVERY. Wielkość: M. Zależności: CON-06, CORE-03.

**Dlaczego:** Ten sam problem porównania występuje przy ekipie, serwisie i usługach; inne dowody niż dla produktu.

**Zakres:** Brief → quotes → zakres włączeń/wyłączeń → dostępność → evidence/reviews → rekomendacja i pytania. Consumer profile nie zawiera prywatnego adresu w skill.

**Ukończone, gdy:**

- Oferty mają porównywalny scope

- Opinie to weak evidence, nie gwarancja

- Brak automatycznego wysłania request

- Najtańsza oferta nie wygrywa mimo braków


#### LIF-05 · P3 · Zaprojektować subscription-review

Typ: workflow + context. Status: DISCOVERY. Wielkość: S. Zależności: CON-05.

**Dlaczego:** Powtarzalne opłaty łączą zakupy i wybór narzędzi, ale nie potrzeba nowego finansowego OS.

**Zakres:** User-provided list/usage → duplicate value → known annual cost → keep/downgrade/cancel candidates. Przepływ nie korzysta z inwestycyjnego record-store.

**Ukończone, gdy:**

- Koszt policzony ze znanych inputs

- Brak dostępu do kont nie jest zastępowany domysłem

- Nie anuluje bez zlecenia

- Nie traktuje niskiego usage jako automatycznej decyzji


#### LIF-06 · P3 · Zaprojektować document-to-action dla spraw domowych

Typ: workflow/template. Status: DISCOVERY. Wielkość: M. Zależności: brak.

**Dlaczego:** Terminy i obowiązki w dokumentach mogą dawać większą wartość niż kolejne streszczenie.

**Zakres:** Z supplied dokumentu wydobyć termin, warunek, krok i source location; przygotować checklistę/draft odpowiedzi. Privacy i data minimization.

**Ukończone, gdy:**

- Nie wymyśla deadline

- Interpretacja prawna odróżniona od tekstu dokumentu

- Żadnego wysłania ani zapisania do zewnętrznego store bez odpowiedniego zlecenia


### Existing portfolio


#### EXI-01 · P1 · Rozliczyć bieżące AIS/RT i evidence gaps

Typ: evals/readiness. Status: PROPOSED. Wielkość: M. Zależności: ENG-01, ENG-02.

Powiązania historyczne do rozliczenia: AIS-05, AIS-21, AIS-22, RT-001.

**Dlaczego:** Historyczne backlogi są cenne, ale stare FAIL/PASS są związane z poprzednią wersją.

**Zakres:** Po ENG-01 potwierdzić aktualny stan i priorytet znanych failures; re-test tylko affected paths. Osobna kolejka maintenance, bez blokowania wszystkich nowych pomysłów.

**Ukończone, gdy:**

- Brak ponownego zlecania wykonanej poprawki

- High unresolved regression blokuje affected release

- Current receipt i pending mają jawny zakres


#### EXI-02 · P2 · Domknąć dowody dla Career candidates

Typ: evals/pilot. Status: PROPOSED. Wielkość: M. Zależności: ENG-04.

**Dlaczego:** Job discovery, validity, CV i interview już istnieją jako candidates; budowanie zamienników traci wartość.

**Zakres:** Priorytet według aktualnego recruitment use case; 3–5 real uses i routing/evidence cases. Mastery CV pozostaje approved private input.

**Ukończone, gdy:**

- Brak invented experience

- Validity przed kosztownym tailoring

- Dokładna wersja ma evidence

- Nie promuje wszystkich tylko dla kompletności


#### EXI-03 · P2 · Sformalizować career-opportunity-to-interview gdy pilot to uzasadni

Typ: workflow. Status: PROPOSED. Wielkość: M. Zależności: EXI-02, ENG-10.

**Dlaczego:** docs/processes.json już pokazuje suggested pathway, ale bez formalnego runtime workflow.

**Zakres:** Reużyć istniejące skills; etapy optional/required zależnie od wejścia; register tylko kanały z dependencies. Z supplied interview pomija discovery.

**Ukończone, gdy:**

- Suggested vs registered jest jasne

- Missing candidate nie jest symulowany

- Flow nie wymusza całej ścieżki do wąskiej prośby


#### EXI-04 · P1 · Sprawdzić przenośność report-composer i visual-output-design

Typ: existing skills/contracts. Status: PROPOSED. Wielkość: M. Zależności: ENG-01, CON-06.

**Dlaczego:** Main i installed Lab mają różne wersje; nowe domeny nie powinny dziedziczyć sztywnych wymagań Investing przypadkowo.

**Zakres:** Ustalić profiles dla purchase/technical memo; composer owns structure, visual owns encoding. Optional presentation degraduje się uczciwie; obowiązkowy visual pozostaje blocked gdy runtime go nie obsługuje.

**Ukończone, gdy:**

- Nie zmienia domyślnie całej architektury raportów

- Nie wymaga wykresu do krótkiego zakupu

- Nie deklaruje render/client PASS

- Jest test current version i kanału


#### EXI-05 · P2 · Rozwijać OAF/Commerce/Investment OS na podstawie realnych gaps

Typ: integration/control. Status: PROPOSED. Wielkość: M. Zależności: ENG-09, ENG-12.

**Dlaczego:** Te domeny są już mocno rozbudowane; ekspansja powinna usuwać konkretne niedociągnięcia.

**Zakres:** Re-test affected runtime fixtures, wersjonować kontrakt, zachować domenowe stores. Consumer nie reuse investment-record-store; red-team inwestycyjny nie staje się generic critic.

**Ukończone, gdy:**

- Nowy skill ma concrete recurring gap

- Brak kopiowania starych product-research/ecommerce aliasów do nowych implementacji

- Zmiana shared core nie powoduje niejawnej migracji istniejących flow


## Źródła i ograniczenia przeglądu


- [Architektura](https://github.com/aras-2003/ai-skills/blob/956885438f12968f958f9c733dc685e2d1b1ae18/docs/ARCHITECTURE.md) — przypięte do przejrzanego main.

- [Model development/release](https://github.com/aras-2003/ai-skills/blob/956885438f12968f958f9c733dc685e2d1b1ae18/docs/DEVELOPMENT-RELEASE-MODEL.md) — przypięte do przejrzanego main.

- [Lifecycle](https://github.com/aras-2003/ai-skills/blob/956885438f12968f958f9c733dc685e2d1b1ae18/docs/LIFECYCLE.md) — przypięte do przejrzanego main.

- [Workflow tworzenia skills](https://github.com/aras-2003/ai-skills/blob/956885438f12968f958f9c733dc685e2d1b1ae18/workflows/skill-development/WORKFLOW.md) — przypięte do przejrzanego main.

- [Meta chain](https://github.com/aras-2003/ai-skills/blob/956885438f12968f958f9c733dc685e2d1b1ae18/skills/meta/README.md) — przypięte do przejrzanego main.

- [Aktualny katalog](https://github.com/aras-2003/ai-skills/blob/956885438f12968f958f9c733dc685e2d1b1ae18/CATALOG.md) — przypięte do przejrzanego main.

- [Core — istniejący plan](https://github.com/aras-2003/ai-skills/blob/956885438f12968f958f9c733dc685e2d1b1ae18/skills/core/README.md) — przypięte do przejrzanego main.

- [Learning — istniejący plan](https://github.com/aras-2003/ai-skills/blob/956885438f12968f958f9c733dc685e2d1b1ae18/skills/learning/README.md) — przypięte do przejrzanego main.

- [Tender — istniejący plan](https://github.com/aras-2003/ai-skills/blob/956885438f12968f958f9c733dc685e2d1b1ae18/skills/tender/README.md) — przypięte do przejrzanego main.

- [Web Design — istniejący plan](https://github.com/aras-2003/ai-skills/blob/956885438f12968f958f9c733dc685e2d1b1ae18/skills/web-design/README.md) — przypięte do przejrzanego main.

- [Integrated report architecture](https://github.com/aras-2003/ai-skills/blob/956885438f12968f958f9c733dc685e2d1b1ae18/docs/INTEGRATED-REPORT-ARCHITECTURE.md) — przypięte do przejrzanego main.

- [Runtime eval protocol](https://github.com/aras-2003/ai-skills/blob/956885438f12968f958f9c733dc685e2d1b1ae18/scripts/eval/README.md) — przypięte do przejrzanego main.

- [Readiness](https://github.com/aras-2003/ai-skills/blob/956885438f12968f958f9c733dc685e2d1b1ae18/release/production-readiness.yaml) — przypięte do przejrzanego main.

- [Flow catalog](https://github.com/aras-2003/ai-skills/blob/956885438f12968f958f9c733dc685e2d1b1ae18/docs/processes.json) — przypięte do przejrzanego main.


Lokalnie odczytano także manifesty Lab 0.29.0 oraz audit/automation/README, runner state i backlogi AIS/RT z 30.09–02.10. Są historycznym materiałem porównawczym. Nie wykonano nowej kampanii runtime, nie potwierdzano aktualnych GitHub branch protections i nie zakładano, że istniejący artykułowy plugin został zweryfikowany. Backlog powstał przez analizę źródeł i dostępnego kontekstu, bez modyfikacji repozytorium, synced sources, skills ani instalacji.


## Decyzja rozszerzająca — Strategy, 5 października 2026

Po pierwotnej analizie przyjęto osobną domenę **Strategy**, pogłębioną analizę konkurencji i osobny workflow **strategy-design**, w tym strategię marketingową. Dodano **17 zadań STR-01…STR-17**; backlog ma teraz **72 zadania**. Pierwotne 55 wpisów i datowana analiza pozostają historycznym punktem wyjścia; statusy/owners/acceptance utrzymujemy w BACKLOG.json.

### Zakres i granice domeny

Strategy wybiera kierunek, where-to-play/how-to-win i sposób przechwycenia wartości. OAF projektuje organizację umożliwiającą wykonanie; Commerce waliduje konkretną opportunity; Investing wykonuje własne underwriting/valuation/portfolio gates; Career/Learning dopasowują wnioski do osobistego kontekstu. Strategy może działać samodzielnie i nie jest obowiązkowym etapem innych flow.

Docelowe źródło: skills/strategy. Rozliczyć historyczny strategy-ea/README: reuse zaplanowanego strategy-challenge, link do wdrożonych OAF zamiast duplikatów. Nie przenosić działających skills dla samej kosmetyki katalogu.

### Dwa odrębne workflow

- **strategic-analysis:** question/scope → selektywne environment/industry/deep competition/position → evidence synthesis → uncertainties → strategic evidence pack i next gate. Narrow request kieruje do najwęższego specialista; current supplied pack pozwala pominąć research.
- **strategy-design:** objectives/constraints + evidence gate → diagnosis → odmienne strategic options → conditional scenarios + challenge → choices/value proposition/advantage/sacrifices → capability/resource implications → measures, validation plan i review triggers. Nie kończy się na SWOT albo liście projektów. Materiał może być proposed/provisional; bez krytycznych danych nie deklarujemy ukończonej zatwierdzonej strategii.
- **Marketing branch:** customer/demand evidence → segmentation/targeting/positioning → value proposition/brand → channel roles/acquisition/retention mix → known budget/resources → measures and staged experiments. To strategia funkcjonalna zgodna z business choices; content calendar, creative i campaign execution są downstream. Reuse Commerce specialists tylko dla zgodnego scope, także obsługa services/B2B bez wymuszania eCommerce economics.

### Pogłębiona analiza konkurencji

Proponowany **competitive-intelligence-review** obejmuje strategic groups, segmenty, business/revenue models, pozycjonowanie, capabilities/resources, distribution, defensibility, observed moves i hipotezy reakcji. Oddziela fakty od interpretacji intencji. Reuse aktualnego evidence pack z Commerce competition-landscape-review; nie wykonuje tego samego researchu drugi raz. Porter analizuje strukturę branży; deep competition analizuje konkretnych graczy i ich strategie — to różne zakresy.

### Skills i kolejność przyrostów

1. STR-01 boundaries; STR-02 environment, STR-03 industry, STR-04 deep competition, STR-05 position; STR-06 analysis oraz zaplanowany STR-09 challenge.
2. STR-07 options i STR-10 design, STR-11 marketing specialist. STR-08 scenarios warunkowo według ryzyka/niepewności; optional dependency z explicit on_missing, nie ukryty obowiązkowy etap.
3. STR-12…15 profiles, STR-16 handoffs i STR-17 pilots/evals. Profile projektować razem z kontraktami analitycznymi, a nie jako dekorację po ukończeniu tekstu.

To plan staged implementation, nie zlecenie stworzenia wszystkich komponentów naraz. WIP istniejącej roadmap zachowany; wąskie cases nie uruchamiają pełnego pipeline.

### Kontrakty prezentacji poszczególnych części

| Część | Zalecana prezentacja | Integralność i interpretacja |
|---|---|---|
| PESTEL | Executive implications + material-factor matrix/cards; timeline gdy horyzont zmienia decyzję | Factor → source/date → mechanism → impact/horizon → uncertainty → implication; bez wymuszonego 0–5 score |
| 5 sił Portera | Industry boundary + pięć grounded pressure assessments; optional force diagram i adjacent evidence | Force → economic mechanism → evidence → value-capture implication; bez średniej/radar chart z invented scores |
| SWOT/TOWS | Compact SWOT + wybrane powiązania findings do strategic options | Internal S/W, external O/T; source finding IDs i inherited confidence; nie wszystkie combinations obowiązkowo |
| Deep competition | Strategic-group overview + comparable evidence matrix + material competitor profiles | Perceptual map tylko przy defensible axes/data; brak fikcyjnych customer perceptions i zamiarów |
| Strategy design | Decision headline → choices/option comparison → rationale/trade-offs → capability/resources → staged roadmap/measures | Traceability finding → proposed/rejected option → choice; nie myli task list ze strategią |
| Marketing strategy | STP/value proposition → brand/channel roles → assumptions/budget/measurement → experiments | Budget/CAC/ROI wyłącznie known inputs lub labelled scenarios; vanity metrics oddzielone od outcomes |

**Nie tworzymy drugiego report engine.** report-composer owns reading flow, profiles i provenance; visual-output-design owns semantic visual encoding i rzeczywisty renderer. Analiza jest upstream: renderer nie może dopisać facts, scores, weights ani causal relationships. Jedna coherent report response, evidence i interpretacja przy danej sekcji; chat default, external deck/PDF/editable file tylko na żądanie. Wąskie zadanie ma wąski profile; czytelność mobile, bez znaczeń opartych wyłącznie na kolorze. Actual renderer + truthful fallback, bez phantom visuals i bez deklaracji client-display PASS. Existing required visual-floor contracts zachowują uczciwy blocked status, gdy brak qualifying renderer.

### Kryteria pilotów

Dwa pionowe przypadki: eCommerce category → marketing strategy oraz organisation/service-business → strategy design → właściwy OAF handoff. Weryfikować niezależnie routing, factual evidence, feasibility/choices, framework selection i section-level presentation. Dodatkowe negatives: narrow PESTEL, known-product economics, execution of existing strategy, one-security research. Testować conflicting/stale data, supplied pack reuse, missing internal evidence i unavailable renderer. Nie utożsamiać atrakcyjnej macierzy z poprawnym wnioskiem; NOT_RUN pozostaje NOT_RUN.

### Nowe zadania wykonawcze

#### STR-01 · P1 · Zdefiniować osobną domenę Strategy i rozliczyć strategy-ea

Typ: domain/specification. Status: PROPOSED. Wielkość: S. Zależności: ENG-01, ENG-06.

**Dlaczego:** Wybór kierunku i sposobu konkurowania ma inny kontrakt niż OAF wykonania, Commerce i Investing.

**Zakres:** Docelowe skills/strategy. Zakres: otoczenie, struktura branży, konkurencja, pozycja, wybory i design. Zmapować historyczny strategy-ea: reuse strategy-challenge; wskazać istniejące OAF i PRO bez migracji działających skills.

**Ukończone, gdy:**

- Jawne trigger/non-trigger PL/EN
- Strategy nie jest obowiązkowym etapem każdej domeny
- Historyczne nazwy nie prowadzą do duplikowania implemented OAF
- Profil i bieżące dane organizacji pozostają w project context

#### STR-02 · P1 · Zbudować strategic-environment-scan z PESTEL

Typ: new skill. Status: PROPOSED. Wielkość: M. Zależności: STR-01.

**Dlaczego:** Potrzebna jest analiza materialnych zmian, a nie lista ogólnych trendów.

**Zakres:** Zakres, geografia i horyzont; PESTEL tylko dla czynników zmieniających decyzję. Factor → evidence → mechanism → exposed entities → impact/horizon → implication. Aktualność i sprzeczności jawne.

**Ukończone, gdy:**

- Źródło/data przy decydujących claims
- Rozróżnienie faktu, interpretacji, scenariusza i unknown
- Brak wymuszonego wypełniania wszystkich sześciu kategorii
- Stop gdy dalszy research nie zmienia opcji lub trzeba przetestować assumption

#### STR-03 · P1 · Zbudować industry-structure-review z 5 siłami Portera

Typ: new skill. Status: PROPOSED. Wielkość: M. Zależności: STR-01.

**Dlaczego:** Atrakcyjny popyt nie oznacza możliwości utrzymania marży lub przechwycenia wartości.

**Zakres:** Najpierw granice branży, buyer, geografia i business model. Następnie rivalry, new entrants, substitutes, buyer/supplier power; causal economic mechanisms i role platforms/complements tam gdzie materialne. Porter nie zastępuje company-level competitive review.

**Ukończone, gdy:**

- Każda ocena force ma uzasadnienie i evidence
- Potencjalni entrants i substitutes są odróżnieni
- Market growth nie kompensuje strukturalnej presji na profitability
- Nie tworzy pozornie precyzyjnego industry attractiveness score

#### STR-04 · P1 · Zbudować competitive-intelligence-review: pogłębiona analiza konkurencji

Typ: new skill + reuse adapter. Status: PROPOSED. Wielkość: L. Zależności: STR-01, ENG-10.

**Dlaczego:** Obecny competition-landscape-review obejmuje produkt/cenę/brand/distribution/acquisition; strategiczny deep dive wymaga więcej niż ponownego wykonania tej tabeli.

**Zakres:** Granice rynku i strategic groups; direct/indirect/substitutes; segmenty, value proposition, model przychodów, zasoby/capabilities, distribution, moat/imitability, ruchy i możliwe reakcje. Reuse istniejącego Commerce evidence pack, jeśli aktualny i zakres zgodny; research wyłącznie gaps. Oddzielać observed move od hypothesis of intent.

**Ukończone, gdy:**

- Znany scope/geografia/as-of
- Każdy profil ma observed facts, interpretations i unknowns
- Ceny/oferty porównywane na zgodnych wariantach i okresach
- Brak marketingowego claim o przewadze jako niezależnego dowodu
- Hipoteza reakcji konkurenta nie jest potwierdzonym zamiarem
- Lekki commerce landscape nie uruchamia automatycznie deep dive

#### STR-05 · P1 · Zbudować strategic-position-review: zasoby, przewagi i ograniczenia

Typ: new skill. Status: PROPOSED. Wielkość: M. Zależności: STR-01.

**Dlaczego:** Strategia potrzebuje odpowiedzi, czy dany podmiot ma zdolność wygrać, niezależnie od atrakcyjności branży.

**Zakres:** Supplied current position/results/resources; VRIO i capability fit warunkowo. Odróżnić istniejące zdolności od aspiracji; koszt pozyskania braków, dependency, right-to-win i defensibility. Dla organizacji reuse OAF capability evidence bez ponownego projektowania organizacji.

**Ukończone, gdy:**

- Internal strengths/weaknesses mają evidence
- Capability assertion nie powstaje z deklaracji marketingowej
- VRIO nie gwarantuje sustainable advantage bez uzasadnienia
- Bez danych wewnętrznych pozycja pozostaje provisional

#### STR-06 · P1 · Zbudować strategic-analysis jako selektywny flow diagnostyczny

Typ: workflow. Status: PROPOSED. Wielkość: L. Zależności: STR-02, STR-03, STR-04, STR-05.

**Dlaczego:** Jeden entrypoint ma zapewnić analizę strategiczną bez obowiązkowego framework parade.

**Zakres:** Question/scope → selected environment/industry/competition/position stages → synthesis → critical uncertainties → handoff. Entry: broad diagnostic, narrow framework/deep competition, supplied evidence. Wynik strategic evidence pack; opcje w analizie są hipotezami, nie zatwierdzoną strategią.

**Ukończone, gdy:**

- Dobiera tylko etapy zmieniające decyzję
- Known competition request może trafić prosto do STR-04
- Supplied aktualny pack pomija zrobiony research
- Registry/channels i required/optional/on_missing jawne przy implementacji
- Brak narzędzi/danych nie jest ukrywany
- Output: ustalenia, mechanizmy, uncertainties, opcje do design/test i next gate

#### STR-07 · P1 · Zbudować strategic-options-design: pogłębiony projekt opcji

Typ: new skill. Status: PROPOSED. Wielkość: L. Zależności: STR-05, STR-06.

**Dlaczego:** Pogłębiony design wymaga realnych wyborów i konsekwencji; lista inicjatyw nie jest strategią.

**Zakres:** Z celów i accepted/provisional evidence pack wypracować 2–4 odmiennych opcji: where-to-play/how-to-win, value proposition, advantage, required capabilities/resources, what-not-to-do i trade-offs. Include keep/defer/no-go gdy viable; wybór wymaga zasobów/ograniczeń lub oznaczonych scenariuszy.

**Ukończone, gdy:**

- Opcje nie są kosmetycznymi wariantami tej samej odpowiedzi
- Każda ma causal rationale, sacrifices, feasibility i evidence links
- Nie wymyśla budżetu/zdolności/mandatu
- Wskazuje strongest viable alternative i co zmieni decyzję
- Output odróżnia rekomendację, hypothesis i user-approved choice

#### STR-08 · P2 · Zbudować strategic-scenario-review i signposts

Typ: new skill. Status: PROPOSED. Wielkość: M. Zależności: STR-07.

**Dlaczego:** Deep strategy design powinien sprawdzać odporność opcji na niepewność, nie udawać jednej prognozy.

**Zakres:** Najważniejsze niezależne uncertainties → kilka spójnych scenariuszy → option robustness → no-regret moves, contingent bets, reversible steps → measurable signposts. Nie wymuszać macierzy 2x2 i prawdopodobieństw.

**Ukończone, gdy:**

- Scenariusze odróżnione od prognoz/faktów
- Assumptions i causal relationships widoczne
- No arbitrary probability ani score
- Każdy material signpost ma obserwowalny warunek i implication
- Dla małej decyzji wystarcza compact sensitivity

#### STR-09 · P1 · Zrealizować istniejący plan strategy-challenge

Typ: reuse planned skill. Status: PROPOSED. Wielkość: M. Zależności: STR-01, ENG-03.

**Dlaczego:** Historyczny strategy-ea już planuje tę metodę; potrzebna jest niezależna kontrola logiki i alternatives.

**Zakres:** Pre-mortem, weakest assumption, missing alternatives, competitor response, evidence contradiction, falsification; kontrola before design approval. Brak własnego pełnego research engine, brak generic critic do każdej odpowiedzi.

**Ukończone, gdy:**

- Challenge wskazuje najmniejszy test/poprawkę
- Nie zamienia interpretacji w potwierdzone fakty
- Nie odrzuca strategii dla stylistycznego upodobania
- Znany severe feasibility/evidence problem widoczny, nie ukryty w average

#### STR-10 · P1 · Zbudować strategy-design: od diagnozy do kompletnej strategii

Typ: workflow. Status: PROPOSED. Wielkość: L. Zależności: STR-06, STR-07, STR-09.

**Dlaczego:** Osobny flow design ma inną odpowiedzialność i success criteria niż analiza.

**Zakres:** Goals/constraints + evidence gate → strategic diagnosis → options → conditional scenarios/challenge → recommended choices → strategic objectives → capability/resource implications → staged validation, measures and review triggers. Entry: analyse-then-design lub supplied evidence. Missing decision-critical data stops final design, while supported sections remain reviewable. Business strategy i funkcjonalne strategie jako explicit modes.

**Ukończone, gdy:**

- Diagnoza nie udaje wyboru kierunku
- Strategy obejmuje choices, differentiation, sacrifices i causal logic, nie tylko task list
- Nie powtarza aktualnej analizy bez potrzeby
- Synthesis oddziela proposed od approved
- Nie projektuje governance/operating model ani inwestycyjnej alokacji
- Warunki stop/handoff i framework selection jawne
- Optional STR-08 ma explicit on_missing

#### STR-11 · P1 · Zbudować marketing-strategy-design jako specjalistę strategy-design

Typ: new specialist + workflow branch. Status: PROPOSED. Wielkość: L. Zależności: STR-04, STR-07, STR-10.

**Dlaczego:** Strategia marketingowa to decyzje o rynku, odbiorcy, pozycjonowaniu i wzroście; nie sam kalendarz contentu ani lista kanałów.

**Zakres:** Business goals → demand/customer evidence → segmentation/targeting/positioning → value proposition/brand → acquisition/retention/channel roles → mix trade-offs → known budget/resources, constraints and measurement → staged experiments. Reuse Commerce demand/differentiation/acquisition/unit-economics gdzie fit, Writing/native tools do downstream execution. Szerszy zakres także dla services/B2B; nie zmuszać non-commerce do commerce calculator.

**Ukończone, gdy:**

- STP i kanały wynikają z dowodów, nie generycznych personas
- Channel plan ma funkcję, rationale, assumptions i trade-offs
- Budżet/CAC/ROI nie są wymyślane; arithmetic w kodzie i unknown jawne
- Cele biznesowe odróżnione od vanity metrics
- Brand, acquisition i retention nie mieszają poziomów strategii i taktyki
- Obsługa B2B/services/eCommerce ma jawne assumptions
- Brak automatycznego uruchomienia kampanii/content/publication

#### STR-12 · P1 · Zaprojektować prezentację raportu PESTEL

Typ: existing composer/renderer profiles. Status: PROPOSED. Wielkość: M. Zależności: STR-02.

**Dlaczego:** Raport ma pomagać odczytać materialność, horyzont, dowody i implikacje poszczególnych czynników.

**Zakres:** Profile w report-composer + semantic payload. Executive implications → material factors by P/E/S/T/E/L → mechanism/impact/horizon/evidence/uncertainty → options/signposts. Matrix/cards/timeline tylko gdy odpowiadają na pytanie; severity/confidence separate, no fake numeric heatmap.

**Ukończone, gdy:**

- Każdy factor ma traceable source i adjacent implication
- Brak nieuzasadnionego 0–5 score
- Framework findings oddzielone od strategy choices
- Inline presentation czytelna desktop/mobile i bez color-only meaning
- Evidence-based visual z units/as-of; uczciwy documented renderer/fallback
- Nie tworzy nowego strategic-report generator

#### STR-13 · P1 · Zaprojektować prezentację 5 sił Portera

Typ: existing composer/renderer profiles. Status: PROPOSED. Wielkość: M. Zależności: STR-03.

**Dlaczego:** Klasyczny schemat ma pokazać causal pressure na ekonomikę branży, a nie arbitralne liczby.

**Zakres:** Boundary header → five-force overview → grounded pressure assessment → evidence/mechanism per force → combined implications for value capture and options. Diagram opcjonalny z adjacent evidence table; pressure ordinal tylko anchored rationale. Brak radar chart z invented scores.

**Ukończone, gdy:**

- Company competitive review nie miesza się z industry forces
- Każda force ma evidence/mechanism i scope
- Wizualny przegląd nie ukrywa niepewności
- Combined conclusion nie jest średnią pięciu score
- Brak renderer nie generuje phantom diagram

#### STR-14 · P1 · Zaprojektować SWOT/TOWS jako syntezę i most do design

Typ: reference + composer profile. Status: PROPOSED. Wielkość: M. Zależności: STR-02, STR-03, STR-04, STR-05, STR-07.

**Dlaczego:** SWOT bez dowodów jest listą opinii; TOWS powinno łączyć ustalenia z konkretnymi wyborami.

**Zakres:** Internal S/W z STR-05, external O/T z environment/industry/competition, stable finding IDs. Compact SWOT → wybrane TOWS links → proposed options → criteria/test. Nie generować obowiązkowo każdej kombinacji SO/ST/WO/WT. Nie wydzielać SWOT w osobny skill bez recurring independent need.

**Ukończone, gdy:**

- S/W i O/T nie są zamienione
- Każda pozycja dziedziczy evidence/uncertainty
- TOWS option ma links do wspierających findings
- Framework nie wzmacnia confidence względem source analysis
- Aktualna synteza nie wymaga ponownego researchu

#### STR-15 · P1 · Zaprojektować prezentację deep competition i strategy design

Typ: existing composer/renderer profiles. Status: PROPOSED. Wielkość: L. Zależności: STR-04, STR-10, STR-11, STR-12, STR-13, STR-14.

**Dlaczego:** Przegląd konkurentów oraz wybranej strategii wymaga czytelnej hierarchii, porównywalnych danych i traceability.

**Zakres:** Deep competition: strategic groups, evidence-backed profile/matrix, differentiation/response, missing facts. Design: choices & trade-offs, option comparison, rationale, capabilities/resources, staged roadmap and measures. Marketing: STP/positioning, channel roles, budgets with known inputs and measurement. Section: finding → evidence → visual → implication → choice; findings link do chosen/rejected options.

**Ukończone, gdy:**

- Perceptual map tylko przy defensible axes/data; nie udaje customer research
- Brak incomparable pricing/score
- Map/diagram/rendering od istniejących tools, bez drugiego dashboarda
- Wizualizacja nie dodaje niezweryfikowanych przewag ani causal claims
- Reader widzi dlaczego opcja została wybrana i co odrzucono
- Narrow task nie wymaga całego report profile
- Chat default, external editable report/deck tylko na żądanie

#### STR-16 · P1 · Zdefiniować handoff Strategy do Commerce/OAF/Investing/Career/Learning

Typ: integration/contracts. Status: PROPOSED. Wielkość: M. Zależności: STR-06, STR-10, CORE-04.

**Dlaczego:** Wspólny wsad strategiczny nie może przejąć downstream decyzji ani zduplikować specialistów.

**Zakres:** Strategic evidence pack: decision/scope/horizon, finding IDs, provenance/as-of, hypotheses, options, assumptions, unknowns, recommended gate, status. Domain adapters, no new global store. Commerce consumes opportunity thesis; OAF goals/capability implications; Investing sector mechanism/scenarios before existing theme/security/portfolio review; Career/Learning competence hypotheses after personal context.

**Ukończone, gdy:**

- Handoff nie przenosi nieudzielonych zgód
- Strategy nie rekomenduje portfolio weights/security trade ani nie udaje underwriting
- Nie duplikuje trend-theme-research
- OAF design wymaga właściwych downstream evidence gates
- Przekazanie tylko gdy użytkowy cel tego wymaga
- Stary lub incompatible pack oznaczony, nie przyjęty silently

#### STR-17 · P1 · Zweryfikować pełne Strategy flow i jakość prezentacji

Typ: evals/pilot/catalog. Status: PROPOSED. Wielkość: L. Zależności: STR-06, STR-10, STR-11, STR-15, STR-16, ENG-04.

**Dlaczego:** Framework completeness i atrakcyjny raport nie dowodzą trafnej analizy ani wykonalnego design.

**Zakres:** Pilot: eCommerce category → marketing strategy, organisation/service business → strategy design → OAF handoff. Dodatkowo standalone deep competition, supplied evidence bypass, narrow PESTEL, existing-strategy execution failure, single-security research, stale/conflicting data, unavailable renderer. PL/EN natural routing, exact-version independent receipts, baseline quality/cost.

**Ukończone, gdy:**

- Real-use pilot i value vs baseline
- Competitor facts nie mieszają się z intentions
- Framework list nie zastępuje choices/feasibility
- Każdy report section zachowuje evidence i supported visuals
- Narrow prompt nie uruchamia pełnego pipeline
- Marketing forecast nie daje invented ROI
- Evals bez rubric leakage i brak runtime evidence pozostaje NOT_RUN
- Catalog/registry/channels aktualizowane dopiero dla rzeczywistych implementations


---

## Hardening addendum — skill-platform controls before broad expansion

**Decision date:** 2026-10-05

Benchmarking the current repository against external Agent Skills implementations identified a narrow set of engineering controls worth adopting without replacing the existing architecture. The current repository remains stronger in eval isolation, exact-version evidence, package provenance, lifecycle and release governance; the purpose of this addendum is to close security and scale-related gaps before the catalog grows substantially.

### Sequencing decision

Treat **ENG-15 → ENG-16**, strengthened **ENG-10**, and **ENG-17** as a near-term **P0 hardening tranche**. Broad net-new skill/domain expansion should not materially outrun these controls. Existing pilots, evidence gathering and already-committed work can continue where they help validate the controls.

### ENG-15 · P0 · Agent Skill Security Scanner

Add an offline/deterministic CI scanner for runtime skill contents. Cover remote fetch-and-execute, obfuscated execution, credential stores and environment access, network calls, credential+network exfiltration shapes, install-time execution lures and unpinned dependency installation. Findings must be machine-readable, tested and consumable by release review. Runtime fixtures and evaluator content must not be confused with shipped runtime content.

### ENG-16 · P0 · Capability and side-effect contract

Declare the capabilities a skill requires or may exercise: network, filesystem, shell/exec, credential classes, external actions/writes and required tools/connectors. Keep portable Agent Skills compatibility; repository-side/generated manifests may hold runtime-specific detail. Validate declared behavior against static observations and channel availability.

### ENG-10 · P0 · Global routing collision gate

Strengthen the existing routing-boundary work rather than create a duplicate task. Add positive/near-miss cases, catalog-wide expected-skill ranking and collision reporting. Lexical similarity is an early-warning sensor only; it never replaces semantic/natural-routing runtime evidence.

### ENG-17 · P0 · Generated machine registry

Generate a registry.json from canonical sources rather than maintaining a second manual catalog. Keep roles distinct: CATALOG.md for humans, registry.json for machines/discovery, capabilities.json for the actually installed runtime/channel state.

### ENG-18 · P1 · Controlled skill improvement

Explore automated improvement only after real failure evidence is sufficient. Do not copy a naive generate-tests → mutate → same-model-score loop. Keep development evals separate from held-out regression/holdout data; optimizer must not see evaluator-only rubrics or the entire holdout corpus. Output a candidate diff and evidence plan, then pass through existing validation, security, routing, runtime pilot and skill-release-review. Never auto-promote.

### Explicit non-change

Do not introduce a rule that every production skill must ship scripts/references/assets. The existing principle remains: add deterministic code, references and assets when the task requires them. A reusable reasoning procedure can still be a valid skill when prose is the correct implementation.


## Decyzja wykonawcza — przeglądy domen po zamknięciu jakości, 6 października 2026

Przyjęta zasada: **nie degradujemy maturity**. Brak aktualnego runtime receipt pozostaje jawną luką dowodową, ale sam w sobie nie zmienia zadeklarowanego maturity istniejącego komponentu. Nie przedłużamy też hurtowo wyjątków ani nie deklarujemy PASS bez obserwacji.

Najpierw zamykamy bieżące procesy/kampanie jakościowe z jawnie zapisanym wynikiem i dowodami. Dopiero potem uruchamiamy przegląd jednej domeny naraz (WIP 1). Pierwszy zakres obejmuje istniejące domeny Meta, Career, Commerce, Investing i OAF; kolejność wybieramy po zamknięciu jakości na podstawie rzeczywistego użycia, ryzyka i zależności. Puste/planned domain directories nie są audytowane jak gotowe produkty.

Każdy domenowy review wiąże dokładne source/runtime versions; sprawdza odpowiedzialność i sąsiednie routingi, zależności, testy/evidence, security/capabilities, prywatność i nieufne wejścia oraz zgodność kanałów. Wynikiem dla każdego komponentu jest jedna z decyzji: retain, adopt, adapt, update, defer albo no-change, wraz z uzasadnieniem, minimalnym zakresem, testami, zależnościami i kryteriami akceptacji. Sam review nie wdraża zmian, nie zmienia maturity ani nie autoryzuje publikacji; każda aktualizacja przechodzi istniejący lifecycle.

Backlog: `ENG-19` ustala gate/protokół, `DOM-01`–`DOM-05` prowadzą domeny, `ENG-20` utwardza supply chain/CI/publikację, a `ENG-21` porządkuje minimalne governance publicznego repo. `ENG-15` i `ENG-17` zmieniono tak, by rozbudowywały istniejący skaner i katalog, zamiast tworzyć duplikaty.


## Addendum — free-first test platform decision, 2026-10-09

The current backlog already contains the core mechanics for eval isolation, local execution, browser E2E, failure injection and CI hardening, but it lacked one explicit target architecture for the test toolchain. **ENG-22 (P1)** closes that gap without creating a parallel eval framework.

Target sequencing: keep `evals/`, receipts and campaign protocol canonical; integrate Promptfoo Community as a pinned regression harness over the existing runner; layer GitHub Actions by cost/coverage; emit vendor-neutral OpenTelemetry/OpenInference traces; inspect them locally in Phoenix OSS; add trajectory and forbidden-action assertions; and introduce persistent TEST storage only when a real persistence case requires it. No additional ChatGPT plugin or paid evaluation SaaS is part of the baseline.
