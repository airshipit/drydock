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

class Validators:
    def __init__(self, name, code):
        self.name = name
        self.code = code

    def report_results(self, results):
        # https://github.com/att-comdev/ucp-integration/blob/master/docs/source/api-conventions.rst#output-structure
        message_list = []
        for result in results:
            rd = result.to_dict()
            if isinstance(rd, dict) and rd['error']:
                item = {
                    "message": rd['message'],
                    "error": True,
                    "name": self.name,
                    "documents": [],
                    "level": "Error",
                    "diagnostic": "Context Type = %s, Context = %s" % (rd['context_type'], rd['context']),
                    "kind": "ValidationMessage"
                }
                message_list.append(item)
        return results, message_list

    def execute(site_design, orchestrator=None):
        pass
