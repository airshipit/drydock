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
"""Handle resources for bootdata API endpoints.

THIS API IS DEPRECATED
"""

from oslo_config import cfg

from .base import StatefulResource


class BootdataResource(StatefulResource):

    bootdata_options = [
        cfg.StrOpt(
            'prom_init',
            default='/etc/drydock/bootdata/join.sh',
            help='Path to file to distribute for prom_init.sh')
    ]

    def __init__(self, orchestrator=None, **kwargs):
        super(BootdataResource, self).__init__(**kwargs)
        self.authorized_roles = ['anyone']
        self.orchestrator = orchestrator

        cfg.CONF.register_opts(
            BootdataResource.bootdata_options, group='bootdata')

        init_file = open(cfg.CONF.bootdata.prom_init, 'r')
        self.prom_init = init_file.read()
        init_file.close()

    def on_get(self, req, resp, hostname, data_key):
        if data_key == 'promservice':
            resp.body = BootdataResource.prom_init_service
            resp.content_type = 'text/plain'
            return
        elif data_key == 'vfservice':
            resp.body = BootdataResource.vfs_service
            resp.content_type = 'text/plain'
            return
        elif data_key == 'prominit':
            resp.body = self.prom_init
            resp.content_type = 'text/plain'
            return
        elif data_key == 'promconfig':
            # The next PS will be a complete rewrite of the bootdata system
            # so not wasting time refactoring this
            # TODO(sh8121att) rebuild bootdata API for BootAction framework
            resp.content = 'text/plain'
            return


#            bootdata = self.state_manager.get_bootdata_key(hostname)
#
#            if bootdata is None:
#                resp.status = falcon.HTTP_404
#                return
#            else:
#                resp.content_type = 'text/plain'
#
#                host_design_id = bootdata.get('design_id', None)
#                host_design = self.orchestrator.get_effective_site(
#                    host_design_id)
#
#                host_model = host_design.get_baremetal_node(hostname)
#
#                part_selectors = ['all', hostname]
#
#                if host_model.tags is not None:
#                    part_selectors.extend(host_model.tags)
#
#                all_configs = host_design.get_promenade_config(part_selectors)
#
#                part_list = [i.document for i in all_configs]
#
#                resp.body = "---\n" + "---\n".join([
#                    base64.b64decode(i.encode()).decode('utf-8')
#                    for i in part_list
#                ]) + "\n..."
#                return

    prom_init_service = (
        "[Unit]\n"
        "Description=Promenade Initialization Service\n"
        "Documentation=http://github.com/att-comdev/drydock\n"
        "After=network-online.target local-fs.target\n"
        "ConditionPathExists=!/var/lib/prom.done\n\n"
        "[Service]\n"
        "Type=simple\n"
        "ExecStart=/var/tmp/prom_init.sh /etc/prom_init.yaml\n\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n")

    vfs_service = (
        "[Unit]\n"
        "Description=SR-IOV Virtual Function configuration\n"
        "Documentation=http://github.com/att-comdev/drydock\n"
        "After=network.target local-fs.target\n\n"
        "[Service]\n"
        "Type=simple\n"
        "ExecStart=/bin/sh -c '/bin/echo 4 >/sys/class/net/ens3f0/device/sriov_numvfs'\n\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n")


def list_opts():
    return {'bootdata': BootdataResource.bootdata_options}
