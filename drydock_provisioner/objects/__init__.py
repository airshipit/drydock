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
#
# Models for drydock_provisioner
#
import logging

from copy import deepcopy


def register_all():
    # NOTE(sh8121att) - Import all versioned objects so
    # they are available via RPC. Any new object definitions
    # need to be added here.
    __import__('drydock_provisioner.objects.network')
    __import__('drydock_provisioner.objects.node')
    __import__('drydock_provisioner.objects.hostprofile')
    __import__('drydock_provisioner.objects.hwprofile')
    __import__('drydock_provisioner.objects.site')
    __import__('drydock_provisioner.objects.promenade')

# Utility class for calculating inheritance

class Utils(object):

    """
    apply_field_inheritance - apply inheritance rules to a single field value

    param child_field - value of the child field, or the field receiving
                        the inheritance
    param parent_field - value of the parent field, or the field supplying
                        the inheritance

    return the correct value for child_field based on the inheritance algorithm

    Inheritance algorithm

    1. If child_field is not None, '!' for string vals or -1 for numeric
       vals retain the value
    of child_field

    2. If child_field is '!' return None to unset the field value

    3. If child_field is -1 return None to unset the field value

    4. If child_field is None return parent_field
    """

    @staticmethod
    def apply_field_inheritance(child_field, parent_field):

        if child_field is not None:
            if child_field != '!' and child_field != -1:
                return child_field
            else:
                return None
        else:
            return parent_field

    """
    merge_lists - apply inheritance rules to a list of simple values

    param child_list - list of values from the child
    param parent_list - list of values from the parent

    return a merged list with child values taking prority

    1. All members in the child list not starting with '!'

    2. If a member in the parent list has a corresponding member in the
    chid list prefixed with '!' it is removed

    3. All remaining members of the parent list
    """
    @staticmethod
    def merge_lists(child_list, parent_list):

        effective_list = []

        try:
            # Probably should handle non-string values
            effective_list.extend(
                filter(lambda x: not x.startswith("!"), child_list))

            effective_list.extend(
                filter(lambda x: ("!" + x) not in child_list,
                       filter(lambda x: x not in effective_list, parent_list)))
        except TypeError:
            raise TypeError("Error iterating list argument")

        return effective_list

    """
    merge_dicts - apply inheritance rules to a dict

    param child_dict - dict of k:v from child
    param parent_dict - dict of k:v from the parent

    return a merged dict with child values taking prority

    1. All members in the child dict with a key not starting with '!'

    2. If a member in the parent dict has a corresponding member in the
    chid dict where the key is prefixed with '!' it is removed

    3. All remaining members of the parent dict
    """
    @staticmethod
    def merge_dicts(child_dict, parent_dict):

        effective_dict = {}

        try:
            # Probably should handle non-string keys
            use_keys = filter(lambda x: ("!" + x) not in child_dict.keys(),
                              parent_dict)

            for k in use_keys:
                effective_dict[k] = deepcopy(parent_dict[k])

            use_keys = filter(lambda x: not x.startswith("!"), child_dict)

            for k in use_keys:
                effective_dict[k] = deepcopy(child_dict[k])
        except TypeError:
            raise TypeError("Error iterating dict argument")
            
        return effective_dict
