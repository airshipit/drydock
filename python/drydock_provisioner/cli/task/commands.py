# Copyright 2017 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains commands related to tasks against designs."""
import click
import json
import yaml

from drydock_provisioner.cli.task.actions import TaskList
from drydock_provisioner.cli.task.actions import TaskShow
from drydock_provisioner.cli.task.actions import TaskCreate
from drydock_provisioner.cli.task.actions import TaskBuildData


@click.group()
def task():
    """Drydock task commands."""


@task.command(name='create')
@click.option(
    '--design-ref', '-d', help='The design reference for this action')
@click.option('--action', '-a', help='The action to perform')
@click.option(
    '--node-names',
    '-n',
    help='The nodes targeted by this action, comma separated')
@click.option(
    '--rack-names',
    '-r',
    help='The racks targeted by this action, comma separated')
@click.option(
    '--node-tags',
    '-t',
    help='The nodes by tag name targeted by this action, comma separated')
@click.option(
    '--block/--no-block',
    '-b',
    help='The CLI will wait until the created completes before exitting',
    default=False)
@click.option(
    '--poll-interval',
    help='Polling interval to check task status in blocking mode.',
    default=15)
@click.pass_context
def task_create(ctx,
                design_ref=None,
                action=None,
                node_names=None,
                rack_names=None,
                node_tags=None,
                block=False,
                poll_interval=15):
    """Create a task."""
    if not design_ref:
        ctx.fail(
            'Error: Design reference must be specified using --design-ref')

    if not action:
        ctx.fail('Error: Action must be specified using --action')

    click.echo(
        json.dumps(
            TaskCreate(
                ctx.obj['CLIENT'],
                design_ref=design_ref,
                action_name=action,
                node_names=[x.strip() for x in node_names.split(',')]
                if node_names else [],
                rack_names=[x.strip() for x in rack_names.split(',')]
                if rack_names else [],
                node_tags=[x.strip()
                           for x in node_tags.split(',')] if node_tags else [],
                block=block,
                poll_interval=poll_interval).invoke()))


@task.command(name='list')
@click.pass_context
def task_list(ctx):
    """List tasks."""
    click.echo(json.dumps(TaskList(ctx.obj['CLIENT']).invoke()))


@task.command(name='show')
@click.option('--task-id', '-t', help='The required task id')
@click.option(
    '--block/--no-block',
    '-b',
    help='The CLI will wait until the created completes before exitting',
    default=False)
@click.pass_context
def task_show(ctx, task_id=None, block=False):
    """show a task's details."""
    if not task_id:
        ctx.fail('The task id must be specified by --task-id')

    click.echo(
        json.dumps(TaskShow(ctx.obj['CLIENT'], task_id=task_id).invoke()))


@task.command(name='builddata')
@click.option('--task-id', '-t', help='The required task id')
@click.option(
    '--output', '-o', help='The output format (yaml|json)', default='yaml')
@click.pass_context
def task_builddata(ctx, task_id=None, output='yaml'):
    """Show builddata assoicated with ``task_id``."""
    if not task_id:
        ctx.fail('The task id must be specified by --task-id')

    task_bd = TaskBuildData(ctx.obj['CLIENT'], task_id=task_id).invoke()

    if output == 'json':
        click.echo(json.dumps(task_bd))
    else:
        if output != 'yaml':
            click.echo(
                'Invalid output format {}, defaulting to YAML.'.format(output))
        click.echo(
            yaml.safe_dump(
                task_bd, allow_unicode=True, default_flow_style=False))
