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
""" cli.design.commands
    Contains commands related to designs
"""
import click

from drydock_provisioner.cli.design.actions import DesignList
from drydock_provisioner.cli.design.actions import DesignShow
from drydock_provisioner.cli.design.actions import DesignCreate

@click.group()
def design():
    """ Drydock design commands
    """
    pass

@design.command(name='create')
@click.option('--base-design',
              '-b',
              help='The base design to model this new design after')
@click.pass_context
def design_create(ctx, base_design=None):
    """ Create a design
    """
    click.echo(DesignCreate(ctx.obj['CLIENT'], base_design).invoke())

@design.command(name='list')
@click.pass_context
def design_list(ctx):
    """ List designs
    """
    click.echo(DesignList(ctx.obj['CLIENT']).invoke())

@design.command(name='show')
@click.option('--design-id',
              '-i',
              help='The design id to show')
@click.pass_context
def design_show(ctx, design_id):
    """ show designs
    """
    if not design_id:
        ctx.fail('The design id must be specified by --design-id')

    click.echo(DesignShow(ctx.obj['CLIENT'], design_id).invoke())
