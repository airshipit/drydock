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
""" The entrypoint for the cli commands
"""
import os
import logging
import click

from drydock_provisioner.drydock_client.session import DrydockSession
from drydock_provisioner.drydock_client.client import DrydockClient
from .design import commands as design

@click.group()
@click.option('--debug/--no-debug',
              help='Enable or disable debugging',
              default=False)
@click.option('--token',
              '-t',
              help='The auth token to be used',
              default=lambda: os.environ.get('DD_TOKEN', ''))
@click.option('--url',
              '-u',
              help='The url of the running drydock instance',
              default=lambda: os.environ.get('DD_URL', ''))
@click.pass_context
def drydock(ctx, debug, token, url):
    """ Drydock CLI to invoke the running instance of the drydock API
    """
    if not ctx.obj:
        ctx.obj = {}

    ctx.obj['DEBUG'] = debug

    if not token:
        ctx.fail("Error: Token must be specified either by "
                 "--token or DD_TOKEN from the environment")

    if not url:
        ctx.fail("Error: URL must be specified either by "
                 "--url or DD_URL from the environment")

    # setup logging for the CLI
    # Setup root logger
    logger = logging.getLogger('drydock_cli')

    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logging_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - '
                                  '%(filename)s:%(funcName)s - %(message)s')
    logging_handler.setFormatter(formatter)
    logger.addHandler(logging_handler)
    logger.debug('logging for cli initialized')

    # setup the drydock client using the passed parameters.
    ctx.obj['CLIENT'] = DrydockClient(DrydockSession(host=url,
                                                     token=token))

drydock.add_command(design.design)
