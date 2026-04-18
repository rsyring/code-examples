#!/usr/bin/env python3
from pathlib import Path
import shutil


projects_dpath = Path('~/projects').expanduser()
ce_dpath = projects_dpath / 'code-examples'

# (source relative to ~/projects, dest relative to this repo)
copies = [
    ('mu-pkg/src/mu/config.py', 'configs/mu-config.py'),
    ('env-config-pkg/src/env_config/config.py', 'configs/env-config-config.py'),
    ('juke-inc-pkg/src/juke/config.py', 'configs/juke-config.py'),
    ('podu-pkg/src/podu/config.py', 'configs/podu-config.py'),
]

for src_rel, dest_rel in copies:
    src = projects_dpath / src_rel
    dest = ce_dpath / dest_rel
    shutil.copy2(src, dest)
    print(f'Copied {src} -> {dest}')
