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
"""Object models for BootActions."""
import base64
from jinja2 import Template
import ulid2
import yaml

import oslo_versionedobjects.fields as ovo_fields

import drydock_provisioner.objects.base as base
import drydock_provisioner.objects.fields as hd_fields

import drydock_provisioner.config as config
import drydock_provisioner.error as errors

from drydock_provisioner.statemgmt.design.resolver import ReferenceResolver


@base.DrydockObjectRegistry.register
class BootAction(base.DrydockPersistentObject, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'name':
        ovo_fields.StringField(),
        'source':
        hd_fields.ModelSourceField(nullable=False),
        'asset_list':
        ovo_fields.ObjectField('BootActionAssetList', nullable=False),
        'node_filter':
        ovo_fields.ObjectField('NodeFilterSet', nullable=True),
        'target_nodes':
        ovo_fields.ListOfStringsField(nullable=True),
        'signaling':
        ovo_fields.BooleanField(default=True),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.target_nodes:
            self.target_nodes = []

    # NetworkLink keyed by name
    def get_id(self):
        return self.get_name()

    def get_name(self):
        return self.name

    def render_assets(self,
                      nodename,
                      site_design,
                      action_id,
                      design_ref,
                      type_filter=None):
        """Render all of the assets in this bootaction.

        Render the assets of this bootaction and return them in a list.
        The ``nodename`` and ``action_id`` will be
        used to build the context for any assets utilizing the ``template``
        pipeline segment.

        :param nodename: name of the node the assets are destined for
        :param site_design: a objects.SiteDesign instance holding the design sets
        :param action_id: a 128-bit ULID action_id of the boot action
                          the assets are part of
        :param design_ref: the design ref this boot action was initiated under
        :param type_filter: optional filter of the types of assets to render
        """
        assets = list()
        for a in self.asset_list:
            if type_filter is None or (type_filter is not None
                                       and a.type == type_filter):
                a.render(nodename, site_design, action_id, design_ref)
                assets.append(a)

        return assets


@base.DrydockObjectRegistry.register
class BootActionList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'objects': ovo_fields.ListOfObjectsField('BootAction'),
    }


