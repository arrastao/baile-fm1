#!/usr/bin/env python3
"""Check storage, immutable upstream boundaries and Windows wrapper assumptions."""
from pathlib import Path
import hashlib,json,re,subprocess
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'sdk/manifest.json').read_text())
for name,digest in manifest['files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
sha=json.loads((root/'baile-layout.json').read_text())['upstream_commit']
for directory in ['sdk','app/board','app/synth','web/engine','web/synth','third_party']:
    changed=subprocess.check_output(['git','diff',sha,'--',directory],cwd=root)
    assert not changed,directory
header=(root/'app/instrument.h').read_text()
offset=int(re.search(r'GROOVE_SAMPLE_OFFSET = (\d+)',header)[1]);size=int(re.search(r'GROOVE_SAMPLE_BYTES = (\d+)',header)[1])
assert offset+size==json.loads((root/'baile-layout.json').read_text())['user_bytes']==405504
script=(root/'sdk/Build.ps1').read_text()
for needle in ["$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))",'$sdk = $PSScriptRoot','user_bytes=536576',
               "Add-Type -Path (Join-Path $sdk 'Package.cs')",'[FM1.Package]::Create',
               "    Run (Join-Path $bin 'pi32v2-ld.exe') $link",'(V(?:0[1-9]|[1-9][0-9]{1,2}))']:
    assert script.count(needle)==1,needle
assert (root/'sdk/Package.cs').read_text().count('UserSize = 536576')==1
art=(root/'app/baile_art.h').read_text()
for name,height in [('boot',160),('tamborzao',38),('voltmix',38),('bolha',38)]:
    runs=list(map(int,re.search(r'art_'+name+r'\[\]=\{([^}]+)',art)[1].split(',')))
    assert sum((v>>5)+1 for v in runs)==160*height
assert 'mandelao' not in art
print('SDK/engine/board unchanged; asset images valid; storage and build inputs consistent.')
