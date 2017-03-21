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

            # Design Data
            self.design = {}

            self.design['parent_profile'] = spec.get('host_profile', None)
            self.design['hardware_profile'] = spec.get('hardware_profile', None)


            oob = spec.get('oob', {})

            self.design['oob_type'] = oob.get('type', None)
            self.design['oob_network'] = oob.get('network', None)
            self.design['oob_account'] = oob.get('account', None)
            self.design['oob_credential'] = oob.get('credential', None)

            storage = spec.get('storage', {})
            self.design['storage_layout'] = storage.get('layout', 'lvm')

            bootdisk = storage.get('bootdisk', {})
            self.design['bootdisk_device'] = bootdisk.get('device', None)
            self.design['bootdisk_root_size'] = bootdisk.get('root_size', None)
            self.design['bootdisk_boot_size'] = bootdisk.get('boot_size', None)

            partitions = storage.get('partitions', [])
            self.design['partitions'] = []

            for p in partitions:
                self.design['partitions'].append(HostPartition(self.api_version, **p))

            interfaces = spec.get('interfaces', [])
            self.design['interfaces'] = []

            for i in interfaces:
                self.design['interfaces'].append(HostInterface(self.api_version, **i))

            node_metadata = spec.get('metadata', {})

            metadata_tags = node_metadata.get('tags', [])
            self.design['tags'] = []

            for t in metadata_tags:
                self.design['tags'].append(t)

            owner_data = node_metadata.get('owner_data', {})
            self.design['owner_data'] = {}

            for k, v in owner_data.items():
                self.design['owner_data'][k] = v

            self.design['rack'] = node_metadata.get('rack', None)

        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')

    def get_rack(self):
        return self.design['rack']

    def get_name(self):
        return self.name

    def has_tag(self, tag):
        if tag in self.design['tags']:
            return True

        return False

    def apply_inheritance(self, site):
        # No parent to inherit from, just apply design values
        # and return
        if self.design['parent_profile'] is None:
            self.applied = deepcopy(self.design)
            return

        parent = site.get_host_profile(self.design['parent_profile'])

        if parent is None:
            raise NameError("Cannot find parent profile %s for %s"
                            % (self.design['parent_profile'], self.name))

        parent.apply_inheritance(site)

        # First compute inheritance for simple fields
        inheritable_field_list = [
            "hardware_profile", "oob_type", "oob_network",
            "oob_credential", "oob_account", "storage_layout",
            "bootdisk_device", "bootdisk_root_size", "bootdisk_boot_size",
            "rack"]

        # Create applied data from self design values and parent
        # applied values

        self.applied = {}

        for f in inheritable_field_list:
            self.applied[f] = Utils.apply_field_inheritance(
                                self.design.get(f, None),
                                parent.applied.get(f, None))

        # Now compute inheritance for complex types
        self.applied['tags'] = Utils.merge_lists(self.design['tags'],
                                                 parent.applied['tags'])

        self.applied['owner_data'] = Utils.merge_dicts(
            self.design['owner_data'], parent.applied['owner_data'])

        self.applied['interfaces'] = HostInterface.merge_lists(
            self.design['interfaces'], parent.applied['interfaces'])

        self.applied['partitions'] = HostPartition.merge_lists(
            self.design['partitions'], parent.applied['partitions'])

        return


