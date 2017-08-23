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
import yaml
import base64

from oslo_config import cfg

from .base import StatefulResource

class BootdataResource(StatefulResource):

    bootdata_options = [
        cfg.StrOpt('prom_init', default='/etc/drydock/bootdata/join.sh', help='Path to file to distribute for prom_init.sh')
    ]

    def __init__(self, orchestrator=None, **kwargs):
        super(BootdataResource, self).__init__(**kwargs)
        self.authorized_roles = ['anyone']
        self.orchestrator = orchestrator

        cfg.CONF.register_opts(BootdataResource.bootdata_options, group='bootdata')

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
            bootdata = self.state_manager.get_bootdata_key(hostname)

            if bootdata is None:
                resp.status = falcon.HTTP_404
                return
            else:
                resp.content_type = 'text/plain'

                host_design_id = bootdata.get('design_id', None)
                host_design = self.orchestrator.get_effective_site(host_design_id)

                host_model = host_design.get_baremetal_node(hostname)

                part_selectors = ['all', hostname]

                if host_model.tags is not None:
                    part_selectors.extend(host_model.tags)

                all_configs = host_design.get_promenade_config(part_selectors)

                part_list = [i.document for i in all_configs]  

                resp.body = "---\n" + "---\n".join([base64.b64decode(i.encode()).decode('utf-8') for i in part_list]) + "\n..."
                return


    prom_init_service = \
r"""[Unit]
Description=Promenade Initialization Service
Documentation=http://github.com/att-comdev/drydock
After=network.target local-fs.target
ConditionPathExists=!/var/lib/prom.done

[Service]
Type=simple
ExecStart=/var/tmp/prom_init.sh /etc/prom_init.yaml

[Install]
WantedBy=multi-user.target
"""

    vfs_service = \
r"""[Unit]
Description=SR-IOV Virtual Function configuration
Documentation=http://github.com/att-comdev/drydock
After=network.target local-fs.target

[Service]
Type=simple
ExecStart=/bin/sh -c '/bin/echo 4 >/sys/class/net/ens3f0/device/sriov_numvfs'

[Install]
WantedBy=multi-user.target
"""

def list_opts():
    return {'bootdata': BootdataResource.bootdata_options}
