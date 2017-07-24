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
import json
import threading
import traceback

import drydock_provisioner.objects.task as obj_task
from .base import StatefulResource

class TasksResource(StatefulResource):

    def __init__(self, orchestrator=None, **kwargs):
        super(TasksResource, self).__init__(**kwargs)
        self.authorized_roles = ['user']
        self.orchestrator = orchestrator

    def on_get(self, req, resp):
        task_id_list = [str(x.get_id()) for x in self.state_manager.tasks]
        resp.body = json.dumps(task_id_list)

    def on_post(self, req, resp):
        try:
            json_data = self.req_json(req)
            
            design_id = json_data.get('design_id', None)
            action = json_data.get('action', None)
            node_filter = json_data.get('node_filter', None)

            if design_id is None or action is None:
                self.info(req.context, "Task creation requires fields design_id, action")
                self.return_error(resp, falcon.HTTP_400, message="Task creation requires fields design_id, action", retry=False)
                return

            task = self.orchestrator.create_task(obj_task.OrchestratorTask, design_id=design_id,
                                                    action=action, node_filter=node_filter)

            task_thread = threading.Thread(target=self.orchestrator.execute_task, args=[task.get_id()])
            task_thread.start()

            resp.body = json.dumps(task.to_dict())
            resp.status = falcon.HTTP_201
        except Exception as ex:
            self.error(req.context, "Unknown error: %s\n%s" % (str(ex), traceback.format_exc()))
            self.return_error(resp, falcon.HTTP_500, message="Unknown error", retry=False)


class TaskResource(StatefulResource):

    def __init__(self, orchestrator=None, **kwargs):
        super(TaskResource, self).__init__(**kwargs)
        self.authorized_roles = ['user']
        self.orchestrator = orchestrator

    def on_get(self, req, resp, task_id):
        try:
            task = self.state_manager.get_task(task_id)

            if task is None:
                self.info(req.context, "Task %s does not exist" % task_id )
                self.return_error(resp, falcon.HTTP_404, message="Task %s does not exist" % task_id, retry=False)
                return

            resp.body = json.dumps(task.to_dict())
            resp.status = falcon.HTTP_200
        except Exception as ex:
            self.error(req.context, "Unknown error: %s" % (str(ex)))
            self.return_error(resp, falcon.HTTP_500, message="Unknown error", retry=False)
