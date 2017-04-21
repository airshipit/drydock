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
# ingester - Ingest host topologies to define site design and
# 			persist design to helm-drydock's statemgmt service

import logging
import yaml

import helm_drydock.model.site as site
import helm_drydock.model.network as network
import helm_drydock.model.hwprofile as hwprofile
import helm_drydock.model.node as node
import helm_drydock.model.hostprofile as hostprofile

from helm_drydock.statemgmt import DesignState, SiteDesign, DesignError

class Ingester(object):

    def __init__(self):
        logging.basicConfig(format="%(asctime)-15s [%(levelname)] %(module)s %(process)d %(message)s")
        self.log = logging.Logger("ingester")
        self.registered_plugins = {}

    def enable_plugins(self, plugins=[]):
        if len(plugins) == 0:
            self.log.error("Cannot have an empty plugin list.")

        for plugin in plugins:
            try:
                new_plugin = plugin()
                plugin_name = new_plugin.get_name()
                self.registered_plugins[plugin_name] = new_plugin
            except:
                self.log.error("Could not enable plugin %s" % (plugin.__name__))

        if len(self.registered_plugins) == 0:
            self.log.error("Could not enable at least one plugin")
            raise Exception("Could not enable at least one plugin")
    """
      enable_plugins

      params: plugins - A list of class objects denoting the ingester plugins to be enabled

      Enable plugins that can be used for ingest_data calls. Each plugin should use
      helm_drydock.ingester.plugins.IngesterPlugin as its base class. As long as one
      enabled plugin successfully initializes, the call is considered successful. Otherwise
      it will throw an exception
    """
    
    def ingest_data(self, plugin_name='', design_state=None, **kwargs):
        if design_state is None:
            self.log.error("ingest_data called without valid DesignState handler")
            raise Exception("Invalid design_state handler")

        # TODO this method needs refactored to handle design base vs change

        design_data = None

        try:
            design_data = design_state.get_design_base()
        except DesignError:
            design_data = SiteDesign()
            design_state.post_design_base(design_data)

        if plugin_name in self.registered_plugins:
            design_items = self.registered_plugins[plugin_name].ingest_data(**kwargs)
            # Need to persist data here, but we don't yet have the statemgmt service working
            for m in design_items:
                if type(m) is site.Site:
                    design_data.add_site(m)
                elif type(m) is network.Network:
                    design_data.add_network(m)
                elif type(m) is network.NetworkLink:
                    design_data.add_network_link(m)
                elif type(m) is hostprofile.HostProfile:
                    design_data.add_host_profile(m)
                elif type(m) is hwprofile.HardwareProfile:
                    design_data.add_hardware_profile(m)
                elif type(m) is node.BaremetalNode:
                    design_data.add_baremetal_node(m)
            design_state.put_design_base(design_data)
        else:
            self.log.error("Could not find plugin %s to ingest data." % (plugin_name))
            raise LookupError("Could not find plugin %s" % plugin_name)
    """
      ingest_data

      params: plugin_name - Which plugin should be used for ingestion
      params: params - A map of parameters that will be passed to the plugin's ingest_data method

      Execute a data ingestion using the named plugin (assuming it is enabled) 
    """

