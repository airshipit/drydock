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


class MtuRational(Validators):
    MIN_MTU_SIZE = 1280
    MAX_MTU_SIZE = 65536

    def __init__(self):
        super().__init__('MTU Rationality', 'DD2003')

    def run_validation(self, site_design, orchestrator=None):
        """
        Ensure that the MTU for each network is equal or less than the MTU defined
        for the parent NetworkLink for that network.

        Ensure that each defined MTU is a rational size, say > 1400 and < 64000
        """
        network_links = site_design.network_links or []
        networks = site_design.networks or []

        parent_mtu_check = {}

        for network_link in network_links:
            mtu = network_link.mtu
            if mtu and (mtu < MtuRational.MIN_MTU_SIZE
                        or mtu > MtuRational.MAX_MTU_SIZE):
                msg = ("MTU must be between %d and %d, value is %d" %
                       (MtuRational.MIN_MTU_SIZE, MtuRational.MAX_MTU_SIZE,
                        mtu))
                self.report_error(
                    msg, [network_link.doc_ref],
                    "Define a valid MTU. Standard is 1500, Jumbo is 9100.")

            # add assigned network to dict with parent mtu
            assigned_network = network_link.native_network
            parent_mtu_check[assigned_network] = mtu

        for network in networks:
            network_mtu = network.mtu

            if network_mtu and (network_mtu < MtuRational.MIN_MTU_SIZE
                                or network_mtu > MtuRational.MAX_MTU_SIZE):
                msg = ("MTU must be between %d and %d, value is %d" %
                       (MtuRational.MIN_MTU_SIZE, MtuRational.MAX_MTU_SIZE,
                        mtu))
                self.report_error(
                    msg, [network.doc_ref],
                    "Define a valid MTU. Standard is 1500, Jumbo is 9100.")

            name = network.name
            parent_mtu = parent_mtu_check.get(name)
            if network_mtu and parent_mtu:
                # check to make sure mtu for network is <= parent network link
                if network_mtu > parent_mtu:
                    msg = 'MTU must be <= the parent Network Link; for Network %s' % (
                        network.name)
                    self.report_error(msg, [
                        network.doc_ref
                    ], "Define a MTU less than or equal to that of the carrying network link."
                                      )

        return
