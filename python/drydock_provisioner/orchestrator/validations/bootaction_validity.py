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

from drydock_provisioner import error as errors
from drydock_provisioner.orchestrator.validations.validators import Validators


class BootactionDefined(Validators):
    """Issue warnings if no bootactions are defined for a node."""

    def __init__(self):
        super().__init__('Bootaction Definition', 'DD4001')

    def run_validation(self, site_design, orchestrator=None):
        """Validate each node has at least one bootaction."""
        node_list = site_design.baremetal_nodes or []
        ba_list = site_design.bootactions or []

        nodes_with_ba = [n for ba in ba_list for n in ba.target_nodes]
        nodes_wo_ba = [n for n in node_list if n.name not in nodes_with_ba]

        for n in nodes_wo_ba:
            msg = "Node %s is not in scope for any bootactions." % n.name
            self.report_warn(
                msg, [n.doc_ref],
                "It is expected all nodes have at least one post-deploy action."
            )
        return


class BootactionPackageListValid(Validators):
    """Check that bootactions with pkg_list assets are valid."""

    def __init__(self):
        super().__init__('Bootaction pkg_list Validation', 'DD4002')
        version_fields = '(\d+:)?([a-zA-Z0-9.+~-]+)(-[a-zA-Z0-9.+~]+)'
        self.version_fields = re.compile(version_fields)

    def run_validation(self, site_design, orchestrator=None):
        """Validate that each package list in bootaction assets is valid."""
        ba_list = site_design.bootactions or []

        for ba in ba_list:
            for a in ba.asset_list:
                if a.type == 'pkg_list':
                    if not a.location and not a.package_list:
                        msg = "Bootaction has asset of type 'pkg_list' but no valid package data"
                        self.report_error(
                            msg, [ba.doc_ref],
                            "pkg_list bootaction assets must specify a list of packages."
                        )
                    elif a.package_list:
                        for p, v in a.package_list.items():
                            try:
                                self.validate_package_version(v)
                            except errors.InvalidPackageListFormat as ex:
                                msg = str(ex)
                                self.report_error(
                                    msg, [ba.doc_ref],
                                    "pkg_list version specifications must be in a valid format."
                                )
        return

    def validate_package_version(self, v):
        """Validate that a version specification is valid.

        :param v: a string package specification.
        """
        if not v:
            return

        spec_match = self.version_fields.fullmatch(v)

        if not spec_match:
            raise errors.InvalidPackageListFormat(
                "Version specifier %s is not a valid format." % v)
