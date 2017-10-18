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

from drydock_provisioner import policy
from drydock_provisioner import config

from drydock_provisioner.drivers.node.maasdriver.api_client import MaasRequestFactory
from drydock_provisioner.drivers.node.maasdriver.models.machine import Machines

from .base import BaseResource


class NodesResource(BaseResource):
    def __init__(self):
        super().__init__()

    @policy.ApiEnforcer('physical_provisioner:read_data')
    def on_get(self, req, resp):
        try:
            maas_client = MaasRequestFactory(config.config_mgr.conf.maasdriver.maas_api_url,
                                             config.config_mgr.conf.maasdriver.maas_api_key)

            machine_list = Machines(maas_client)
            machine_list.refresh()

            node_view = list()
            for m in machine_list:
                node_view.append(dict(hostname=m.hostname, memory=m.memory, cpu_count=m.cpu_count, status_name=m.status_name, boot_mac=m.boot_mac))

            resp.body = json.dumps(node_view)
            resp.status = falcon.HTTP_200
        except Exception as ex:
            self.error(req.context, "Unknown error: %s" % str(ex), exc_info=ex)
            self.return_error(
                resp, falcon.HTTP_500, message="Unknown error", retry=False)
