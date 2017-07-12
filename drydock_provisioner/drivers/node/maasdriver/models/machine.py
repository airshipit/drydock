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

import drydock_provisioner.error as errors
import drydock_provisioner.drivers.node.maasdriver.models.base as model_base
import drydock_provisioner.drivers.node.maasdriver.models.interface as maas_interface

import bson
import yaml

class Machine(model_base.ResourceBase):

    resource_url = 'machines/{resource_id}/'
    fields = ['resource_id', 'hostname', 'power_type', 'power_state', 'power_parameters', 'interfaces',
              'boot_interface', 'memory', 'cpu_count', 'tag_names', 'status_name', 'boot_mac', 'owner_data']
    json_fields = ['hostname', 'power_type']

    def __init__(self, api_client, **kwargs):
        super(Machine, self).__init__(api_client, **kwargs)

        # Replace generic dicts with interface collection model
        if getattr(self, 'resource_id', None) is not None:
            self.interfaces = maas_interface.Interfaces(api_client, system_id=self.resource_id)
            self.interfaces.refresh()
        else:
            self.interfaces = None

    def get_power_params(self):
        url = self.interpolate_url()

        resp = self.api_client.get(url, op='power_parameters')

        if resp.status_code == 200:
            self.power_parameters = resp.json()

    def commission(self, debug=False):
        url = self.interpolate_url()

        # If we want to debug this node commissioning, enable SSH
        # after commissioning and leave the node powered up

        options = {'enable_ssh': '1' if debug else '0'}

        resp = self.api_client.post(url, op='commission', files=options)

        # Need to sort out how to handle exceptions
        if not resp.ok:
            self.logger.error("Error commissioning node, received HTTP %s from MaaS" % resp.status_code)
            self.logger.debug("MaaS response: %s" % resp.text)
            raise errors.DriverError("Error commissioning node, received HTTP %s from MaaS" % resp.status_code)

    def deploy(self, user_data=None, platform=None, kernel=None):
        deploy_options = {}

        if user_data is not None:
            deploy_options['user_data'] = user_data

        if platform is not None:
            deploy_options['distro_series'] = platform

        if kernel is not None:
            deploy_options['hwe_kernel'] = kernel

        url = self.interpolate_url()
        resp = self.api_client.post(url, op='deploy',
                                files=deploy_options if len(deploy_options) > 0 else None)

        if not resp.ok:
            self.logger.error("Error deploying node, received HTTP %s from MaaS" % resp.status_code)
            self.logger.debug("MaaS response: %s" % resp.text)
            raise errors.DriverError("Error deploying node, received HTTP %s from MaaS" % resp.status_code)

    def get_network_interface(self, iface_name):
        if self.interfaces is not None:
            iface = self.interfaces.singleton({'name': iface_name})
            return iface

    def get_details(self):
        url = self.interpolate_url()

        resp = self.api_client.get(url, op='details')

        if resp.status_code == 200:
            detail_config = bson.loads(resp.text)
            return detail_config

    def set_owner_data(self, key, value):
        """
        Add/update/remove node owner data. If the machine is not currently allocated to a user
        it cannot have owner data

        :param key: Key of the owner data
        :param value: Value of the owner data. If None, the key is removed
        """

        url = self.interpolate_url()

        resp = self.api_client.post(url, op='set_owner_data', files={key: value})

        if resp.status_code != 200:
            self.logger.error("Error setting node metadata, received HTTP %s from MaaS" % resp.status_code)
            self.logger.debug("MaaS response: %s" % resp.text)
            raise errors.DriverError("Error setting node metadata, received HTTP %s from MaaS" % resp.status_code)


    def to_dict(self):
        """
        Serialize this resource instance into a dict matching the
        MAAS representation of the resource
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
        """
        Create a instance of this resource class based on a dict
        of MaaS type attributes

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
                refined_dict['boot_mac'] = obj_dict['boot_interface']['mac_address']

        i = cls(api_client, **refined_dict)
        return i

