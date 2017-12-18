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
        'type': ovo_fields.StringField(nullable=True),
        'path': ovo_fields.StringField(nullable=True),
        'location': ovo_fields.StringField(nullable=True),
        'data': ovo_fields.StringField(nullable=True),
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

        super().__init__(permissions=mode, **kwargs)
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
        node = site_design.get_baremetal_node(nodename)

        tpl_ctx = {
            'node': {
                'hostname': nodename,
                'tags': [t for t in node.tags],
                'labels': {k: v
                           for (k, v) in node.owner_data.items()},
                'network': {},
            },
            'action': {
                'key': ulid2.ulid_to_base32(action_id),
                'report_url': config.config_mgr.conf.bootactions.report_url,
                'design_ref': design_ref,
            }
        }

        for a in node.addressing:
            if a.address is not None:
                tpl_ctx['node']['network'][a.network] = dict()
                tpl_ctx['node']['network'][a.network]['ip'] = a.address
                network = site_design.get_network(a.network)
                tpl_ctx['node']['network'][a.network]['cidr'] = network.cidr
                tpl_ctx['node']['network'][a.network][
                    'dns_suffix'] = network.dns_domain

        if self.location is not None:
            rendered_location = self.execute_pipeline(
                self.location, self.location_pipeline, tpl_ctx=tpl_ctx)
            data_block = self.resolve_asset_location(rendered_location)
        else:
            data_block = self.data.encode('utf-8')

        value = self.execute_pipeline(
            data_block, self.data_pipeline, tpl_ctx=tpl_ctx)

        if isinstance(value, str):
            value = value.encode('utf-8')
        self.rendered_bytes = value

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
