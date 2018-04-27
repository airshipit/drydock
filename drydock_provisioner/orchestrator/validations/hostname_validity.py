# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
from drydock_provisioner.orchestrator.validations.validators import Validators


class HostnameValidity(Validators):
    def __init__(self):
        super().__init__('Hostname Validity', 'DD3003')

    def run_validation(self, site_design, orchestrator=None):
        """Validate that node hostnames do not contain '__' """
        node_list = site_design.baremetal_nodes or []

        invalid_nodes = [n for n in node_list if '__' in n.name]

        for n in invalid_nodes:
            msg = "Hostname %s invalid." % n.name
            self.report_error(
                msg, [n.doc_ref],
                "Hostnames cannot contain '__' (double underscore)")
        return
