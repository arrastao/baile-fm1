#!/usr/bin/env python3
"""Check SDK provenance, asset integrity, publication hygiene and local doc links."""
from pathlib import Path
import hashlib
import json
import re
import struct
import sys
import urllib.parse
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from fwsc_identity import identity, reidentify, unwrap

manifest = json.loads((ROOT / 'sdk/manifest.json').read_text())
for name, digest in manifest['files'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name

bank = (ROOT / 'assets/audio/tamborzao.fm1s').read_bytes()
assert len(bank) == 65036
assert hashlib.sha256(bank).hexdigest() == 'ad3faba4ed5240959843d94e01a1b6e6ff2d9ec089e29453335524823c5dec31'
assert struct.unpack_from('<I', bank, 12)[0] == zlib.crc32(bank[:12] + bytes(8) + bank[20:])
header = (ROOT / 'app/baile_bank.h').read_text()
array = re.search(r'baile_bank\[\].*?=\s*\{([^}]+)\}', header, re.S)
assert array, 'embedded bank not found'
assert bytes(int(x.strip(), 0) for x in array[1].split(',') if x.strip()) == bank
assert 'GROOVE_SAMPLE_BYTES = 335872' in (ROOT / 'app/instrument.h').read_text()
assert '405504U,7U' in (ROOT / 'tools/build_firmware.py').read_text()

stock = (ROOT / 'sdk/firmware/FM-1_015.fwsc').read_bytes()
variant = reidentify(stock, 'FM-1_803')
assert identity(variant) == 'FM-1_803'
assert unwrap(stock) == unwrap(variant), 'version wrapper changed the update image'
try:
    reidentify(stock, 'FM-1_8490133')
except ValueError:
    pass
else:
    raise AssertionError('long M-UPGRADE version was accepted')

for doc in ROOT.glob('*.md'):
    if doc.name in ['LICENSE.md', 'THIRD_PARTY.md']:
        continue  # retained upstream notices can reference upstream-only files
    text = doc.read_text()
    links = re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text)
    links += re.findall(r'(?:src|href)="([^"]+)"', text)
    for link in links:
        url = urllib.parse.urlsplit(link)
        if url.scheme or url.netloc or not url.path or url.path.startswith('../'):
            continue
        target = ROOT / urllib.parse.unquote(url.path)
        assert target.exists(), f'{doc.name}: missing {link}'

for folder in ['app', 'tools', 'tests', 'preview', 'assets', 'docs', '.github']:
    for path in (ROOT / folder).rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        assert path.suffix not in ['.nor', '.dylib', '.so', '.o'], path
        assert not path.name.startswith(('Backup-', 'backup-')), path
        if path.suffix in ['.md', '.json', '.py', '.js', '.mjs', '.c', '.h', '.yml', '.log']:
            text = path.read_text()
            assert ('/' + 'Users' + '/') not in text and ('/' + 'private' + '/tmp/') not in text, path
            assert not re.search(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}', text), path
print('SDK hashes, embedded bank, version wrapper, documentation links and publication hygiene: passed')
