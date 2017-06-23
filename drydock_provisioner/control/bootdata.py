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

from .base import StatefulResource

class BootdataResource(StatefulResource):

    def __init__(self, orchestrator=None, **kwargs):
        super(BootdataResource, self).__init__(**kwargs)
        self.authorized_roles = ['anyone']
        self.orchestrator = orchestrator

    def on_get(self, req, resp, hostname, data_key):
        if data_key == 'systemd':
            resp.body = BootdataResource.systemd_definition
            resp.content_type = 'text/plain'
            return
        elif data_key == 'prominit':
            resp.body = BootdataResource.prom_init
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

                part_list = []

                all_parts = self.state_manager.get_promenade_parts('all')

                if all_parts is not None:
                    part_list.extend([i.document for i in all_parts])

                host_parts = self.state_manager.get_promenade_parts(hostname)

                if host_parts is not None:
                    part_list.extend([i.document for i in host_parts])

                for t in host_model.tags:
                    tag_parts = self.state_manager.get_promenade_parts(t)
                    if t is not None:
                        part_list.extend([i.document for i in tag_parts])

                resp.body = "---\n" + "---\n".join(part_list) + "...\n"
                return

    systemd_definition = \
"""[Unit]
Description=Promenade Initialization Service
Documentation=http://github.com/att-comdev/drydock
After=network.target local-fs.target
ConditionPathExists=!/var/lib/prom.done

[Service]
Type=simple
Environment=HTTP_PROXY=http://one.proxy.att.com:8080 HTTPS_PROXY=http://one.proxy.att.com:8080 NO_PROXY=127.0.0.1,localhost,135.16.101.87,135.16.101.86,135.16.101.85,135.16.101.84,135.16.101.83,135.16.101.82,135.16.101.81,135.16.101.80,kubernetes
ExecStartPre=/bin/echo 4 >/sys/class/net/ens3f0/device/sriov_numvfs
ExecStart=/var/tmp/prom_init.sh /etc/prom_init.yaml

[Install]
WantedBy=multi-user.target
"""
    prom_init = \
"""!/bin/bash
echo $HTTP_PROXY
echo $NO_PROXY
cat $1
"""