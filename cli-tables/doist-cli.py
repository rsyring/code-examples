import logging
from pprint import pprint

import click
from flask import Blueprint, current_app
from prettytable import PrettyTable
import rich

from . import entities as ents
from .libs import actions, sync, utils


log = logging.getLogger(__name__)
cli_bp = Blueprint('cli', __name__, cli_group=None)


@cli_bp.cli.command()
def schedule():
    """Run schedule jobs"""
    from .schedule import run

    schedule_logger = logging.getLogger('schedule')
    schedule_logger.setLevel(level=logging.DEBUG)

    try:
        print('Scheduler running...')
        run()
    except KeyboardInterrupt:
        click.echo('exiting')


@cli_bp.cli.command()
@click.option('--all', 'is_all', is_flag=True, help='Show all fields')
def api_user(is_all: bool):
    """Print API user details"""
    api = sync.SyncAPI()
    user = api.user()

    if not is_all:
        user = utils.take_items(user, 'id', 'email')

    pprint(user)


@cli_bp.cli.command()
@click.option('--sync-full', is_flag=True)
@click.option('--dry-run', is_flag=True)
def sprint_names(sync_full: bool, dry_run: bool):
    """Bump sprint name end dates"""

    with sync.Manager.session(full_sync=sync_full, dry_run=dry_run):
        action_desc = ents.Section.sprint_end_date()

        if action_desc:
            print(utils.indented('Actions:', action_desc))


@cli_bp.cli.command()
@click.argument('resp_key')
@click.argument('filter_field', required=False)
@click.argument('filter_value', required=False)
def json_schema(resp_key, filter_field: str, filter_value: str):
    """Show JSON record from sync API"""
    da = sync.Manager()

    resp_data: dict = da.sync(full=True)

    recs = resp_data[resp_key]
    if not filter_field:
        pprint(recs[-1])
        return

    for rec in [rec for rec in recs if rec[filter_field] == filter_value]:
        pprint(rec)


@cli_bp.cli.command()
def activity():
    """Show event items from Activity API"""
    api = sync.SyncAPI()
    resp: dict = api.activity()
    results = resp['results']
    print('Total items:', len(results))
    print('Next cursor:', resp['next_cursor'])
    if not results:
        return
    rich.print('First item:', results[0], sep='\n')
    rich.print('Last item:', results[-1], sep='\n')


@cli_bp.cli.command('sync')
@click.option('--full', is_flag=True)
def _sync(full):
    """Sync latest data, no actions taken"""
    da = sync.Manager()
    # Sync so we are sure we have the latest data
    da.sync(full=full)


@cli_bp.cli.command()
@click.option('--sync-full', is_flag=True)
@click.option('--dry-run', is_flag=True)
def nightly(sync_full: bool, dry_run: bool):
    """Actions ran each night"""
    with sync.Manager.session(full_sync=sync_full, dry_run=dry_run):
        action_desc = ents.Task.demote_current()
        action_desc += ents.Task.promote_triaged()
        action_desc += ents.Task.clear_now()

        if action_desc:
            print(utils.indented('Actions:', action_desc))


@cli_bp.cli.command('actions')
@click.option('--sync-full', is_flag=True)
@click.option('--dry-run', is_flag=True)
def _actions(sync_full: bool, dry_run: bool):
    """Run periodic actions"""
    actions.run_periodic(sync_full=sync_full, dry_run=dry_run)


@cli_bp.cli.command()
@click.argument('project_name')
@click.option('--sync-full', is_flag=True)
@click.option('--reorder-all', 'reorder', is_flag=True)
def task_rank(project_name: str, sync_full: bool, reorder: bool):
    """Show task ranking for a project, maybe reorder"""
    with sync.Manager.session(full_sync=sync_full, dry_run=not reorder):
        proj = ents.Project.get_by(name=project_name)
        if not proj:
            utils.print_exit('Error: project not found', code=1)

        table = PrettyTable(
            ('Id', 'Ours', 'Theirs', 'Section', 'Labels', 'Priority', 'Due', 'Task'),
        )
        table.align = 'l'
        for row in ents.Task.q_ranked().where(ents.Project.name == project_name):
            table.add_row(
                (
                    row.task_id,
                    row.custom_order_rank,
                    row.child_order_rank,
                    row.section_name,
                    ','.join(sorted(row.labels)),
                    row.priority,
                    row.due_date or row.due_at,
                    row.content[0:45],
                ),
            )

        print(table)


@cli_bp.cli.command()
@click.option('--sync-full', is_flag=True)
def task_misranked(sync_full: bool):
    """List projects where task re-ordering is needed"""
    with sync.Manager.session(full_sync=sync_full, dry_run=True):
        projs = ents.Task.projects_misranked()

        if not projs:
            print('No projects have mis-ranked tasks')
            return

        for proj in projs:
            print(proj.project_id, proj.project_name)


@cli_bp.cli.command()
@click.argument('bind', default='127.0.0.1:5001')
@click.option('--workers', default=8)
def gunicorn(bind, workers):
    """Run app with gunicorn"""
    # Keep import inside function to avoid needing gunicorn installed
    # unless it's going to be used.
    from flac.contrib.gunicorn import AppServer

    # Add the options you need, see:
    # https://docs.gunicorn.org/en/latest/settings.html
    opts = {'bind': bind, 'workers': workers}

    app = current_app._get_current_object()
    AppServer(app, opts).run()
