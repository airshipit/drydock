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
# Models for drydock_provisioner
#
from copy import deepcopy
import uuid
import datetime

import oslo_versionedobjects.fields as ovo_fields

import drydock_provisioner.objects as objects
import drydock_provisioner.objects.base as base
import drydock_provisioner.objects.fields as hd_fields


@base.DrydockObjectRegistry.register
class Site(base.DrydockPersistentObject, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'name': ovo_fields.StringField(),
        'status': hd_fields.SiteStatusField(default=hd_fields.SiteStatus.Unknown),
        'source': hd_fields.ModelSourceField(),
        'tag_definitions': ovo_fields.ObjectField('NodeTagDefinitionList',
                                               nullable=True),
        'repositories': ovo_fields.ObjectField('RepositoryList', nullable=True),
        'authorized_keys': ovo_fields.ListOfStringsField(nullable=True),
    }

    def __init__(self, **kwargs):
        super(Site, self).__init__(**kwargs)

    def get_id(self):
        return self.name

    def get_name(self):
        return self.name

    def add_tag_definition(self, tag_definition):
        self.tag_definitions.append(tag_definition)

    def add_key(self, key_string):
        self.authorized_keys.append(key_string)

@base.DrydockObjectRegistry.register
class NodeTagDefinition(base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'tag': ovo_fields.StringField(),
        'type': ovo_fields.StringField(),
        'definition': ovo_fields.StringField(),
        'source':   hd_fields.ModelSourceField(),
    }

    def __init__(self, **kwargs):
        super(NodeTagDefinition, self).__init__(**kwargs)

    # TagDefinition keyed by tag
    def get_id(self):
        return self.tag

@base.DrydockObjectRegistry.register
class NodeTagDefinitionList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'objects': ovo_fields.ListOfObjectsField('NodeTagDefinition'),
    }

# Need to determine how best to define a repository that can encompass
# all repositories needed
@base.DrydockObjectRegistry.register
class Repository(base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'name': ovo_fields.StringField(),
    }

    def __init__(self, **kwargs):
        super(Repository, self).__init__(**kwargs)

    # TagDefinition keyed by tag
    def get_id(self):
        return self.name

@base.DrydockObjectRegistry.register
class RepositoryList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'objects': ovo_fields.ListOfObjectsField('Repository'),
    }

