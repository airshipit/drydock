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
import re

from drydock_provisioner.orchestrator.validations.validators import Validators


class HostnameValidity(Validators):
    def __init__(self):
        super().__init__('Hostname Validity', 'DD3003')

    def run_validation(self, site_design, orchestrator=None):
        # Check FQDN length is <= 255 characters per RFC 1035

        node_list = site_design.baremetal_nodes or []
        invalid_nodes = [
            n for n in node_list if len(n.get_fqdn(site_design)) > 255
        ]

        for n in invalid_nodes:
            msg = "FQDN %s is invalid, greater than 255 characters." % n.get_fqdn(
                site_design)
            self.report_error(
                msg, [n.doc_ref],
                "RFC 1035 requires full DNS names to be < 256 characters.")

        # Check each label in the domain name is <= 63 characters per RFC 1035
        # and only contains A-Z,a-z,0-9,-

        valid_label = re.compile('[a-z0-9-]{1,63}', flags=re.I)

        for n in node_list:
            domain_labels = n.get_fqdn(site_design).split('.')
            for l in domain_labels:
                if not valid_label.fullmatch(l):
                    msg = "FQDN %s is invalid - label '%s' is invalid." % (
                        n.get_fqdn(site_design), l)
                    self.report_error(
                        msg, [n.doc_ref],
                        "RFC 1035 requires each label in a DNS name to be <= 63 characters and contain "
                        "only A-Z, a-z, 0-9, and hyphens.")
