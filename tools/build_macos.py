#!/usr/bin/env python3
"""Compile and package BAILE on macOS using the original Tamborzao build route.

Does not flash or otherwise communicate with a device.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import pack

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT/'tools/assets.py')], cwd=ROOT, check=True)
subprocess.run([sys.executable, str(ROOT/'tests/source_contract.py')], cwd=ROOT, check=True)
subprocess.run([sys.executable, str(ROOT/'tools/native_probe.py')], cwd=ROOT, check=True)
subprocess.run([sys.executable, str(ROOT/'tests/native_layout.py')], cwd=ROOT, check=True)
generated = ROOT/'build/dx7/generated'
config = json.loads((ROOT/'baile-layout.json').read_text())
report = json.loads((generated/'build-report.json').read_text())
product = re.search(r'#define FM1_UPDATE_PRODUCT "([^"]+)"', (ROOT/'app/version.h').read_text())[1]
assert report['product'] == product and report['fits']
app = (generated/'application.bin').read_bytes()
assert len(app) == report['app_bytes']
data, flash_bytes, limit = pack.create(app, str(ROOT/'sdk/tools/pack'), product, config['user_bytes'])
output = ROOT/'build/BAILE-0.6-MAC.fwsc'
output.write_bytes(data)
report.update(firmware=output.name, package_bytes=len(data), flash_image_bytes=flash_bytes,
              package_sha256=hashlib.sha256(data).hexdigest(), user_bytes=config['user_bytes'],
              packager='Python port of pinned SDK Package.cs; original SDK boot; explicit BAILE user partition',
              application_limit=limit, hardware_validated=False)
(generated/'macos-package.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2), flush=True)
