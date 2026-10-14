import argparse
import os,sys,json,hashlib,importlib.util
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('extracted_lab_plugin')
parser.add_argument('artifact_zip')
parser.add_argument('pinned_draft_source', nargs='?')
parser.add_argument('--site-root', type=Path, default=Path(__file__).resolve().parents[1])
args=parser.parse_args()
artifact=Path(args.extracted_lab_plugin).resolve()
archive=Path(args.artifact_zip).resolve()
site_root=args.site_root.resolve()
os.environ['PLUGIN_ROOT']=str(artifact)
spec=importlib.util.spec_from_file_location('catalog',artifact/'mcp/skill_catalog.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
manifest=json.loads((artifact/'release-manifest.json').read_text())
assert len(manifest['source_revision'])==40
components={c['name']:c for c in manifest['components']}
rows=[]
for entry in m.entries():
    s=m.load_skill(entry['name']); c=components[s['name']]
    s.update(kind=c['kind'],instruction_sha256=hashlib.sha256(s['instructions'].encode()).hexdigest())
    s.pop('execution_mode');s.pop('source_revision')
    s['reference_files']={r['path']:r['content'] for r in s['reference_files']}
    surface_digest=hashlib.sha256()
    for path,content in sorted({'SKILL.md':s['instructions'],**s['reference_files']}.items()):
        surface_digest.update(path.encode()+b'\0'+content.encode()+b'\0')
    s['host_surface_sha256']=surface_digest.hexdigest()
    assert '## Lab runtime eval inputs' not in s['instructions']
    rows.append(s)
release={k:manifest[k] for k in ('channel','version','source_revision','release_id','payload_content_sha256')}
release.update(skill_count=len(rows),catalog_digest=m.catalog_digest(),artifact_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
assert len(rows) == len(components) and {row['name'] for row in rows} == set(components), 'Lab catalog must match every manifest component'
draft_release=None
if args.pinned_draft_source:
    draft_spec=importlib.util.spec_from_file_location('draft_catalog',Path(__file__).with_name('draft-catalog.py'))
    draft_module=importlib.util.module_from_spec(draft_spec);draft_spec.loader.exec_module(draft_module)
    draft_release=draft_module.add_drafts(args.pinned_draft_source,rows)
runtime_digest=hashlib.sha256('\n'.join(row['name']+':'+row['content_sha256'] for row in sorted(rows,key=lambda row:row['name'])).encode()).hexdigest()
runtime_release={**release,'channel':'private-lab-with-drafts' if draft_release else 'lab','skill_count':len(rows),'catalog_digest':runtime_digest,'artifact_scope':'base_lab_with_extension' if draft_release else 'complete_lab'}
rows.sort(key=lambda row:row['name'])
out=site_root/'lib/skill-catalog.ts'
out.write_text('// Generated from the complete source-bound Lab artifact; evaluator material excluded.\nexport const LAB_RELEASE = '+json.dumps(release,ensure_ascii=False)+' as const;\nexport const DRAFT_RELEASE = '+(json.dumps(draft_release,ensure_ascii=False)+' as const' if draft_release else 'null')+';\nexport const RUNTIME_RELEASE = '+json.dumps(runtime_release,ensure_ascii=False)+' as const;\nexport const SKILL_CATALOG = '+json.dumps(rows,ensure_ascii=False)+' as const;\n')
print(json.dumps(runtime_release))
