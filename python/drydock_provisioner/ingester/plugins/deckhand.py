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
"""This data ingester will consume YAML site topology documents."""

import yaml
import logging
import jsonschema
import os
import pkg_resources
import copy
import hashlib

import drydock_provisioner.objects.fields as hd_fields

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

from drydock_provisioner import error as errors
from drydock_provisioner import objects
from drydock_provisioner.ingester.plugins import IngesterPlugin

cache_opts = {
    'cache.type': 'memory',
    'expire': 1800,
}

cache = CacheManager(**parse_cache_config_options(cache_opts))

class DeckhandIngester(IngesterPlugin):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('drydock.ingester.deckhand')

        self.load_schemas()

    def get_name(self):
        return "deckhand"

    def ingest_data(self, **kwargs):
        """Parse and save design data.

        :param content: String of valid Deckhand YAML

        :returns: a tuple of a status response and a list of parsed objects from drydock_provisioner.objects
        """
        def local_parse():
            return self.parse_docs(kwargs.get('content'))

        if 'content' in kwargs:
            try:
                # Hash the input to use as the cache key. This is not a security
                # related hash, so use cheap and fast MD5
                hv = hashlib.md5(kwargs.get('content', b'')).hexdigest()
                local_cache = cache.get_cache('parsed_docs')
                results = local_cache.get(key=hv, createfunc=local_parse)
                parse_status, models = results
            except Exception as ex:
                self.logger.debug("Error parsing design - hash %s", hv, exc_info=ex)
                raise ex
        else:
            raise ValueError('Missing parameter "content"')

        return parse_status, models

    def parse_docs(self, doc_blob):
        """Translate a YAML string into the internal Drydock model.

        Returns a tuple of a objects.TaskStatus instance to summarize all
        document processing and a list of models yielded by successful processing

        :param doc_blob: bytes representing a utf-8 encoded YAML string
        """
        models = []
        yaml_string = doc_blob.decode()
        self.logger.debug("yamlingester:parse_docs - Parsing YAML string.")
        try:
            parsed_data = yaml.safe_load_all(yaml_string)
        except yaml.YAMLError as err:
            if hasattr(err, 'problem_mark'):
                mark = err.problem_mark
                raise errors.IngesterError(
                    "Error parsing YAML at (l:%s, c:%s): %s" %
                    (mark.line + 1, mark.column + 1, err))
            else:
                raise errors.IngesterError("Error parsing YAML: %s" % (err))

        # tracking processing status to provide a complete summary of issues
        ps = objects.Validation()
        ps.set_status(hd_fields.ValidationResult.Success)
        for d in parsed_data:
            try:
                (schema_ns, doc_kind, doc_version) = d.get('schema',
                                                           '').split('/')
            except ValueError as ex:
                self.logger.error(
                    "Error with document structure.", exc_info=ex)
                self.logger.debug("Error document\n%s" % yaml.dump(d))
                continue
            if schema_ns == 'drydock':
                try:
                    doc_ref = objects.DocumentReference(
                        doc_type=hd_fields.DocumentType.Deckhand,
                        doc_schema=d.get('schema'),
                        doc_name=d.get('metadata', {}).get('name', 'Unknown'))
                    doc_errors = self.validate_drydock_document(d)
                    if len(doc_errors) > 0:
                        for e in doc_errors:
                            ps.add_detail_msg(
                                objects.ValidationMessage(
                                    msg="%s:%s schema validation error: %s" %
                                    (doc_kind, doc_version, e),
                                    name="DD001",
                                    docs=[doc_ref],
                                    error=True,
                                    level=hd_fields.MessageLevels.ERROR,
                                    diagnostic=
                                    "Invalid input file - see Drydock Troubleshooting Guide for DD001"
                                ))
                        ps.set_status(hd_fields.ActionResult.Failure)
                        continue
                    model = self.process_drydock_document(d)
                    model.doc_ref = doc_ref
                    models.append(model)
                except errors.IngesterError as ie:
                    msg = "Error processing document: %s" % str(ie)
                    self.logger.warning(msg)
                    ps.add_detail_msg(
                        objects.ValidationMessage(
                            msg=msg,
                            name="DD000",
                            error=True,
                            level=hd_fields.MessageLevels.ERROR,
                            docs=[doc_ref],
                            diagnostic="Exception during document processing "
                            "- see Drydock Troubleshooting Guide "
                            "for DD000"))
                    ps.set_status(hd_fields.ActionResult.Failure)
                except Exception as ex:
                    msg = "Unexpected error processing document: %s" % str(ex)
                    self.logger.error(msg, exc_info=True)
                    ps.add_detail_msg(
                        objects.ValidationMessage(
                            msg=msg,
                            name="DD000",
                            error=True,
                            level=hd_fields.MessageLevels.ERROR,
                            docs=[doc_ref],
                            diagnostic="Unexpected exception during document "
                            "processing - see Drydock Troubleshooting "
                            "Guide for DD000"))
                    ps.set_status(hd_fields.ActionResult.Failure)
        return (ps, models)

    def process_drydock_document(self, doc):
        """Process a parsed YAML document.

        :param doc: The dictionary from parsing the YAML document
        """
        (schema_ns, kind, version) = doc.get('schema', '').split('/')
        if version == 'v1':
            doc_processor = DeckhandIngester.v1_doc_handlers.get(kind, None)
        else:
            doc_processor = None

        if doc_processor is None:
            raise errors.IngesterError(
                "Invalid document - Kind %s and Version %s" % (kind, version))
        metadata = doc.get('metadata', {})
        doc_name = metadata.get('name')
        return doc_processor(self, doc_name, doc.get('data', {}))

    def validate_drydock_document(self, doc):
        """Validate a parsed document via jsonschema.

        If a schema for a document Kind is not available, the document is
        considered valid. Schema is chosen by the doc['kind'] field.

        Returns a empty list for valid documents, otherwise returns a list
        of all found errors

        :param doc: dictionary of the parsed document.
        """
        schemaname = doc.get('schema', '')
        (schema_ns, doc_kind, doc_version) = schemaname.split('/')

        errors_found = []

        if doc_version == 'v1':
            if schemaname in self.v1_doc_schemas:
                validator = jsonschema.Draft4Validator(
                    self.v1_doc_schemas.get(schemaname))
                for error in validator.iter_errors(doc.get('data', [])):
                    errors_found.append(error.message)

        return errors_found

    def process_drydock_region(self, name, data):
        """Process the data/spec section of a Region document.

        :param name: the document name attribute
        :param data: the dictionary of the data/spec section
        """
        model = objects.Site()

        # Need to add validation logic, we'll assume the input is
        # valid for now
        model.name = name
        model.status = hd_fields.SiteStatus.Unknown
        model.source = hd_fields.ModelSource.Designed

        model.tag_definitions = objects.NodeTagDefinitionList()

        tag_defs = data.get('tag_definitions', [])

        for t in tag_defs:
            tag_model = objects.NodeTagDefinition()
            tag_model.tag = t.get('tag', '')
            tag_model.type = t.get('definition_type', '')
            tag_model.definition = t.get('definition', '')

            if tag_model.type not in ['lshw_xpath']:
                raise errors.IngesterError(
                    'Unknown definition_type in '
                    'tag_definition instance: %s' % (t.definition_type))
            model.tag_definitions.append(tag_model)

        auth_keys = data.get('authorized_keys', [])

        model.authorized_keys = [k for k in auth_keys]

        repos = data.get('repositories', None)

        if repos:
            model.repositories = self.process_drydock_region_repo_list(repos)

        return model

    def process_drydock_region_repo_list(self, data):
        """Process a package repository list.

        :param data: The data from the ``repositories`` key in a Region document
        """
        model = objects.RepositoryList()

        for k, v in data.items():
            if k == 'remove_unlisted':
                model.remove_unlisted = v
            else:
                model.append(objects.Repository(name=k, **v))

        return model

    def process_drydock_rack(self, name, data):
        """Process the data/spec section of a Rack document.

        :param name: the document name attribute
        :param data: the dictionary of the data/spec section
        """
        model = objects.Rack()

        model.source = hd_fields.ModelSource.Designed
        model.name = name

        model.tor_switches = objects.TorSwitchList()
        tors = data.get('tor_switches', {})

        for k, v in tors.items():
            tor = objects.TorSwitch()
            tor.switch_name = k
            tor.mgmt_ip = v.get('mgmt_ip', None)
            tor.sdn_api_uri = v.get('sdn_api_url', None)
            model.tor_switches.append(tor)

        model.location = copy.deepcopy(data.get('location', {}))

        model.local_networks = [n for n in data.get('local_networks', [])]

        return model

    def process_drydock_networklink(self, name, data):
        """Process the data/spec section of a NetworkLink document.

        :param name: the document name attribute
        :param data: the dictionary of the data/spec section
        """
        model = objects.NetworkLink()

        model.source = hd_fields.ModelSource.Designed
        model.name = name

        model.metalabels = data.get('labels', {})

        bonding = data.get('bonding', {})

        model.bonding_mode = bonding.get(
            'mode', hd_fields.NetworkLinkBondingMode.Disabled)

        if model.bonding_mode in \
            (hd_fields.NetworkLinkBondingMode.LACP,
             hd_fields.NetworkLinkBondingMode.RoundRobin,
             hd_fields.NetworkLinkBondingMode.Standby):
            model.bonding_mon_rate = bonding.get('mon_rate', '100')
            model.bonding_up_delay = bonding.get('up_delay', '200')
            model.bonding_down_delay = bonding.get('down_delay', '200')

        if model.bonding_mode == hd_fields.NetworkLinkBondingMode.LACP:
            model.bonding_xmit_hash = bonding.get('hash', 'layer3+4')
            model.bonding_peer_rate = bonding.get('peer_rate', 'fast')

        model.mtu = data.get('mtu', None)
        model.linkspeed = data.get('linkspeed', None)

        trunking = data.get('trunking', {})
        model.trunk_mode = trunking.get(
            'mode', hd_fields.NetworkLinkTrunkingMode.Disabled)
        model.native_network = trunking.get('default_network', None)

        model.allowed_networks = data.get('allowed_networks', None)

        return model

    def process_drydock_network(self, name, data):
        """Process the data/spec section of a Network document.

        :param name: the document name attribute
        :param data: the dictionary of the data/spec section
        """
        model = objects.Network()

        model.source = hd_fields.ModelSource.Designed
        model.name = name

        model.metalabels = data.get('labels', {})

        model.cidr = data.get('cidr', None)
        model.vlan_id = data.get('vlan', None)
        model.mtu = data.get('mtu', None)
        model.routedomain = data.get('routedomain', None)

        dns = data.get('dns', {})
        model.dns_domain = dns.get('domain', 'local')
        model.dns_servers = dns.get('servers', None)

        ranges = data.get('ranges', [])
        model.ranges = []

        for r in ranges:
            model.ranges.append({
                'type': r.get('type', None),
                'start': r.get('start', None),
                'end': r.get('end', None),
            })

        routes = data.get('routes', [])
        model.routes = []

        for r in routes:
            model.routes.append({
                'subnet': r.get('subnet', None),
                'gateway': r.get('gateway', None),
                'metric': r.get('metric', None),
                'routedomain': r.get('routedomain', None),
            })

        dhcp_relay = data.get('dhcp_relay', None)

        if dhcp_relay is not None:
            model.dhcp_relay_self_ip = dhcp_relay.get('self_ip', None)
            model.dhcp_relay_upstream_target = dhcp_relay.get(
                'upstream_target', None)

        return model

    def process_drydock_hwprofile(self, name, data):
        """Process the data/spec section of a HardwareProfile document.

        :param name: the document name attribute
        :param data: the dictionary of the data/spec section
        """
        model = objects.HardwareProfile()

        model.name = name
        model.source = hd_fields.ModelSource.Designed

        model.vendor = data.get('vendor', None)
        model.generation = data.get('generation', None)
        model.hw_version = data.get('hw_version', None)
        model.bios_version = data.get('bios_version', None)
        model.boot_mode = data.get('boot_mode', None)
        model.bootstrap_protocol = data.get('bootstrap_protocol', None)
        model.pxe_interface = data.get('pxe_interface', None)

        model.devices = objects.HardwareDeviceAliasList()

        device_aliases = data.get('device_aliases', {})

        for d, v in device_aliases.items():
            dev_model = objects.HardwareDeviceAlias()
            dev_model.source = hd_fields.ModelSource.Designed
            dev_model.alias = d
            dev_model.bus_type = v.get('bus_type', None)
            dev_model.dev_type = v.get('dev_type', None)
            dev_model.address = v.get('address', None)
            model.devices.append(dev_model)

        model.cpu_sets = data.get('cpu_sets', None) or dict()

        model.hugepages_confs = objects.HugepagesConfList()

        for c, d in data.get('hugepages', {}).items():
            conf = objects.HugepagesConf(
                name=c, size=d.get('size'), count=d.get('count'))
            model.hugepages_confs.append(conf)

        return model

    def process_drydock_hostprofile(self, name, data):
        """Process the data/spec section of a HostProfile document.

        :param name: the document name attribute
        :param data: the dictionary of the data/spec section
        """
        model = objects.HostProfile()
        model.name = name
        model.source = hd_fields.ModelSource.Designed

        self.process_host_common_fields(data, model)

        return model

    def process_drydock_bootaction(self, name, data):
        """Process the data/spec section of a BootAction document.

        :param name: the document name attribute
        :Param data: the dictionary of the parsed data/spec section
        """
        model = objects.BootAction()
        model.name = name
        model.source = hd_fields.ModelSource.Designed

        assets = data.get('assets')

        model.asset_list = objects.BootActionAssetList()

        for a in assets:
            ba = self.process_bootaction_asset(a)
            model.asset_list.append(ba)

        node_filter = data.get('node_filter', None)

        if node_filter is not None:
            nfs = self.process_bootaction_nodefilter(node_filter)
            model.node_filter = nfs

        model.signaling = data.get('signaling', None)
        return model

    def process_bootaction_asset(self, asset_dict):
        """Process a dictionary representing a BootAction Data Asset.

        :param asset_dict: dictionary representing the bootaction asset
        """
        model = objects.BootActionAsset(**asset_dict)
        return model

    def process_bootaction_nodefilter(self, nf):
        """Process a dictionary representing a BootAction NodeFilter Set.

        :param nf: dictionary representing the bootaction nodefilter set.
        """
        model = objects.NodeFilterSet()
        model.filter_set_type = nf.get('filter_set_type', None)
        model.filter_set = []

        for nf in nf.get('filter_set', []):
            nf_model = objects.NodeFilter(**nf)
            model.filter_set.append(nf_model)

        return model

    def process_drydock_node(self, name, data):
        """Process the data/spec section of a BaremetalNode document.

        :param name: the document name attribute
        :param data: the dictionary of the data/spec section
        """
        model = objects.BaremetalNode()
        model.name = name
        model.source = hd_fields.ModelSource.Designed

        self.process_host_common_fields(data, model)

        node_metadata = data.get('metadata', {})
        model.boot_mac = node_metadata.get('boot_mac', None)

        addresses = data.get('addressing', [])

        if len(addresses) == 0:
            raise errors.IngesterError('BaremetalNode needs at least'
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
                self.log.error("Invalid address assignment %s on Node %s" %
                               (address, self.name))

        return model

    def process_host_common_fields(self, data, model):
        """Process fields common to the host-based documents.

        Update the provided model with the values of fields common
        to BaremetalNode and HostProfile documents.

        :param data: dictionary from YAML parsing of the document data/spec section
        :param model: instance of objects.HostProfile or objects.BaremetalNode to update
        """
        model.parent_profile = data.get('host_profile', None)
        model.hardware_profile = data.get('hardware_profile', None)

        oob = data.get('oob', {})

        model.oob_parameters = {}
        for k, v in oob.items():
            if k == 'type':
                model.oob_type = oob.get('type', None)
            else:
                model.oob_parameters[k] = v

        (model.storage_devices,
         model.volume_groups) = self.process_node_storage(
             data.get('storage', {}))

        interfaces = data.get('interfaces', {})
        model.interfaces = objects.HostInterfaceList()

        for k, v in interfaces.items():
            int_model = objects.HostInterface()

            # A null value indicates this interface should be removed
            # from any parent profiles
            if v is None:
                int_model.device_name = '!' + k
                continue

            int_model.device_name = k
            int_model.network_link = v.get('device_link', None)

            int_model.hardware_slaves = []
            slaves = v.get('slaves', [])

            for s in slaves:
                int_model.hardware_slaves.append(s)

            int_model.networks = []
            networks = v.get('networks', [])

            for n in networks:
                int_model.networks.append(n)

            if 'sriov' in v:
                int_model.sriov = True
                int_model.vf_count = v.get('sriov', {}).get('vf_count', 0)
                int_model.trustedmode = v.get('sriov', {}).get(
                    'trustedmode', False)

            model.interfaces.append(int_model)

        platform = data.get('platform', {})

        model.image = platform.get('image', None)
        model.kernel = platform.get('kernel', None)

        model.kernel_params = {}
        for k, v in platform.get('kernel_params', {}).items():
            model.kernel_params[k] = v

        model.primary_network = data.get('primary_network', None)

        node_metadata = data.get('metadata', {})
        metadata_tags = node_metadata.get('tags', [])

        model.tags = metadata_tags

        owner_data = node_metadata.get('owner_data', {})
        model.owner_data = {}

        for k, v in owner_data.items():
            model.owner_data[k] = v

        model.rack = node_metadata.get('rack', None)

        return model

    def process_node_storage(self, storage):
        """Process the storage data for a node-based document.

        Return a tuple of of two lists the first is a StorageDeviceList, the
        second is a VolumeGroupList.

        :param storage: dictionary of the storage section of a document
        """
        phys_devs = storage.get('physical_devices', {})

        storage_devices = objects.HostStorageDeviceList()

        for k, v in phys_devs.items():
            sd = objects.HostStorageDevice(name=k)
            sd.source = hd_fields.ModelSource.Designed

            if 'labels' in v:
                sd.labels = v.get('labels').copy()

            if 'volume_group' in v:
                vg = v.get('volume_group')
                sd.volume_group = vg
            elif 'partitions' in v:
                sd.partitions = objects.HostPartitionList()
                for vv in v.get('partitions', []):
                    part_model = objects.HostPartition()

                    part_model.name = vv.get('name')
                    part_model.source = hd_fields.ModelSource.Designed
                    part_model.part_uuid = vv.get('part_uuid', None)
                    part_model.size = vv.get('size', None)

                    if 'labels' in vv:
                        part_model.labels = vv.get('labels').copy()

                    if 'volume_group' in vv:
                        part_model.volume_group = vv.get('vg')
                    elif 'filesystem' in vv:
                        fs_info = vv.get('filesystem', {})
                        part_model.mountpoint = fs_info.get('mountpoint', None)
                        part_model.fstype = fs_info.get('fstype', 'ext4')
                        part_model.mount_options = fs_info.get(
                            'mount_options', 'defaults')
                        part_model.fs_uuid = fs_info.get('fs_uuid', None)
                        part_model.fs_label = fs_info.get('fs_label', None)

                    sd.partitions.append(part_model)
            storage_devices.append(sd)

        volume_groups = objects.HostVolumeGroupList()
        vol_groups = storage.get('volume_groups', {})

        for k, v in vol_groups.items():
            vg = objects.HostVolumeGroup(name=k)
            vg.vg_uuid = v.get('vg_uuid', None)
            vg.logical_volumes = objects.HostVolumeList()
            volume_groups.append(vg)
            for vv in v.get('logical_volumes', []):
                lv = objects.HostVolume(name=vv.get('name'))
                lv.size = vv.get('size', None)
                lv.lv_uuid = vv.get('lv_uuid', None)
                if 'filesystem' in vv:
                    fs_info = vv.get('filesystem', {})
                    lv.mountpoint = fs_info.get('mountpoint', None)
                    lv.fstype = fs_info.get('fstype', 'ext4')
                    lv.mount_options = fs_info.get('mount_options', 'defaults')
                    lv.fs_uuid = fs_info.get('fs_uuid', None)
                    lv.fs_label = fs_info.get('fs_label', None)

                vg.logical_volumes.append(lv)

        return (storage_devices, volume_groups)

    def load_schemas(self):
        self.v1_doc_schemas = dict()
        schema_dir = self._get_schema_dir()

        for schema_file in os.listdir(schema_dir):
            f = open(os.path.join(schema_dir, schema_file), 'r')
            for schema in yaml.safe_load_all(f):
                schema_for = schema['metadata']['name']
                if schema_for in self.v1_doc_schemas:
                    self.logger.warning(
                        "Duplicate document schemas found for document kind %s."
                        % schema_for)
                self.logger.debug(
                    "Loaded schema for document kind %s." % schema_for)
                self.v1_doc_schemas[schema_for] = schema.get('data')
            f.close()

    def _get_schema_dir(self):
        return pkg_resources.resource_filename('drydock_provisioner',
                                               'schemas')

    # Mapping of handlers for different document kinds
    v1_doc_handlers = {
        'Region': process_drydock_region,
        'Rack': process_drydock_rack,
        'NetworkLink': process_drydock_networklink,
        'Network': process_drydock_network,
        'HardwareProfile': process_drydock_hwprofile,
        'HostProfile': process_drydock_hostprofile,
        'BaremetalNode': process_drydock_node,
        'BootAction': process_drydock_bootaction,
    }