@base.DrydockObjectRegistry.register
class SiteDesign(base.DrydockPersistentObject, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'id':               ovo_fields.UUIDField(),
        # if null, indicates this is the site base design
        'base_design_id':   ovo_fields.UUIDField(nullable=True),
        'source':           hd_fields.ModelSourceField(),
        'site':             ovo_fields.ObjectField('Site', nullable=True),
        'networks':         ovo_fields.ObjectField('NetworkList', nullable=True),
        'network_links':    ovo_fields.ObjectField('NetworkLinkList', nullable=True),
        'host_profiles':    ovo_fields.ObjectField('HostProfileList', nullable=True),
        'hardware_profiles':    ovo_fields.ObjectField('HardwareProfileList', nullable=True),
        'baremetal_nodes':  ovo_fields.ObjectField('BaremetalNodeList', nullable=True),
        'prom_configs':     ovo_fields.ObjectField('PromenadeConfigList', nullable=True),
    }

    def __init__(self, **kwargs):
        super(SiteDesign, self).__init__(**kwargs)

    # Assign UUID id
    def assign_id(self):
        self.id = uuid.uuid4()
        return self.id

    # SiteDesign Keyed by id
    def get_id(self):
        return self.id

    def get_site(self):
        return self.site
        
    def set_site(self, site):
        self.site = site

    def add_network(self, new_network):
        if new_network is None:
            raise DesignError("Invalid Network model")

        if self.networks is None:
            self.networks = objects.NetworkList()

        self.networks.append(new_network)

    def get_network(self, network_key):
        for n in self.networks:
            if n.get_id() == network_key:
                return n

        raise DesignError("Network %s not found in design state"
                          % network_key)

    def add_network_link(self, new_network_link):
        if new_network_link is None:
            raise DesignError("Invalid NetworkLink model")

        if self.network_links is None:
            self.network_links = objects.NetworkLinkList()

        self.network_links.append(new_network_link)

    def get_network_link(self, link_key):
        for l in self.network_links:
            if l.get_id() == link_key:
                return l

        raise DesignError("NetworkLink %s not found in design state"
                          % link_key)

    def add_host_profile(self, new_host_profile):
        if new_host_profile is None:
            raise DesignError("Invalid HostProfile model")

        if self.host_profiles is None:
            self.host_profiles = objects.HostProfileList()

        self.host_profiles.append(new_host_profile)

    def get_host_profile(self, profile_key):
        for p in self.host_profiles:
            if p.get_id() == profile_key:
                return p

        raise DesignError("HostProfile %s not found in design state"
                          % profile_key)

    def add_hardware_profile(self, new_hardware_profile):
        if new_hardware_profile is None:
            raise DesignError("Invalid HardwareProfile model")

        if self.hardware_profiles is None:
            self.hardware_profiles = objects.HardwareProfileList()

        self.hardware_profiles.append(new_hardware_profile)

    def get_hardware_profile(self, profile_key):
        for p in self.hardware_profiles:
            if p.get_id() == profile_key:
                return p

        raise DesignError("HardwareProfile %s not found in design state"
                          % profile_key)

    def add_baremetal_node(self, new_baremetal_node):
        if new_baremetal_node is None:
            raise DesignError("Invalid BaremetalNode model")

        if self.baremetal_nodes is None:
            self.baremetal_nodes = objects.BaremetalNodeList()

        self.baremetal_nodes.append(new_baremetal_node)

    def get_baremetal_node(self, node_key):
        for n in self.baremetal_nodes:
            if n.get_id() == node_key:
                return n

        raise DesignError("BaremetalNode %s not found in design state"
                          % node_key)

    def add_promenade_config(self, prom_conf):
        if self.prom_configs is None:
            self.prom_configs = objects.PromenadeConfigList()

        self.prom_configs.append(prom_conf)

    def get_promenade_configs(self):
        return self.prom_configs

    def get_promenade_config(self, target_list):
        targeted_docs = []

        if target_list is None or not isinstance(target_list, list):
            return targeted_docs

        for t in target_list:
            targeted_docs.extend(self.prom_configs.select_for_target(t))

        return targeted_docs

    def create(self, ctx, state_manager):
        self.created_at = datetime.datetime.now()
        self.created_by = ctx.user

        state_manager.post_design(self)

    def save(self, ctx, state_manager):
        self.updated_at = datetime.datetime.now()
        self.updated_by = ctx.user

        state_manager.put_design(self)

    """
    Support filtering on rack name, node name or node tag
    for now. Each filter can be a comma-delimited list of
    values. The final result is an intersection of all the
    filters
    """
    def get_filtered_nodes(self, node_filter):
        effective_nodes = self.baremetal_nodes

        # filter by rack
        rack_filter = node_filter.get('rackname', None)

        if rack_filter is not None:
            rack_list = rack_filter.split(',')
            effective_nodes = [x 
                               for x in effective_nodes
                               if x.get_rack() in rack_list]
        # filter by name
        name_filter = node_filter.get('nodename', None)

        if name_filter is not None:
            name_list = name_filter.split(',')
            effective_nodes = [x
                               for x in effective_nodes
                               if x.get_name() in name_list]
        # filter by tag
        tag_filter = node_filter.get('tags', None)

        if tag_filter is not None:
            tag_list = tag_filter.split(',')
            effective_nodes = [x
                               for x in effective_nodes
                               for t in tag_list
                               if x.has_tag(t)]

        return effective_nodes

