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

import logging

from copy import deepcopy

from helm_drydock.error import DesignError

class DesignStateClient(object):

    def __init__(self):
        self.log = logging.Logger('orchestrator')

    """
    load_design_data - Pull all the defined models in statemgmt and assemble
    them into a representation of the site. Does not compute inheritance.
    Throws an exception if multiple Site models are found.

    param design_state - Instance of statemgmt.DesignState to load data from

    return a Site model populated with all components from the design state
    """

    def load_design_data(self, site_name, design_state=None, change_id=None):
        if design_state is None:
            raise ValueError("Design state is None")

        design_data = None

        if change_id is None:
            try:
                design_data = design_state.get_design_base()
            except DesignError(e):
                raise e
        else:
            design_data = design_state.get_design_change(change_id)

        site = design_data.get_site(site_name)

        networks = design_data.get_networks()

        for n in networks:
            if n.site == site_name:
                site.networks.append(n)

        network_links = design_data.get_network_links()

        for l in network_links:
            if l.site == site_name:
                site.network_links.append(l)

        host_profiles = design_data.get_host_profiles()

        for p in host_profiles:
            if p.site == site_name:
                site.host_profiles.append(p)

        hardware_profiles = design_data.get_hardware_profiles()

        for p in hardware_profiles:
            if p.site == site_name:
                site.hardware_profiles.append(p)

        baremetal_nodes = design_data.get_baremetal_nodes()

        for n in baremetal_nodes:
            if n.site == site_name:
                site.baremetal_nodes.append(n)

        return site

    def compute_model_inheritance(self, site_root):
        
        # For now the only thing that really incorporates inheritance is
        # host profiles and baremetal nodes. So we'll just resolve it for
        # the baremetal nodes which recursively resolves it for host profiles
        # assigned to those nodes

        site_copy = deepcopy(site_root)

        effective_nodes = []

        for n in site_copy.baremetal_nodes:
            resolved = n.apply_host_profile(site_copy)
            resolved = resolved.apply_hardware_profile(site_copy)
            resolved = resolved.apply_network_connections(site_copy)
            effective_nodes.append(resolved)

        site_copy.baremetal_nodes = effective_nodes
        
        return site_copy
    """
    compute_model_inheritance - given a fully populated Site model,
    compute the effecitve design by applying inheritance and references

    return a Site model reflecting the effective design for the site
    """
