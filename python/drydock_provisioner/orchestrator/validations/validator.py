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
"""Business Logic Validation"""

import drydock_provisioner.objects.fields as hd_fields

from drydock_provisioner.objects.validation import Validation

from drydock_provisioner.orchestrator.validations.boot_storage_rational import BootStorageRational
from drydock_provisioner.orchestrator.validations.hugepages_validity import HugepagesValidity
from drydock_provisioner.orchestrator.validations.ip_locality_check import IpLocalityCheck
from drydock_provisioner.orchestrator.validations.mtu_rational import MtuRational
from drydock_provisioner.orchestrator.validations.network_trunking_rational import NetworkTrunkingRational
from drydock_provisioner.orchestrator.validations.no_duplicate_ips_check import NoDuplicateIpsCheck
from drydock_provisioner.orchestrator.validations.platform_selection import PlatformSelection
from drydock_provisioner.orchestrator.validations.rational_network_bond import RationalNetworkBond
from drydock_provisioner.orchestrator.validations.storage_partititioning import StoragePartitioning
from drydock_provisioner.orchestrator.validations.storage_sizing import StorageSizing
from drydock_provisioner.orchestrator.validations.unique_network_check import UniqueNetworkCheck
from drydock_provisioner.orchestrator.validations.hostname_validity import HostnameValidity
from drydock_provisioner.orchestrator.validations.oob_valid_ipmi import IpmiValidity
from drydock_provisioner.orchestrator.validations.oob_valid_libvirt import LibvirtValidity
from drydock_provisioner.orchestrator.validations.bootaction_validity import BootactionDefined
from drydock_provisioner.orchestrator.validations.bootaction_validity import BootactionPackageListValid


class Validator():
    def __init__(self, orchestrator):
        """Create a validator with a reference to the orchestrator.

        :param orchestrator: instance of Orchestrator
        """
        self.orchestrator = orchestrator

    def validate_design(self,
                        site_design,
                        result_status=None,
                        include_output=False):
        """Validate the design in site_design passes all validation rules.

        Apply all validation rules to the design in site_design. If result_status is
        defined, update it with validation messages. Otherwise a new status instance
        will be created and returned.

        :param site_design: instance of objects.SiteDesign
        :param result_status: instance of objects.TaskStatus
        """
        if result_status is None:
            result_status = Validation()

        validation_error = False
        for rule in rule_set:
            message_list = rule.execute(
                site_design=site_design, orchestrator=self.orchestrator)
            result_status.message_list.extend(message_list)
            error_msg = [m for m in message_list if m.error]
            result_status.error_count = result_status.error_count + len(
                error_msg)
            if len(error_msg) > 0:
                validation_error = True

        if validation_error:
            result_status.set_status(hd_fields.ValidationResult.Failure)
            result_status.message = "Site design failed validation."
            result_status.reason = "See detail messages."
        else:
            result_status.set_status(hd_fields.ValidationResult.Success)
            result_status.message = "Site design passed validation"

        return result_status


rule_set = [
    BootStorageRational(),
    HugepagesValidity(),
    IpLocalityCheck(),
    MtuRational(),
    NetworkTrunkingRational(),
    NoDuplicateIpsCheck(),
    PlatformSelection(),
    RationalNetworkBond(),
    StoragePartitioning(),
    StorageSizing(),
    UniqueNetworkCheck(),
    HostnameValidity(),
    IpmiValidity(),
    LibvirtValidity(),
    BootactionDefined(),
    BootactionPackageListValid(),
]
