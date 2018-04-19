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
"""Model representing MAAS node/machine resource."""
import logging

import drydock_provisioner.error as errors
import drydock_provisioner.drivers.node.maasdriver.models.base as model_base
import drydock_provisioner.drivers.node.maasdriver.models.interface as maas_interface
import drydock_provisioner.drivers.node.maasdriver.models.blockdev as maas_blockdev
import drydock_provisioner.drivers.node.maasdriver.models.volumegroup as maas_vg

from bson import BSON

LOG = logging.getLogger(__name__)

class Machine(model_base.ResourceBase):

    resource_url = 'machines/{resource_id}/'
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
        'boot_ip',
        'owner_data',
        'block_devices',
        'volume_groups',
    ]
    json_fields = ['hostname', 'power_type']

    def __init__(self, api_client, **kwargs):
        super(Machine, self).__init__(api_client, **kwargs)

        # Replace generic dicts with interface collection model
        if hasattr(self, 'resource_id'):
            self.interfaces = maas_interface.Interfaces(
                api_client, system_id=self.resource_id)
            self.interfaces.refresh()
            try:
                self.block_devices = maas_blockdev.BlockDevices(
                    api_client, system_id=self.resource_id)
                self.block_devices.refresh()
            except Exception:
                self.logger.warning("Failed loading node %s block devices." %
                                    (self.resource_id))
            try:
                self.volume_groups = maas_vg.VolumeGroups(
                    api_client, system_id=self.resource_id)
                self.volume_groups.refresh()
            except Exception:
                self.logger.warning("Failed load node %s volume groups." %
                                    (self.resource_id))
        else:
            self.interfaces = None
            self.block_devices = None
            self.volume_groups = None

    def interface_for_ip(self, ip_address):
        """Find the machine interface that will respond to ip_address.

        :param ip_address: The IP address to check interfaces

        :return: The interface that responds to this IP or None
        """
        for i in self.interfaces:
            if i.responds_to_ip(ip_address):
                return i
        return None

    def get_power_params(self):
        """Load power parameters for this node from MaaS."""
        url = self.interpolate_url()

        resp = self.api_client.get(url, op='power_parameters')

        if resp.status_code == 200:
            self.power_parameters = resp.json()

    def reset_network_config(self):
        """Reset the node networking configuration."""
        self.logger.info("Resetting networking configuration on node %s" %
                         (self.resource_id))

        url = self.interpolate_url()

        resp = self.api_client.post(url, op='restore_networking_configuration')

        if not resp.ok:
            msg = "Error resetting network on node %s: %s - %s" \
                  % (self.resource_id, resp.status_code, resp.text)
            self.logger.error(msg)
            raise errors.DriverError(msg)

    def reset_storage_config(self):
        """Reset storage config on this machine.

        Removes all the volume groups/logical volumes and all the physical
        device partitions on this machine.
        """
        self.logger.info("Resetting storage configuration on node %s" %
                         (self.resource_id))
        if self.volume_groups is not None and self.volume_groups.len() > 0:
            for vg in self.volume_groups:
                self.logger.debug("Removing VG %s" % vg.name)
                vg.delete()
        else:
            self.logger.debug("No VGs configured on node %s" %
                              (self.resource_id))

        if self.block_devices is not None:
            for d in self.block_devices:
                if d.partitions is not None and d.partitions.len() > 0:
                    self.logger.debug(
                        "Clearing partitions on device %s" % d.name)
                    d.clear_partitions()
                else:
                    self.logger.debug(
                        "No partitions found on device %s" % d.name)
        else:
            self.logger.debug("No block devices found on node %s" %
                              (self.resource_id))

    def set_storage_layout(self,
                           layout_type='flat',
                           root_device=None,
                           root_size=None,
                           boot_size=None,
                           root_lv_size=None,
                           root_vg_name=None,
                           root_lv_name=None):
        """Set machine storage layout for the root disk.

        :param layout_type: Whether to use 'flat' (partitions) or 'lvm' for the root filesystem
        :param root_device: Name of the block device to place the root partition on
        :param root_size: Size of the root partition in bytes
        :param boot_size: Size of the boot partition in bytes
        :param root_lv_size: Size of the root logical volume in bytes for LVM layout
        :param root_vg_name: Name of the volume group with root LV
        :param root_lv_name: Name of the root LV
        """
        try:
            url = self.interpolate_url()
            self.block_devices.refresh()

            root_dev = self.block_devices.singleton({'name': root_device})

            if root_dev is None:
                msg = "Error: cannot find storage device %s to set as root device" % root_device
                self.logger.error(msg)
                raise errors.DriverError(msg)

            root_dev.set_bootable()

            data = {
                'storage_layout': layout_type,
                'root_device': root_dev.resource_id,
            }

            self.logger.debug("Setting node %s storage layout to %s" %
                              (self.hostname, layout_type))

            if root_size:
                data['root_size'] = root_size

            if boot_size:
                data['boot_size'] = boot_size

            if layout_type == 'lvm':
                if root_lv_size:
                    data['lv_size'] = root_lv_size
                if root_vg_name:
                    data['vg_name'] = root_vg_name
                if root_lv_name:
                    data['lv_name'] = root_lv_name

            resp = self.api_client.post(
                url, op='set_storage_layout', files=data)

            if not resp.ok:
                raise Exception("MAAS Error: %s - %s" % (resp.status_code,
                                                         resp.text))
        except Exception as ex:
            msg = "Error: failed configuring node %s storage layout: %s" % (
                self.resource_id, str(ex))
            self.logger.error(msg)
            raise errors.DriverError(msg)

    def release(self, erase_disk=False):
        """Release a node so it can be redeployed.

        :param erase_disk: If true, the local disks on the machine will be quick wiped
        """
        url = self.interpolate_url()

        options = {'erase': erase_disk}

        resp = self.api_client.post(url, op='release', files=options)

        if not resp.ok:
            brief_msg = ("Error releasing node, received HTTP %s from MaaS" %
                         resp.status_code)
            self.logger.error(brief_msg)
            self.logger.debug("MaaS response: %s" % resp.text)
            raise errors.DriverError(brief_msg)

    def commission(self, debug=False):
        """Start the MaaS commissioning process.

        :param debug: If true, enable ssh on the node and leave it power up after commission
        """
        url = self.interpolate_url()

        # If we want to debug this node commissioning, enable SSH
        # after commissioning and leave the node powered up

        options = {'enable_ssh': '1' if debug else '0'}

        resp = self.api_client.post(url, op='commission', files=options)

        # Need to sort out how to handle exceptions
        if not resp.ok:
            self.logger.error(
                "Error commissioning node, received HTTP %s from MaaS" %
                resp.status_code)
            self.logger.debug("MaaS response: %s" % resp.text)
            raise errors.DriverError(
                "Error commissioning node, received HTTP %s from MaaS" %
                resp.status_code)

    def deploy(self, user_data=None, platform=None, kernel=None):
        """Start the MaaS deployment process.

        :param user_data: cloud-init user data
        :param platform: Which image to install
        :param kernel: Which kernel to enable
        """
        deploy_options = {}

        if user_data is not None:
            deploy_options['user_data'] = user_data

        if platform is not None:
            deploy_options['distro_series'] = platform

        if kernel is not None:
            deploy_options['hwe_kernel'] = kernel

        url = self.interpolate_url()
        resp = self.api_client.post(
            url,
            op='deploy',
            files=deploy_options if len(deploy_options) > 0 else None)

        if not resp.ok:
            self.logger.error(
                "Error deploying node, received HTTP %s from MaaS" %
                resp.status_code)
            self.logger.debug("MaaS response: %s" % resp.text)
            raise errors.DriverError(
                "Error deploying node, received HTTP %s from MaaS" %
                resp.status_code)

    def get_network_interface(self, iface_name):
        if self.interfaces is not None:
            iface = self.interfaces.singleton({'name': iface_name})
            return iface

    def get_details(self):
        url = self.interpolate_url()

        resp = self.api_client.get(url, op='details')

        if resp.status_code == 200:
            detail_config = BSON.decode(resp.content)
            return detail_config

    def set_owner_data(self, key, value):
        """Add/update/remove node owner data.

        If the machine is not currently allocated to a user
        it cannot have owner data

        :param key: Key of the owner data
        :param value: Value of the owner data. If None, the key is removed
        """
        url = self.interpolate_url()

        resp = self.api_client.post(
            url, op='set_owner_data', files={key: value})

        if resp.status_code != 200:
            self.logger.error(
                "Error setting node metadata, received HTTP %s from MaaS" %
                resp.status_code)
            self.logger.debug("MaaS response: %s" % resp.text)
            raise errors.DriverError(
                "Error setting node metadata, received HTTP %s from MaaS" %
                resp.status_code)

    def to_dict(self):
        """Serialize this resource instance into a dict.

        The dict format matches the
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
        """Create a instance of this resource class based on a dict.

        Dict format matches MaaS type attributes

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
                if len(obj_dict['boot_interface']['links']) > 0:
                    refined_dict['boot_ip'] = obj_dict['boot_interface'][
                        'links'][0].get('ip_address', None)

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
        """Acquire a commissioned node fro deployment.

        :param node_name: The hostname of a node to acquire
        """
        self.refresh()

        node = self.singleton({'hostname': node_name})

        if node is None:
            self.logger.info("Node %s not found" % (node_name))
            raise errors.DriverError("Node %s not found" % (node_name))

        if node.status_name != 'Ready':
            self.logger.info(
                "Node %s status '%s' does not allow deployment, should be 'Ready'."
                % (node_name, node.status_name))
            raise errors.DriverError(
                "Node %s status '%s' does not allow deployment, should be 'Ready'."
                % (node_name, node.status_name))

        url = self.interpolate_url()

        resp = self.api_client.post(
            url, op='allocate', files={'system_id': node.resource_id})

        if not resp.ok:
            self.logger.error(
                "Error acquiring node, MaaS returned %s" % resp.status_code)
            self.logger.debug("MaaS response: %s" % resp.text)
            raise errors.DriverError(
                "Error acquiring node, MaaS returned %s" % resp.status_code)

        return node

    def identify_baremetal_node(self, node_model, update_name=True):
        """Find MaaS node resource matching Drydock BaremetalNode.

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

                maas_node = self.singleton({
                    'power_params.power_address':
                    node_oob_ip
                })
            except ValueError:
                self.logger.warn(
                    "Error locating matching MaaS resource for OOB IP %s" %
                    (node_oob_ip))
                return None
        else:
            # Use boot_mac for node's not using IPMI
            node_boot_mac = node_model.boot_mac

            if node_boot_mac is not None:
                maas_node = self.singleton({'boot_mac': node_model.boot_mac})

        if maas_node is None:
            self.logger.info(
                "Could not locate node %s in MaaS" % node_model.name)
            return None

        self.logger.debug("Found MaaS resource %s matching Node %s" %
                          (maas_node.resource_id, node_model.get_id()))

        if maas_node.hostname != node_model.name and update_name:
            maas_node.hostname = node_model.name
            maas_node.update()
            self.logger.debug("Updated MaaS resource %s hostname to %s" %
                              (maas_node.resource_id, node_model.name))

        return maas_node

    def query(self, query):
        """Custom query method to deal with complex fields."""
        result = list(self.resources.values())
        for (k, v) in query.items():
            if k.startswith('power_params.'):
                field = k[13:]
                result = [
                    i for i in result if str(
                        getattr(i, 'power_parameters', {}).get(field, None)) ==
                    str(v)
                ]
            else:
                result = [
                    i for i in result if str(getattr(i, k, None)) == str(v)
                ]

        return result

    def add(self, res):
        """Create a new resource in this collection in MaaS.

        Customize as Machine resources use 'system_id' instead of 'id'

        :param res: A instance of the Machine model
        """
        data_dict = res.to_dict()
        url = self.interpolate_url()

        resp = self.api_client.post(url, files=data_dict)

        if resp.status_code == 200:
            resp_json = resp.json()
            res.set_resource_id(resp_json.get('system_id'))
            return res

        raise errors.DriverError(
            "Failed updating MAAS url %s - return code %s" %
            (url, resp.status_code))
