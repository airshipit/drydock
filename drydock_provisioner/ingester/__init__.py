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
import  uuid
import importlib

import drydock_provisioner.objects as objects
import drydock_provisioner.objects.site as site
import drydock_provisioner.objects.network as network
import drydock_provisioner.objects.hwprofile as hwprofile
import drydock_provisioner.objects.node as node
import drydock_provisioner.objects.hostprofile as hostprofile
import drydock_provisioner.objects.promenade as prom

from drydock_provisioner.statemgmt import DesignState

class Ingester(object):

    def __init__(self):
        self.logger = logging.getLogger("drydock.ingester")
        self.registered_plugins = {}

    def enable_plugins(self, plugins=[]):
        """
        enable_plugins

        :params plugins: - A list of strings naming class objects denoting the ingester plugins to be enabled

        Enable plugins that can be used for ingest_data calls. Each plugin should use
        drydock_provisioner.ingester.plugins.IngesterPlugin as its base class. As long as one
        enabled plugin successfully initializes, the call is considered successful. Otherwise
        it will throw an exception
        """
        if len(plugins) == 0:
            self.log.error("Cannot have an empty plugin list.")

        for plugin in plugins:
            try:
                (module, x, classname) = plugin.rpartition('.')

                if module == '':
                    raise Exception()
                mod = importlib.import_module(module)
                klass = getattr(mod, classname)
                new_plugin = klass()
                plugin_name = new_plugin.get_name()
                self.registered_plugins[plugin_name] = new_plugin
            except Exception as ex:
                self.logger.error("Could not enable plugin %s - %s" % (plugin, str(ex)))

        if len(self.registered_plugins) == 0:
            self.logger.error("Could not enable at least one plugin")
            raise Exception("Could not enable at least one plugin")

    
    def ingest_data(self, plugin_name='', design_state=None, design_id=None, context=None, **kwargs):
        """
        ingest_data - Execute a data ingestion using the named plugin (assuming it is enabled) 

        :param plugin_name: - Which plugin should be used for ingestion
        :param design_state: - An instance of statemgmt.DesignState
        :param design_id: - The ID of the SiteDesign all parsed designed parts should be added
        :param context: - Context of the request requesting ingestion
        :param kwargs: - Keywork arguments to pass to the ingester plugin
        """
        if design_state is None:
            self.logger.error("Ingester:ingest_data called without valid DesignState handler")
            raise ValueError("Invalid design_state handler")

        # If no design_id is specified, instantiate a new one
        if 'design_id' is None:
            self.logger.error("Ingester:ingest_data required kwarg 'design_id' missing")
            raise ValueError("Ingester:ingest_data required kwarg 'design_id' missing")
        
        design_data = design_state.get_design(design_id)

        self.logger.debug("Ingester:ingest_data ingesting design parts for design %s" % design_id)

        if plugin_name in self.registered_plugins:
            try:
                design_items = self.registered_plugins[plugin_name].ingest_data(**kwargs)
            except ValueError as vex:
                self.logger.warn("Ingester:ingest_data - Error process data - %s" % (str(vex)))
                return None
            self.logger.debug("Ingester:ingest_data parsed %s design parts" % str(len(design_items)))
            for m in design_items:
                if context is not None:
                    m.set_create_fields(context)
                if type(m) is site.Site:
                    design_data.set_site(m)
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
                elif type(m) is prom.PromenadeConfig:
                    design_data.add_promenade_config(m)
            design_state.put_design(design_data)
            return design_items
        else:
            self.logger.error("Could not find plugin %s to ingest data." % (plugin_name))
            raise LookupError("Could not find plugin %s" % plugin_name)


