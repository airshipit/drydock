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

import drydock_provisioner.config as config
import drydock_provisioner.objects as objects
import drydock_provisioner.ingester as ingester
import drydock_provisioner.statemgmt as statemgmt
import drydock_provisioner.orchestrator as orch
import drydock_provisioner.control.api as api

def start_drydock():
    objects.register_all()
    
    # Setup root logger
    logger = logging.getLogger('drydock')

    logger.setLevel(config.DrydockConfig.global_config.get('log_level'))
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Specalized format for API logging
    logger = logging.getLogger('drydock.control')
    logger.propagate = False
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(user)s - %(req_id)s - %(external_ctx)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    state = statemgmt.DesignState()

    orchestrator = orch.Orchestrator(config.DrydockConfig.orchestrator_config.get('drivers', {}),
                             state_manager=state)
    input_ingester = ingester.Ingester()
    input_ingester.enable_plugins(config.DrydockConfig.ingester_config.get('plugins', []))

    return api.start_api(state_manager=state, ingester=input_ingester,
                         orchestrator=orchestrator)

drydock = start_drydock()

