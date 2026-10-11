# Paczka 2026-10-10 — Lab 0.34.0 candidate

Zakres i dokładne head SHA PR-ów: `bundle.json`. Ta paczka integruje 19 PR-ów na osobnej gałęzi; #146 jest zastąpiony przez istniejący kod main. Milestone i etykieta wskazują zakres częściowych zmian, nie zamknięcie całych zadań ENG/AUD.

## Warstwy i bramki

1. Integracja źródeł: 64 skille, 19 workflowów. Zachowano oba zestawy testów przy konfliktach i wygenerowano katalog z połączonego źródła.
2. Statyczna walidacja: contracts, security, capabilities, readiness, routing/isolation, testy deterministyczne i buildery. Historyczne R18 pozostaje bez zmian; jego exact-source gate blokuje nowe zachowanie. Nie wolno pomijać tej kontroli przy merge/promotion.
3. Lab 0.34.0: wersja kandydacka; manifest ustala dokładny source SHA i digests. Dziesięć nowych draft skills i dwa nowe workflowy pozostają poza runtime allowlistą. Nie zmieniamy maturity ani production snapshot.
4. Prywatny Cloud Next: osobny source SHA Site, embedded Lab source SHA, release ID, catalog/tool-schema digests i numer wersji. Publikacja kandydata wymaga oficjalnego Sites workflow; GitHub Release nie wdraża MCP.
5. Kampania runtime: oddzielny świeży przebieg, niezależny executor bez rubryk, niezależna ocena rzeczywistych outputów i traces. Żaden obecny test modelowy nie ma PASS.
6. Merge/promotion: dopiero po wymaganym CI, rzeczywistych dowodach dla zmienionego zachowania, bez unresolved high-severity failure i z review związanym z dokładną rewizją. Draft GitHub Release nie jest produkcyjnym wydaniem.

## Przygotowanie i odtwarzanie

Po commicie całej paczki, na czystym checkoutcie:

```sh
python scripts/package/build_lab_plugin.py --output .tmp/lab-0.34.0
python scripts/package/artifact_validation.py .tmp/lab-0.34.0 --lab
python scripts/eval/validate_isolation.py --artifact .tmp/lab-0.34.0
python scripts/eval/release_bundle.py prepare --lab .tmp/lab-0.34.0 --output ../campaign-release-2026-10-10
python scripts/eval/release_bundle.py validate --output ../campaign-release-2026-10-10
```

Generator obejmuje wszystkie authored cases ze źródeł, wszystkie istniejące pary input/rubric oraz loader parity dla wszystkich entrypointów Lab. Pliki historyczne nie są edytowane. Queue i rubryki należą do kontrolera; executor otrzymuje wyłącznie osobny input. Nie przekazuj executorowi tego czatu, queue, test YAML ani całego archiwum kontrolera.

Przed wykonaniem kontroler musi przejrzeć fixture_quality/target/mode. Historyczne przypadki z innym profilem lub nieznanym targetem wymagają nowej jawnej rubryki/overlay we własnym przebiegu; nie zmieniaj oryginału. Weak/generic assertions wymagają doprecyzowania przed wynikiem, nie po jego obserwacji. Definicje source-only nie są testami zainstalowanego MCP: wykonuj je osobno, dostarczając tylko właściwe instrukcje i zasoby, albo oznacz NOT_RUN.

## Kolejność kampanii

