#!/usr/bin/env python
"""
#MISE description="ZFS-on-ROOT prep"
#MISE silent=true
"""

import contextlib
from dataclasses import dataclass
from os import environ
from pathlib import Path
import subprocess

import click
import watchfiles


projects_dpath = Path.home() / 'projects'

# No slash on end so rsync gets dir and not dir contents
zor_dpath = projects_dpath / 'zfs-on-root'


def sub_run(*args, **kwargs):
    kwargs.setdefault('check', True)
    return subprocess.run(args, stdin=subprocess.PIPE, **kwargs)


def sync_to_host(zor_src_dpath: Path, rsync_dest: str, *args):
    sub_run(
        'rsync',
        '-hav',
        '--delete',
        '--exclude',
        '.git',
        '--exclude',
        '*.egg-info',
        '--exclude',
        '*.pyc',
        '--exclude',
        '*.ruff_cache',
        '--delete-excluded',
        # Protect (don't delete) .venv on dest side
        '--filter=P .venv',
        # Protect (don't delete) .pyc on dest side
        '--filter=P *.pyc',
        zor_src_dpath,
        rsync_dest,
        *args,
    )


def watcher(zor_src_dpath: Path, rsync_dest: str):
    with contextlib.suppress(KeyboardInterrupt):
        for _changes in watchfiles.watch(zor_src_dpath, step=1_000):
            sync_to_host(zor_src_dpath, rsync_dest)


@dataclass
class Config:
    ssh_user: str
    ssh_root: str = ''

    def __post_init__(self):
        _, host = self.ssh_user.split('@')
        self.ssh_root = f'root@{host}'


pass_config = click.make_pass_decorator(Config)


@click.group()
@click.option('--ssh-dest', type=str, default=environ.get('ZOR_SSH_DEST', ''))
@click.pass_context
def cli(ctx: click.Context, ssh_dest: str):
    if not ssh_dest:
        raise click.ClickException('Set ZOR_SSH_DEST or use --ssh-dest')

    ctx.obj = Config(ssh_dest)


@cli.command()
@pass_config
def ssh_copy_id(conf: Config):
    """Run 1st"""
    sub_run('ssh-copy-id', '-f', conf.ssh_user)
    sub_run('ssh', conf.ssh_user, 'sudo', 'cp', '-r', '~/.ssh', '/root')


@cli.command()
@pass_config
def drives(conf: Config):
    """Show the drives with lsblk"""
    print('LSBLK')
    sub_run('ssh', conf.ssh_user, 'lsblk', '-io', 'KNAME,TYPE,SIZE,MODEL,PATH,FSTYPE,LABEL')
    print('\nLS BY-PARTLABEL')
    sub_run('ssh', conf.ssh_user, 'ls', '-l', '/dev/disk/by-partlabel')
    print('\nLS BY-ID')
    sub_run('ssh', conf.ssh_user, 'ls', '-l', '/dev/disk/by-id')


@cli.command()
@click.argument('zor-cache-part', required=False)
@click.option('--skip-apt', is_flag=True, default=False)
@click.option('--keep-zor-cache', is_flag=True, default=False)
@pass_config
def prep(conf: Config, zor_cache_part, skip_apt, keep_zor_cache):
    if not skip_apt:
        sub_run('ssh', conf.ssh_root, 'apt', 'update')

        sub_run(
            'ssh',
            conf.ssh_root,
            'echo',
            'refind refind/install_to_esp boolean false',
            '|',
            'debconf-set-selections',
        )

        sub_run(
            'ssh',
            conf.ssh_root,
            'DEBIAN_FRONTEND=noninteractive',
            'apt-get',
            '-y',
            'install',
            'gdisk',
            'debootstrap',
            'zfs-initramfs',
            'refind',
        )

    uv_check = sub_run(
        'ssh',
        conf.ssh_root,
        'ls',
        '$HOME/.local/bin/uv',
        check=False,
    )
    if uv_check.returncode:
        print('uv missing, installing')
        sub_run(
            'ssh',
            conf.ssh_root,
            'curl',
            '-LsSf',
            'https://astral.sh/uv/install.sh',
            '|',
            'sh',
        )

    sub_run('ssh', conf.ssh_root, 'mkdir', '-p', '/mnt/usb-data')
    if zor_cache_part:
        sub_run(
            'ssh',
            conf.ssh_root,
            'mountpoint',
            '-q',
            '/mnt/usb-data',
            '||',
            'mount',
            zor_cache_part,
            '/mnt/usb-data',
        )
    if zor_cache_part and not keep_zor_cache:
        sub_run(
            'ssh',
            conf.ssh_root,
            'rm',
            '-r',
            '/mnt/usb-data/zor-cache',
            '||',
            'true',
        )


@cli.command()
@click.argument('zor_proj', default=zor_dpath, type=click.Path(path_type=Path))
@pass_config
def install_prereqs(conf: Config, zor_proj: Path):
    sync_to_host('/home/rsyring/.local/bin/uv', f'{conf.ssh_root}:/root/.local/bin/uv', '--mkpath')
    sub_run(
        'ssh',
        conf.ssh_root,
        '~/.local/bin/uv',
        'tool',
        'update-shell',
    )
    sub_run(
        'ssh',
        conf.ssh_root,
        'apt',
        'update',
    )
    sub_run(
        'ssh',
        conf.ssh_root,
        'apt',
        'install',
        'gdisk',
        'zfsutils-linux',
        # TODO: install refind and answer "no" to the prompt
        'refind',
        'debootstrap',
    )


@cli.command()
@click.argument('zor_proj', default=zor_dpath, type=click.Path(path_type=Path))
@pass_config
def watch(conf: Config, zor_proj: Path):
    rsync_target = f'{conf.ssh_root}:/opt'

    # Initial sync & install
    sync_to_host(zor_proj, rsync_target)
    sub_run(
        'ssh',
        conf.ssh_root,
        '~/.local/bin/uv',
        'tool',
        'install',
        '-e',
        '/opt/zfs-on-root',
    )

    print('Initial sync complete, watching for changes...')

    # Now sync on local changes
    watcher(zor_proj, rsync_target)


if __name__ == '__main__':
    cli()
