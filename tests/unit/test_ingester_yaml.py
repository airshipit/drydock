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
"""Test that YAML ingestion works."""

from drydock_provisioner.ingester.plugins.yaml import YamlIngester

class TestClass(object):
    def test_ingest_singledoc(self, input_files):
        input_file = input_files.join("singledoc.yaml")

        ingester = YamlIngester()

        f = open(str(input_file), 'rb')
        yaml_string = f.read()

        status, models = ingester.ingest_data(content=yaml_string)

        assert status.status == 'success'
        assert len(models) == 1

    def test_ingest_multidoc(self, input_files):
        input_file = input_files.join("multidoc.yaml")

        ingester = YamlIngester()

        f = open(str(input_file), 'rb')
        yaml_string = f.read()

        status, models = ingester.ingest_data(content=yaml_string)

        assert status.status == 'success'
        assert len(models) == 3
