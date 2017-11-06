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
from drydock_provisioner.objects.task import TaskStatusMessage


class Validator():
    def validate_design(self, site_design, result_status=None):
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
        for rule in rule_set:
            output = rule(site_design)
            result_status.message_list.extend(output)
            error_msg = [m for m in output if m.error]
            result_status.error_count = result_status.error_count + len(
                error_msg)
            if len(error_msg) > 0:
                validation_error = True

        if validation_error:
            result_status.set_status(hd_fields.ValidationResult.Failure)
        else:
            result_status.set_status(hd_fields.ValidationResult.Success)

        return result_status

    # TODO: (sh8121att) actually implement validation logic
    @classmethod
    def no_duplicate_IPs_check(cls, site_design):
        message_list = []
        message_list.append(TaskStatusMessage(msg='Unique Ip', error=False, ctx_type='NA', ctx='NA'))

        return message_list

    # TODO: (sh8121att) actually implement validation logic
    @classmethod
    def no_outside_IPs_check(cls, site_design):
        message_list = []
        message_list.append(TaskStatusMessage(msg='No outside Ip', error=False, ctx_type='NA', ctx='NA'))

        return message_list


rule_set = [Validator.no_duplicate_IPs_check, Validator.no_outside_IPs_check]