1. Preflight: zweryfikuj lock/source, manifest Lab, narzędzia i rzeczywisty runtime_info. Gdy live MCP wskazuje poprzednią wersję, nie oceniaj nowej paczki na jego podstawie. Zapisz nowy `observed-baseline.json` zawierający surowe runtime_info i list_skills, z czasem UTC. Nie kopiuj oczekiwanej tożsamości do pola observed.
2. P0: deny/no-save, explicit isolated write, unknown target, unavailable canonical read, failed write, duplicate append, brak nieautoryzowanej aktywacji tezy/policy/transaction; `NOT_WRITTEN`, `SAVED`, `WRITE_FAILED` i `BLOCKED_CANONICAL_READ` oceniaj po rzeczywistym trace. Testuj thesis-monitor, attention-triage oraz trzy zmienione workflowy i ich sąsiadów.
3. Wszystkie loader-parity: porównaj pełne instrukcje i dozwolone references z Lab. Sprawdź workflow reference, brak tests/evals/rubrics, stabilność digestów i błędy dla unknown skill/path traversal.
4. Routing: naturalny i explicit, positive/negative/near-miss PL/EN, uppercase/lowercase, no-skill oraz granice investment attention/security/opportunity/observation. `routed_only` nie potwierdza wykonania workflowu.
5. Behavior: wszystkie authored i runtime fixtures, pozostałe dotknięte dependencies i flowy. Każdy test używa świeżej sesji; zachowaj pierwszą próbę i każdą naprawę jako nowy run.
6. Report/Presentation: source-only kontrakty; trzy różne profile raportu i prezentacji. Rzeczywista creation/edit/export capability, prywatność, niezależna kontrola content vs layout, DOCX/PDF/PPTX round-trip, edytowalność, links/TOC/citations, render wszystkich stron/slajdów. Brak provider action oznacza NOT_RUN/BLOCKED, nie PASS. Syntetyczne wejścia nie zawierają zgody na publiczne udostępnianie.
7. Output router: deterministic tests oraz niezależne natural-language intent → preclassified input → policy → owner execution, combined outputs, oddzielne delivery states i brak niezamówionej publikacji. Planner nie jest modelem klasyfikującym intencję.
8. Cloud integracja: charts — payload/dane/accessibility i rzeczywista widoczność w Chat osobno; błędy rendererów, route-only stop, workflow references. Desktop/Work/Web w osobnych próbach; mobile skills-only bez obietnicy MCP.

## Dane, ślady i ocena

Używaj syntetycznych fixtures. Realne write/read-back wymagają wskazanego izolowanego test store/namespace, rzeczywistego konektora, autoryzacji i cleanup. Brak store nie upoważnia do użycia production ani alternatywnej bazy. Zapis do pamięci lub mock to dowód symulacji, nie PASS integracji.

Każdy run zapisuje case/input hash, source/Lab/Site identity, model/provider/reasoning/surface, UTC start/end, rzeczywiste tools i ich argumenty/wyniki bez sekretów, final answer, pliki/read-back oraz screenshot tam, gdzie potrzebna jest obserwacja klienta. Wyniki w nowym `runs/<run-id>/`; nigdy nie nadpisuj poprzednich receipts. Niezależny evaluator ocenia każdą assertion z odniesieniem do dowodu i wystawia PASS/FAIL/REVIEW_REQUIRED/NOT_RUN osobno dla behavior, integration, identity i client_display. Dopiero zweryfikowany import zgodny z istniejącym receipt protocol może służyć formalnym release gates; przygotowany queue nie jest receipt.

Raport końcowy: macierz PR → komponent → przypadki → wynik → defekt → retest, coverage per component/surface, oddzielne source-only i observed installed cases, lista blokad i aktualne CI. Zachowaj historical R18 oraz runtime receipts. Nowy aktywny baseline i finalny release review powinny być osobną zmianą po wykonaniu kampanii. Nie zamykaj całego ticketu na podstawie częściowej implementacji.

## Oznaczenia GitHub i rollback

Milestone `2026-10-10 | Lab 0.34.0 candidate` i label `release:2026-10-10` wskazują paczkę; `release:partial-scope` na ticketach oznacza, że obejmuje tylko opisany increment. PR #146 oznaczony jako superseded. Draft prerelease przechowuje konkretne archiwa i SHA; nie publikuj go jako verified production release przed gate review.

Rollback Cloud Next: użyj poprzedniej natywnej wersji tego samego prywatnego Site i zgodnych runtime environment identity, zachowując Site/plugin/access. Nie podpinaj nowego archiwum do starego SHA. GitHub production branch, dane i historyczne kampanie pozostają zachowane.
