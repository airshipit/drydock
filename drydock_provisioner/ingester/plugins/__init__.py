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
# Plugins to parse incoming topology and translate it to helm-drydock's
# model representation

import logging

class IngesterPlugin(object):

    def __init__(self):
        self.log = logging.Logger('ingester')
        return

    def get_data(self):
        return "ingester_skeleton"

    def ingest_data(self, **kwargs):
        return {}
