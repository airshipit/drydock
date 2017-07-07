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
import json

class DesignError(Exception):
    pass

class StateError(Exception):
    pass

class OrchestratorError(Exception):
    pass

class TransientOrchestratorError(OrchestratorError):
    pass

class PersistentOrchestratorError(OrchestratorError):
    pass

class DriverError(Exception):
    pass

class TransientDriverError(DriverError):
    pass

class PersistentDriverError(DriverError):
    pass

class ApiError(Exception):
    def __init__(self, msg, code=500):
        super().__init__(msg)
        self.message = msg
        self.status_code = code

    def to_json(self):
        err_dict = {'error': msg, 'type': self.__class__.__name__}}
        return json.dumps(err_dict)

class InvalidFormat(ApiError):
    def __init__(self, msg, code=400):
        super(InvalidFormat, self).__init__(msg, code=code) 
