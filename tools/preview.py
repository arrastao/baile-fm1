#!/usr/bin/env python3
"""Portable preview only; hardware builds use the unmodified sdk/Build.ps1."""
import argparse, base64, hashlib, html, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('target', choices=['host', 'web'])
p.add_argument('--wasi-sdk', type=Path)
a = p.parse_args()
manifest = json.loads((ROOT/'sdk/manifest.json').read_text())
for name, digest in manifest['files'].items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
        raise SystemExit('SDK integrity failure: '+name)
out = ROOT/'build'/a.target
out.mkdir(parents=True, exist_ok=True)
sources = sorted(str(f) for folder in ['app','web','third_party/synth']
                 for f in (ROOT/folder).rglob('*.c') if 'board' not in f.parts)
flags = ['-std=c11','-O2','-fwrapv','-fno-fast-math','-ffp-contract=off',
         '-DFM1_HOST_TEST','-DFM1_OPEN_WEB','-Wno-unknown-attributes']
flags += ['-I'+str(ROOT/d) for d in ['web/engine','web/synth','third_party/synth','sdk/include','app/synth','app']]
if a.target == 'host':
    optional = out/'optional.c'
    optional.write_text('void groove_midi_panel_reset(void) {}\nvoid groove_midi_panel_track_reset(unsigned t) {(void)t;}\n')
    flags += ['-dynamiclib'] if sys.platform == 'darwin' else ['-shared','-fPIC']
    result = out/('baile.dylib' if sys.platform == 'darwin' else 'baile.so')
    subprocess.run(['clang',*flags,*sources,str(optional),'-lm','-o',str(result)],check=True)
else:
    if not a.wasi_sdk: p.error('--wasi-sdk must point to WASI SDK 27')
    result = out/'baile.wasm'
    subprocess.run([str(a.wasi_sdk.resolve()/'bin/clang'),*flags,'-mexec-model=reactor',*sources,
                    '-Wl,--strip-all','-Wl,-z,stack-size=131072','-Wl,--initial-memory=4194304',
                    '-Wl,--max-memory=33554432','-o',str(result)],check=True)
    payload = dict(schema=1, release_version='BAILE rebuild preview',
                   sha256=hashlib.sha256(result.read_bytes()).hexdigest(),
                   bytes=result.stat().st_size,data=base64.b64encode(result.read_bytes()).decode())
    page = (ROOT/'sdk/Update.html.in').read_text()
    replacements = {'/*FM1_PAYLOAD*/':'const FM1_PACKAGE = null;',
        '/*FM1_SIMULATOR*/':'const FM1_SIMULATOR = '+json.dumps(payload)+';',
        '/*FM1_SOURCE_URL*/':'https://github.com/m-vave/fm1_open',
        '/*FM1_NOTICES*/':html.escape((ROOT/'LICENSE.md').read_text()+'\n'+(ROOT/'THIRD_PARTY.md').read_text())}
    for marker, file in [('I18N','I18n.js'),('SCRIPT','WebUpdate.js'),('SIM_SCRIPT','Simulator.js'),('SAMPLE_SCRIPT','Samples.js')]:
        replacements['/*FM1_'+marker+'*/'] = (ROOT/'sdk'/file).read_text()
    for marker,value in replacements.items(): page = page.replace(marker,value)
    assert '/*FM1_' not in page
    (out/'index.html').write_text(page)
    custom = ROOT/'preview/index.html'
    if custom.exists():
        (out/'BAILE.html').write_text(custom.read_text().replace('/*BAILE_WASM*/',payload['data']))
print(result)
