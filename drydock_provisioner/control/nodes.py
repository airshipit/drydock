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

from drydock_provisioner import policy
from drydock_provisioner import config

from drydock_provisioner.drivers.node.maasdriver.api_client import MaasRequestFactory
from drydock_provisioner.drivers.node.maasdriver.models.machine import Machines

from .base import StatefulResource


class NodesResource(StatefulResource):
    def __init__(self, orchestrator=None, **kwargs):
        """Object initializer.

        :param orchestrator: instance of orchestrator.Orchestrator
        """
        super().__init__(**kwargs)
        self.orchestrator = orchestrator

    @policy.ApiEnforcer('physical_provisioner:read_data')
    def on_get(self, req, resp):
        try:
            maas_client = MaasRequestFactory(
                config.config_mgr.conf.maasdriver.maas_api_url,
                config.config_mgr.conf.maasdriver.maas_api_key)

            machine_list = Machines(maas_client)
            machine_list.refresh()

            node_view = list()
            for m in machine_list:
                m.get_power_params()
                node_view.append(
                    dict(
                        hostname=m.hostname,
                        memory=m.memory,
                        cpu_count=m.cpu_count,
                        status_name=m.status_name,
                        boot_mac=m.boot_mac,
                        power_state=m.power_state,
                        power_address=m.power_parameters.get('power_address'),
                        boot_ip=m.boot_ip))

            resp.body = json.dumps(node_view)
            resp.status = falcon.HTTP_200
        except Exception as ex:
            self.error(req.context, "Unknown error: %s" % str(ex), exc_info=ex)
            self.return_error(
                resp, falcon.HTTP_500, message="Unknown error", retry=False)

    @policy.ApiEnforcer('physical_provisioner:read_data')
    def on_post(self, req, resp):
        try:
            json_data = self.req_json(req)
            node_filter = json_data.get('node_filter', None)
            site_design = json_data.get('site_design', None)
            if node_filter is None or site_design is None:
                not_provided = []
                if node_filter is None:
                    not_provided.append('node_filter')
                if site_design is None:
                    not_provided.append('site_design')
                self.info(req.context, 'Missing required input value(s) %s' % not_provided)
                self.return_error(
                    resp,
                    falcon.HTTP_400,
                    message='Missing input required value(s) %s' % not_provided,
                    retry=False)
                return
            nodes = self.orchestrator.process_node_filter(node_filter=node_filter,
                                                          site_design=site_design)
            # Guarantees an empty list is returned if there are no nodes
            if not nodes:
                nodes = []
            resp.body = json.dumps(nodes)
            resp.status = falcon.HTTP_200
        except Exception as ex:
            self.error(req.context, "Unknown error: %s" % str(ex), exc_info=ex)
            self.return_error(
                resp, falcon.HTTP_500, message="Unknown error", retry=False)


class NodeBuildDataResource(StatefulResource):
    """Resource for returning build data for a node."""

    @policy.ApiEnforcer('physical_provisioner:read_build_data')
    def on_get(self, req, resp, hostname):
        try:
            latest = req.params.get('latest', 'false').upper()
            latest = True if latest == 'TRUE' else False

            node_bd = self.state_manager.get_build_data(
                node_name=hostname, latest=latest)

            if not node_bd:
                self.return_error(
                    resp,
                    falcon.HTTP_404,
                    message="No build data found",
                    retry=False)
            else:
                node_bd = [bd.to_dict() for bd in node_bd]
                resp.status = falcon.HTTP_200
                resp.body = json.dumps(node_bd)
                resp.content_type = falcon.MEDIA_JSON
        except Exception as ex:
            self.error(req.context, "Unknown error: %s" % str(ex), exc_info=ex)
            self.return_error(
                resp, falcon.HTTP_500, message="Unknown error", retry=False)
