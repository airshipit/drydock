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
import falcon

from .designs import DesignsResource, DesignPartsResource
from .tasks import TasksResource
from .base import DrydockRequest
from .middleware import AuthMiddleware, ContextMiddleware, LoggingMiddleware

def start_api(state_manager):
    control_api = falcon.API(request_type=DrydockRequest,
                             middleware=[AuthMiddleware(), ContextMiddleware(), LoggingMiddleware()])

    # API for managing orchestrator tasks
    control_api.add_route('/tasks', TasksResource(state_manager=state_manager))
    control_api.add_route('/tasks/{task_id}', TaskResource(state_manager=state_manager))

    # API for managing site design data
    control_api.add_route('/designs', DesignsResource(state_manager=state_manager))
    control_api.add_route('/designs/{design_id}', DesignResource(state_manager=state_manager))
    control_api.add_route('/designs/{design_id}/parts', DesignsPartsResource(state_manager=state_manager))
    control_api.add_route('/designs/{design_id}/parts/{kind}', DesignsPartsKindsResource(state_manager=state_manager))
    control_api.add_route('/designs/{design_id}/parts/{kind}/{name}', DesignsPartResource(state_manager=state_manager))

    return control_api
