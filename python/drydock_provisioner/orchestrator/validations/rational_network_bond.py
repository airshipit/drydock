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


class RationalNetworkBond(Validators):
    def __init__(self):
        super().__init__('Network Bond Rationality', 'DD1006')

    def run_validation(self, site_design, orchestrator=None):
        """
        This check ensures that each NetworkLink has a rational bonding setup.
        If the bonding mode is set to 'disabled' then it ensures that no other options are specified.
        If the bonding mode it set to '802.3ad' then it ensures that the bonding up delay and the bonding down delay
        are both greater then or equal to the mon rate.
        If the bonding mode is set to active-backup or balanced-rr then it ensures that the bonding hash and the
        bonding peer rate are both NOT defined.
        """
        network_links = site_design.network_links or []

        for network_link in network_links:
            bonding_mode = network_link.bonding_mode

            if bonding_mode == 'disabled':
                # check to make sure nothing else is specified
                if any([
                        getattr(network_link, x) for x in [
                            'bonding_peer_rate', 'bonding_xmit_hash',
                            'bonding_mon_rate', 'bonding_up_delay',
                            'bonding_down_delay'
                        ]
                ]):
                    msg = 'If bonding mode is disabled no other bond option can be specified'
                    self.report_error(
                        msg, [network_link.doc_ref],
                        "Enable a bonding mode or remove the bond options.")

            elif bonding_mode == '802.3ad':
                # check if up_delay and down_delay are >= mon_rate
                mon_rate = network_link.bonding_mon_rate
                if network_link.bonding_up_delay < mon_rate:
                    msg = ('Up delay %d is less than mon rate %d' %
                           (network_link.bonding_up_delay, mon_rate))
                    self.report_error(
                        msg, [network_link.doc_ref],
                        "Link up delay must be equal or greater than the mon_rate"
                    )

                if network_link.bonding_down_delay < mon_rate:
                    msg = ('Down delay %d is less than mon rate %d' %
                           (network_link.bonding_down_delay, mon_rate))
                    self.report_error(
                        msg, [network_link.doc_ref],
                        "Link down delay must be equal or greater than the mon_rate"
                    )

            elif bonding_mode in ['active-backup', 'balanced-rr']:
                # make sure hash and peer_rate are NOT defined
                if network_link.get('bonding_xmit_hash'):
                    msg = ('Hash cannot be defined if bond mode is %s' %
                           (bonding_mode))
                    self.report_error(
                        msg, [network_link.doc_ref],
                        "Hash mode is only applicable to LACP (802.3ad)")

                if network_link.get('bonding_peer_rate'):
                    msg = ('Peer rate cannot be defined if bond mode is %s' %
                           (bonding_mode))
                    self.report_error(
                        msg, [network_link.doc_ref],
                        "Peer rate is only applicable to LACP (802.3ad)")

        return
