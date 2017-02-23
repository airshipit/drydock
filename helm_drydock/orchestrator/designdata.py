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

    def load_design_data(self, design_state=None):
        if len(design_state.get_sites()) != 1:
            self.log.error("Invalid design state, should only have 1 Site model")
            raise Exception("Invalid design state, should only have 1 Site model")

        site = design_state.get_sites()[0]
        site_name = site.name

        networks = design_state.get_networks()

        for n in networks:
            if n.site == site_name:
                site.networks.append(n)

        network_links = design_state.get_network_links()

        for l in network_links:
            if l.site == site_name:
                site.network_links.append(l)

        host_profiles = design_state.get_host_profiles()

        for p in host_profiles:
            if p.site == site_name:
                site.host_profiles.append(p)

        hardware_profiles = design_state.get_hardware_profiles()

        for p in hardware_profiles:
            if p.site == site_name:
                site.hardware_profiles.append(p)

        baremetal_nodes = design_state.get_baremetal_nodes()

        for n in baremetal_nodes:
            if n.site == site_name:
                site.baremetal_nodes.append(n)


        return site

    """
    compute_model_inheritance - given a fully populated Site model, compute the effecitve
    design by applying inheritance and references

    return a Site model reflecting the effective design for the site
    """
    def compute_model_inheritance(self, site_root):
        