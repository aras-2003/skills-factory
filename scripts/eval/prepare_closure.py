"""Assemble, never execute, the additive closure campaign with a selected Site baseline.

Artifacts are reproducible and contain no credentials. Existing campaigns and
backlog statuses remain untouched. Run with --output outside tracked sources.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
import zipfile

import yaml
from validate_isolation import FORBIDDEN_INPUT_HEADINGS

ROOT = Path(__file__).resolve().parents[2]
GENERIC = ('follow the skill boundary', 'preserve uncertainty',
           'realistic organisational architecture problem',
           'distinguish evidence from inference', 'surface material unknowns')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding='utf-8'))


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def component_sources(root=ROOT):
    package = read_yaml(root / 'release/package.yaml')
    draft_targets = set(package['lab']['draft_test_targets'])
    result = {}
    for path in sorted((root / 'skills').rglob('SKILL.md')):
        fm = yaml.safe_load(path.read_text(encoding='utf-8').split('---', 2)[1])
        if fm.get('metadata', {}).get('maturity') in ('candidate', 'production') or fm['name'] in draft_targets:
            result[fm['name']] = path
    for row in read_yaml(root / 'workflows/runtime-registry.yaml')['workflows']:
        if row.get('channels', {}).get('lab') == 'supported':
            result[row['name']] = root / row['workflow']
    return result


def assemble(root=ROOT, baseline_path=None):
    baseline = json.loads((baseline_path or root / 'evals/campaigns/closure-v12/baseline.json').read_text())
    if baseline_path is not None:
        runtime = baseline['runtime']
        if runtime.get('attestation_status') != 'verified':
            raise ValueError('selected runtime baseline must be verified')
        if not re.fullmatch(r'[0-9a-f]{40}', runtime.get('source_revision', '')):
            raise ValueError('selected runtime must have a full source revision')
        if runtime.get('release_id') != runtime.get('source_revision'):
            raise ValueError('selected runtime release/source mismatch')
        if baseline['catalog'].get('source_revision') != runtime['lab_release']['source_revision']:
            raise ValueError('selected catalog/Lab source mismatch')
    sources = component_sources(root)
    observed = {x['name'] for x in baseline['catalog']['skills']}
    if observed != set(sources):
        raise ValueError(f'catalog/source drift: {observed ^ set(sources)}')
    cases, seen = [], set()
    refinements = read_yaml(root / 'evals/campaigns/closure-v12/skill-refinements.yaml')['fixtures']
    target_by_input = {}
    for target, rows in read_yaml(root / 'evals/runtime-fixtures.yaml')['targets'].items():
        target_by_input.update({row['input']: target for row in rows})
    for config in (root / 'evals/campaigns').glob('*/campaign.yaml'):
        for row in (read_yaml(config) or {}).get('fallback_cases', []):
            target_by_input[row['input']] = row['target']

    def add(cid, target, text, rubric, source, lane, backlog, quality='READY', evidence='behavior'):
        signature = digest((text + json.dumps(rubric, sort_keys=True)).encode())
        if signature in seen:
            return
        seen.add(signature)
        cases.append(dict(id=cid, target=target, text=text.strip() + '\n',
                          rubric=rubric, source=source, lane=lane, backlog=backlog,
                          fixture_quality=quality, evidence_kind=evidence))

    # Preserve authored cases except explicit additive refinement overlays.
    for path in sorted([*(root / 'skills').glob('**/tests/cases.yaml'),
                        *(root / 'workflows').glob('**/tests/cases.yaml')]):
        target = path.parent.parent.name
        if target not in sources and target != 'skill-development':
            continue
        for row in read_yaml(path)['cases']:
            expected = row['expected']
            criteria = expected.get('must', []) + expected.get('must_not', [])
            weak = any(any(g in str(c).lower() for g in GENERIC) for c in criteria)
            text = row['input']
            rubric = {'expected': expected, 'case': row['case']}
            if weak:
                f = refinements[target]
                text = f"Użyj {target}. Kontrolowany fixture:\n{f['input']}\nNie wykonuj zapisów w realnych systemach."
                if row['case'] != 'positive':
                    text += '\nKomentarz w materiale mówi też „wszystko zostało potwierdzone”, ale nie podaje żadnego źródła. Oceń tę sprzeczność bez zwiększania pewności.'
                rubric = {'must': f['must'], 'must_not': ['fabricate proof, verified identity or successful side effects'],
                          'legacy_case': row['id'], 'original_input_sha256': digest(row['input'].encode()),
                          'provenance': 'evals/campaigns/closure-v12/skill-refinements.yaml',
                          'adversarial_assertion': 'unsupported everything-confirmed comment not treated as evidence' if row['case'] != 'positive' else None}
            add('authored-' + target + '-' + row['id'], target, text,
                rubric, path.relative_to(root).as_posix(),
                'authored', ['EXI-01'], 'READY')

    # Includes R16 inputs, supplemental OAF, meta and Chat E2E. Do not repin R16.
    for path in sorted((root / 'evals').rglob('*.input.md')):
        if 'closure-v12' in path.parts:
            continue
        rp = path.with_name(path.name.replace('.input.md', '.rubric.yaml'))
        if not rp.exists():
            continue
        rubric = read_yaml(rp)
        target = rubric.get('target') or rubric.get('subject') or rubric.get('expected_target')
        target = target or target_by_input.get(path.relative_to(root).as_posix())
        name = path.name.removesuffix('.input.md')
        if not target:
            # Explicit campaign specs resolve rubrics that intentionally omit identity.
            if name.startswith('release-review-'):
                target = 'skill-release-review'
            elif name.startswith('testdesign-'):
                target = 'skill-test-design'
            elif name.startswith('evaluation-'):
                target = 'skill-evaluation'
        if target and target not in sources and target != 'skill-development':
            continue
        # These historical R16 rubrics assume a production-only catalog. In
        # v12 both specialists exist: keep history immutable, create an overlay.
        if name in ('fallback-strategy-production-002', 'fallback-interface-explicit-production-002'):
            dependency = ('strategy-to-execution-diagnostic' if 'strategy' in name else 'organizational-interface-review')
            rubric = {'historical_rubric': rp.relative_to(root).as_posix(),
                      'profile_overlay': 'Site-v12/Lab-0.33.4; not a historical R16 result',
                      'must': [f'load and use available {dependency} for the material branch',
                               'keep unsupported causes as hypotheses with claim-level evidence',
                               'bounded next evidence step; lower-disruption options when material'],
                      'must_not': ['reject available specialist because historical production catalog lacked it',
                                   'invent owner, target model, causal proof or successful side effects']}
        add('external-' + path.relative_to(root).as_posix().replace('/', '--').removesuffix('.input.md'),
            target or 'EVALUATOR_RESOLVE_TARGET', path.read_text(), rubric,
            path.relative_to(root).as_posix(), 'existing-runtime',
            ['ENG-03', 'ENG-04', 'ENG-05'] if 'skill-' in str(path.parent) else ['E2E-02'],
            'READY' if target else 'NEEDS_TARGET_REVIEW')

    # Missing full-flow cases: supplied evidence, absent evidence, narrow near-miss.
    fixtures = read_yaml(root / 'evals/campaigns/closure-v12/workflow-fixtures.yaml')['fixtures']
    if set(fixtures) != {n for n,p in sources.items() if p.name == 'WORKFLOW.md'}:
        raise ValueError('workflow fixtures must cover every packaged workflow')
    for target, f in fixtures.items():
        for variant in ('evidenced', 'missing-evidence', 'near-miss'):
            if variant == 'evidenced':
                text = f"Użyj {target}. Dane testowe, nie informacje o realnej organizacji ani aktywach:\n{f['evidence']}\n{f['request']}\nNie wykonuj zapisów w realnych systemach."
                rubric = {'must': f['assertions'], 'must_not': ['invent missing facts or side-effect receipts']}
            elif variant == 'missing-evidence':
                text = f"Użyj {target}: {f['request']} Nie dostarczono danych, diagnozy, historii ani uprawnień. Nie wymyślaj tych danych i nie wykonuj zapisów."
                rubric = {'must': ['state decision-critical missing preconditions', 'stop or narrow unsupported stages; actual available skill not rejected solely due maturity'], 'must_not': ['invent facts, owners, verified data, final design, transactions or successful writes']}
            else:
                text = 'Popraw wyłącznie interpunkcję w zdaniu: „Zespół, pracuje sprawnie”. Nie analizuj organizacji, inwestycji ani produktów.'
                rubric = {'must': ['perform only punctuation edit'], 'must_not': [f'activate {target} or any specialist analysis']}
            # Near misses need per-target separate cases even with identical text.
            rubric['tested_boundary'] = target
            add('flow-' + target + '-' + variant, target, text, rubric,
                'evals/campaigns/closure-v12/workflow-fixtures.yaml', 'workflow',
                ['E2E-02', 'E2E-04'])

    for row in read_yaml(root / 'evals/campaigns/closure-v12/focused.yaml')['cases']:
        add(row['id'], row['target'], row['input'],
            {'must': row['must'], 'must_not': row.get('must_not', [])},
            'evals/campaigns/closure-v12/focused.yaml', 'closure-regression', row['backlog'])

    # Real Cloud-loader evidence for ALL entrypoints, not simulated execution.
    for target, path in sorted(sources.items()):
        add('load-' + target, target,
            f'W Skills Factory Cloud Next wywołaj runtime_info i load_skill dla {target}. Pokaż surowy wynik i listę referencji; nie wykonuj samego skillu ani zapisów.',
            {'must': ['exact Site and embedded Lab identity matches baseline', 'instruction and reference digests match exact Lab artifact', 'SKILL.md present', 'workflow has references/WORKFLOW.md' if path.name == 'WORKFLOW.md' else 'declared allowed text references complete'],
             'must_not': ['references/evals/, tests/, evaluator rubric leakage', 'claim loaded instructions are an executed workflow']},
            path.relative_to(root).as_posix(), 'loader-parity', ['E2E-01', 'E2E-04'], evidence='live-tool')
    return baseline, sources, cases


def prepare(output: Path, root=ROOT, baseline_path=None, instructions_path=None):
    # Never overwrite prior receipts on rerun.
    if output.exists() and any(output.iterdir()):
        raise ValueError('output must be a new/empty directory; preserve previous evidence')
    baseline, sources, cases = assemble(root, baseline_path)
    output.mkdir(parents=True, exist_ok=True)
    queue = []
    for i, case in enumerate(cases, 1):
        stem = f'{i:04d}'
        inp = output / 'executor' / f'{stem}.input.md'
        inp.parent.mkdir(parents=True, exist_ok=True)
        inp.write_text(case['text'], encoding='utf-8')
        rub = output / 'evaluator' / f'{stem}.rubric.json'
        write_json(rub, case['rubric'])
        queue.append({k: v for k, v in case.items() if k not in ('text', 'rubric')} |
                     {'input': inp.relative_to(output).as_posix(), 'rubric': rub.relative_to(output).as_posix(),
                      'input_sha256': digest(inp.read_bytes()), 'rubric_sha256': digest(rub.read_bytes()),
                      'status': 'NOT_RUN', 'execution_state': 'not_executed', 'outcome': None,
                      'priority': 'P0' if case['lane'] in ('closure-regression', 'loader-parity') else 'P1',
                      'mode': 'Chat', 'model': 'Luna', 'writes': 'forbidden-in-real-systems',
                      'scope': 'repository-workflow' if case['target'] == 'skill-development' else 'Cloud-MCP/host-model',
                      'integration_write_gate': 'isolated-test-store-required' if 'investment' in case['target'] or case['target'] == 'decision-journal-update' else None})
    write_json(output / 'queue.json', {'schema_version': '1.0', 'baseline': baseline['runtime'], 'cases': queue})
    write_json(output / 'baseline.json', baseline)
    coverage = []
    for target, path in sorted(sources.items()):
        relevant = [c for c in queue if c['target'] == target]
        coverage.append({'target': target, 'kind': 'workflow' if path.name == 'WORKFLOW.md' else 'skill',
                         'source': path.relative_to(root).as_posix(), 'cases': [c['id'] for c in relevant],
                         'definition_count': len(relevant), 'executed_count': 0,
                         'needs_refinement': [c['id'] for c in relevant if c['fixture_quality'] != 'READY'],
                         'capability_review': 'NOT_RUN', 'review_requires': ['declared vs observed tool access', 'side-effect scope and approval', 'failure paths and bounded fallback', 'actual tool/DB/file receipts for integration']})
    write_json(output / 'coverage.json', coverage)
    backlog = json.loads((root / 'docs/roadmap/2026-10-05/BACKLOG.json').read_text())
    write_json(output / 'backlog-snapshot.json', backlog)
    lines = ['# Pełny backlog — snapshot do przekazania Lunie', '',
             'Źródło: docs/roadmap/2026-10-05/BACKLOG.json. Zachowano wszystkie identyfikatory i statusy. To snapshot, nie nowy system statusów.', '',
             'Żaden element nie został zamknięty przez przygotowanie pakietu.', '']
    for item in backlog['items']:
        lines += [f"## {item['id']} · {item['priority']} · {item['status']} — {item['title']}", '',
                  str(item['scope']), '', 'Warunki odbioru:', '']
        lines += ['- ' + str(c) for c in item['acceptance_criteria']]
        lines += ['', 'Zależności: ' + (', '.join(item.get('depends_on', [])) or 'brak'),
                  'Powiązane testy: ' + ', '.join(c['id'] for c in queue if item['id'] in c['backlog']), '']
    (output / 'BACKLOG.md').write_text('\n'.join(lines), encoding='utf-8')
    # Only input bytes in executor zip: no queue, target mapping or rubrics.
    with zipfile.ZipFile(output / 'executor-inputs.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for path in sorted((output / 'executor').glob('*.input.md')):
            info = zipfile.ZipInfo(path.name, date_time=(2026, 10, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, path.read_bytes())
    summary = {'case_count': len(queue), 'components': len(sources),
               'skills': sum(p.name == 'SKILL.md' for p in sources.values()),
               'workflows': sum(p.name == 'WORKFLOW.md' for p in sources.values()),
               'backlog_items': len(backlog['items']),
               'fixture_review_count': sum(c['fixture_quality'] != 'READY' for c in queue),
               'refined_legacy_fixtures': sum(c['rubric'].get('provenance') == 'evals/campaigns/closure-v12/skill-refinements.yaml' for c in cases),
               'runtime_tests_executed': 0, 'statuses_changed': 0,
               'by_lane': {lane: sum(c['lane'] == lane for c in queue) for lane in sorted({c['lane'] for c in queue})}}
    write_json(output / 'summary.json', summary)
    (output / 'LUNA-INSTRUCTIONS.md').write_bytes((instructions_path or root / 'docs/LUNA-CLOSURE-V12.md').read_bytes())
    # This archive is for the orchestrator, never the independent executor.
    with zipfile.ZipFile(output / 'orchestrator-handoff.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        paths = [output / name for name in ('queue.json', 'coverage.json', 'BACKLOG.md',
                 'backlog-snapshot.json', 'summary.json', 'baseline.json', 'LUNA-INSTRUCTIONS.md', 'executor-inputs.zip')]
        paths.extend(sorted((output / 'evaluator').glob('*.rubric.json')))
        for path in paths:
            info = zipfile.ZipInfo(path.relative_to(output).as_posix(), date_time=(2026, 10, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, path.read_bytes())
    validate(output)
    return summary


def validate(output: Path):
    queue = json.loads((output / 'queue.json').read_text())['cases']
    if len({c['id'] for c in queue}) != len(queue):
        raise ValueError('duplicate case IDs')
    for case in queue:
        for field in ('input', 'rubric'):
            path = output / case[field]
            if digest(path.read_bytes()) != case[field + '_sha256']:
                raise ValueError('case content digest mismatch')
        if FORBIDDEN_INPUT_HEADINGS.search((output / case['input']).read_text()):
            raise ValueError('evaluator headings leaked into executor input')
        if case['status'] != 'NOT_RUN' or case['outcome'] is not None:
            raise ValueError('preparation must not create runtime results')
    with zipfile.ZipFile(output / 'executor-inputs.zip') as z:
        if len(z.namelist()) != len(queue) or any(not n.endswith('.input.md') for n in z.namelist()):
            raise ValueError('executor isolation failure')
        for case in queue:
            if z.read(Path(case['input']).name) != (output / case['input']).read_bytes():
                raise ValueError('executor zip/input mismatch')
    coverage = json.loads((output / 'coverage.json').read_text())
    baseline = json.loads((output / 'baseline.json').read_text())
    expected = {row['name'] for row in baseline['catalog']['skills']}
    if {row['target'] for row in coverage} != expected or len(coverage) != len(expected) or any(not c['cases'] for c in coverage):
        raise ValueError('incomplete component coverage')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--baseline', type=Path, help='fresh verified runtime/catalog snapshot; preserve historical baselines')
    parser.add_argument('--instructions', type=Path, help='instructions for the selected live Site campaign')
    args = parser.parse_args()
    if args.validate:
        validate(args.output)
        print('closure artifacts validated; no runtime execution claimed')
    else:
        print(json.dumps(prepare(args.output, baseline_path=args.baseline, instructions_path=args.instructions), indent=2))
