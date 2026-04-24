from collections.abc import Iterable
from os import environ
from pathlib import Path
import subprocess
from urllib.parse import unquote

from furl import furl


class CalledProcessError(subprocess.CalledProcessError):
    def __init__(self, exc: subprocess.CalledProcessError):
        self.returncode = exc.returncode
        self.cmd = exc.cmd
        self.output = exc.output
        self.stderr = exc.stderr

    def __str__(self):
        return (
            super().__str__() + f'\nSTDOUT: {self.stdout[:100]}' + f'\nSTDERR: {self.stderr[:100]}'
        )


def sub_run(
    *args,
    capture=False,
    returns: None | Iterable[int] = None,
    **kwargs,
) -> subprocess.CompletedProcess:
    kwargs.setdefault('check', not bool(returns))
    capture = kwargs.setdefault('capture_output', capture)
    args = args + kwargs.pop('args', ())
    env = kwargs.pop('env', None)
    if env:
        kwargs['env'] = environ | env
    if capture:
        kwargs.setdefault('text', True)

    try:
        result = subprocess.run(args, **kwargs)
        if returns and result.returncode not in returns:
            raise subprocess.CalledProcessError(result.returncode, args[0])
        return result
    except subprocess.CalledProcessError as e:
        if capture:
            raise CalledProcessError(e) from e
        raise


def op_read(uri: str):
    parts = furl(uri)
    segments = parts.path.segments
    if len(segments) > 2:
        acct_args = ('--account', parts.host)
        vault = segments[0]
        uri = unquote(parts.set(host=vault, path=segments[1:]).url)
    else:
        acct_args = ()
    return sub_run('op', *acct_args, 'read', '-n', uri, capture=True).stdout


def env_op_read(env_key: str, op_ref: str):
    """Lookup an environment key or get it's value from the op cli tool as follows:

    - If `env_key` is present in os.environ, use it as the value
    - If systemd credentials are being used, treat the env_key as the credentials filename and use
        the file's contents if present.
    - If f'{env_key}_SECREF' is present in os.environ, us it as the op secret reference URL
    - Use `up_ref` as the op secret reference URL

    """
    if env_key in environ:
        return environ[env_key]

    if systemd_creds_dir := (environ.get('CREDENTIALS_DIRECTORY')):
        creds_fpath = Path(systemd_creds_dir) / env_key
        if creds_fpath.exists():
            return creds_fpath.read_text()

    op_ref = environ.get(f'{env_key}_SECREF', op_ref)
    return op_read(op_ref)


def first(iterable, empty_val=None):
    try:
        return next(iter(iterable))
    except StopIteration:
        return empty_val
