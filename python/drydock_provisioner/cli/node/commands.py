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
import json
import yaml

from prettytable import PrettyTable

from drydock_provisioner.cli.node.actions import NodeList
from drydock_provisioner.cli.node.actions import NodeBuildData


@click.group()
def node():
    """ Drydock node commands
    """


@node.command(name='list')
@click.option(
    '--output', '-o', help='Output format: table|json', default='table')
@click.pass_context
def node_list(ctx, output='table'):
    """List nodes."""
    nodelist = NodeList(ctx.obj['CLIENT']).invoke()

    if output == 'table':
        pt = PrettyTable()

        pt.field_names = [
            'Node Name', 'Status', 'CPUs', 'Memory', 'PXE MAC', 'Mgmt IP',
            'IPMI IP', 'Power State'
        ]

        for n in nodelist:
            pt.add_row([
                n['hostname'], n['status_name'], n['cpu_count'], n['memory'],
                n['boot_mac'], n['boot_ip'], n['power_address'],
                n['power_state']
            ])

        click.echo(pt)
    elif output == 'json':
        click.echo(json.dumps(nodelist))


@node.command(name='builddata')
@click.option(
    '--latest/--no-latest',
    help='Retrieve only the latest data items.',
    default=True)
@click.option(
    '--output', '-o', help='Output format: yaml|json', default='yaml')
@click.argument('nodename')
@click.pass_context
def node_builddata(ctx, nodename, latest=True, output='yaml'):
    """List build data for ``nodename``."""
    node_bd = NodeBuildData(ctx.obj['CLIENT'], nodename, latest).invoke()

    if output == 'json':
        click.echo(json.dumps(node_bd))
    else:
        if output != 'yaml':
            click.echo(
                "Invalid output format {}, default to YAML.".format(output))
        click.echo(
            yaml.safe_dump(
                node_bd, allow_unicode=True, default_flow_style=False))
