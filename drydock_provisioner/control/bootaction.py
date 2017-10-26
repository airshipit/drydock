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
"""Handle resources for boot action API endpoints. """

import falcon
import ulid2
import tarfile
import io
import logging

from .base import StatefulResource

logger = logging.getLogger('drydock')

class BootactionResource(StatefulResource):
    def __init__(self, orchestrator=None, **kwargs):
        super().__init__(**kwargs)
        self.orchestrator = orchestrator

    def on_post(self, req, resp, action_id):
        """Post status messages or final status for a boot action.

        This endpoint does not use the standard oslo_policy enforcement as this endpoint
        is accessed by unmanned nodes. Instead it uses a internal key authentication

        :param req: falcon request
        :param resp: falcone response
        :param action_id: ULID ID of the boot action
        """


class BootactionAssetsResource(StatefulResource):
    def __init__(self, orchestrator=None, **kwargs):
        super().__init__(**kwargs)
        self.orchestrator = orchestrator

    def do_get(self, req, resp, hostname, asset_type):
        """Render ``unit`` type boot action assets for hostname.

        Get the boot action context for ``hostname`` from the database
        and render all ``unit`` type assets for the host. Validate host
        is providing the correct idenity key in the ``X-Bootaction-Key``
        header.

        :param req: falcon request object
        :param resp: falcon response object
        :param hostname: URL path parameter indicating the calling host
        :param asset_type: Asset type to include in the response - ``unit``, ``file``, ``pkg_list``, ``all``
        """
        try:
            ba_ctx = self.state_manager.get_boot_action_context(hostname)
        except Exception as ex:
            self.logger.error(
                "Error locating boot action for %s" % hostname, exc_info=ex)
            raise falcon.HTTPNotFound()

        if ba_ctx is None:
            raise falcon.HTTPNotFound(
                description="Error locating boot action for %s" % hostname)

        BootactionUtils.check_auth(ba_ctx, req)

        asset_type_filter = None if asset_type == 'all' else asset_type

        try:
            task = self.state_manager.get_task(ba_ctx['task_id'])
            design_status, site_design = self.orchestrator.get_effective_site(
                task.design_ref)

            assets = list()
            for ba in site_design.bootactions:
                if hostname in ba.target_nodes:
                    action_id = ulid2.generate_binary_ulid()
                    assets.extend(
                        ba.render_assets(
                            hostname,
                            site_design,
                            action_id,
                            type_filter=asset_type_filter))
                    self.state_manager.post_boot_action(
                        hostname, ba_ctx['task_id'], ba_ctx['identity_key'],
                        action_id)

            tarball = BootactionUtils.tarbuilder(asset_list=assets)
            resp.set_header('Content-Type', 'application/gzip')
            resp.set_header('Content-Disposition',
                            "attachment; filename=\"%s-%s.tar.gz\"" %
                            (hostname, asset_type))
            resp.data = tarball
            resp.status = falcon.HTTP_200
            return
        except Exception as ex:
            self.logger.debug("Exception in boot action API.", exc_info=ex)
            raise falcon.HTTPInternalServerError(str(ex))


class BootactionUnitsResource(BootactionAssetsResource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_get(self, req, resp, hostname):
        self.logger.debug(
            "Accessing boot action units resource for host %s." % hostname)
        super().do_get(req, resp, hostname, 'unit')


class BootactionFilesResource(BootactionAssetsResource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_get(self, req, resp, hostname):
        super().do_get(req, resp, hostname, 'file')


class BootactionUtils(object):
    """Utility class shared by Boot Action API resources."""

    @staticmethod
    def check_auth(ba_ctx, req):
        """Check request authentication based on boot action context.

        Raise proper Falcon exception if authentication fails, otherwise
        silently return

        :param ba_ctx: Boot Action context from database
        :param req: The falcon request object of the API call
        """
        identity_key = req.get_header('X-Bootaction-Key', default='')

        if identity_key == '':
            raise falcon.HTTPUnauthorized(
                title='Unauthorized',
                description='No X-Bootaction-Key',
                challenges=['Bootaction-Key'])

        if ba_ctx['identity_key'] != bytes.fromhex(identity_key):
            logger.warn(
                "Forbidding boot action access - node: %s, identity_key: %s, req header: %s"
                % (ba_ctx['node_name'], str(ba_ctx['identity_key']),
                   str(bytes.fromhex(identity_key))))
            raise falcon.HTTPForbidden(
                title='Unauthorized', description='Invalid X-Bootaction-Key')

    @staticmethod
    def tarbuilder(asset_list=None):
        """Create a tar file from rendered assets.

        Add each asset in ``asset_list`` to a tar file with the defined
        path and permission. The assets need to have the rendered_bytes field
        populated. Return a tarfile.TarFile.

        :param hostname: the hostname the tar is destined for
        :param balltype: the type of assets being included
        :param asset_list: list of objects.BootActionAsset instances
        """
        tarbytes = io.BytesIO()
        tarball = tarfile.open(
            mode='w:gz', fileobj=tarbytes, format=tarfile.GNU_FORMAT)
        asset_list = asset_list or []
        for a in asset_list:
            fileobj = io.BytesIO(a.rendered_bytes)
            tarasset = tarfile.TarInfo(name=a.path)
            tarasset.size = len(a.rendered_bytes)
            tarasset.mode = a.permissions if a.permissions else 0o600
            tarasset.uid = 0
            tarasset.gid = 0
            tarball.addfile(tarasset, fileobj=fileobj)
        tarball.close()
        return tarbytes.getvalue()
