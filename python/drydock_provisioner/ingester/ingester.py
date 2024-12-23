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
"""Ingest host topologies to define site design."""
import logging
import importlib

from drydock_provisioner import error as errors

import drydock_provisioner.objects as objects
import drydock_provisioner.objects.site as site
import drydock_provisioner.objects.network as network
import drydock_provisioner.objects.hwprofile as hwprofile
import drydock_provisioner.objects.node as node
import drydock_provisioner.objects.hostprofile as hostprofile
import drydock_provisioner.objects.promenade as prom
import drydock_provisioner.objects.rack as rack
import drydock_provisioner.objects.bootaction as bootaction


class Ingester(object):

    def __init__(self):
        self.logger = logging.getLogger("drydock.ingester")
        self.registered_plugin = None

    def enable_plugin(self, plugin):
        """Enable a ingester plugin for use parsing design documents.

        :params plugin: - A string naming a class object denoting the ingester plugin to be enabled
        """
        if plugin is None or plugin == '':
            self.log.error("Cannot have an empty plugin string.")

        try:
            (module, x, classname) = plugin.rpartition('.')

            if module == '':
                raise Exception()
            mod = importlib.import_module(module)
            klass = getattr(mod, classname)
            self.registered_plugin = klass()
        except Exception as ex:
            self.logger.error("Could not enable plugin %s - %s" %
                              (plugin, str(ex)))

        if self.registered_plugin is None:
            self.logger.error("Could not enable at least one plugin")
            raise Exception("Could not enable at least one plugin")

    def ingest_data(self,
                    design_state=None,
                    design_ref=None,
                    context=None,
                    **kwargs):
        """Execute a data ingestion of the design reference.

        Return a tuple of the processing status and a instance of objects.SiteDesign
        populated with all the processed design parts.

        :param design_state: - An instance of statemgmt.state.DrydockState
        :param design_ref: - The design reference to source design data from
        :param context: - Context of the request requesting ingestion
        :param kwargs: - Keywork arguments to pass to the ingester plugin
        """
        if design_state is None:
            self.logger.error(
                "Ingester:ingest_data called without valid DrydockState handler"
            )
            raise ValueError("Invalid design_state handler")

        # If no design_id is specified, instantiate a new one
        if design_ref is None:
            self.logger.error(
                "Ingester:ingest_data required kwarg 'design_ref' missing")
            raise ValueError(
                "Ingester:ingest_data required kwarg 'design_ref' missing")

        self.logger.debug(
            "Ingester:ingest_data ingesting design parts for design %s" %
            design_ref)
        design_blob = design_state.get_design_documents(design_ref)
        self.logger.debug("Ingesting design data of %d bytes." %
                          len(design_blob))

        try:
            status, design_items = self.registered_plugin.ingest_data(
                content=design_blob, **kwargs)
        except errors.IngesterError as vex:
            self.logger.warning(
                "Ingester:ingest_data - Unexpected error processing data - %s"
                % (str(vex)))
            return None, None
        self.logger.debug("Ingester:ingest_data parsed %s design parts" %
                          str(len(design_items)))
        design_data = objects.SiteDesign()
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
            elif type(m) is rack.Rack:
                design_data.add_rack(m)
            elif type(m) is bootaction.BootAction:
                design_data.add_bootaction(m)
        return status, design_data
