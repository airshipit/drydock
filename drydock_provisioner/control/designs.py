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
import falcon
import json
import uuid
import logging

import drydock_provisioner.objects as hd_objects
import drydock_provisioner.error as errors

from .base import StatefulResource

class DesignsResource(StatefulResource):

    def __init__(self, **kwargs):
        super(DesignsResource, self).__init__(**kwargs)
        self.authorized_roles = ['user']

    def on_get(self, req, resp):
        state = self.state_manager

        designs = list(state.designs.keys())

        resp.body = json.dumps(designs)
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp):
        try:
            json_data = self.req_json(req)
            design = None
            if json_data is not None:
                base_design = json_data.get('base_design_id', None)

                if base_design is not None:
                    base_design = uuid.UUID(base_design)
                    design = hd_objects.SiteDesign(base_design_id=base_design_uuid)
            else:
                design = hd_objects.SiteDesign()
            design.assign_id()
            design.create(req.context, self.state_manager)

            resp.body = json.dumps(design.obj_to_simple())
            resp.status = falcon.HTTP_201
        except errors.StateError as stex:
            self.error(req.context, "Error updating persistence")
            self.return_error(resp, falcon.HTTP_500, message="Error updating persistence", retry=True)
        except errors.InvalidFormat as fex:
            self.error(req.context, str(fex))
            self.return_error(resp, falcon.HTTP_400, message=str(fex), retry=False)


class DesignResource(StatefulResource):

    def __init__(self, orchestrator=None, **kwargs):
        super(DesignResource, self).__init__(**kwargs)
        self.authorized_roles = ['user']
        self.orchestrator = orchestrator

    def on_get(self, req, resp, design_id):
        source = req.params.get('source', 'designed')

        try:
            design = None
            if source == 'compiled':
                design = self.orchestrator.get_effective_site(design_id)
            elif source == 'designed':
                design = self.orchestrator.get_described_site(design_id)

            resp.body = json.dumps(design.obj_to_simple())
        except errors.DesignError:
            self.error(req.context, "Design %s not found" % design_id)
            self.return_error(resp, falcon.HTTP_404, message="Design %s not found" % design_id, retry=False)

class DesignsPartsResource(StatefulResource):

    def __init__(self, ingester=None, **kwargs):
        super(DesignsPartsResource, self).__init__(**kwargs)
        self.ingester = ingester
        self.authorized_roles = ['user']

        if ingester is None:
            self.error(None, "DesignsPartsResource requires a configured Ingester instance")
            raise ValueError("DesignsPartsResource requires a configured Ingester instance")

    def on_post(self, req, resp, design_id):
        ingester_name = req.params.get('ingester', None)

        if ingester_name is None:
            self.error(None, "DesignsPartsResource POST requires parameter 'ingester'")
            self.return_error(resp, falcon.HTTP_400, message="POST requires parameter 'ingester'", retry=False)
        else:
            try:
                raw_body = req.stream.read(req.content_length or 0)
                if raw_body is not None and len(raw_body) > 0:
                    parsed_items = self.ingester.ingest_data(plugin_name=ingester_name, design_state=self.state_manager,
                                                             content=raw_body, design_id=design_id, context=req.context)
                    resp.status = falcon.HTTP_201
                    resp.body = json.dumps([x.obj_to_simple() for x in parsed_items])
                else:
                    self.return_error(resp, falcon.HTTP_400, message="Empty body not supported", retry=False)    
            except ValueError:
                self.return_error(resp, falcon.HTTP_500, message="Error processing input", retry=False)
            except LookupError:
                self.return_error(resp, falcon.HTTP_400, message="Ingester %s not registered" % ingester_name, retry=False)

    def on_get(self, req, resp, design_id):
        try:
            design = self.state_manager.get_design(design_id)
        except DesignError:
            self.return_error(resp, falcon.HTTP_404, message="Design %s nout found" % design_id, retry=False)

        part_catalog = []

        site = design.get_site()

        part_catalog.append({'kind': 'Region', 'key': site.get_id()})

        part_catalog.extend([{'kind': 'Netowrk', 'key': n.get_id()} for n in design.networks])

        part_catalog.extend([{'kind': 'NetworkLink', 'key': l.get_id()} for l in design.network_links])

        part_catalog.extend([{'kind': 'HostProfile', 'key': p.get_id()} for p in design.host_profiles])

        part_catalog.extend([{'kind': 'HardwareProfile', 'key': p.get_id()} for p in design.hardware_profiles])

        part_catalog.extend([{'kind': 'BaremetalNode', 'key': n.get_id()} for n in design.baremetal_nodes])

        resp.body = json.dumps(part_catalog)
        resp.status = falcon.HTTP_200
        return


class DesignsPartsKindsResource(StatefulResource):
    def __init__(self, **kwargs):
        super(DesignsPartsKindsResource, self).__init__(**kwargs)
        self.authorized_roles = ['user']

    def on_get(self, req, resp, design_id, kind):
        pass

class DesignsPartResource(StatefulResource):

    def __init__(self, orchestrator=None, **kwargs):
        super(DesignsPartResource, self).__init__(**kwargs)
        self.authorized_roles = ['user']
        self.orchestrator = orchestrator

    def on_get(self, req , resp, design_id, kind, name):
        source = req.params.get('source', 'designed')

        try:
            design = None
            if source == 'compiled':
                design = self.orchestrator.get_effective_site(design_id)
            elif source == 'designed':
                design = self.orchestrator.get_described_site(design_id)

            part = None
            if kind == 'Site':
                part = design.get_site()
            elif kind == 'Network':
                part = design.get_network(name)
            elif kind == 'NetworkLink':
                part = design.get_network_link(name)
            elif kind == 'HardwareProfile':
                part = design.get_hardware_profile(name)
            elif kind == 'HostProfile':
                part = design.get_host_profile(name)
            elif kind == 'BaremetalNode':
                part = design.get_baremetal_node(name)
            else:
                self.error(req.context, "Kind %s unknown" % kind)
                self.return_error(resp, falcon.HTTP_404, message="Kind %s unknown" % kind, retry=False)
                return

            resp.body = json.dumps(part.obj_to_simple())
        except errors.DesignError as dex:
            self.error(req.context, str(dex))
            self.return_error(resp, falcon.HTTP_404, message=str(dex), retry=False)
