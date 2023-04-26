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
import base64

from threading import Lock, Condition

import drydock_provisioner.error as errors
import drydock_provisioner.drivers.node.maasdriver.models.base as model_base
import drydock_provisioner.drivers.node.maasdriver.models.interface as maas_interface
import drydock_provisioner.drivers.node.maasdriver.models.blockdev as maas_blockdev
import drydock_provisioner.drivers.node.maasdriver.models.volumegroup as maas_vg
import drydock_provisioner.drivers.node.maasdriver.models.node_results as maas_nr

from bson import BSON

LOG = logging.getLogger(__name__)

power_lock = Lock()
power_cv = Condition(lock=power_lock)


class Machine(model_base.ResourceBase):

    resource_url = 'machines/{resource_id}/'
    fields = [
        'resource_id', 'hostname', 'power_type', 'power_state',
        'power_parameters', 'interfaces', 'boot_interface', 'memory',
        'cpu_count', 'tag_names', 'status_name', 'boot_mac', 'boot_ip',
        'owner_data', 'block_devices', 'volume_groups', 'domain'
    ]
    json_fields = ['hostname', 'power_type', 'domain']

    def __init__(self, api_client, **kwargs):
        super(Machine, self).__init__(api_client, **kwargs)

        # Replace generic dicts with interface collection model
        if getattr(self, 'resource_id', None):
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

    def interface_for_mac(self, mac_address):
        """Find the machine interface that owns the specified ``mac_address``.

        :param str mac_address: The MAC address

        :return: the interface that responds to this MAC or None
        """
        for i in self.interfaces:
            if i.responds_to_mac(mac_address):
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
                    self.logger.debug("Clearing partitions on device %s" %
                                      d.name)
                    d.clear_partitions()
                else:
                    self.logger.debug("No partitions found on device %s" %
                                      d.name)
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

            resp = self.api_client.post(url,
                                        op='set_storage_layout',
                                        files=data)

            if not resp.ok:
                raise Exception("MAAS Error: %s - %s" %
                                (resp.status_code, resp.text))
        except Exception as ex:
            msg = "Error: failed configuring node %s storage layout: %s" % (
                self.resource_id, str(ex))
            self.logger.error(msg)
            raise errors.DriverError(msg)

    def release(self, erase_disk=False, secure_erase=False, quick_erase=False):
        """Release a node so it can be redeployed.
           Release is opposite of acquire/allocate. After a successful release, the node
           will be in Ready state.

        :param erase_disk: If true, the local disks on the machine will be erased.
        :param secure_erase: If erase_disk and secure_erase are set to True, and
                             quick_erase is not specified (default to False), MaaS
                             will try secure_erase first. If the drive does not
                             support secure erase, MaaS will overwirte th entire
                             drive with null butes.
        :param quick_erase:  If erase_disk and quick_erase are true, 1MB at the
                             start and at the end of the drive will be erased to make
                             data recovery inconvenient.
                             If all three parameters are True and the drive supports
                             secure erase, secure_erase will have precedence.
                             If the all three parameters are true, but the disk drive
                             does not support secure erase, MaaS will do quick erase.
                             But, if the disk drive supports neither secure nor
                             quick erase, the disk will be re-written with null bytes.
                             If erase_disk is true, but both secure_erase and quick_erase
                             are Fasle (default), MAAS will overwrite the whole disk
                             with null bytes.
                             If erase_disk is false, MaaS will not erase the drive, before
                             releasing the node.
        """
        url = self.interpolate_url()

        options = {
            'erase': erase_disk,
            'secure_erase': secure_erase,
            'quick_erase': quick_erase,
        }

        resp = self.api_client.post(url, op='release', files=options)

        if not resp.ok:
            brief_msg = ("Error releasing node, received HTTP %s from MaaS" %
                         resp.status_code)
            self.logger.error(brief_msg)
            self.logger.debug("MaaS response: %s" % resp.text)
            raise errors.DriverError(brief_msg)

    def delete(self):
        """ Reset the node storage, and delete it.
           After node deletion, the node resource is purged from MaaS resources.
           MaaS API machine delete call, only removes the machine from MaaS resource list.
           AFter delete, he namchine needs to be manually pwowered on to be re-enlisted
           in MaaS as a New node.

        :param erase_disk: If true, the node storage is reset, before node resource
         is deleted from maas.
        """
        url = self.interpolate_url()
        resp = self.api_client.delete(url)

        if not resp.ok:
            brief_msg = ("Error deleting node, received HTTP %s from MaaS" %
                         resp.status_code)
            self.logger.error(brief_msg)
            self.logger.debug("MaaS response: %s" % resp.text)
            raise errors.DriverError(brief_msg)

    def commission(self, debug=False, skip_bmc_config=False):
        """Start the MaaS commissioning process.

        :param debug: If true, enable ssh on the node and leave it power up after commission
        :param skip_bmc_config: If true, skip re-configuration of the BMC for IPMI based machines
        """
        url = self.interpolate_url()

        # If we want to debug this node commissioning, enable SSH
        # after commissioning and leave the node powered up

        options = {
            'enable_ssh': '1' if debug else '0',
            'skip_bmc_config': '1' if skip_bmc_config else '0',
        }

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

        :param user_data: ``str`` of cloud-init user data
        :param platform: Which image to install
        :param kernel: Which kernel to enable
        """
        deploy_options = {}

        if user_data is not None:
            deploy_options['user_data'] = base64.b64encode(
                user_data.encode('utf-8')).decode('utf-8')

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

    def get_task_results(self, result_type='all'):
        """Get the result from tasks run during node deployment.

        :param str result_type: the type of results to return. One of
                         ``all``, ``commissioning``, ``testing``, ``deploy``
        """
        node_results = maas_nr.NodeResults(self.api_client,
                                           system_id_list=[self.resource_id],
                                           result_type=result_type)
        node_results.refresh()

        return node_results

    def set_owner_data(self, key, value):
        """Add/update/remove node owner data.

        If the machine is not currently allocated to a user
        it cannot have owner data

        :param key: Key of the owner data
        :param value: Value of the owner data. If None, the key is removed
        """
        url = self.interpolate_url()

        resp = self.api_client.post(url,
                                    op='set_workload_annotations',
                                    files={key: value})

        if resp.status_code != 200:
            self.logger.error(
                "Error setting node metadata, received HTTP %s from MaaS" %
                resp.status_code)
            self.logger.debug("MaaS response: %s" % resp.text)
            raise errors.DriverError(
                "Error setting node metadata, received HTTP %s from MaaS" %
                resp.status_code)

    def set_power_parameters(self, power_type, **kwargs):
        """Set power parameters for this node.

        Only available after the node has been added to MAAS.

        :param power_type: The type of power management for the node
        :param kwargs: Each kwargs key will be prepended with 'power_parameters_' and
                       added to the list of updates for the node.
        """
        with power_cv:
            if not power_type:
                raise errors.DriverError(
                    "Cannot set power parameters. Must specify a power type.")

            url = self.interpolate_url()

            if kwargs:
                power_params = dict()

                self.logger.debug("Setting node power type to %s." %
                                  power_type)
                self.power_type = power_type
                power_params['power_type'] = power_type

                for k, v in kwargs.items():
                    power_params['power_parameters_' + k] = v

                self.logger.debug("Updating node %s power parameters: %s" % (
                    self.hostname,
                    str({
                        **power_params,
                        **{
                            k: "<redacted>"
                            for k in power_params if k in [
                                "power_parameters_power_pass"
                            ]
                        },
                    }),
                ))
                resp = self.api_client.put(url, files=power_params)

                if resp.status_code == 200:
                    return True

                raise errors.DriverError(
                    "Failed updating power parameters MAAS url %s - return code %s\n"
                    % (url, resp.status_code.resp.text))

    def reset_power_parameters(self):
        """Reset power type and parameters for this node to manual.
        This is done to address the MaaS api issue detecting multiple BMC NIC
        after a node delete.

        Only available after the node has been added to MAAS.
        """
        with power_cv:
            url = self.interpolate_url()

            self.logger.debug(
                "Resetting node power type for machine {}".format(
                    self.resource_id))
            self.power_type = 'manual'
            power_params = {'power_type': 'manual'}
            resp = self.api_client.put(url, files=power_params)

            if resp.status_code == 200:
                return True

            raise errors.DriverError(
                "Failed updating power parameters MAAS url {} - return code {}\n"
                .format(url, resp.status_code.resp.text))

    def update_identity(self, n, domain="local", use_node_oob_params=False):
        """Update this node's identity based on the Node object ``n``

        :param objects.Node n: The Node object to use as reference
        :param str domain: The DNS domain to register this node under
        :param bool use_node_oob_params: If true, overwrite the discovered OOB params (type and creds)
                    with those in the Node object. Applies to compatible types (i.e. ipmi and redfish)
        """
        try:
            self.hostname = n.name
            self.domain = domain
            self.update()
            if n.oob_type == 'libvirt':
                self.logger.debug(
                    "Updating node %s MaaS power parameters for libvirt." %
                    (n.name))
                oob_params = n.oob_parameters
                self.set_power_parameters(
                    'virsh',
                    power_address=oob_params.get('libvirt_uri'),
                    power_id=n.name)
            elif use_node_oob_params and (n.oob_type == "ipmi"
                                          or n.oob_type == "redfish"):
                self.logger.debug(
                    "Updating node {} MaaS power parameters for {}.".format(
                        n.name, n.oob_type))
                oob_params = n.oob_parameters
                oob_network = oob_params.get("network")
                oob_address = n.get_network_address(oob_network)
                self.set_power_parameters(
                    n.oob_type,
                    power_address=oob_address,
                    power_user=oob_params.get("account"),
                    power_pass=oob_params.get("credential"),
                )
            self.logger.debug("Updated MaaS resource %s hostname to %s" %
                              (self.resource_id, n.name))
        except Exception as ex:
            self.logger.debug("Error updating MAAS node: %s" % str(ex))

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
        self.refresh(params={'hostname': node_name})

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

        resp = self.api_client.post(url,
                                    op='allocate',
                                    files={'system_id': node.resource_id})

        if not resp.ok:
            self.logger.error("Error acquiring node, MaaS returned %s" %
                              resp.status_code)
            self.logger.debug("MaaS response: %s" % resp.text)
            raise errors.DriverError("Error acquiring node, MaaS returned %s" %
                                     resp.status_code)

        return node

    def identify_baremetal_node(self, node_model, probably_exists=True):
        """Find MaaS node resource matching Drydock BaremetalNode.

        Performs one or more queries to the MaaS API to find a Machine matching
        the provided Drydock BaremetalNode model, in the following order, and
        returns the first match found:

        1. If ``probably_exists`` is True, queries by hostname:
                GET /MAAS/api/2.0/machines/?hostname={hostname}
        2a. For ipmi or redfish, looks for a matching BMC address:
                GET /MAAS/api/2.0/machines/?op=power_parameters
            and if a matching system_id is found:
                GET /MAAS/api/2.0/machines/{system_id}/
        2b. For virsh, queries by mac address:
            GET /MAAS/api/2.0/machines/?mac_address={mac_address}

        :param node_model: Instance of objects.node.BaremetalNode to search
                           MaaS for matching resource
        :param probably_exists: whether the machine is likely to exist in MAAS
                                with the correct hostname
        :returns: instance of maasdriver.models.Machine
        """
        maas_node = None

        if probably_exists:
            maas_node = self.find_node_with_hostname(node_model.name)
            if maas_node:
                return maas_node

        if node_model.oob_type == 'ipmi' or node_model.oob_type == 'redfish':
            node_oob_network = node_model.oob_parameters['network']
            node_oob_ip = node_model.get_network_address(node_oob_network)

            if node_oob_ip is None:
                self.logger.warn("Node model missing OOB IP address")
                raise ValueError('Node model missing OOB IP address')

            maas_node = self.find_node_with_power_address(node_oob_ip)
        else:
            # Use boot_mac for node's not using IPMI
            maas_node = self.find_node_with_mac(node_model.boot_mac)

        if maas_node is None:
            self.logger.info("Could not locate node %s in MaaS" %
                             node_model.name)
        else:
            self.logger.debug("Found MaaS resource %s matching Node %s" %
                              (maas_node.resource_id, node_model.get_id()))

        return maas_node

    def find_node_with_hostname(self, hostname):
        """Find the first maching node with hostname ``hostname``"""
        url = self.interpolate_url()
        # query the MaaS API for machines with a matching mac address.
        # this call returns a json list, each member representing a complete
        # Machine
        self.logger.debug("Finding {} with hostname: {}".format(
            self.collection_resource.__name__, hostname))

        resp = self.api_client.get(url, params={"hostname": hostname})

        if resp.status_code == 200:
            json_list = resp.json()

            for node in json_list:
                # construct a Machine from the first API result and return it
                self.logger.debug(
                    "Finding {} with hostname: {}: Found: {}: {}".format(
                        self.collection_resource.__name__,
                        hostname,
                        node.get("system_id"),
                        node.get("hostname"),
                    ))
                return self.collection_resource.from_dict(
                    self.api_client, node)

        return None

    def find_node_with_power_address(self, power_address):
        """Find the first matching node that has a BMC with IP ``power_address``"""
        url = self.interpolate_url()
        # query the MaaS API for all power parameters at once.
        # this call returns a json dict, mapping system id to power parameters

        self.logger.debug("Finding {} with power address: {}".format(
            self.collection_resource.__name__, power_address))

        resp = self.api_client.get(url, op="power_parameters")

        if resp.status_code == 200:
            json_dict = resp.json()

            for system_id, power_params in json_dict.items():
                self.logger.debug(
                    "Finding {} with power address: {}: Considering: {}: {}".
                    format(
                        self.collection_resource.__name__,
                        power_address,
                        system_id,
                        power_params.get("power_address"),
                    ))
                if power_params.get("power_address") == power_address:
                    self.logger.debug(
                        "Finding {} with power address: {}: Found: {}: {}".
                        format(
                            self.collection_resource.__name__,
                            power_address,
                            system_id,
                            power_params.get("power_address"),
                        ))

                    # the API result isn't quite enough to contruct a Machine,
                    # so construct one with the system_id and then refresh
                    res = self.collection_resource(
                        self.api_client,
                        resource_id=system_id,
                        power_parameters=power_params,
                    )
                    res.refresh()
                    return res

        return None

    def find_node_with_mac(self, mac_address):
        """Find the first maching node that own a NIC with ``mac_address``"""
        url = self.interpolate_url()
        # query the MaaS API for machines with a matching mac address.
        # this call returns a json list, each member representing a complete
        # Machine
        resp = self.api_client.get(url, params={'mac_address': mac_address})

        if resp.status_code == 200:
            json_list = resp.json()

            # if len(json_list) > 1:
            #     # XXX: is this check worth it? maybe we ignore
            #     raise ValueError('Multiple machines found with mac_address: {}'.format(mac_address))

            for o in json_list:
                # construct a Machine from the first API result and return it
                return self.collection_resource.from_dict(self.api_client, o)

        return None

    def query(self, query):
        """Custom query method to deal with complex fields."""
        result = list(self.resources.values())
        for (k, v) in query.items():
            if k.startswith('power_params.'):
                field = k[13:]
                result = [
                    i for i in result if str(
                        getattr(i, 'power_parameters', {}).get(field, None))
                    == str(v)
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

    def empty_refresh(self):
        """Check connectivity to MAAS machines API

        Sends a valid query that should return an empty list of machines
        """
        self.refresh(params={'mac_address': '00:00:00:00:00:00'})
