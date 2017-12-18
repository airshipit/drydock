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
"""Models for representing build data."""
import uuid

from datetime import datetime

from drydock_provisioner import objects

import drydock_provisioner.error as errors


class BuildData(object):
    """Build data

    :param node_name: The name of the node the data was collected from.
    :param task_id: The uuid.UUID ID of the task initiating the collection
    :param collected_data: Date/time the data was collected
    :param generator: String description of the source of data (e.g. ``lshw``)
    :param data_format: String MIME-type of ``data_element``
    :param data_element: Data to be saved, will be cast to ``str``
    """

    def __init__(self,
                 node_name=None,
                 task_id=None,
                 collected_date=None,
                 generator=None,
                 data_format=None,
                 data_element=None):
        """Initiator for BuildData."""
        if not all((node_name, task_id, generator, data_format, data_element)):
            raise ValueError("Required field missing.")

        try:
            if isinstance(data_element, bytes):
                data_element = data_element.decode('utf-8')
            elif not isinstance(data_element, str):
                data_element = str(data_element)
        except Exception as ex:
            raise errors.BuildDataError(
                "Error saving build data - data_element type %s could"
                "not be cast to string." % str(type(data_element)))

        self.node_name = node_name
        self.task_id = task_id
        self.collected_date = collected_date or datetime.utcnow()
        self.generator = generator
        self.data_format = data_format
        self.data_element = data_element

    @classmethod
    def obj_name(cls):
        return cls.__name__

    def to_db(self):
        """Convert this instance to a dictionary for use persisting to a db.

        include_id=False can be used for doing an update where the primary key
        of the table shouldn't included in the values set

        :param include_id: Whether to include task_id in the dictionary
        """
        _dict = {
            'node_name':
            self.node_name,
            'task_id':
            self.task_id.bytes,
            'collected_date':
            None if self.collected_date is None else str(self.collected_date),
            'generator':
            self.generator,
            'data_format':
            self.data_format,
            'data_element':
            self.data_element,
        }

        return _dict

    def to_dict(self, verbosity=2):
        """Convert this instance to a dictionary.

        Intended for use in JSON serialization
        ``verbosity`` of 1 omits the data_element

        :param verbosity: integer of how verbose to make the result.
        """
        _dict = {
            'node_name':
            self.node_name,
            'task_id':
            str(self.task_id),
            'collected_date':
            None if self.collected_date is None else str(self.collected_date),
            'generator':
            self.generator,
            'data_format':
            self.data_format,
        }

        if verbosity > 1:
            _dict['data_element'] = self.data_element

        return _dict

    @classmethod
    def from_db(cls, d):
        """Create an instance from a DB-based dictionary.

        :param d: Dictionary of instance data
        """
        d['task_id'] = uuid.UUID(bytes=bytes(d.get('task_id')))

        i = BuildData(**d)

        return i


# Add BuildData to objects scope
setattr(objects, BuildData.obj_name(), BuildData)
