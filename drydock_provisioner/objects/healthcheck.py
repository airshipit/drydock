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
"""Models for representing health check status."""

class HealthCheck(object):
    """Specialized status for health check status."""

    def __init__(self):
        self.error_count = 0
        self.code = 200
        self.message = ''
        self.status = 'Success'
        self.message_list = []

    def add_detail_msg(self, msg=None):
        """Add a detailed health check message.

        :param msg: instance of HealthCheckMessage
        """
        self.message_list.append(msg)

        if msg.error or msg.level == "Error":
            self.error_count = self.error_count + 1
            self.code = 503
            self.message = 'DryDock failed to respond'
            self.status = 'Failure'

    def to_dict(self):
        return {
            'kind': 'Status',
            'apiVersion': 'v1.0',
            'metadata': {},
            'status': self.status,
            'message': self.message,
            'reason': 'HealthCheck',
            'details': {
                'errorCount': self.error_count,
                'messageList': [x.to_dict() for x in self.message_list],
            },
            'code': self.code
        }

    def is_healthy(self):
        if self.error_count == 0:
            return True
        return False


class HealthCheckMessage(object):
    """Message describing details of a health check."""

    def __init__(self, msg, error=False):
        self.message = msg
        self.error = error

    def to_dict(self):
        """Convert to a dictionary in prep for JSON/YAML serialization."""
        _dict = {
            'message': self.message,
            'error': self.error,
            'kind': 'SimpleMessage',
        }
        return _dict
