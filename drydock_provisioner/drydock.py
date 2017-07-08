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
import logging
import sys
import os

from oslo_config import cfg

import drydock_provisioner.config as config
import drydock_provisioner.objects as objects
import drydock_provisioner.ingester as ingester
import drydock_provisioner.statemgmt as statemgmt
import drydock_provisioner.orchestrator as orch
import drydock_provisioner.control.api as api

def start_drydock():
    objects.register_all()

    # Setup configuration parsing
    cli_options = [
        cfg.BoolOpt('debug', short='d', default=False, help='Enable debug logging'),
    ]

    cfg.CONF.register_cli_opts(cli_options)
    config.config_mgr.register_options()
    cfg.CONF(sys.argv[1:])

    if cfg.CONF.debug:
        cfg.CONF.set_override(name='log_level', override='DEBUG', group='logging')

    # Setup root logger
    logger = logging.getLogger(cfg.CONF.logging.global_logger_name)

    logger.setLevel(cfg.CONF.logging.log_level)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Specalized format for API logging
    logger = logging.getLogger(cfg.CONF.logging.control_logger_name)
    logger.propagate = False
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(user)s - %(req_id)s - %(external_ctx)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    state = statemgmt.DesignState()

    orchestrator = orch.Orchestrator(cfg.CONF.plugins, state_manager=state)
    input_ingester = ingester.Ingester()
    input_ingester.enable_plugins(cfg.CONF.plugins.ingester)

    # Check if we have an API key in the environment
    # Hack around until we move MaaS configs to the YAML schema
    if 'MAAS_API_KEY' in os.environ:
        cfg.CONF.set_override(name='maas_api_key', override=os.environ['MAAS_API_KEY'], group='maasdriver')


    wsgi_callable = api.start_api(state_manager=state, ingester=input_ingester, orchestrator=orchestrator)

    # Now that loggers are configured, log the effective config
    cfg.CONF.log_opt_values(logging.getLogger(cfg.CONF.logging.global_logger_name), logging.DEBUG)

    return wsgi_callable


drydock = start_drydock()

