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
            resp.boy = BootdataResource.prom_init
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

                resp.body = "---\n" + "---\n".join(part_list) + "\n..."
                return

    systemd_definition = \
r"""[Unit]
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
r"""#!/usr/bin/env bash

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root." 1>&2
   exit 1
fi


set -ex

#Promenade Variables
DOCKER_PACKAGE="docker.io"
DOCKER_VERSION=1.12.6-0ubuntu1~16.04.1

#Proxy Variables
DOCKER_HTTP_PROXY=${DOCKER_HTTP_PROXY:-${HTTP_PROXY:-${http_proxy}}}
DOCKER_HTTPS_PROXY=${DOCKER_HTTPS_PROXY:-${HTTPS_PROXY:-${https_proxy}}}
DOCKER_NO_PROXY=${DOCKER_NO_PROXY:-${NO_PROXY:-${no_proxy}}}


mkdir -p /etc/docker
cat <<EOS > /etc/docker/daemon.json
{
  "live-restore": true,
  "storage-driver": "overlay2"
}
EOS

#Configuration for Docker Behind a Proxy
mkdir -p /etc/systemd/system/docker.service.d

#Set HTTPS Proxy Variable
cat <<EOF > /etc/systemd/system/docker.service.d/http-proxy.conf
[Service]
Environment="HTTP_PROXY=${DOCKER_HTTP_PROXY}"
EOF

#Set HTTPS Proxy Variable
cat <<EOF > /etc/systemd/system/docker.service.d/https-proxy.conf
[Service]
Environment="HTTPS_PROXY=${DOCKER_HTTPS_PROXY}"
EOF

#Set No Proxy Variable
cat <<EOF > /etc/systemd/system/docker.service.d/no-proxy.conf
[Service]
Environment="NO_PROXY=${DOCKER_NO_PROXY}"
EOF

#Reload systemd and docker if present
systemctl daemon-reload
systemctl restart docker || true

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
    $DOCKER_PACKAGE=$DOCKER_VERSION \


if [ -f "${PROMENADE_LOAD_IMAGE}" ]; then
  echo === Loading updated promenade image ===
  docker load -i "${{PROMENADE_LOAD_IMAGE}}"
fi

docker pull quay.io/attcomdev/promenade:experimental
docker run -t --rm \
    -v /:/target \
    quay.io/attcomdev/promenade:experimental \
    promenade \
        -v \
        join \
            --hostname $(hostname) \
            --config-path /target$(realpath $1)
touch /var/lib/prom.done
"""