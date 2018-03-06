# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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

from drydock_provisioner.control.base import StatefulResource
from drydock_provisioner.drivers.node.maasdriver.actions.node import ValidateNodeServices
from drydock_provisioner.objects.healthcheck import HealthCheck
from drydock_provisioner.objects.healthcheck import HealthCheckMessage
from drydock_provisioner.objects.fields import ActionResult
import drydock_provisioner.objects.fields as hd_fields
import drydock_provisioner.policy as policy


class HealthResource(StatefulResource):
    """
    Returns empty response body that Drydock is healthy
    """

    def __init__(self, orchestrator=None, **kwargs):
        """Object initializer.

        :param orchestrator: instance of Drydock orchestrator
        """
        super().__init__(**kwargs)
        self.orchestrator = orchestrator

    def on_get(self, req, resp):
        """
        Returns 204 on healthy, otherwise 503, without response body.
        """
        hc = HealthCheckCombined(
            state_manager=self.state_manager,
            orchestrator=self.orchestrator,
            extended=False)
        return hc.get(req, resp)


class HealthExtendedResource(StatefulResource):
    """
    Returns response body that Drydock is healthy
    """

    def __init__(self, orchestrator=None, **kwargs):
        """Object initializer.

        :param orchestrator: instance of Drydock orchestrator
        """
        super().__init__(**kwargs)
        self.orchestrator = orchestrator

    @policy.ApiEnforcer('physical_provisioner:health_data')
    def on_get(self, req, resp):
        """
        Returns 200 on success, otherwise 503, with a response body.
        """
        hc = HealthCheckCombined(
            state_manager=self.state_manager,
            orchestrator=self.orchestrator,
            extended=True)
        return hc.get(req, resp)


class HealthCheckCombined(object):
    """
    Returns Drydock health check status.
    """

    def __init__(self, state_manager=None, orchestrator=None, extended=False):
        """Object initializer.

        :param orchestrator: instance of Drydock orchestrator
        """
        self.state_manager = state_manager
        self.orchestrator = orchestrator
        self.extended = extended

    def get(self, req, resp):
        """
        Returns updated response with body if extended.
        """
        health_check = HealthCheck()
        # Test database connection
        try:
            now = self.state_manager.get_now()
            if now is None:
                raise Exception('None received from database for now()')
        except Exception as ex:
            hcm = HealthCheckMessage(
                msg='Unable to connect to database', error=True)
            health_check.add_detail_msg(msg=hcm)

        # Test MaaS connection
        try:
            task = self.orchestrator.create_task(
                action=hd_fields.OrchestratorAction.Noop)
            maas_validation = ValidateNodeServices(task, self.orchestrator,
                                                   self.state_manager)
            maas_validation.start()
            if maas_validation.task.get_status() == ActionResult.Failure:
                raise Exception('MaaS task failure')
        except Exception as ex:
            hcm = HealthCheckMessage(
                msg='Unable to connect to MaaS', error=True)
            health_check.add_detail_msg(msg=hcm)

        if self.extended:
            resp.body = json.dumps(health_check.to_dict())

        if health_check.is_healthy() and self.extended:
            resp.status = falcon.HTTP_200
        elif health_check.is_healthy():
            resp.status = falcon.HTTP_204
        else:
            resp.status = falcon.HTTP_503
