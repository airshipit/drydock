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
# AIC YAML Ingester - This data ingester will consume a AIC YAML design
#                   file 
#   
import yaml
import logging

import drydock_provisioner.objects.fields as hd_fields

from drydock_provisioner import objects
from drydock_provisioner.ingester.plugins import IngesterPlugin

class YamlIngester(IngesterPlugin):

    def __init__(self):
        super(YamlIngester, self).__init__()
        self.logger = logging.getLogger('drydock.ingester.yaml')

    def get_name(self):
        return "yaml"

    """
    AIC YAML ingester params

    filenames - Array of absolute path to the YAML files to ingest

    returns an array of objects from drydock_provisioner.model

    """
    def ingest_data(self, **kwargs):
        models = []

        if 'filenames' in kwargs:
            # TODO validate filenames is array
            for f in kwargs.get('filenames'):
                try:
                    file = open(f,'rt')
                    contents = file.read()
                    file.close()
                    models.extend(self.parse_docs(contents))
                except OSError as err:
                    self.logger.error(
                        "Error opening input file %s for ingestion: %s" 
                        % (filename, err))
                    continue
        elif 'content' in kwargs:
            models.extend(self.parse_docs(kwargs.get('content')))
        else:
            raise ValueError('Missing parameter "filename"')
        
        return models

    """
    Translate a YAML string into the internal Drydock model
    """
    def parse_docs(self, yaml_string):
        models = []

        self.logger.debug("yamlingester:parse_docs - Parsing YAML string \n%s" % (yaml_string))

        try:
            parsed_data = yaml.load_all(yaml_string)
        except yaml.YAMLError as err:
            raise ValueError("Error parsing YAML in %s: %s" % (f,err))

        for d in parsed_data:
            kind = d.get('kind', '')
            api = d.get('apiVersion', '')
            if api.startswith('drydock/'):
                (foo, api_version) = api.split('/')
                if kind != '':
                    if kind == 'Region':
                        if api_version == 'v1':
                            model = objects.Site()

                            metadata = d.get('metadata', {})

                            # Need to add validation logic, we'll assume the input is
                            # valid for now
                            model.name = metadata.get('name', '')
                            model.status = hd_fields.SiteStatus.Unknown
                            model.source = hd_fields.ModelSource.Designed

                            spec = d.get('spec', {})

                            model.tag_definitions = objects.NodeTagDefinitionList()

                            tag_defs = spec.get('tag_definitions', [])

                            for t in tag_defs:
                                tag_model = objects.NodeTagDefinition()
                                tag_model.tag = t.get('tag', '')
                                tag_model.type = t.get('definition_type', '')
                                tag_model.definition = t.get('definition', '')

                                if tag_model.type not in ['lshw_xpath']:
                                    raise ValueError('Unknown definition type in ' \
                                        'NodeTagDefinition: %s' % (self.definition_type))
                                model.tag_definitions.append(tag_model)

                            models.append(model)
                        else:
                            raise ValueError('Unknown API version %s of Region kind' %s (api_version))
                    elif kind == 'NetworkLink':
                        if api_version == "v1":
                            model = objects.NetworkLink()

                            metadata = d.get('metadata', {})
                            spec = d.get('spec', {})

                            model.name = metadata.get('name', '')
                            model.site = metadata.get('region', '')

                            bonding = spec.get('bonding', {})
                            model.bonding_mode = bonding.get('mode',
                                                            hd_fields.NetworkLinkBondingMode.Disabled)

                            # How should we define defaults for CIs not in the input?
                            if model.bonding_mode == hd_fields.NetworkLinkBondingMode.LACP:
                                model.bonding_xmit_hash = bonding.get('hash', 'layer3+4')
                                model.bonding_peer_rate = bonding.get('peer_rate', 'fast')
                                model.bonding_mon_rate = bonding.get('mon_rate', '100')
                                model.bonding_up_delay = bonding.get('up_delay', '200')
                                model.bonding_down_delay = bonding.get('down_delay', '200')

                            model.mtu = spec.get('mtu', None)
                            model.linkspeed = spec.get('linkspeed', None)

                            trunking = spec.get('trunking', {})
                            model.trunk_mode = trunking.get('mode', hd_fields.NetworkLinkTrunkingMode.Disabled)
                            model.native_network = trunking.get('default_network', None)

                            model.allowed_networks = spec.get('allowed_networks', None)

                            models.append(model)
                        else:
                            raise ValueError('Unknown API version of object')
                    elif kind == 'Network':
                            if api_version == "v1":
                                model = objects.Network()

                                metadata = d.get('metadata', {})
                                spec = d.get('spec', {})

                                model.name = metadata.get('name', '')
                                model.site = metadata.get('region', '')

                                model.cidr = spec.get('cidr', None)
                                model.allocation_strategy = spec.get('allocation', 'static')
                                model.vlan_id = spec.get('vlan', None)
                                model.mtu = spec.get('mtu', None)

                                dns = spec.get('dns', {})
                                model.dns_domain = dns.get('domain', 'local')
                                model.dns_servers = dns.get('servers', None)

                                ranges = spec.get('ranges', [])
                                model.ranges = []

                                for r in ranges:
                                    model.ranges.append({'type':    r.get('type', None),
                                                         'start':   r.get('start', None),
                                                         'end':     r.get('end', None),
                                                        })

                                routes = spec.get('routes', [])
                                model.routes = []

                                for r in routes:
                                    model.routes.append({'subnet':  r.get('subnet', None),
                                                         'gateway': r.get('gateway', None),
                                                         'metric':  r.get('metric', None),
                                                        })
                                models.append(model)
                    elif kind == 'HardwareProfile':
                        if api_version == 'v1':
                            metadata = d.get('metadata', {})
                            spec = d.get('spec', {})

                            model = objects.HardwareProfile()

                            # Need to add validation logic, we'll assume the input is
                            # valid for now
                            model.name = metadata.get('name', '')
                            model.site = metadata.get('region', '')
                            model.source = hd_fields.ModelSource.Designed

                            model.vendor = spec.get('vendor', None)
                            model.generation = spec.get('generation', None)
                            model.hw_version = spec.get('hw_version', None)
                            model.bios_version = spec.get('bios_version', None)
                            model.boot_mode = spec.get('boot_mode', None)
                            model.bootstrap_protocol = spec.get('bootstrap_protocol', None)
                            model.pxe_interface = spec.get('pxe_interface', None)
                        
                            model.devices = objects.HardwareDeviceAliasList()

                            device_aliases = spec.get('device_aliases', {})

                            for d in device_aliases:
                                dev_model = objects.HardwareDeviceAlias()
                                dev_model.source = hd_fields.ModelSource.Designed
                                dev_model.alias = d.get('alias', None)
                                dev_model.bus_type = d.get('bus_type', None)
                                dev_model.dev_type = d.get('dev_type', None)
                                dev_model.address = d.get('address', None)
                                model.devices.append(dev_model)

                            models.append(model)
                    elif kind == 'HostProfile' or kind == 'BaremetalNode':
                        if api_version == "v1":
                            model = None

                            if kind == 'HostProfile':
                                model = objects.HostProfile()
                            else:
                                model = objects.BaremetalNode()

                            metadata = d.get('metadata', {})
                            spec = d.get('spec', {})

                            model.name = metadata.get('name', '')
                            model.site = metadata.get('region', '')
                            model.source = hd_fields.ModelSource.Designed

                            model.parent_profile = spec.get('host_profile', None)
                            model.hardware_profile = spec.get('hardware_profile', None)

                            oob = spec.get('oob', {})

                            model.oob_parameters = {}
                            for k,v in oob.items():
                                if k == 'type':
                                    model.oob_type = oob.get('type', None)
                                else:
                                    model.oob_parameters[k] = v

                            storage = spec.get('storage', {})
                            model.storage_layout = storage.get('layout', 'lvm')

                            bootdisk = storage.get('bootdisk', {})
                            model.bootdisk_device = bootdisk.get('device', None)
                            model.bootdisk_root_size = bootdisk.get('root_size', None)
                            model.bootdisk_boot_size = bootdisk.get('boot_size', None)

                            partitions = storage.get('partitions', [])
                            model.partitions = objects.HostPartitionList()

                            for p in partitions:
                                part_model = objects.HostPartition()

                                part_model.name = p.get('name', None)
                                part_model.source = hd_fields.ModelSource.Designed
                                part_model.device = p.get('device', None)
                                part_model.part_uuid = p.get('part_uuid', None)
                                part_model.size = p.get('size', None)
                                part_model.mountpoint = p.get('mountpoint', None)
                                part_model.fstype = p.get('fstype', 'ext4')
                                part_model.mount_options = p.get('mount_options', 'defaults')
                                part_model.fs_uuid = p.get('fs_uuid', None)
                                part_model.fs_label = p.get('fs_label', None)

                                model.partitions.append(part_model)

                            interfaces = spec.get('interfaces', [])
                            model.interfaces = objects.HostInterfaceList()

                            for i in interfaces:
                                int_model = objects.HostInterface()

                                int_model.device_name = i.get('device_name', None)
                                int_model.network_link = i.get('device_link', None)

                                int_model.hardware_slaves = []
                                slaves = i.get('slaves', [])

                                for s in slaves:
                                    int_model.hardware_slaves.append(s)

                                int_model.networks = []
                                networks = i.get('networks', [])

                                for n in networks:
                                    int_model.networks.append(n)
                                
                                model.interfaces.append(int_model)

                            platform = spec.get('platform', {})

                            model.image = platform.get('image', None)
                            model.kernel = platform.get('kernel', None)

                            model.kernel_params = {}
                            for k,v in platform.get('kernel_params', {}).items():
                                model.kernel_params[k] = v

                            model.primary_network = spec.get('primary_network', None)
                            
                            node_metadata = spec.get('metadata', {})
                            metadata_tags = node_metadata.get('tags', [])
                            model.tags = []

                            for t in metadata_tags:
                                model.tags.append(t)

                            owner_data = node_metadata.get('owner_data', {})
                            model.owner_data = {}

                            for k, v in owner_data.items():
                                model.owner_data[k] = v

                            model.rack = node_metadata.get('rack', None)

                            if kind == 'BaremetalNode':
                                model.boot_mac = node_metadata.get('boot_mac', None)

                                addresses = spec.get('addressing', [])

                                if len(addresses) == 0:
                                    raise ValueError('BaremetalNode needs at least' \
                                                     ' 1 assigned address')

                                model.addressing = objects.IpAddressAssignmentList()
                                
                                for a in addresses:
                                    assignment = objects.IpAddressAssignment()

                                    address = a.get('address', '')
                                    if address == 'dhcp':
                                        assignment.type = 'dhcp'
                                        assignment.address = None
                                        assignment.network = a.get('network')

                                        model.addressing.append(assignment)
                                    elif address != '':
                                        assignment.type = 'static'
                                        assignment.address = a.get('address')
                                        assignment.network = a.get('network')

                                        model.addressing.append(assignment)
                                    else:
                                        self.log.error("Invalid address assignment %s on Node %s" 
                                                        % (address, self.name))
                            models.append(model)
                        else:
                            raise ValueError('Unknown API version %s of Kind HostProfile' % (api_version))
                else:
                    self.log.error(
                        "Error processing document in %s, no kind field"
                        % (f))
                    continue
            elif api.startswith('promenade/'):
                (foo, api_version) = api.split('/')
                if api_version == 'v1':
                    metadata = d.get('metadata', {})

                    target = metadata.get('target', 'all')
                    name = metadata.get('name', None)

                    model = objects.PromenadeConfig(target=target, name=name, kind=kind,
                                        document=yaml.dump(d, default_flow_style=False).replace('\n\n','\n'))
                    models.append(model)
        return models
