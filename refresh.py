#!/usr/bin/env python3
from pathlib import Path
import shutil


projects_dpath = Path('~/projects').expanduser()
ce_dpath = projects_dpath / 'code-examples'

# (source relative to ~/projects, dest relative to this repo)
copies = [
    # Agents
    ('kilo-src/AGENTS.md', 'agents/kilo-agents.md'),
    ('ynabr-src/AGENTS.md', 'agents/ynabr-agents.md'),
    # Configs
    ('mu-pkg/src/mu/config.py', 'configs/mu-config.py'),
    ('env-config-pkg/src/env_config/config.py', 'configs/env-config-config.py'),
    ('juke-inc-pkg/src/juke/config.py', 'configs/juke-config.py'),
    ('podu-pkg/src/podu/config.py', 'configs/podu-config.py'),
    # CLI
    ('mu-pkg/src/mu/libs/logs.py', 'cli/mu-logs.py'),  # logging integration
    ('kilo-src/tasks/zor-prep.py', 'cli/zor-prep.py'),
    # CLI tables
    ('doist-pkg/src/doist/cli.py', 'cli-tables/doist-cli.py'),
    # Health checks
    ('doist-pkg/src/doist/views.py', 'health-checks/doist-views.py'),
    ('doist-pkg/src/doist_tests/test_views.py', 'health-checks/doist-test-views.py'),
    # Utils
    ('juke-inc-pkg/src/juke/libs/utils.py', 'utils/juke-utils.py'),
    ('mu-pkg/src/mu/libs/testing.py', 'utils/mu-testing.py'),
]

for src_rel, dest_rel in copies:
    src = projects_dpath / src_rel
    dest = ce_dpath / dest_rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
