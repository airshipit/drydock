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
"""Business Logic Validation"""

from drydock_provisioner import objects
from drydock_provisioner.objects import fields as hd_fields


class Validators:
    def __init__(self, long_name, name):
        self.name = name
        self.long_name = long_name
        self.reset_message_list()

    def report_msg(self, msg, docs, diagnostic, error, level):
        """Add a validation message to the result list.

        :param msg: String - msg, will be prepended with validator long name
        :param docs: List - List of document references related to this validation message
        :param diagnostic: String - Diagnostic information for t/s this error
        :param error: Bool - Whether this message indicates an error
        :param level: String - More detailed of the severity level of this message
        """
        fmt_msg = "%s: %s" % (self.long_name, msg)
        msg_obj = objects.ValidationMessage(
            fmt_msg,
            self.name,
            error=error,
            level=level,
            docs=docs,
            diagnostic=diagnostic)
        self.messages.append(msg_obj)

    def report_error(self, msg, docs, diagnostic):
        self.report_msg(msg, docs, diagnostic, True,
                        hd_fields.MessageLevels.ERROR)

    def report_warn(self, msg, docs, diagnostic):
        self.report_msg(msg, docs, diagnostic, False,
                        hd_fields.MessageLevels.WARN)

    def report_info(self, msg, docs, diagnostic):
        self.report_msg(msg, docs, diagnostic, False,
                        hd_fields.MessageLevels.INFO)

    def error_count(self):
        errors = [x for x in self.messages if x.error]
        return len(errors)

    def reset_message_list(self):
        self.messages = []

    def execute(self, site_design, orchestrator=None):
        self.reset_message_list()
        self.run_validation(site_design, orchestrator=orchestrator)
        if self.error_count() == 0:
            self.report_info("Validation successful.", [], "")

        return self.messages
