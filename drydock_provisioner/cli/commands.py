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

@click.group()
@click.option('--debug/--no-debug', default=False)
@click.option('--token')
@click.option('--url')
@click.pass_context
def drydock(ctx, debug, token, url):
    ctx.obj['DEBUG'] = debug

    if not token:
        ctx.obj['TOKEN'] = os.environ['DD_TOKEN']
    else:
        ctx.obj['TOKEN'] = token

    if not url:
        ctx.obj['URL'] = os.environ['DD_URL']
    else:
        ctx.obj['URL'] = url

@drydock.group()
def create():
    pass

@drydock.group()
def list()
    pass

@drydock.group()
def show():
    pass

@create.command()
def design