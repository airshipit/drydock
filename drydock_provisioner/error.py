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


class IngesterError(DesignError):
    pass


class InvalidDesignReference(DesignError):
    pass


class StateError(Exception):
    pass


class TaskNotFoundError(StateError):
    pass


class OrchestratorError(Exception):
    pass


class MaxRetriesReached(OrchestratorError):
    pass


class CollectSubaskTimeout(OrchestratorError):
    pass


class TransientOrchestratorError(OrchestratorError):
    pass


class PersistentOrchestratorError(OrchestratorError):
    pass


class BootactionError(Exception):
    pass


class UnknownPipelineSegment(BootactionError):
    pass


class PipelineFailure(BootactionError):
    pass


class InvalidAssetLocation(BootactionError):
    pass


class BuildDataError(Exception):
    pass


class DriverError(Exception):
    pass


class TransientDriverError(DriverError):
    pass


class PersistentDriverError(DriverError):
    pass


class NotEnoughStorage(DriverError):
    pass


class InvalidSizeFormat(DriverError):
    pass


class ApiError(Exception):
    def __init__(self, msg, code=500):
        super().__init__(msg)
        self.message = msg
        self.status_code = code

    def to_json(self):
        err_dict = {'error': self.message, 'type': self.__class__.__name__}
        return json.dumps(err_dict)


class InvalidFormat(ApiError):
    def __init__(self, msg, code=400):
        super(InvalidFormat, self).__init__(msg, code=code)


class ClientError(ApiError):
    def __init__(self, msg, code=500):
        super().__init__(msg)


class ClientUnauthorizedError(ClientError):
    def __init__(self, msg):
        super().__init__(msg, code=401)


class ClientForbiddenError(ClientError):
    def __init__(self, msg):
        super().__init__(msg, code=403)