@base.DrydockObjectRegistry.register
class BootActionAsset(base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'type': hd_fields.BootactionAssetTypeField(nullable=True),
        'path': ovo_fields.StringField(nullable=True),
        'location': ovo_fields.StringField(nullable=True),
        'data': ovo_fields.StringField(nullable=True),
        'package_list': ovo_fields.DictOfNullableStringsField(nullable=True),
        'location_pipeline': ovo_fields.ListOfStringsField(nullable=True),
        'data_pipeline': ovo_fields.ListOfStringsField(nullable=True),
        'permissions': ovo_fields.IntegerField(nullable=True),
    }

    def __init__(self, **kwargs):
        if 'permissions' in kwargs:
            mode = kwargs.pop('permissions')
            if isinstance(mode, str):
                mode = int(mode, base=8)
        else:
            mode = None

        ba_type = kwargs.get('type', None)

        package_list = None
        if ba_type == hd_fields.BootactionAssetType.PackageList:
            if isinstance(kwargs.get('data'), dict):
                package_list = self._extract_package_list(kwargs.pop('data'))
            # If the data section doesn't parse as a dictionary
            # then the package data needs to be sourced dynamically
            # Otherwise the Bootaction is invalid
            elif not kwargs.get('location'):
                raise errors.InvalidPackageListFormat(
                    "Requires a top-level mapping/object.")

        super().__init__(package_list=package_list, permissions=mode, **kwargs)
        self.rendered_bytes = None

    def render(self, nodename, site_design, action_id, design_ref):
        """Render this asset into a base64 encoded string.

        The ``nodename`` and ``action_id`` will be used to construct
        the context for evaluating the ``template`` pipeline segment

        :param nodename: the name of the node where the asset will be deployed
        :param site_design: instance of objects.SiteDesign
        :param action_id: a 128-bit ULID boot action id
        :param design_ref: The design ref this bootaction was initiated under
        """
        tpl_ctx = self._get_template_context(nodename, site_design, action_id,
                                             design_ref)

        if self.location is not None:
            rendered_location = self.execute_pipeline(
                self.location, self.location_pipeline, tpl_ctx=tpl_ctx)
            data_block = self.resolve_asset_location(rendered_location)
            if self.type == hd_fields.BootactionAssetType.PackageList:
                self._parse_package_list(data_block)
        elif self.type != hd_fields.BootactionAssetType.PackageList:
            data_block = self.data.encode('utf-8')

        if self.type != hd_fields.BootactionAssetType.PackageList:
            value = self.execute_pipeline(
                data_block, self.data_pipeline, tpl_ctx=tpl_ctx)

            if isinstance(value, str):
                value = value.encode('utf-8')
            self.rendered_bytes = value

    def _parse_package_list(self, data):
        """Parse data expecting a list of packages to install.

        Expect data to be a bytearray reprsenting a JSON or YAML
        document.

        :param data: A bytearray of data to parse
        """
        try:
            data_string = data.decode('utf-8')
            parsed_data = yaml.safe_load(data_string)

            if isinstance(parsed_data, dict):
                self.package_list = self._extract_package_list(parsed_data)
            else:
                raise errors.InvalidPackageListFormat(
                    "Package data should have a top-level mapping/object.")
        except yaml.YAMLError as ex:
            raise errors.InvalidPackageListFormat(
                "Invalid YAML in package list: %s" % str(ex))

    def _extract_package_list(self, pkg_dict):
        """Extract package data into object model.

        :param pkg_dict: a dictionary of packages to install
        """
        package_list = dict()
        for k, v in pkg_dict.items():
            if (isinstance(k, str) and (not v or isinstance(v, str))):
                package_list[k] = v
            else:
                raise errors.InvalidPackageListFormat(
                    "Keys and values must be strings.")
        return package_list

    def _get_template_context(self, nodename, site_design, action_id,
                              design_ref):
        """Create a context to be used for template rendering.

        :param nodename: The name of the node for the bootaction
        :param site_design: The full site design
        :param action_id: the ULID assigned to the boot action using this context
        :param design_ref: The design reference representing ``site_design``
        """

        return dict(
            node=self._get_node_context(nodename, site_design),
            action=self._get_action_context(action_id, design_ref))

    def _get_action_context(self, action_id, design_ref):
        """Create the action-specific context items for template rendering.

        :param action_id: ULID of this boot action
        :param design_ref: Design reference representing the site design
        """
        return dict(
            key=ulid2.ulid_to_base32(action_id),
            report_url=config.config_mgr.conf.bootactions.report_url,
            design_ref=design_ref)

    def _get_node_context(self, nodename, site_design):
        """Create the node-specific context items for template rendering.

        :param nodename: name of the node this boot action targets
        :param site_design: full site design
        """
        node = site_design.get_baremetal_node(nodename)
        return dict(
            hostname=nodename,
            domain=node.get_domain(site_design),
            tags=[t for t in node.tags],
            labels={k: v
                    for (k, v) in node.owner_data.items()},
            network=self._get_node_network_context(node, site_design),
            interfaces=self._get_node_interface_context(node))

    def _get_node_network_context(self, node, site_design):
        """Create a node's network configuration context.

        :param node: node object
        :param site_design: full site design
        """
        network_context = dict()
        for a in node.addressing:
            if a.address is not None:
                network = site_design.get_network(a.network)
                network_context[a.network] = dict(
                    ip=a.address,
                    cidr=network.cidr,
                    dns_suffix=network.dns_domain)
                if a.network == node.primary_network:
                    network_context['default'] = network_context[a.network]

        return network_context

    def _get_node_interface_context(self, node):
        """Create a node's network interface context.

        :param node: the node object
        """
        interface_context = dict()
        for i in node.interfaces:
            interface_context[i.device_name] = dict(sriov=i.sriov)
            if i.sriov:
                interface_context[i.device_name]['vf_count'] = i.vf_count
                interface_context[i.device_name]['trustedmode'] = i.trustedmode
        return interface_context

    def resolve_asset_location(self, asset_url):
        """Retrieve the data asset from the url.

        Returns the asset as a bytestring.

        :param asset_url: URL to retrieve the data asset from
        """
        try:
            return ReferenceResolver.resolve_reference(asset_url)
        except Exception as ex:
            raise errors.InvalidAssetLocation(
                "Unable to resolve asset reference %s: %s" % (asset_url,
                                                              str(ex)))

    def execute_pipeline(self, data, pipeline, tpl_ctx=None):
        """Execute a pipeline against a data element.

        Returns the manipulated ``data`` element

        :param data: The data element to be manipulated by the pipeline
        :param pipeline: list of pipeline segments to execute
        :param tpl_ctx: The optional context to be made available to the ``template`` pipeline
        """
        segment_funcs = {
            'base64_encode': self.eval_base64_encode,
            'base64_decode': self.eval_base64_decode,
            'utf8_decode': self.eval_utf8_decode,
            'utf8_encode': self.eval_utf8_encode,
            'template': self.eval_template,
        }

        for s in pipeline:
            try:
                data = segment_funcs[s](data, ctx=tpl_ctx)
            except KeyError:
                raise errors.UnknownPipelineSegment(
                    "Bootaction pipeline segment %s unknown." % s)
            except Exception as ex:
                raise errors.PipelineFailure(
                    "Error when running bootaction pipeline segment %s: %s - %s"
                    % (s, type(ex).__name__, str(ex)))

        return data

    def eval_base64_encode(self, data, ctx=None):
        """Encode data as base64.

        Light weight wrapper around base64 library to shed the ctx kwarg

        :param data: data to be encoded
        :param ctx: throwaway, just allows a generic interface for pipeline segments
        """
        return base64.b64encode(data)

    def eval_base64_decode(self, data, ctx=None):
        """Decode data from base64.

        Light weight wrapper around base64 library to shed the ctx kwarg

        :param data: data to be decoded
        :param ctx: throwaway, just allows a generic interface for pipeline segments
        """
        return base64.b64decode(data)

    def eval_utf8_decode(self, data, ctx=None):
        """Decode data from bytes to UTF-8 string.

        :param data: data to be decoded
        :param ctx: throwaway, just allows a generic interface for pipeline segments
        """
        return data.decode('utf-8')

    def eval_utf8_encode(self, data, ctx=None):
        """Encode data from UTF-8 to bytes.

        :param data: data to be encoded
        :param ctx: throwaway, just allows a generic interface for pipeline segments
        """
        return data.encode('utf-8')

    def eval_template(self, data, ctx=None):
        """Evaluate data as a Jinja2 template.

        :param data: The template
        :param ctx: Optional ctx to inject into the template render
        """
        template = Template(data)
        return template.render(ctx)


@base.DrydockObjectRegistry.register
class BootActionAssetList(base.DrydockObjectListBase, base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'objects': ovo_fields.ListOfObjectsField('BootActionAsset'),
    }


@base.DrydockObjectRegistry.register
class NodeFilterSet(base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'filter_set_type': ovo_fields.StringField(nullable=False),
        'filter_set': ovo_fields.ListOfObjectsField('NodeFilter'),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@base.DrydockObjectRegistry.register
class NodeFilter(base.DrydockObject):

    VERSION = '1.0'

    fields = {
        'filter_type': ovo_fields.StringField(nullable=False),
        'node_names': ovo_fields.ListOfStringsField(nullable=True),
        'node_tags': ovo_fields.ListOfStringsField(nullable=True),
        'node_labels': ovo_fields.DictOfStringsField(nullable=True),
        'rack_names': ovo_fields.ListOfStringsField(nullable=True),
        'rack_labels': ovo_fields.DictOfStringsField(nullable=True),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
