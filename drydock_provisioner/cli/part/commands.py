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
""" cli.part.commands
    Contains commands related to parts of designs
"""
import click

from drydock_provisioner.cli.part.actions import PartList
from drydock_provisioner.cli.part.actions import PartShow
from drydock_provisioner.cli.part.actions import PartCreate

@click.group()
@click.option('--design-id',
              '-d',
              help='The id of the design containing the target parts')
@click.pass_context
def part(ctx, design_id=None):
    """ Drydock part commands
    """
    if not design_id:
        ctx.fail('Error: Design id must be specified using --design-id')

    ctx.obj['DESIGN_ID'] = design_id

@part.command(name='create')
@click.option('--file',
              '-f',
              help='The file name containing the part to create')
@click.pass_context
def part_create(ctx, file=None):
    """ Create a part
    """
    if not file:
        ctx.fail('A file to create a part is required using --file')

    with open(file, 'r') as file_input:
        file_contents = file_input.read()
        # here is where some yaml validation could be done
        click.echo(PartCreate(ctx.obj['CLIENT'],
                              design_id=ctx.obj['DESIGN_ID'],
                              yaml=file_contents).invoke())

@part.command(name='list')
@click.pass_context
def part_list(ctx):
    """ List parts of a design
    """
    click.echo(PartList(ctx.obj['CLIENT'], design_id=ctx.obj['DESIGN_ID']).invoke())

@part.command(name='show')
@click.option('--source',
              '-s',
              help='designed | compiled')
@click.option('--kind',
              '-k',
              help='The kind value of the document to show')
@click.option('--key',
              '-i',
              help='The key value of the document to show')
@click.pass_context
def part_show(ctx, source, kind, key):
    """ show a part of a design
    """
    if not kind:
        ctx.fail('The kind must be specified by --kind')
    
    if not key:
        ctx.fail('The key must be specified by --key')

    click.echo(PartShow(ctx.obj['CLIENT'], design_id=ctx.obj['DESIGN_ID'], kind=kind, key=key, source=source).invoke())