class HostInterface(object):

    def __init__(self, api_version, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = api_version

        if self.api_version == "v1.0":
            self.device_name = kwargs.get('device_name', None)

            self.design = {}
            self.design['network_link'] = kwargs.get('device_link', None)

            self.design['hardware_slaves'] = []
            slaves = kwargs.get('slaves', [])

            for s in slaves:
                self.design['hardware_slaves'].append(s)

            self.design['networks'] = []
            networks = kwargs.get('networks', [])

            for n in networks:
                self.design['networks'].append(n)
        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')

    # Ensure applied_data exists 
    def ensure_applied_data(self):
        if getattr(self, 'applied', None) is None:
            self.applied = deepcopy(self.design)

        return

    def get_name(self):
        return self.device_name

    def get_applied_hw_slaves(self):
        self.ensure_applied_data()

        return self.applied.get('hardware_slaves', [])

    def get_applied_slave_selectors(self):
        self.ensure_applied_data()

        return self.applied.get('selectors', None)

    # Return number of slaves for this interface
    def get_applied_slave_count(self):
        self.ensure_applied_data()
        
        return len(self.applied.get('hardware_slaves', []))

    def get_network_configs(self):
        self.ensure_applied_data()
        return self.applied.get('attached_networks', [])

    # The device attribute may be hardware alias that translates to a
    # physical device address. If the device attribute does not match an
    # alias, we assume it directly identifies a OS device name. When the
    # apply_hardware_profile method is called on the parent Node of this
    # device, the selector will be decided and applied

    def add_selector(self, sel_type, address='', dev_type=''):
        self.ensure_applied_data()

        if self.applied.get('selectors', None) is None:
            self.applied['selectors'] = []

        new_selector = {}
        new_selector['selector_type'] = sel_type
        new_selector['address'] = address
        new_selector['device_type'] = dev_type

        self.applied['selectors'].append(new_selector)

    def apply_link_config(self, net_link):
        if (net_link is not None and
            isinstance(net_link, NetworkLink) and 
            net_link.name == self.design.get('network_link', '')):

            self.ensure_applied_data()

            self.applied['attached_link'] = deepcopy(net_link)
            return True
        return False

    def apply_network_config(self, network):
        if network.name in self.design['networks']:
            self.ensure_applied_data()
            if self.applied.get('attached_networks', None) is None:
                self.applied['attached_networks'] = []
            self.applied['attached_networks'].append(deepcopy(network))
            return True
        else:
            return False

    def set_network_address(self, network_name, address):
        self.ensure_applied_data()

        if self.applied.get('attached_networks', None) is None:
            return False

        for n in self.applied.get('attached_networks', []):
            if n.name == network_name:
                setattr(n, 'assigned_address', address)

    """
    Merge two lists of HostInterface models with child_list taking
    priority when conflicts. If a member of child_list has a device_name
    beginning with '!' it indicates that HostInterface should be
    removed from the merged list
    """

    @staticmethod
    def merge_lists(child_list, parent_list):
        effective_list = []

        if len(child_list) == 0 and len(parent_list) > 0:
            for p in parent_list:
                pp = deepcopy(p)
                pp.ensure_applied_data()
                effective_list.append(pp)
        elif len(parent_list) == 0 and len(child_list) > 0:
            for i in child_list:
                if i.get_name().startswith('!'):
                    continue
                else:
                    ii = deepcopy(i)
                    ii.ensure_applied_data()
                    effective_list.append(ii)
        elif len(parent_list) > 0 and len(child_list) > 0:
            parent_interfaces = []
            for i in parent_list:
                parent_name = i.get_name()
                parent_interfaces.append(parent_name)
                add = True
                for j in child_list:
                    if j.get_name() == ("!" + parent_name):
                        add = False
                        break
                    elif j.device_name == parent_name:
                        m = HostInterface(j.api_version)
                        m.device_name = j.get_name()
                        m.design['network_link'] = \
                            Utils.apply_field_inheritance(
                                j.design.get('network_link', None),
                                i.applied.get('network_link', None))

                        s = [x for x 
                             in i.applied.get('hardware_slaves', [])
                             if ("!" + x) not in j.design.get(
                                'hardware_slaves', [])]

                        s.extend(
                            [x for x
                             in j.design.get('hardware_slaves', [])
                             if not x.startswith("!")])

                        m.design['hardware_slaves'] = s

                        n = [x for x
                             in i.applied.get('networks',[])
                             if ("!" + x) not in j.design.get(
                                'networks', [])]

                        n.extend(
                            [x for x
                             in j.design.get('networks', [])
                             if not x.startswith("!")])

                        m.design['networks'] = n
                        m.ensure_applied_data()

                        effective_list.append(m)
                        add = False
                        break

                if add:
                    ii = deepcopy(i)
                    ii.ensure_applied_data()
                    effective_list.append(ii)

            for j in child_list:
                if (j.device_name not in parent_interfaces
                    and not j.device_name.startswith("!")):
                    jj = deepcopy(j)
                    jj.ensure_applied_data()
                    effective_list.append(jj)

        return effective_list


class HostPartition(object):

    def __init__(self, api_version, **kwargs):
        self.api_version = api_version

        if self.api_version == "v1.0":
            self.name = kwargs.get('name', None)

            self.design = {}
            self.design['device'] = kwargs.get('device', None)
            self.design['part_uuid'] = kwargs.get('part_uuid', None)
            self.design['size'] = kwargs.get('size', None)
            self.design['mountpoint'] = kwargs.get('mountpoint', None)
            self.design['fstype'] = kwargs.get('fstype', 'ext4')
            self.design['mount_options'] = kwargs.get('mount_options', 'defaults')
            self.design['fs_uuid'] = kwargs.get('fs_uuid', None)
            self.design['fs_label'] = kwargs.get('fs_label', None)

            self.applied = kwargs.get('applied', None)
            self.build = kwargs.get('build', None)
        else:
            raise ValueError('Unknown API version of object')

    # Ensure applied_data exists 
    def ensure_applied_data(self):
        if getattr(self, 'applied', None) is None:
            self.applied = deepcopy(self.design)

        return

    def get_applied_device(self):
        self.ensure_applied_data()

        return self.applied.get('device', '')

    def get_name(self):
        return self.name

    # The device attribute may be hardware alias that translates to a
    # physical device address. If the device attribute does not match an
    # alias, we assume it directly identifies a OS device name. When the
    # apply_hardware_profile method is called on the parent Node of this
    # device, the selector will be decided and applied

    def set_selector(self, sel_type, address='', dev_type=''):
        self.ensure_applied_data()

        selector = {}
        selector['type'] = sel_type
        selector['address'] = address
        selector['device_type'] = dev_type

        self.applied['selector'] = selector

    def get_selector(self):
        self.ensure_applied_data()
        return self.applied.get('selector', None)

    """
    Merge two lists of HostPartition models with child_list taking
    priority when conflicts. If a member of child_list has a name
    beginning with '!' it indicates that HostPartition should be
    removed from the merged list
    """

    @staticmethod
    def merge_lists(child_list, parent_list):
        effective_list = []

        if len(child_list) == 0 and len(parent_list) > 0:
            for p in parent_list:
                pp = deepcopy(p)
                pp.ensure_applied_data()
                effective_list.append(pp)
        elif len(parent_list) == 0 and len(child_list) > 0:
            for i in child_list:
                if i.get_name().startswith('!'):
                    continue
                else:
                    ii = deepcopy(i)
                    ii.ensure_applied_data()
                    effective_list.append(ii)
        elif len(parent_list) > 0 and len(child_list) > 0:
            inherit_field_list = ["device", "part_uuid", "size",
                                  "mountpoint", "fstype", "mount_options",
                                  "fs_uuid", "fs_label"]
            parent_partitions = []
            for i in parent_list:
                parent_name = i.get_name()
                parent_partitions.append(parent_name)
                add = True
                for j in child_list:
                    if j.get_name() == ("!" + parent_name):
                        add = False
                        break
                    elif j.get_name() == parent_name:
                        p = HostPartition(j.api_version)
                        p.name = j.get_name()

                        for f in inherit_field_list:
                            j_f = j.design.get(f, None)
                            i_f = i.applied.get(f, None)
                            p.design.set(p,
                                Utils.apply_field_inheritance(j_f, i_f))
                        add = False
                        p.ensure_applied_data()
                        effective_list.append(p)
            if add:
                ii = deepcopy(i)
                ii.ensure_applied_data()
                effective_list.append(ii)

        for j in child_list:
            if (j.get_name() not in parent_list and
                not j.get_name().startswith("!")):
                jj = deepcopy(j)
                jj.ensure_applied_data
                effective_list.append(jj)

        return effective_list