class Machines(model_base.ResourceCollectionBase):

    collection_url = 'machines/'
    collection_resource = Machine

    def __init__(self, api_client, **kwargs):
        super(Machines, self).__init__(api_client)

    # Add the OOB power parameters to each machine instance
    def collect_power_params(self):
        for k, v in self.resources.items():
            v.get_power_params()

    def acquire_node(self, node_name):
        """
        Acquire a commissioned node fro deployment

        :param node_name: The hostname of a node to acquire
        """

        self.refresh()

        node = self.singleton({'hostname': node_name})

        if node is None:
            self.logger.info("Node %s not found" % (node_name))
            raise errors.DriverError("Node %s not found" % (node_name))

        if node.status_name != 'Ready':
            self.logger.info("Node %s status '%s' does not allow deployment, should be 'Ready'." %
                                    (node_name, node.status_name))
            raise errors.DriverError("Node %s status '%s' does not allow deployment, should be 'Ready'." %
                                    (node_name, node.status_name))

        url = self.interpolate_url()

        resp = self.api_client.post(url, op='allocate', files={'system_id': node.resource_id})

        if not resp.ok:
            self.logger.error("Error acquiring node, MaaS returned %s" % resp.status_code)
            self.logger.debug("MaaS response: %s" % resp.text)
            raise errors.DriverError("Error acquiring node, MaaS returned %s" % resp.status_code)

        return node
    
    def identify_baremetal_node(self, node_model, update_name=True):
        """
        Search all the defined MaaS Machines and attempt to match
        one against the provided Drydock BaremetalNode model. Update
        the MaaS instance with the correct hostname

        :param node_model: Instance of objects.node.BaremetalNode to search MaaS for matching resource
        :param update_name: Whether Drydock should update the MaaS resource name to match the Drydock design
        """
        
        maas_node = None

        if node_model.oob_type == 'ipmi':
            node_oob_network = node_model.oob_parameters['network']
            node_oob_ip = node_model.get_network_address(node_oob_network)

            if node_oob_ip is None:
                self.logger.warn("Node model missing OOB IP address")
                raise ValueError('Node model missing OOB IP address')

            try:
                self.collect_power_params()

                maas_node = self.singleton({'power_params.power_address': node_oob_ip})
            except ValueError as ve:
                self.logger.warn("Error locating matching MaaS resource for OOB IP %s" % (node_oob_ip))
                return None
        else:
            # Use boot_mac for node's not using IPMI
            node_boot_mac = node_model.boot_mac

            if node_boot_mac is not None:
                maas_node = self.singleton({'boot_mac': node_model.boot_mac})

        if maas_node is None:
            self.logger.info("Could not locate node %s in MaaS" % node_model.name)
            return None

        self.logger.debug("Found MaaS resource %s matching Node %s" % (maas_node.resource_id, node_model.get_id()))

        if maas_node.hostname != node_model.name and update_name:
            maas_node.hostname = node_model.name
            maas_node.update()
            self.logger.debug("Updated MaaS resource %s hostname to %s" % (maas_node.resource_id, node_model.name))

        return maas_node

    def query(self, query):
        """
        Custom query method to deal with complex fields
        """
        result = list(self.resources.values())
        for (k, v) in query.items():
            if k.startswith('power_params.'):
                field = k[13:]
                result = [i for i in result
                          if str(getattr(i,'power_parameters', {}).get(field, None)) == str(v)]
            else:
                result = [i for i in result
                          if str(getattr(i, k, None)) == str(v)]

        return result


    def add(self, res):
        """
        Create a new resource in this collection in MaaS

        Customize as Machine resources use 'system_id' instead of 'id'
        """
        data_dict = res.to_dict()
        url = self.interpolate_url()

        resp = self.api_client.post(url, files=data_dict)

        if resp.status_code == 200:
            resp_json = resp.json()
            res.set_resource_id(resp_json.get('system_id'))
            return res
        
        raise errors.DriverError("Failed updating MAAS url %s - return code %s"
                % (url, resp.status_code))
