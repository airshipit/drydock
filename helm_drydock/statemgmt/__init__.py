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
from copy import deepcopy
from datetime import datetime
from datetime import timezone
from threading import Lock

import uuid

import helm_drydock.model.node as node
import helm_drydock.model.hostprofile as hostprofile
import helm_drydock.model.network as network
import helm_drydock.model.site as site
import helm_drydock.model.hwprofile as hwprofile

from helm_drydock.error import DesignError, StateError

class DesignState(object):

    def __init__(self):
        self.design_base = None
        self.design_base_lock = Lock()

        self.design_changes = []
        self.design_changes_lock = Lock()

        self.builds = []
        self.builds_lock = Lock()

        return

    # TODO Need to lock a design base or change once implementation
    # has started
    def get_design_base(self):
        if self.design_base is None:
            raise DesignError("No design base submitted")

        return deepcopy(self.design_base)

    def post_design_base(self, site_design):
        if site_design is not None and isinstance(site_design, SiteDesign):
            my_lock = self.design_base_lock.acquire(blocking=True,
                timeout=10)
            if my_lock:
                self.design_base = deepcopy(site_design)
                self.design_base_lock.release()
                return True
            raise StateError("Could not acquire lock")
        else:
            raise DesignError("Design change must be a SiteDesign instance")

    def put_design_base(self, site_design):
        if site_design is not None and isinstance(site_design, SiteDesign):
            my_lock = self.design_base_lock.acquire(blocking=True,
                timeout=10)
            if my_lock:
                self.design_base.merge_updates(site_design)
                self.design_base_lock.release()
                return True
            raise StateError("Could not acquire lock")
        else:
            raise DesignError("Design base must be a SiteDesign instance")

    def get_design_change(self, changeid):
        match = [x for x in self.design_changes if x.changeid == changeid]

        if len(match) == 0:
            raise DesignError("No design change %s found." % (changeid))
        else:
            return deepcopy(match[0])

    def post_design_change(self, site_design):
        if site_design is not None and isinstance(site_design, SiteDesign):
            my_lock = self.design_changes_lock.acquire(block=True,
                timeout=10)
            if my_lock:
                exists = [(x) for x
                          in self.design_changes
                          if x.changeid == site_design.changeid]
                if len(exists) > 0:
                    self.design_changs_lock.release()
                    raise DesignError("Existing change %s found" %
                        (site_design.changeid))

                self.design_changes.append(deepcopy(site_design))
                self.design_changes_lock.release()
                return True
            raise StateError("Could not acquire lock")
        else:
            raise DesignError("Design change must be a SiteDesign instance")

    def put_design_change(self, site_design):
        if site_design is not None and isinstance(site_design, SiteDesign):
            my_lock = self.design_changes_lock.acquire(block=True,
                timeout=10)
            if my_lock:
                changeid = site_design.changeid
                for c in self.design_changes:
                    if c.changeid == changeid:
                        c.merge_updates(site_design)
                        return True
            raise StateError("Could not acquire lock")
        else:
            raise DesignError("Design change must be a SiteDesign instance")

    def get_current_build(self):
        latest_stamp = 0
        current_build = None

        for b in self.builds:
            if b.build_id > latest_stamp:
                latest_stamp = b.build_id
                current_build = b

        return deepcopy(current_build)

    def get_build(self, build_id):
        for b in self.builds:
            if b.build_id == build_id:
                return b

        return None

    def post_build(self, site_build):
        if site_build is not None and isinstance(site_build, SiteBuild):
            my_lock = self.builds_lock.acquire(block=True, timeout=10)
            if my_lock:
                exists = [b for b in self.builds
                          if b.build_id == site_build.build_id]

                if len(exists) > 0:
                    self.builds_lock.release()
                    raise DesignError("Already a site build with ID %s" %
                        (str(site_build.build_id)))
                self.builds.append(deepcopy(site_build))
                self.builds_lock.release()
                return True
            raise StateError("Could not acquire lock")
        else:
            raise DesignError("Design change must be a SiteDesign instance")

    def put_build(self, site_build):
        if site_build is not None and isinstance(site_build, SiteBuild):
            my_lock = self.builds_lock.acquire(block=True, timeout=10)
            if my_lock:
                buildid = site_build.buildid
                for b in self.builds:
                    if b.buildid == buildid:
                        b.merge_updates(site_build)
                        self.builds_lock.release()
                        return True
                self.builds_lock.release()
                return False
            raise StateError("Could not acquire lock")
        else:
            raise DesignError("Design change must be a SiteDesign instance")

