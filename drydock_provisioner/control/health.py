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
import falcon
import json

from drydock_provisioner.control.base import BaseResource
from drydock_provisioner.drivers.node.maasdriver.actions.node import ValidateNodeServices
from drydock_provisioner.objects.fields import ActionResult
import drydock_provisioner.objects.fields as hd_fields


class HealthResource(BaseResource):
    """
    Return empty response/body to show
    that Drydock is healthy
    """
    def __init__(self, state_manager=None, orchestrator=None, **kwargs):
        """Object initializer.

        :param state_manager: instance of Drydock state_manager
        """
        super().__init__(**kwargs)
        self.state_manager = state_manager
        self.orchestrator = orchestrator

    def on_get(self, req, resp):
        """
        Returns 204 on success, otherwise 500 with a response body.
        """
        healthy = True
        # Test database connection
        try:
            now = self.state_manager.get_now()
            if now is None:
                raise Exception('None received from database for now()')
        except Exception as ex:
            healthy = False
            resp.body = json.dumps({
                'type': 'error',
                'message': 'Database error',
                'retry': True
            })
            resp.status = falcon.HTTP_500

        # Test MaaS connection
        try:
            task = self.orchestrator.create_task(action=hd_fields.OrchestratorAction.Noop)
            maas_validation = ValidateNodeServices(task, self.orchestrator, self.state_manager)
            maas_validation.start()
            if maas_validation.task.get_status() == ActionResult.Failure:
                raise Exception('MaaS task failure')
        except Exception as ex:
            healthy = False
            resp.body = json.dumps({
                'type': 'error',
                'message': 'MaaS error',
                'retry': True
            })
            resp.status = falcon.HTTP_500

        if healthy:
            resp.status = falcon.HTTP_204
