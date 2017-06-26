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
FROM drydock_base:0.1

ENV DEBIAN_FRONTEND noninteractive
ENV container docker

ADD drydock.conf /etc/drydock/drydock.conf
ADD . /tmp/drydock

WORKDIR /tmp/drydock

RUN python3 setup.py install

EXPOSE 9000

CMD ["uwsgi","--http",":9000","-w","drydock_provisioner.drydock","--callable","drydock","--enable-threads","-L","--python-autoreload","1","--pyargv","--config-file /etc/drydock/drydock.conf"]