class SiteDesign(object):

    def __init__(self, ischange=False, changeid=None):
        if ischange:
            if changeid is not None:
                self.changeid = changeid
            else:
                self.changeid = uuid.uuid4()
        else:
            # Base design
            self.changeid = 0

        self.sites = []
        self.networks = []
        self.network_links = []
        self.host_profiles = []
        self.hardware_profiles = []
        self.baremetal_nodes = []

    def add_site(self, new_site):
        if new_site is None or not isinstance(new_site, site.Site):
            raise DesignError("Invalid Site model")

        self.sites.append(new_site)

    def update_site(self, update):
        if update is None or not isinstance(update, site.Site):
            raise DesignError("Invalid Site model")

        for i, s in enumerate(self.sites):
            if s.get_name() == update.get_name():
                self.sites[i] = deepcopy(update)
                return True

        return False

    def get_sites(self):
        return self.sites

    def get_site(self, site_name):
        for s in self.sites:
            if s.name == site_name:
                return s

        raise DesignError("Site %s not found in design state" % site_name)

    def add_network(self, new_network):
        if new_network is None or not isinstance(new_network, network.Network):
            raise DesignError("Invalid Network model")

        self.networks.append(new_network)

    def update_network(self, update):
        if update is None or not isinstance(update, network.Network):
            raise DesignError("Invalid Network model")

        for i, n in enumerate(self.networks):
            if n.get_name() == update.get_name():
                self.networks[i] = deepcopy(update)
                return True

        return False

    def get_networks(self):
        return self.networks

    def get_network(self, network_name):
        for n in self.networks:
            if n.name == network_name:
                return n

        raise DesignError("Network %s not found in design state"
                          % network_name)

    def add_network_link(self, new_network_link):
        if new_network_link is None or not isinstance(new_network_link,
                                                      network.NetworkLink):
            raise DesignError("Invalid NetworkLink model")

        self.network_links.append(new_network_link)

    def update_network_link(self, update):
        if update is None or not isinstance(update, network.NetworkLink):
            raise DesignError("Invalid NetworkLink model")

        for i, n in enumerate(self.network_links):
            if n.get_name() == update.get_name():
                self.network_links[i] = deepcopy(update)
                return True

        return False

    def get_network_links(self):
        return self.network_links

    def get_network_link(self, link_name):
        for l in self.network_links:
            if l.name == link_name:
                return l

        raise DesignError("NetworkLink %s not found in design state"
                          % link_name)

    def add_host_profile(self, new_host_profile):
        if new_host_profile is None or not isinstance(new_host_profile,
                                                      hostprofile.HostProfile):
            raise DesignError("Invalid HostProfile model")

        self.host_profiles.append(new_host_profile)

    def update_host_profile(self, update):
        if update is None or not isinstance(update, hostprofile.HostProfile):
            raise DesignError("Invalid HostProfile model")

        for i, h in enumerate(self.host_profiles):
            if h.get_name() == update.get_name():
                self.host_profiles[i] = deepcopy(h)
                return True

        return False

    def get_host_profiles(self):
        return self.host_profiles

    def get_host_profile(self, profile_name):
        for p in self.host_profiles:
            if p.name == profile_name:
                return p

        raise DesignError("HostProfile %s not found in design state"
                          % profile_name)

    def add_hardware_profile(self, new_hardware_profile):
        if (new_hardware_profile is None or
            not isinstance(new_hardware_profile, hwprofile.HardwareProfile)):
            raise DesignError("Invalid HardwareProfile model")

        self.hardware_profiles.append(new_hardware_profile)

    def update_hardware_profile(self, update):
        if update is None or not isinstance(update, hwprofile.HardwareProfile):
            raise DesignError("Invalid HardwareProfile model")

        for i, h in enumerate(self.hardware_profiles):
            if h.get_name() == update.get_name():
                self.hardware_profiles[i] = deepcopy(h)
                return True

        return False

    def get_hardware_profiles(self):
        return self.hardware_profiles

    def get_hardware_profile(self, profile_name):
        for p in self.hardware_profiles:
            if p.name == profile_name:
                return p

        raise DesignError("HardwareProfile %s not found in design state"
                          % profile_name)

    def add_baremetal_node(self, new_baremetal_node):
        if (new_baremetal_node is None or
            not isinstance(new_baremetal_node, node.BaremetalNode)):
            raise DesignError("Invalid BaremetalNode model")

        self.baremetal_nodes.append(new_baremetal_node)

    def update_baremetal_node(self, update):
        if (update is None or not isinstance(update, node.BaremetalNode)):
            raise DesignError("Invalid BaremetalNode model")

        for i, b in enumerate(self.baremetal_nodes):
            if b.get_name() == update.get_name():
                self.baremetal_nodes[i] = deepcopy(b)
                return True

        return False

    def get_baremetal_nodes(self):
        return self.baremetal_nodes

    def get_baremetal_node(self, node_name):
        for n in self.baremetal_nodes:
            if n.name == node_name:
                return n

        raise DesignError("BaremetalNode %s not found in design state"
                          % node_name)

    # Only merge the design parts included in the updated site
    # design. Changes are merged at the part level, not for fields
    # within a design part
    #
    # TODO convert update_* methods to use exceptions and convert to try block
    def merge_updates(self, updates):
        if updates is not None and isinstance(updates, SiteDesign):
            if updates.changeid == self.changeid:
                for u in updates.sites:
                    if not self.update_site(u):
                        self.add_site(u)
                for u in updates.networks:
                    if not self.update_network(u):
                        self.add_network(u)
                for u in updates.network_links:
                    if not self.update_network_link(u):
                        self.add_network_link(u)
                for u in updates.host_profiles:
                    if not self.update_host_profile(u):
                        self.add_host_profile(u)
                for u in updates.hardware_profiles:
                    if not self.update_hardware_profile(u):
                        self.add_hardware_profile(u)
                for u in updates.baremetal_nodes:
                    if not self.update_baremetal_node(u):
                        self.add_baremetal_node(u)


class SiteBuild(SiteDesign):

    def __init__(self, build_id=None):
        super(SiteBuild, self).__init__()

        if build_id is None:
            self.buildid = datetime.datetime.now(timezone.utc).timestamp()
        else:
            self.buildid = build_id

    def get_filtered_nodes(self, node_filter):
        effective_nodes = self.get_baremetal_nodes()

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
    """
    Support filtering on rack name, node name or node tag
    for now. Each filter can be a comma-delimited list of
    values. The final result is an intersection of all the
    filters
    """

    def set_nodes_status(self, node_filter, status):
        target_nodes = self.get_filtered_nodes(node_filter)

        for n in target_nodes:
            n.set_status(status)
