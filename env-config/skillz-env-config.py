from dataclasses import dataclass
from pathlib import Path
from typing import Self

import yaml


env_config_fpath = Path(__file__).parents[3] / 'env-config.yaml'


@dataclass
class EnvVar:
    env_var: str
    secret_ref: str


@dataclass
class EnvConfig:
    github: EnvVar
    slack: EnvVar

    @classmethod
    def load(cls) -> Self:
        conf = yaml.safe_load(env_config_fpath.read_text()) or {}
        profile_data = conf.get('profile', {}).get('skillz', {}) or {}

        return cls(
            github=EnvVar(
                env_var='GH_TOKEN',
                secret_ref=profile_data.get('GH_TOKEN', ''),
            ),
            slack=EnvVar(
                env_var='SLACK_API_TOKEN',
                secret_ref=profile_data.get('SLACK_API_TOKEN', ''),
            ),
        )
