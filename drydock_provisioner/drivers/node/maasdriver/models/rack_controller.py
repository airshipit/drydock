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


class RackController(model_base.ResourceBase):
    """Model for a rack controller singleton."""

    # These are the services that must be 'running'
    # to consider a rack controller healthy
    REQUIRED_SERVICES = ['http', 'tgt', 'dhcpd', 'ntp_rack', 'rackd',
                         'tftp']
    resource_url = 'rackcontrollers/{resource_id}/'
    fields = [
        'resource_id', 'hostname', 'power_type', 'power_state',
        'power_parameters', 'interfaces', 'boot_interface', 'memory',
        'cpu_count', 'tag_names', 'status_name', 'boot_mac', 'owner_data',
        'service_set',
    ]
    json_fields = ['hostname', 'power_type']

    def __init__(self, api_client, **kwargs):
        super().__init__(api_client, **kwargs)

        # Replace generic dicts with interface collection model
        if getattr(self, 'resource_id', None) is not None:
            self.interfaces = maas_interface.Interfaces(
                api_client, system_id=self.resource_id)
            self.interfaces.refresh()
        else:
            self.interfaces = None

    def get_power_params(self):
        """Get parameters for managing server power."""
        url = self.interpolate_url()

        resp = self.api_client.get(url, op='power_parameters')

        if resp.status_code == 200:
            self.power_parameters = resp.json()

    def get_network_interface(self, iface_name):
        """Retrieve network interface on this machine."""
        if self.interfaces is not None:
            iface = self.interfaces.singleton({'name': iface_name})
            return iface

    def get_services(self):
        """Get status of required services on this rack controller."""
        self.refresh()

        svc_status = {svc: None for svc in RackController.REQUIRED_SERVICES}

        self.logger.debug("Checking service status on rack controller %s" % (self.resource_id))

        for s in getattr(self, 'service_set', []):
            svc = s.get('name')
            status = s.get('status')
            if svc in svc_status:
                self.logger.debug("Service %s on rack controller %s is %s" %
                                  (svc, self.resource_id, status))
                svc_status[svc] = status

        return svc_status

    def get_details(self):
        url = self.interpolate_url()

        resp = self.api_client.get(url, op='details')

        if resp.status_code == 200:
            detail_config = bson.loads(resp.text)
            return detail_config

    def to_dict(self):
        """Serialize this resource instance.

        Serialize into a dict matching the MAAS representation of the resource
        """
        data_dict = {}

        for f in self.json_fields:
            if getattr(self, f, None) is not None:
                if f == 'resource_id':
                    data_dict['system_id'] = getattr(self, f)
                else:
                    data_dict[f] = getattr(self, f)

        return data_dict

    @classmethod
    def from_dict(cls, api_client, obj_dict):
        """Create a instance of this resource class based on a dict of MaaS type attributes.

        Customized for Machine due to use of system_id instead of id
        as resource key

        :param api_client: Instance of api_client.MaasRequestFactory for accessing MaaS API
        :param obj_dict: Python dict as parsed from MaaS API JSON representing this resource type
        """
        refined_dict = {k: obj_dict.get(k, None) for k in cls.fields}

        if 'system_id' in obj_dict.keys():
            refined_dict['resource_id'] = obj_dict.get('system_id')

        # Capture the boot interface MAC to allow for node id of VMs
        if 'boot_interface' in obj_dict.keys():
            if isinstance(obj_dict['boot_interface'], dict):
                refined_dict['boot_mac'] = obj_dict['boot_interface'][
                    'mac_address']

        i = cls(api_client, **refined_dict)
        return i


class RackControllers(model_base.ResourceCollectionBase):
    """Model for a collection of rack controllers."""

    collection_url = 'rackcontrollers/'
    collection_resource = RackController

    def __init__(self, api_client, **kwargs):
        super().__init__(api_client)

    # Add the OOB power parameters to each machine instance
    def collect_power_params(self):
        for k, v in self.resources.items():
            v.get_power_params()

    def query(self, query):
        """Custom query method to deal with complex fields."""
        result = list(self.resources.values())
        for (k, v) in query.items():
            if k.startswith('power_params.'):
                field = k[13:]
                result = [
                    i for i in result
                    if str(
                        getattr(i, 'power_parameters', {}).get(field, None)) ==
                    str(v)
                ]
            else:
                result = [
                    i for i in result if str(getattr(i, k, None)) == str(v)
                ]

        return result
