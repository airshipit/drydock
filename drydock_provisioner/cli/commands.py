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
"""The entry point for the cli commands."""
import os
import logging
from urllib.parse import urlparse

import click
from drydock_provisioner.drydock_client.session import DrydockSession
from drydock_provisioner.drydock_client.session import KeystoneClient
from drydock_provisioner.drydock_client.client import DrydockClient
from .design import commands as design
from .part import commands as part
from .task import commands as task
from .node import commands as node

@click.group()
@click.option(
    '--debug/--no-debug', help='Enable or disable debugging', default=False)
# Supported Environment Variables
@click.option(
    '--os_project_domain_name',
    envvar='OS_PROJECT_DOMAIN_NAME',
    required=False)
@click.option(
    '--os_user_domain_name', envvar='OS_USER_DOMAIN_NAME', required=False)
@click.option('--os_project_name', envvar='OS_PROJECT_NAME', required=False)
@click.option('--os_username', envvar='OS_USERNAME', required=False)
@click.option('--os_password', envvar='OS_PASSWORD', required=False)
@click.option('--os_auth_url', envvar='OS_AUTH_URL', required=False)
@click.option(
    '--os_token',
    help='The Keystone token to be used',
    default=lambda: os.environ.get('OS_TOKEN', ''))
@click.option(
    '--url',
    '-u',
    help='The url of the running drydock instance',
    default=lambda: os.environ.get('DD_URL', ''))
@click.pass_context
def drydock(ctx, debug, url, os_project_domain_name, os_user_domain_name, os_project_name,
            os_username, os_password, os_auth_url, os_token):
    """Drydock CLI to invoke the running instance of the drydock API."""
    if not ctx.obj:
        ctx.obj = {}

    ctx.obj['DEBUG'] = debug

    keystone_env = {
        'project_domain_name': os_project_domain_name,
        'user_domain_name': os_user_domain_name,
        'project_name': os_project_name,
        'username': os_username,
        'password': os_password,
        'auth_url': os_auth_url,
    }

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

    try:
        if not os_token:
            logger.debug("Generating Keystone session by env vars: %s" % str(keystone_env))
            ks_sess = KeystoneClient.get_ks_session(**keystone_env)
        else:
            logger.debug("Generating Keystone session by explicit token: %s" % os_token)
            ks_sess = KeystoneClient.get_ks_session(token=os_token)
        KeystoneClient.get_token(ks_sess=ks_sess)
    except Exception as ex:
        logger.debug("Exception getting Keystone session.", exc_info=ex)
        ctx.fail('Error: Unable to authenticate with Keystone')
        return

    try:
        if not url:
            url = KeystoneClient.get_endpoint('physicalprovisioner', ks_sess=ks_sess)
    except Exception as ex:
        logger.debug("Exception getting Drydock endpoint.", exc_info=ex)
        ctx.fail('Error: Unable to discover Drydock API URL')

    # setup the drydock client using the passed parameters.
    url_parse_result = urlparse(url)

    if not os_token:
        token = KeystoneClient.get_token(ks_sess=ks_sess)
        logger.debug("Creating Drydock client with token %s." % token)
    else:
        token = os_token

    if not url_parse_result.scheme:
        ctx.fail('URL must specify a scheme and hostname, optionally a port')
    ctx.obj['CLIENT'] = DrydockClient(
        DrydockSession(
            scheme=url_parse_result.scheme,
            host=url_parse_result.hostname,
            port=url_parse_result.port,
            token=token))

drydock.add_command(design.design)
drydock.add_command(part.part)
drydock.add_command(task.task)
drydock.add_command(node.node)
