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


class HardwareProfile(object):

    def __init__(self, **kwargs):
        self.api_version = kwargs.get('apiVersion', '')

        if self.api_version == "1.0":
            metadata = kwargs.get('metadata', {})
            spec = kwargs.get('spec', {})

            # Need to add validation logic, we'll assume the input is
            # valid for now
            self.name = metadata.get('name', '')
            self.region = metadata.get('region', '')
            self.vendor = spec.get('vendor', '')
            self.generation = spec.get('generation', '')
            self.hw_version = spec.get('hw_version', '')
            self.bios_version = spec.get('bios_version', '')
            self.boot_mode = spec.get('boot_mode', '')
            self.bootstrap_protocol = spec.get('bootstrap_protocol', '')
            self.pxe_interface = spec.get('pxe_interface', '')
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
            raise ValueError('Unknown API version of object')

        return


class HardwareDeviceAlias(object):

    def __init__(self, api_version, **kwargs):
        self.api_version = api_version

        if self.api_version == "1.0":
            self.bus_type = kwargs.get('bus_type', '')
            self.address = kwargs.get('address', '')
            self.alias = kwargs.get('alias', '')
            self.type = kwargs.get('type', '')
        else:
            raise ValueError('Unknown API version of object')

        return


class Site(object):

    def __init__(self, **kwargs):
        self.api_version = kwargs.get('apiVersion', '')

        if self.api_version == "1.0":
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
            raise ValueError('Unknown API version of object')


class NetworkLink(object):

    def __init__(self, **kwargs):
        self.api_version = kwargs.get('apiVersion', '')

        if self.api_version == "1.0":
            metadata = kwargs.get('metadata', {})
            spec = kwargs.get('spec', {})

            self.name = metadata.get('name', '')
            self.region = metadata.get('region', '')

            bonding = spec.get('bonding', {})
            self.bonding_mode = bonding.get('mode', 'none')

            # TODO How should we define defaults for CIs not in the input?
            if self.bonding_mode == '802.3ad':
                self.bonding_xmit_hash = bonding.get('hash', 'layer3+4')
                self.bonding_peer_rate = bonding.get('peer_rate', 'fast')
                self.bonding_mon_rate = bonding.get('mon_rate', '')
                self.bonding_up_delay = bonding.get('up_delay', '')
                self.bonding_down_delay = bonding.get('down_delay', '')

            self.mtu = spec.get('mtu', 1500)
            self.linkspeed = spec.get('linkspeed', 'auto')

            trunking = spec.get('trunking', {})
            self.trunk_mode = trunking.get('mode', 'none')

            self.native_network = spec.get('default_network', '')
        else:
            raise ValueError('Unknown API version of object')


class Network(object):

    def __init__(self, **kwargs):
        self.api_version = kwargs.get('apiVersion', '')

        if self.api_version == "1.0":
            metadata = kwargs.get('metadata', {})
            spec = kwargs.get('spec', {})

            self.name = metadata.get('name', '')
            self.region = metadata.get('region', '')
            self.cidr = spec.get('cidr', '')
            self.allocation_strategy = spec.get('allocation', 'static')
            self.vlan_id = spec.get('vlan_id', 1)
            self.mtu = spec.get('mtu', 0)

            dns = spec.get('dns', {})
            self.dns_domain = dns.get('domain', 'local')
            self.dns_servers = dns.get('servers', '')

            ranges = spec.get('ranges', [])
            self.ranges = []

            for r in ranges:
                self.ranges.append(NetworkAddressRange(self.api_version, **r))

            routes = spec.get('routes', [])
            self.routes = []

            for r in routes:
                self.routes.append(NetworkRoute(self.api_version, **r))
        else:
            raise ValueError('Unknown API version of object')


class NetworkAddressRange(object):

    def __init__(self, api_version, **kwargs):
        self.api_version = api_version

        if self.api_version == "1.0":
            self.type = kwargs.get('type', 'static')
            self.start = kwargs.get('start', '')
            self.end = kwargs.get('end', '')
        else:
            raise ValueError('Unknown API version of object')


class NetworkRoute(object):

    def __init__(self, api_version, **kwargs):
        self.api_version = api_version

        if self.api_version == "1.0":
            self.type = kwargs.get('subnet', '')
            self.start = kwargs.get('gateway', '')
            self.end = kwargs.get('metric', 100)
        else:
            raise ValueError('Unknown API version of object')


class HostProfile(object):

    def __init__(self, **kwargs):
        self.api_version = kwargs.get('apiVersion', '')

        if self.api_version == "1.0":
            metadata = kwargs.get('metadata', {})
            spec = kwargs.get('spec', {})

            self.name = metadata.get('name', '')
            self.region = metadata.get('region', '')

            oob = spec.get('oob', {})
            self.oob_type = oob.get('type', 'ipmi')
            self.oob_network = oob.get('network', 'oob')
            self.oob_account = oob.get('account', '')
            self.oob_credential = oob.get('credential', '')

            storage = spec.get('storage', {})
            self.storage_layout = storage.get('layout', 'lvm')

            bootdisk = storage.get('bootdisk', {})
            self.bootdisk_device = bootdisk.get('device', '')
            self.bootdisk_root_size = bootdisk.get('root_size', '')
            self.bootdisk_boot_size = bootdisk.get('boot_size', '')

            partitions = storage.get('partitions', [])
            self.partitions = []

            for p in partitions:
                self.partitions.append(HostPartition(self.api_version, **p))

            interfaces = spec.get('interfaces', [])
            self.interfaces = []

            for i in interfaces:
                self.interfaces.append(HostInterface(self.api_version, **i))

        else:
            raise ValueError('Unknown API version of object')


class HostInterface(object):

    def __init__(self, api_version, **kwargs):
        self.api_version = api_version

        if self.api_version == "1.0":
            self.device_name = kwargs.get('device_name', '')
            self.network_link = kwargs.get('device_link', '')

            self.hardware_slaves = []
            slaves = kwargs.get('slaves', [])

            for s in slaves:
                self.hardware_slaves.append(s)

            self.networks = []
            networks = kwargs.get('networks', [])

            for n in networks:
                self.networks.append(n)

        else:
            raise ValueError('Unknown API version of object')


class HostPartition(object):

    def __init__(self, api_version, **kwargs):
        self.api_version = api_version

        if self.api_version == "1.0":
            self.name = kwargs.get('name', '')
            self.device = kwargs.get('device', '')
            self.part_uuid = kwargs.get('part_uuid', '')
            self.size = kwargs.get('size', '')
            self.mountpoint = kwargs.get('mountpoint', '')
            self.fstype = kwargs.get('fstype', 'ext4')
            self.mount_options = kwargs.get('mount_options', 'defaults')
            self.fs_uuid = kwargs.get('fs_uuid', '')
            self.fs_label = kwargs.get('fs_label', '')
        else:
            raise ValueError('Unknown API version of object')


# A BaremetalNode is really nothing more than a physical
# instantiation of a HostProfile, so they both represent
# the same set of CIs
class BaremetalNode(HostProfile):

    def __init__(self, **kwargs):
        super(BaremetalNode, self).__init__()
