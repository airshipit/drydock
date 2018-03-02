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
"""Models for representing asynchronous tasks."""

from datetime import datetime

import oslo_versionedobjects.fields as ovo_fields

from drydock_provisioner import objects

import drydock_provisioner.objects.base as base
import drydock_provisioner.error as errors
import drydock_provisioner.objects.fields as hd_fields

from .task import TaskStatus, TaskStatusMessage


class Validation(TaskStatus):
    """Specialized status for design validation status."""

    def __init__(self):
        super().__init__()

    def add_detail_msg(self, msg=None):
        """Add a detailed validation message.

        :param msg: instance of ValidationMessage
        """
        self.message_list.append(msg)

        if msg.error or msg.level == "Error":
            self.error_count = self.error_count + 1

    def to_dict(self):
        return {
            'kind': 'Status',
            'apiVersion': 'v1.0',
            'metadata': {},
            'message': self.message,
            'reason': self.reason,
            'status': self.status,
            'details': {
                'errorCount': self.error_count,
                'messageList': [x.to_dict() for x in self.message_list],
            }
        }


class ValidationMessage(TaskStatusMessage):
    """Message describing details of a validation."""

    def __init__(self, msg, name, error=False, level=None, docs=None, diagnostic=None):
        self.name = name
        self.message = msg
        self.error = error
        self.level = level
        self.diagnostic = diagnostic
        self.ts = datetime.utcnow()
        self.docs = docs

    def to_dict(self):
        """Convert to a dictionary in prep for JSON/YAML serialization."""
        _dict = {
            'kind': 'ValidationMessage',
            'name': self.name,
            'message': self.message,
            'error': self.error,
            'level': self.level,
            'diagnostic': self.diagnostic,
            'ts': str(self.ts),
            'documents': [x.to_dict() for x in self.docs]
        }
        return _dict


@base.DrydockObjectRegistry.register
class DocumentReference(base.DrydockObject):
    """Keep a reference to the original document that data was loaded from."""

    VERSION = '1.0'

    fields = {
        'doc_type': ovo_fields.StringField(),
        'doc_schema': ovo_fields.StringField(nullable=True),
        'doc_name': ovo_fields.StringField(nullable=True),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if (self.doc_type == hd_fields.DocumentType.Deckhand):
            if not all([self.doc_schema, self.doc_name]):
                raise ValueError("doc_schema and doc_name required for Deckhand sources.")
        else:
            raise errors.UnsupportedDocumentType(
                "Document type %s not supported." % self.doc_type)

    def to_dict(self):
        """Serialize to a dictionary for further serialization."""
        d = dict()
        if self.doc_type == hd_fields.DocumentType.Deckhand:
            d['schema'] = self.doc_schema
            d['name'] = self.doc_name

        return d


# Emulate OVO object registration
setattr(objects, Validation.obj_name(), Validation)
setattr(objects, ValidationMessage.obj_name(), ValidationMessage)
