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
""" cli.task.commands
    Contains commands related to tasks against designs
"""
import click

from drydock_provisioner.cli.task.actions import TaskList
from drydock_provisioner.cli.task.actions import TaskShow
from drydock_provisioner.cli.task.actions import TaskCreate

@click.group()
def task():
    """ Drydock task commands
    """

@task.command(name='create')
@click.option('--design-id',
              '-d',
              help='The design id for this action')
@click.option('--action',
              '-a',
              help='The action to perform')
@click.option('--node-names',
              '-n',
              help='The nodes targeted by this action, comma separated')
@click.option('--rack-names',
              '-r',
              help='The racks targeted by this action, comma separated')
@click.option('--node-tags',
              '-t',
              help='The nodes by tag name targeted by this action, comma separated')
@click.pass_context
def task_create(ctx, design_id=None, action=None, node_names=None, rack_names=None, node_tags=None):
    """ Create a task
    """
    if not design_id:
        ctx.fail('Error: Design id must be specified using --design-id')

    if not action:
        ctx.fail('Error: Action must be specified using --action')

    click.echo(TaskCreate(ctx.obj['CLIENT'],
                          design_id=design_id,
                          action_name=action,
                          node_names=[x.strip() for x in node_names.split(',')] if node_names else [],
                          rack_names=[x.strip() for x in rack_names.split(',')] if rack_names else [],
                          node_tags=[x.strip() for x in node_tags.split(',')] if node_tags else []
                          ).invoke())

@task.command(name='list')
@click.pass_context
def task_list(ctx):
    """ List tasks.
    """
    click.echo(TaskList(ctx.obj['CLIENT']).invoke())

@task.command(name='show')
@click.option('--task-id',
              '-t',
              help='The required task id')
@click.pass_context
def task_show(ctx, task_id=None):
    """ show a task's details
    """
    if not task_id:
        ctx.fail('The task id must be specified by --task-id')

    click.echo(TaskShow(ctx.obj['CLIENT'],
                        task_id=task_id).invoke())
