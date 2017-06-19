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
from oslo_config import cfg
import sys

import drydock_provisioner
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

    drydock_provisioner.conf.register_cli_opts(cli_options)
    drydock_provisioner.conf(sys.argv[1:])

    if drydock_provisioner.conf.debug:
        drydock_provisioner.conf.logging.log_level = 'DEBUG'

    # Setup root logger
    logger = logging.getLogger(drydock_provisioner.conf.logging.global_logger_name)

    logger.setLevel(drydock_provisioner.conf.logging.log_level)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Specalized format for API logging
    logger = logging.getLogger(drydock_provisioner.conf.logging.control_logger_name)
    logger.propagate = False
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(user)s - %(req_id)s - %(external_ctx)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    state = statemgmt.DesignState()

    orchestrator = orch.Orchestrator(drydock_provisioner.conf.plugins,
                             state_manager=state)
    input_ingester = ingester.Ingester()
    input_ingester.enable_plugins(drydock_provisioner.conf.plugins.ingester)

    return api.start_api(state_manager=state, ingester=input_ingester,
                         orchestrator=orchestrator)

drydock = start_drydock()

