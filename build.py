#!/usr/bin/env python3
"""Build BAILE locally. No command in this script writes to an FM-1."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def portable_sources():
    return sorted(p for d in ['app', 'web', 'third_party/synth']
                  for p in (ROOT / d).rglob('*.c') if 'board' not in p.parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', choices=['host', 'web', 'firmware'])
    parser.add_argument('--cc', default=os.environ.get('CC', 'clang'))
    parser.add_argument('--wasi-sdk', default=os.environ.get('WASI_SDK_PATH'))
    args, extra = parser.parse_known_args()
    if args.target == 'firmware':
        subprocess.run([sys.executable, str(ROOT / 'tools/build_firmware.py'), *extra], cwd=ROOT, check=True)
        subprocess.run([sys.executable, str(ROOT / 'tests/check_link.py')], cwd=ROOT, check=True)
        return
    if extra:
        parser.error('unrecognized arguments: ' + ' '.join(extra))
    common = ['-std=c11', '-O2', '-fwrapv', '-fno-fast-math', '-ffp-contract=off',
              '-DFM1_HOST_TEST', '-DFM1_OPEN_WEB', '-Wno-unknown-attributes',
              '-Wno-unused-function']
    includes = ['web/engine', 'web/synth', 'third_party/synth', 'sdk/include', 'app/synth', 'app']
    common += ['-I' + str(ROOT / p) for p in includes]
    sources = list(map(str, portable_sources()))
    if args.target == 'host':
        if sys.platform == 'win32':
            parser.error('host target currently supports macOS and Linux; use WSL on Windows')
        folder = ROOT / 'build/host'
        folder.mkdir(parents=True, exist_ok=True)
        output = folder / ('baile.dylib' if sys.platform == 'darwin' else 'baile.so')
        shared = ['-dynamiclib'] if sys.platform == 'darwin' else ['-shared', '-fPIC']
        subprocess.run([args.cc, *shared, *common, *sources,
                        str(ROOT / 'tests/host_optional.c'), '-lm', '-o', str(output)], check=True)
        print(output.relative_to(ROOT))
    else:
        if not args.wasi_sdk:
            parser.error('--wasi-sdk or WASI_SDK_PATH must point to WASI SDK 27')
        sdk = Path(args.wasi_sdk).expanduser().resolve()
        folder = ROOT / 'build/preview'
        shutil.copytree(ROOT / 'preview', folder, dirs_exist_ok=True)
        # The preview's ../assets/art paths are kept the same in the build tree.
        shutil.copytree(ROOT / 'assets/art', ROOT / 'build/assets/art', dirs_exist_ok=True)
        output = folder / 'baile.wasm'
        subprocess.run([str(sdk / 'bin/clang'), '--sysroot=' + str(sdk / 'share/wasi-sysroot'),
                        *common, '-mexec-model=reactor', *sources, '-Wl,--strip-all',
                        '-Wl,-z,stack-size=131072', '-Wl,--initial-memory=4194304',
                        '-Wl,--max-memory=33554432', '-o', str(output)], check=True)
        print('Preview: python3 -m http.server 8767 --bind 127.0.0.1 --directory build')
        print('Open http://127.0.0.1:8767/preview/')


if __name__ == '__main__':
    main()
