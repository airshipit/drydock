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
FROM python:3.5

ENV DEBIAN_FRONTEND noninteractive
ENV container docker
ENV PORT 9000
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

# Copy direct dependency requirements only to build a dependency layer
COPY ./requirements-lock.txt /tmp/drydock/
RUN pip3 install \
    --no-cache-dir \
    -r /tmp/drydock/requirements-lock.txt

COPY . /tmp/drydock

WORKDIR /tmp/drydock
RUN python3 setup.py install

EXPOSE $PORT

ENTRYPOINT ["./entrypoint.sh"]

CMD ["server"]
