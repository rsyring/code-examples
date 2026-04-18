from collections.abc import Iterable
import functools
import logging
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import time

from click.globals import get_current_context
import httpx


log = logging.getLogger(__name__)


def need_root(f):
    """
    Require this command to be ran by the root user.
    """

    def new_func(*args, **kwargs):
        if os.geteuid() != 0:
            get_current_context().fail('You must be root to run this command.')
        return f(*args, **kwargs)

    return functools.update_wrapper(new_func, f)


class CalledProcessError(subprocess.CalledProcessError):
    @classmethod
    def from_cpe(cls, exc: subprocess.CalledProcessError):
        return cls(
            returncode=exc.returncode,
            cmd=exc.cmd,
            output=exc.output,
            stderr=exc.stderr,
        )

    def __str__(self):
        return super().__str__() + f'\nSTDOUT: {self.stdout}' + f'\nSTDERR: {self.stderr}'


def sub_run(
    *args,
    capture=False,
    returns: None | Iterable[int] = None,
    **kwargs,
) -> subprocess.CompletedProcess:
    kwargs.setdefault('check', not bool(returns))
    capture = kwargs.setdefault('capture_output', capture)
    args = (*args, *kwargs.pop('args', ()))
    env = kwargs.pop('env', None)
    if env:
        kwargs['env'] = os.environ | env
    if capture or 'input' in kwargs:
        kwargs.setdefault('text', True)

    try:
        log.debug(f'Running: {" ".join(str(a) for a in args)}')
        result = subprocess.run(args, **kwargs)
        if returns and result.returncode not in returns:
            raise subprocess.CalledProcessError(result.returncode, args[0])
        return result
    except subprocess.CalledProcessError as e:
        if capture:
            raise CalledProcessError.from_cpe(e) from e
        raise
    except Exception as e:
        raise CalledProcessError('n/a', args, '', '') from e


def sudo_run(*args, sudo_user=None, sudo_path=None, **kwargs):
    user_args = ('-u', sudo_user) if sudo_user else ()
    # Sudo only looks for bins in: `sudo grep secure_path /etc/sudoers`
    # If we want to adjust the path, then we need to use `env` to do it.
    env_args = ('env', f'PATH={sudo_path}') if sudo_path else ()
    return sub_run('sudo', *user_args, *env_args, args=args, **kwargs)


def systemctl(*args, **kwargs):
    return sub_run('systemctl', args=args, **kwargs)


def first(iterable, empty_val=None):
    try:
        return next(iter(iterable))
    except StopIteration:
        return empty_val


def download_url(url: str, dest: os.PathLike, *, timeout=30, force: bool = False) -> Path:
    dest = Path(dest)
    if not dest.is_absolute() and len(dest.parts) == 1:
        dest = Path(tempfile.gettempdir()) / dest.name
    else:
        dest = dest.resolve()

    if dest.exists() and not force:
        log.info(f'{dest} already exists.  Not downloading again.')
        return dest

    tmp = dest.with_suffix(dest.suffix + '.part')

    with httpx.stream('GET', url, timeout=timeout) as resp:
        resp.raise_for_status()
        with tmp.open('wb') as f:
            for chunk in resp.iter_bytes():
                if chunk:
                    f.write(chunk)

    tmp.replace(dest)

    return dest


def wait_seq(count, secs):
    extra = [secs] * count
    return (0.1, 0.25, 0.5, 0.75, 1, *extra)


def retry(func, *args, waiting_for, secs=1, count=30, exc: Exception | None = None, **kwargs):
    retry_on_exc = bool(exc)
    exc = exc or Exception

    for wait_for in wait_seq(count, secs):
        try:
            val = func(*args, **kwargs)
            if val:
                return val
        except exc:
            if not retry_on_exc:
                raise

        log.info(f'Waiting {wait_for}s for {waiting_for}')
        time.sleep(wait_for)

    raise Exception('Retry failed')


def trim_start(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


def deep_merge(base, overrides, ignore_extras: bool = True):
    result = dict(base)
    for key, override_value in overrides.items():
        if key not in base and ignore_extras:
            continue
        base_value = result.get(key)
        if isinstance(base_value, dict) and isinstance(override_value, dict):
            result[key] = deep_merge(base_value, override_value, ignore_extras=ignore_extras)
        else:
            result[key] = override_value
    return result


def walk_to_path(start_path: os.PathLike, target_path: os.PathLike):
    """
    Walk from start_path to target_path, yielding each intermediate directory.

    Args:
        start_path (str): The starting directory path
        target_path (str): The target directory path

    Yields:
        str: Each intermediate directory path from start to target (excluding target)
    """
    # Convert to Path objects and resolve to absolute paths
    start = Path(start_path).resolve()
    target = Path(target_path).resolve()

    # Will throw an error if target is not under start
    relative_path = target.relative_to(start)

    # Build the intermediate paths
    current_path = start
    for part in relative_path.parts[:-1]:  # Exclude the final part (target itself)
        current_path = current_path / part
        yield str(current_path)


def dd(s: str):
    """
    A visually minimal dedent function that strips the left most whitespace.  Designed to
    make it easy to indent text in source code and have the result not be indented.

        myvar = dd('''
            [some config]
            with-indenting = 'is helpful'
        ''')

    """
    return textwrap.dedent(s).lstrip()
