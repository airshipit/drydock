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
import logging
import click

@click.group()
@click.pass_context
def design(ctx):
    """ Drydock design commands
    """
    pass

@design.command(name='create')
@click.pass_context
def design_create(ctx):
    """ Create a design
    """
    click.echo('create invoked')

@design.command(name='list')
@click.pass_context
def design_list(ctx):
    """ List designs
    """
    click.echo(ctx.obj['CLIENT'].get_design_ids())

@click.option('--design-id',
              '-id',
              help='The deisgn id to show')
@design.command(name='show')
@click.pass_context
def design_show(ctx, design_id):
    """ show designs
    """
    if not design_id:
        ctx.fail('The design id must be specified by --design-id')

    click.echo('show invoked for {}'.format(design_id))
