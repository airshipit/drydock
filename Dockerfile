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
FROM ubuntu:16.04

ENV DEBIAN_FRONTEND noninteractive
ENV container docker

RUN apt -qq update && \
    apt -y install git \
                   netbase \
                   python3-minimal \
                   python3-setuptools \
                   python3-pip \
                   python3-dev \
                   ca-certificates \
                   gcc \
                   g++ \
                   make \
                   libffi-dev \
                   libssl-dev --no-install-recommends

# Copy direct dependency requirements only to build a dependency layer
COPY ./requirements-direct.txt /tmp/drydock/
RUN pip3 install -r /tmp/drydock/requirements-direct.txt

COPY . /tmp/drydock

WORKDIR /tmp/drydock
RUN python3 setup.py install

EXPOSE 9000

ENTRYPOINT ["./entrypoint.sh"]

CMD ["server"]
