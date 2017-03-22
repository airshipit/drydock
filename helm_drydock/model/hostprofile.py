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
#
# Models for helm_drydock
#
import logging

from copy import deepcopy

from helm_drydock.orchestrator.enum import SiteStatus
from helm_drydock.orchestrator.enum import NodeStatus
from helm_drydock.model.network import Network
from helm_drydock.model.network import NetworkLink
from helm_drydock.model import Utils

class HostProfile(object):

    def __init__(self, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = kwargs.get('apiVersion', '')

        if self.api_version == "v1.0":
            metadata = kwargs.get('metadata', {})
            spec = kwargs.get('spec', {})

            self.name = metadata.get('name', '')
            self.site = metadata.get('region', '')

            self.parent_profile = spec.get('host_profile', None)
            self.hardware_profile = spec.get('hardware_profile', None)

            oob = spec.get('oob', {})
            self.oob_type = oob.get('type', None)
            self.oob_network = oob.get('network', None)
            self.oob_account = oob.get('account', None)
            self.oob_credential = oob.get('credential', None)

            storage = spec.get('storage', {})
            self.storage_layout = storage.get('layout', 'lvm')

            bootdisk = storage.get('bootdisk', {})
            self.bootdisk_device = bootdisk.get('device', None)
            self.bootdisk_root_size = bootdisk.get('root_size', None)
            self.bootdisk_boot_size = bootdisk.get('boot_size', None)

            partitions = storage.get('partitions', [])
            self.partitions = []

            for p in partitions:
                self.partitions.append(HostPartition(self.api_version, **p))

            interfaces = spec.get('interfaces', [])
            self.interfaces = []

            for i in interfaces:
                self.interfaces.append(HostInterface(self.api_version, **i))

            node_metadata = spec.get('metadata', {})

            metadata_tags = node_metadata.get('tags', [])
            self.tags = []

            for t in metadata_tags:
                self.tags.append(t)

            owner_data = node_metadata.get('owner_data', {})
            self.owner_data = {}

            for k, v in owner_data.items():
                self.owner_data[k] = v

            self.rack = node_metadata.get('rack', None)

        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')

    def get_rack(self):
        return self.rack

    def get_name(self):
        return self.name

    def has_tag(self, tag):
        if tag in self.tags:
            return True

        return False

    def apply_inheritance(self, site):
        # We return a deep copy of the profile so as not to corrupt
        # the original model
        self_copy = deepcopy(self)

        if self.parent_profile is None:
            return self_copy

        parent = site.get_host_profile(self.parent_profile)

        if parent is None:
            raise NameError("Cannot find parent profile %s for %s"
                            % (self.parent_profile, self.name))

        parent = parent.apply_inheritance(site)

        # First compute inheritance for simple fields
        inheritable_field_list = [
            "hardware_profile", "oob_type", "oob_network",
            "oob_credential", "oob_account", "storage_layout",
            "bootdisk_device", "bootdisk_root_size", "bootdisk_boot_size",
            "rack"]

        for f in inheritable_field_list:
            setattr(self_copy, f,
                    Utils.apply_field_inheritance(getattr(self, f, None),
                                                  getattr(parent, f, None)))

        # Now compute inheritance for complex types
        self_copy.tags = Utils.merge_lists(self.tags, parent.tags)

        self_copy.owner_data = Utils.merge_dicts(
            self.owner_data, parent.owner_data)

        self_copy.interfaces = HostInterface.merge_lists(
            self.interfaces, parent.interfaces)

        self_copy.partitions = HostPartition.merge_lists(
            self.partitions, parent.partitions)

        return self_copy


class HostInterface(object):

    def __init__(self, api_version, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = api_version

        if self.api_version == "v1.0":
            self.device_name = kwargs.get('device_name', None)
            self.network_link = kwargs.get('device_link', None)

            self.hardware_slaves = []
            slaves = kwargs.get('slaves', [])

            for s in slaves:
                self.hardware_slaves.append(s)

            self.networks = []
            networks = kwargs.get('networks', [])

            for n in networks:
                self.networks.append(n)
        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')

    # The device attribute may be hardware alias that translates to a
    # physical device address. If the device attribute does not match an
    # alias, we assume it directly identifies a OS device name. When the
    # apply_hardware_profile method is called on the parent Node of this
    # device, the selector will be decided and applied

    def add_selector(self, sel_type, address='', dev_type=''):
        if getattr(self, 'selectors', None) is None:
            self.selectors = []

        new_selector = {}
        new_selector['selector_type'] = sel_type
        new_selector['address'] = address
        new_selector['device_type'] = dev_type

        self.selectors.append(new_selector)

    def get_slave_selectors(self):
        return self.selectors

    # Return number of slaves for this interface
    def get_slave_count(self):
        return len(self.hardware_slaves)

    def apply_link_config(self, net_link):
        if (net_link is not None and
            isinstance(net_link, NetworkLink) and 
            net_link.name == self.network_link):

            self.attached_link = deepcopy(net_link)
            return True
        return False

    def apply_network_config(self, network):
        if network in self.networks:
            if getattr(self, 'attached_networks', None) is None:
                self.attached_networks = []
            self.attached_networks.append(deepcopy(network))
            return True
        else:
            return False

    def set_network_address(self, network_name, address):
        if getattr(self, 'attached_networks', None) is None:
            return False

        for n in self.attached_neteworks:
            if n.name == network_name:
                n.assigned_address = address

    def get_network_configs(self):
        return self.attached_networks

    """
    Merge two lists of HostInterface models with child_list taking
    priority when conflicts. If a member of child_list has a device_name
    beginning with '!' it indicates that HostInterface should be
    removed from the merged list
    """

    @staticmethod
    def merge_lists(child_list, parent_list):
        if len(child_list) == 0:
            return deepcopy(parent_list)

        effective_list = []
        if len(parent_list) == 0:
            for i in child_list:
                if i.device_name.startswith('!'):
                    continue
                else:
                    effective_list.append(deepcopy(i))
            return effective_list

        parent_interfaces = []
        for i in parent_list:
            parent_name = i.device_name
            parent_interfaces.append(parent_name)
            add = True
            for j in child_list:
                if j.device_name == ("!" + parent_name):
                    add = False
                    break
                elif j.device_name == parent_name:
                    m = HostInterface(j.api_version)
                    m.device_name = j.device_name
                    m.network_link = \
                        Utils.apply_field_inheritance(j.network_link,
                                                      i.network_link)
                    s = filter(lambda x: ("!" + x) not in j.hardware_slaves,
                               i.hardware_slaves)
                    s = list(s)

                    s.extend(filter(lambda x: not x.startswith("!"),
                                    j.hardware_slaves))
                    m.hardware_slaves = s

                    n = filter(lambda x: ("!" + x) not in j.networks,
                               i.networks)
                    n = list(n)

                    n.extend(filter(lambda x: not x.startswith("!"),
                                    j.networks))
                    m.networks = n

                    effective_list.append(m)
                    add = False
                    break

            if add:
                effective_list.append(deepcopy(i))

        for j in child_list:
            if (j.device_name not in parent_interfaces
                and not j.device_name.startswith("!")):
                effective_list.append(deepcopy(j))

        return effective_list


class HostPartition(object):

    def __init__(self, api_version, **kwargs):
        self.api_version = api_version

        if self.api_version == "v1.0":
            self.name = kwargs.get('name', None)
            self.device = kwargs.get('device', None)
            self.part_uuid = kwargs.get('part_uuid', None)
            self.size = kwargs.get('size', None)
            self.mountpoint = kwargs.get('mountpoint', None)
            self.fstype = kwargs.get('fstype', 'ext4')
            self.mount_options = kwargs.get('mount_options', 'defaults')
            self.fs_uuid = kwargs.get('fs_uuid', None)
            self.fs_label = kwargs.get('fs_label', None)
        else:
            raise ValueError('Unknown API version of object')

    # The device attribute may be hardware alias that translates to a
    # physical device address. If the device attribute does not match an
    # alias, we assume it directly identifies a OS device name. When the
    # apply_hardware_profile method is called on the parent Node of this
    # device, the selector will be decided and applied

    def set_selector(self, sel_type, address='', dev_type=''):
        selector = {}
        selector['type'] = sel_type
        selector['address'] = address
        selector['device_type'] = dev_type

        self.selector = selector

    def get_selector(self):
        return self.selector

    """
    Merge two lists of HostPartition models with child_list taking
    priority when conflicts. If a member of child_list has a name
    beginning with '!' it indicates that HostPartition should be
    removed from the merged list
    """

    @staticmethod
    def merge_lists(child_list, parent_list):
        if len(child_list) == 0:
            return deepcopy(parent_list)

        effective_list = []
        if len(parent_list) == 0:
            for i in child_list:
                if i.name.startswith('!'):
                    continue
                else:
                    effective_list.append(deepcopy(i))

        inherit_field_list = ["device", "part_uuid", "size",
                              "mountpoint", "fstype", "mount_options",
                              "fs_uuid", "fs_label"]

        parent_partitions = []
        for i in parent_list:
            parent_name = i.name
            parent_partitions.append(parent_name)
            add = True
            for j in child_list:
                if j.name == ("!" + parent_name):
                    add = False
                    break
                elif j.name == parent_name:
                    p = HostPartition(j.api_version)
                    p.name = j.name

                    for f in inherit_field_list:
                        setattr(p, Utils.apply_field_inheritance(getattr(j, f),
                                                                 getattr(i, f))
                                )
                    add = False
                    effective_list.append(p)
            if add:
                effective_list.append(deepcopy(i))

        for j in child_list:
            if j.name not in parent_list:
                effective_list.append(deepcopy(j))

        return effective_list
