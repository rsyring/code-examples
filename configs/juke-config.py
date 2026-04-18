from __future__ import annotations

import os
from pathlib import Path

from serde import field, from_dict, serde
import yaml

from . import exc
from .libs import logs, utils


log = logs.logger()


def find_upwards(d: Path, filename: str):
    root = Path(d.root)

    while d != root:
        attempt = d / filename
        if attempt.exists():
            return attempt
        d = d.parent

    return None


def deserialize_remotes(remotes: dict | None) -> dict[str, Remote]:
    """
    The key should be used as the Remote.ident:

    remotes:
        ghcr:
            url: ...

    Should result in: remotes['ghcr'].ident == 'ghcr'
    """
    if remotes is None:
        return {}

    return {key: from_dict(Remote, data | {'ident': key}) for key, data in remotes.items()}


@serde
class Stack:
    ident: str


@serde
class Remote:
    ident: str
    url: str
    username: str | None = None
    secret_cmd: str | None = None


@serde
class Service:
    image: str
    port: int | None = None
    environment: dict[str, str] = field(default_factory=dict)


@serde
class Config:
    stack: Stack
    services: dict[str, Service]
    remotes: dict[str, Remote] | None = field(deserializer=deserialize_remotes)

    @classmethod
    def from_yaml(cls, yaml_fpath: os.PathLike, env: str = '') -> Config:
        cwd = Path.cwd()
        yaml_fpath = Path(yaml_fpath)

        log.info(f'Loading config from: {yaml_fpath.relative_to(cwd, walk_up=True)}')
        config = yaml.safe_load(yaml_fpath.read_text())

        if env:
            env_yaml_path = yaml_fpath.with_suffix(f'.{env}.yaml')
            if env_yaml_path.exists():
                log.info(f'Loading config from: {env_yaml_path.relative_to(cwd, walk_up=True)}')
                env_config = yaml.safe_load(env_yaml_path.read_text())
                config = utils.deep_merge(config, env_config, ignore_extras=False)

        return from_dict(Config, config)

    @classmethod
    def find_juke(cls, start_at: Path, env: str = '') -> Config:
        if start_at.is_dir():
            config_fpath = find_upwards(start_at, 'juke.yaml')

            if config_fpath is None:
                raise exc.UserError(f'No juke.yaml in {start_at} or parents')

        elif start_at.suffix == '.yaml':
            config_fpath = start_at

        else:
            raise exc.UserError(f'{start_at} should be a directory or .yaml file')

        return cls.from_yaml(config_fpath, env)
