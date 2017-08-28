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
"""Model for MaaS rack-controller API resource."""

import bson

import drydock_provisioner.drivers.node.maasdriver.models.base as model_base
import drydock_provisioner.drivers.node.maasdriver.models.interface as maas_interface
import drydock_provisioner.drivers.node.maasdriver.models.machine as maas_machine


class RackController(maas_machine.Machine):
    """Model for a rack controller singleton."""

    # These are the services that must be 'running'
    # to consider a rack controller healthy
    REQUIRED_SERVICES = ['http', 'tgt', 'dhcpd', 'ntp_rack', 'rackd', 'tftp']
    resource_url = 'rackcontrollers/{resource_id}/'
    fields = [
        'resource_id',
        'hostname',
        'power_type',
        'power_state',
        'power_parameters',
        'interfaces',
        'boot_interface',
        'memory',
        'cpu_count',
        'tag_names',
        'status_name',
        'boot_mac',
        'owner_data',
        'service_set',
    ]
    json_fields = ['hostname', 'power_type']

    def __init__(self, api_client, **kwargs):
        super().__init__(api_client, **kwargs)

    def get_services(self):
        """Get status of required services on this rack controller."""
        self.refresh()

        svc_status = {svc: None for svc in RackController.REQUIRED_SERVICES}

        self.logger.debug("Checking service status on rack controller %s" %
                          (self.resource_id))

        for s in getattr(self, 'service_set', []):
            svc = s.get('name')
            status = s.get('status')
            if svc in svc_status:
                self.logger.debug("Service %s on rack controller %s is %s" %
                                  (svc, self.resource_id, status))
                svc_status[svc] = status

        return svc_status


class RackControllers(model_base.ResourceCollectionBase):
    """Model for a collection of rack controllers."""

    collection_url = 'rackcontrollers/'
    collection_resource = RackController

    def __init__(self, api_client, **kwargs):
        super().__init__(api_client)
