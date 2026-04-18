from pathlib import Path

from serde import serde, yaml

from . import exc


@serde
class AppConfig:
    image: str
    services: list[str]


@serde
class Config:
    project: str
    apps: dict[str, AppConfig]
    id_prefix: str = 'podu'


def find_upwards(d: Path, filename: str):
    root = Path(d.root)

    while d != root:
        attempt = d / filename
        if attempt.exists():
            return attempt
        d = d.parent

    return None


def load(start_at: Path, for_tests: bool = False) -> Config:
    if start_at.is_dir():
        config_fpath = find_upwards(start_at, 'podu.yaml')
        if config_fpath is None:
            raise exc.UserError(f'No podu.yaml in {start_at} or parents')
    elif start_at.suffix == '.yaml':
        config_fpath = start_at
    else:
        raise exc.UserError(f'{start_at} should be a directory or .yaml file')

    config: Config = yaml.from_yaml(Config, config_fpath.read_text())
    if for_tests:
        config.id_prefix = 'podu-tests'

    return config
