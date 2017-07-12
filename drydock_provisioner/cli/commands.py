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
import os

import click

from .design import commands as design

@click.group()
@click.option('--debug/--no-debug', default=False)
@click.option('--token', default=lambda: os.environ.get('DD_TOKEN', None))
@click.option('--url' , default=lambda: os.environ.get('DD_URL', None))
@click.pass_context
def drydock(ctx, debug, token, url):
    """ Base cli command. Peforms validations and sets default values.
    """
    if not ctx.obj:
        ctx.obj = {}

    ctx.obj['DEBUG'] = debug

    option_validation_error = False

    if not token:
        click.echo("Error: Token must be specified either by "
                   "--token or DD_TOKEN from the environment")
        option_validation_error = True

    if not url:
        click.echo("Error: URL must be specified either by "
                   "--url or DD_URL from the environment")
        option_validation_error = True

    if option_validation_error:
        ctx.exit()

drydock.add_command(design.design)
