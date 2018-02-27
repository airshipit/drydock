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

from drydock_provisioner.objects.task import TaskStatus

from drydock_provisioner.orchestrator.validations.boot_storage_rational import BootStorageRational
from drydock_provisioner.orchestrator.validations.ip_locality_check import IpLocalityCheck
from drydock_provisioner.orchestrator.validations.mtu_rational import MtuRational
from drydock_provisioner.orchestrator.validations.network_trunking_rational import NetworkTrunkingRational
from drydock_provisioner.orchestrator.validations.no_duplicate_ips_check import NoDuplicateIpsCheck
from drydock_provisioner.orchestrator.validations.platform_selection import PlatformSelection
from drydock_provisioner.orchestrator.validations.rational_network_bond import RationalNetworkBond
from drydock_provisioner.orchestrator.validations.storage_partititioning import StoragePartitioning
from drydock_provisioner.orchestrator.validations.storage_sizing import StorageSizing
from drydock_provisioner.orchestrator.validations.unique_network_check import UniqueNetworkCheck

class Validator():
    def __init__(self, orchestrator):
        """Create a validator with a reference to the orchestrator.

        :param orchestrator: instance of Orchestrator
        """
        self.orchestrator = orchestrator

    def validate_design(self, site_design, result_status=None, include_output=False):
        """Validate the design in site_design passes all validation rules.

        Apply all validation rules to the design in site_design. If result_status is
        defined, update it with validation messages. Otherwise a new status instance
        will be created and returned.

        :param site_design: instance of objects.SiteDesign
        :param result_status: instance of objects.TaskStatus
        """
        if result_status is None:
            result_status = TaskStatus()

        validation_error = False
        message_lists = []
        for rule in rule_set:
            results, message_list = rule.execute(site_design=site_design, orchestrator=self.orchestrator)
            for item in message_list:
                message_lists.append(item)
            result_status.message_list.extend(results)
            error_msg = [m for m in results if m.error]
            result_status.error_count = result_status.error_count + len(
                error_msg)
            if len(error_msg) > 0:
                validation_error = True

        if validation_error:
            result_status.set_status(hd_fields.ValidationResult.Failure)
        else:
            result_status.set_status(hd_fields.ValidationResult.Success)

        if include_output:
            output = {
                "kind": "Status",
                "api_version": "v1.0",
                "metadata": {},
                "status": "Success",
                "message": "Drydock validations succeeded",
                "reason": "Validation",
                "details": {
                    "error_count": 0,
                    "message_list": []
                },
                "code": 200
            }
            if len(message_lists) > 0:
                output['status'] = "Failure"
                output['details']['error_count'] = len(message_lists)
                output['details']['message_list'] = message_lists
                output['code'] = 400
                return output
        return result_status


rule_set = [
    BootStorageRational(),
    IpLocalityCheck(),
    MtuRational(),
    NetworkTrunkingRational(),
    NoDuplicateIpsCheck(),
    PlatformSelection(),
    RationalNetworkBond(),
    StoragePartitioning(),
    StorageSizing(),
    UniqueNetworkCheck(),
]
