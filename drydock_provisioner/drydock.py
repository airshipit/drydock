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
"""Service initialization for the Drydock API."""
import logging
import sys
import os
import threading

from oslo_config import cfg

from drydock_provisioner import policy
from drydock_provisioner.statemgmt.state import DrydockState
from drydock_provisioner.ingester.ingester import Ingester
from drydock_provisioner.orchestrator.orchestrator import Orchestrator

import drydock_provisioner.config as config
import drydock_provisioner.objects as objects
import drydock_provisioner.control.api as api


def start_drydock(enable_keystone=True):
    objects.register_all()

    # Setup configuration parsing
    cli_options = [
        cfg.BoolOpt(
            'debug', short='d', default=False, help='Enable debug logging'),
    ]

    config.config_mgr.conf.register_cli_opts(cli_options)
    config.config_mgr.register_options(enable_keystone=enable_keystone)
    config.config_mgr.conf(sys.argv[1:])

    if config.config_mgr.conf.debug:
        config.config_mgr.conf.set_override(
            name='log_level', override='DEBUG', group='logging')

    # Setup root logger
    logger = logging.getLogger(
        config.config_mgr.conf.logging.global_logger_name)

    logger.setLevel(config.config_mgr.conf.logging.log_level)
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Specalized format for API logging
    logger = logging.getLogger(
        config.config_mgr.conf.logging.control_logger_name)
    logger.propagate = False
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(user)s - %(req_id)s - %(external_ctx)s - %(message)s'
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    state = DrydockState()
    state.connect_db()

    input_ingester = Ingester()
    input_ingester.enable_plugin(config.config_mgr.conf.plugins.ingester)

    orchestrator = Orchestrator(
        enabled_drivers=config.config_mgr.conf.plugins,
        state_manager=state,
        ingester=input_ingester)

    orch_thread = threading.Thread(target=orchestrator.watch_for_tasks)
    orch_thread.start()

    # Check if we have an API key in the environment
    # Hack around until we move MaaS configs to the YAML schema
    if 'MAAS_API_KEY' in os.environ:
        config.config_mgr.conf.set_override(
            name='maas_api_key',
            override=os.environ['MAAS_API_KEY'],
            group='maasdriver')

    # Setup the RBAC policy enforcer
    policy.policy_engine = policy.DrydockPolicy()
    policy.policy_engine.register_policy()

    # Ensure that the policy_engine is initialized before starting the API
    wsgi_callable = api.start_api(
        state_manager=state,
        ingester=input_ingester,
        orchestrator=orchestrator)

    # Now that loggers are configured, log the effective config
    config.config_mgr.conf.log_opt_values(
        logging.getLogger(config.config_mgr.conf.logging.global_logger_name),
        logging.DEBUG)

    return wsgi_callable


# Initialization compatible with PasteDeploy
def paste_start_drydock(global_conf, disable=None):
    enable_keystone = True

    if disable is not None:
        for d in disable.split():
            if d == 'keystone':
                enable_keystone = False

    return start_drydock(enable_keystone=enable_keystone)
