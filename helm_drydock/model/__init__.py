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


class HardwareProfile(object):

    def __init__(self, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = kwargs.get('apiVersion', '')

        if self.api_version == "v1.0":
            metadata = kwargs.get('metadata', {})
            spec = kwargs.get('spec', {})

            # Need to add validation logic, we'll assume the input is
            # valid for now
            self.name = metadata.get('name', '')
            self.site = metadata.get('region', '')

            self.vendor = spec.get('vendor', None)
            self.generation = spec.get('generation', None)
            self.hw_version = spec.get('hw_version', None)
            self.bios_version = spec.get('bios_version', None)
            self.boot_mode = spec.get('boot_mode', None)
            self.bootstrap_protocol = spec.get('bootstrap_protocol', None)
            self.pxe_interface = spec.get('pxe_interface', None)
            self.devices = []

            device_aliases = spec.get('device_aliases', {})

            pci_devices = device_aliases.get('pci', [])
            scsi_devices = device_aliases.get('scsi', [])

            for d in pci_devices:
                d['bus_type'] = 'pci'
                self.devices.append(
                    HardwareDeviceAlias(self.api_version, **d))

            for d in scsi_devices:
                d['bus_type'] = 'scsi'
                self.devices.append(
                    HardwareDeviceAlias(self.api_version, **d))
        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')

        return

    def resolve_alias(self, alias_type, alias):
        selector = {}
        for d in self.devices:
            if d.alias == alias and d.bus_type == alias_type:
                selector['address'] = d.address
                selector['device_type'] = d.type
                return selector

        return None


class HardwareDeviceAlias(object):

    def __init__(self, api_version, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = api_version

        if self.api_version == "v1.0":
            self.bus_type = kwargs.get('bus_type', None)
            self.address = kwargs.get('address', None)
            self.alias = kwargs.get('alias', None)
            self.type = kwargs.get('type', None)
        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')


class Site(object):

    def __init__(self, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = kwargs.get('apiVersion', '')

        if self.api_version == "v1.0":
            metadata = kwargs.get('metadata', {})

            # Need to add validation logic, we'll assume the input is
            # valid for now
            self.name = metadata.get('name', '')

            self.networks = []
            self.network_links = []
            self.host_profiles = []
            self.hardware_profiles = []
            self.baremetal_nodes = []

        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')

    def get_network(self, network_name):
        for n in self.networks:
            if n.name == network_name:
                return n

        return None

    def get_network_link(self, link_name):
        for l in self.network_links:
            if l.name == link_name:
                return l

        return None

    def get_host_profile(self, profile_name):
        for p in self.host_profiles:
            if p.name == profile_name:
                return p

        return None

    def get_hardware_profile(self, profile_name):
        for p in self.hardware_profiles:
            if p.name == profile_name:
                return p

        return None

    def get_baremetal_node(self, node_name):
        for n in self.baremetal_nodes:
            if n.name == node_name:
                return n

        return None

class NetworkLink(object):

    def __init__(self, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = kwargs.get('apiVersion', '')

        if self.api_version == "v1.0":
            metadata = kwargs.get('metadata', {})
            spec = kwargs.get('spec', {})

            self.name = metadata.get('name', '')
            self.site = metadata.get('region', '')

            bonding = spec.get('bonding', {})
            self.bonding_mode = bonding.get('mode', 'none')

            # How should we define defaults for CIs not in the input?
            if self.bonding_mode == '802.3ad':
                self.bonding_xmit_hash = bonding.get('hash', 'layer3+4')
                self.bonding_peer_rate = bonding.get('peer_rate', 'fast')
                self.bonding_mon_rate = bonding.get('mon_rate', '100')
                self.bonding_up_delay = bonding.get('up_delay', '200')
                self.bonding_down_delay = bonding.get('down_delay', '200')

            self.mtu = spec.get('mtu', 1500)
            self.linkspeed = spec.get('linkspeed', 'auto')

            trunking = spec.get('trunking', {})
            self.trunk_mode = trunking.get('mode', 'none')

            self.native_network = spec.get('default_network', '')
        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')


class Network(object):

    def __init__(self, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = kwargs.get('apiVersion', '')

        if self.api_version == "v1.0":
            metadata = kwargs.get('metadata', {})
            spec = kwargs.get('spec', {})

            self.name = metadata.get('name', '')
            self.site = metadata.get('region', '')

            self.cidr = spec.get('cidr', None)
            self.allocation_strategy = spec.get('allocation', 'static')
            self.vlan_id = spec.get('vlan_id', 1)
            self.mtu = spec.get('mtu', 0)

            dns = spec.get('dns', {})
            self.dns_domain = dns.get('domain', 'local')
            self.dns_servers = dns.get('servers', None)

            ranges = spec.get('ranges', [])
            self.ranges = []

            for r in ranges:
                self.ranges.append(NetworkAddressRange(self.api_version, **r))

            routes = spec.get('routes', [])
            self.routes = []

            for r in routes:
                self.routes.append(NetworkRoute(self.api_version, **r))
        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')


class NetworkAddressRange(object):

    def __init__(self, api_version, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = api_version

        if self.api_version == "v1.0":
            self.type = kwargs.get('type', None)
            self.start = kwargs.get('start', None)
            self.end = kwargs.get('end', None)
        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')


class NetworkRoute(object):

    def __init__(self, api_version, **kwargs):
        self.log = logging.Logger('model')

        self.api_version = api_version

        if self.api_version == "v1.0":
            self.type = kwargs.get('subnet', None)
            self.start = kwargs.get('gateway', None)
            self.end = kwargs.get('metric', 100)
        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')


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

            metadata = spec.get('metadata', {})

            metadata_tags = metadata.get('tags', [])
            self.tags = []

            for t in metadata_tags:
                self.tags.append(t)

            owner_data = metadata.get('owner_data', {})
            self.owner_data = {}

            for k, v in owner_data.items():
                self.owner_data[k] = v

            self.rack = metadata.get('rack', None)

        else:
            self.log.error("Unknown API version %s of %s" %
                (self.api_version, self.__class__))
            raise ValueError('Unknown API version of object')

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

# A BaremetalNode is really nothing more than a physical
# instantiation of a HostProfile, so they both represent
# the same set of CIs
class BaremetalNode(HostProfile):

    def __init__(self, **kwargs):
        super(BaremetalNode, self).__init__(**kwargs)

    def apply_host_profile(self, site):
        return self.apply_inheritance(site)

    # Translate device alises to physical selectors and copy
    # other hardware attributes into this object
    def apply_hardware_profile(self, site):
        self_copy = deepcopy(self)

        if self.hardware_profile is None:
            raise ValueError("Hardware profile not set")

        hw_profile = site.get_hardware_profile(self.hardware_profile)

        for i in self_copy.interfaces:
            for s in i.hardware_slaves:
                selector = hw_profile.resolve_alias("pci", s)
                if selector is None:
                    i.add_selector("name", address=p.device)
                else:
                    i.add_selector("address", address=selector['address'],
                                   dev_type=selector['device_type'])

        for p in self_copy.partitions:
            selector = hw_profile.resolve_alias("scsi", p.device)
            if selector is None:
                p.set_selector("name", address=p.device)
            else:
                p.set_selector("address", address=selector['address'],
                               dev_type=selector['device_type'])


        hardware = {"vendor": getattr(hw_profile, 'vendor', None),
                    "generation": getattr(hw_profile, 'generation', None),
                    "hw_version": getattr(hw_profile, 'hw_version', None),
                    "bios_version": getattr(hw_profile, 'bios_version', None),
                    "boot_mode": getattr(hw_profile, 'boot_mode', None),
                    "bootstrap_protocol": getattr(hw_profile, 
                                                  'bootstrap_protocol',
                                                   None),
                    "pxe_interface": getattr(hw_profile, 'pxe_interface', None)
                    }

        self_copy.hardware = hardware

        return self_copy

    def get_interface(self, iface_name):
        for i in self.interfaces:
            if i.device_name == iface_name:
                return i
        return None

# Utility class for calculating inheritance

class Utils(object):

    """
    apply_field_inheritance - apply inheritance rules to a single field value

    param child_field - value of the child field, or the field receiving
                        the inheritance
    param parent_field - value of the parent field, or the field supplying
                        the inheritance

    return the correct value for child_field based on the inheritance algorithm

    Inheritance algorithm

    1. If child_field is not None, '!' for string vals or -1 for numeric
       vals retain the value
    of child_field

    2. If child_field is '!' return None to unset the field value

    3. If child_field is -1 return None to unset the field value

    4. If child_field is None return parent_field
    """

    @staticmethod
    def apply_field_inheritance(child_field, parent_field):

        if child_field is not None:
            if child_field != '!' and child_field != -1:
                return child_field
            else:
                return None
        else:
            return parent_field

    """
    merge_lists - apply inheritance rules to a list of simple values

    param child_list - list of values from the child
    param parent_list - list of values from the parent

    return a merged list with child values taking prority

    1. All members in the child list not starting with '!'

    2. If a member in the parent list has a corresponding member in the
    chid list prefixed with '!' it is removed

    3. All remaining members of the parent list
    """
    @staticmethod
    def merge_lists(child_list, parent_list):

        if type(child_list) is not list or type(parent_list) is not list:
            raise ValueError("One parameter is not a list")

        effective_list = []

        # Probably should handle non-string values
        effective_list.extend(
            filter(lambda x: not x.startswith("!"), child_list))

        effective_list.extend(
            filter(lambda x: ("!" + x) not in child_list,
                   filter(lambda x: x not in effective_list, parent_list)))

        return effective_list

    """
    merge_dicts - apply inheritance rules to a dict

    param child_dict - dict of k:v from child
    param parent_dict - dict of k:v from the parent

    return a merged dict with child values taking prority

    1. All members in the child dict with a key not starting with '!'

    2. If a member in the parent dict has a corresponding member in the
    chid dict where the key is prefixed with '!' it is removed

    3. All remaining members of the parent dict
    """
    @staticmethod
    def merge_dicts(child_dict, parent_dict):

        if type(child_dict) is not dict or type(parent_dict) is not dict:
            raise ValueError("One parameter is not a dict")

        effective_dict = {}

        # Probably should handle non-string keys
        use_keys = filter(lambda x: ("!" + x) not in child_dict.keys(),
                          parent_dict)

        for k in use_keys:
            effective_dict[k] = deepcopy(parent_dict[k])

        use_keys = filter(lambda x: not x.startswith("!"), child_dict)

        for k in use_keys:
            effective_dict[k] = deepcopy(child_dict[k])

        return effective_dict
