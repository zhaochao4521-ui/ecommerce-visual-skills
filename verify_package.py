"""Verify the two portable public skill packages using Python's standard library."""
from pathlib import Path
import hashlib,json,posixpath,re

ROOT=Path(__file__).resolve().parent
SKILLS=['ecommerce-planning','ecommerce-image-production']

def verify():
    errors=[]
    manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    expected=manifest['files']
    actual={p.relative_to(ROOT).as_posix():p for p in ROOT.rglob('*')
            if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts
            and p.name!='manifest.json'}
    if set(expected)!=set(actual):errors.append('Unexpected or missing files')
    for rel,meta in expected.items():
        f=actual.get(rel)
        if not f:continue
        data=f.read_bytes()
        if hashlib.sha256(data).hexdigest()!=meta['sha256'] or len(data)!=meta['bytes']:
            errors.append('Integrity mismatch: '+rel)
    for name in SKILLS:
        base=ROOT/'skills'/name
        entry=base/'SKILL.md'
        text=entry.read_text(encoding='utf-8')
        if not text.startswith('---\nname: '+name+'\n'):errors.append('Invalid entry: '+name)
        if not (base/'agents/openai.yaml').is_file():errors.append('Missing agent metadata: '+name)
        for f in base.rglob('*'):
            if f.is_symlink():errors.append('Symlink: '+str(f.relative_to(ROOT)))
            if not f.is_file() or f.suffix!='.md':continue
            for target in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8')):
                if target.startswith(('https:','http:','#')):continue
                dest=(f.parent/target.split('#')[0]).resolve()
                if not dest.is_relative_to(base.resolve()):errors.append('External skill dependency: '+target)
                elif not dest.is_file():errors.append('Broken link: '+target)
    result={'ok':not errors,'skills':len(SKILLS),'verified_files':len(expected),'errors':errors}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if not errors else 1

if __name__=='__main__':raise SystemExit(verify())
