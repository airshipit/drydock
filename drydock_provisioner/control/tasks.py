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

from drydock_provisioner import policy
from drydock_provisioner import error as errors

import drydock_provisioner.objects.task as obj_task
from .base import StatefulResource

class TasksResource(StatefulResource):

    def __init__(self, orchestrator=None, **kwargs):
        super(TasksResource, self).__init__(**kwargs)
        self.orchestrator = orchestrator

    @policy.ApiEnforcer('physical_provisioner:read_task')
    def on_get(self, req, resp):
        try:
            task_id_list = [str(x.get_id()) for x in self.state_manager.tasks]
            resp.body = json.dumps(task_id_list)
            resp.status = falcon.HTTP_200
        except Exception as ex:
            self.error(req.context, "Unknown error: %s\n%s" % (str(ex), traceback.format_exc()))
            self.return_error(resp, falcon.HTTP_500, message="Unknown error", retry=False)

    @policy.ApiEnforcer('physical_provisioner:create_task')
    def on_post(self, req, resp):
        # A map of supported actions to the handlers for tasks for those actions
        supported_actions = {
               'validate_design':   TasksResource.task_validate_design,
               'verify_site':       TasksResource.task_verify_site,
               'prepare_site':      TasksResource.task_prepare_site,
               'verify_node':       TasksResource.task_verify_node,
               'prepare_node':      TasksResource.task_prepare_node,
               'deploy_node':       TasksResource.task_deploy_node,
               'destroy_node':      TasksResource.task_destroy_node,
            }

        try:
            ctx = req.context
            json_data = self.req_json(req)

            action = json_data.get('action', None)
            if action not in supported_actions:
                self.error(req,context, "Unsupported action %s" % action)
                self.return_error(resp, falcon.HTTP_400, message="Unsupported action %s" % action, retry=False)
            else:
                supported_actions.get(action)(self, req, resp)

        except Exception as ex:
            self.error(req.context, "Unknown error: %s\n%s" % (str(ex), traceback.format_exc()))
            self.return_error(resp, falcon.HTTP_500, message="Unknown error", retry=False)

    @policy.ApiEnforcer('physical_provisioner:validate_design')
    def task_validate_design(self, req, resp):
        json_data = self.req_json(req)
        action = json_data.get('action', None)

        if action != 'validate_design':
            self.error(req.context, "Task body ended up in wrong handler: action %s in task_validate_design" % action)
            self.return_error(resp, falcon.HTTP_500, message="Error - misrouted request", retry=False)

        try:
            task = self.create_task(json_data)
            resp.body = json.dumps(task.to_dict())
            resp.append_header('Location', "/api/v1.0/tasks/%s" % str(task.task_id))
            resp.status = falcon.HTTP_201
        except errors.InvalidFormat as ex:
            self.error(req.context, ex.msg)
            self.return_error(resp, falcon.HTTP_400, message=ex.msg, retry=False)

    @policy.ApiEnforcer('physical_provisioner:verify_site')
    def task_verify_site(self, req, resp):
        json_data = self.req_json(req)
        action = json_data.get('action', None)

        if action != 'verify_site':
            self.error(req.context, "Task body ended up in wrong handler: action %s in task_verify_site" % action)
            self.return_error(resp, falcon.HTTP_500, message="Error - misrouted request", retry=False)

        try:
            task = self.create_task(json_data)
            resp.body = json.dumps(task.to_dict())
            resp.append_header('Location', "/api/v1.0/tasks/%s" % str(task.task_id))
            resp.status = falcon.HTTP_201
        except errors.InvalidFormat as ex:
            self.error(req.context, ex.msg)
            self.return_error(resp, falcon.HTTP_400, message=ex.msg, retry=False)

    @policy.ApiEnforcer('physical_provisioner:prepare_site')
    def task_prepare_site(self, req, resp):
        json_data = self.req_json(req)
        action = json_data.get('action', None)

        if action != 'prepare_site':
            self.error(req.context, "Task body ended up in wrong handler: action %s in task_prepare_site" % action)
            self.return_error(resp, falcon.HTTP_500, message="Error - misrouted request", retry=False)

        try:
            task = self.create_task(json_data)
            resp.body = json.dumps(task.to_dict())
            resp.append_header('Location', "/api/v1.0/tasks/%s" % str(task.task_id))
            resp.status = falcon.HTTP_201
        except errors.InvalidFormat as ex:
            self.error(req.context, ex.msg)
            self.return_error(resp, falcon.HTTP_400, message=ex.msg, retry=False)

    @policy.ApiEnforcer('physical_provisioner:verify_node')
    def task_verify_node(self, req, resp):
        json_data = self.req_json(req)
        action = json_data.get('action', None)

        if action != 'verify_node':
            self.error(req.context, "Task body ended up in wrong handler: action %s in task_verify_node" % action)
            self.return_error(resp, falcon.HTTP_500, message="Error - misrouted request", retry=False)

        try:
            task = self.create_task(json_data)
            resp.body = json.dumps(task.to_dict())
            resp.append_header('Location', "/api/v1.0/tasks/%s" % str(task.task_id))
            resp.status = falcon.HTTP_201
        except errors.InvalidFormat as ex:
            self.error(req.context, ex.msg)
            self.return_error(resp, falcon.HTTP_400, message=ex.msg, retry=False)

    @policy.ApiEnforcer('physical_provisioner:prepare_node')
    def task_prepare_node(self, req, resp):
        json_data = self.req_json(req)
        action = json_data.get('action', None)

        if action != 'prepare_node':
            self.error(req.context, "Task body ended up in wrong handler: action %s in task_prepare_node" % action)
            self.return_error(resp, falcon.HTTP_500, message="Error - misrouted request", retry=False)

        try:
            task = self.create_task(json_data)
            resp.body = json.dumps(task.to_dict())
            resp.append_header('Location', "/api/v1.0/tasks/%s" % str(task.task_id))
            resp.status = falcon.HTTP_201
        except errors.InvalidFormat as ex:
            self.error(req.context, ex.msg)
            self.return_error(resp, falcon.HTTP_400, message=ex.msg, retry=False)

    @policy.ApiEnforcer('physical_provisioner:deploy_node')
    def task_deploy_node(self, req, resp):
        json_data = self.req_json(req)
        action = json_data.get('action', None)

        if action != 'deploy_node':
            self.error(req.context, "Task body ended up in wrong handler: action %s in task_deploy_node" % action)
            self.return_error(resp, falcon.HTTP_500, message="Error - misrouted request", retry=False)

        try:
            task = self.create_task(json_data)
            resp.body = json.dumps(task.to_dict())
            resp.append_header('Location', "/api/v1.0/tasks/%s" % str(task.task_id))
            resp.status = falcon.HTTP_201
        except errors.InvalidFormat as ex:
            self.error(req.context, ex.msg)
            self.return_error(resp, falcon.HTTP_400, message=ex.msg, retry=False)

    @policy.ApiEnforcer('physical_provisioner:destroy_node')
    def task_destroy_node(self, req, resp):
        json_data = self.req_json(req)
        action = json_data.get('action', None)

        if action != 'destroy_node':
            self.error(req.context, "Task body ended up in wrong handler: action %s in task_destroy_node" % action)
            self.return_error(resp, falcon.HTTP_500, message="Error - misrouted request", retry=False)

        try:
            task = self.create_task(json_data)
            resp.body = json.dumps(task.to_dict())
            resp.append_header('Location', "/api/v1.0/tasks/%s" % str(task.task_id))
            resp.status = falcon.HTTP_201
        except errors.InvalidFormat as ex:
            self.error(req.context, ex.msg)
            self.return_error(resp, falcon.HTTP_400, message=ex.msg, retry=False)

    def create_task(self, task_body):
        """
        Given the parsed body of a create task request, create the task
        and start it in a thread

        :param dict task_body: Dict representing the JSON body of a create task request
           action - The action the task will execute
           design_id - The design context the task will execute in
           node_filter - A filter on which nodes will be affected by the task. The result is
                         an intersection of
           applying all filters
             node_names - A list of node hostnames
             rack_names - A list of rack names that contain the nodes
             node_tags - A list of tags applied to the nodes

        :return: The Task object created
        """
        design_id = task_body.get('design_id', None)
        node_filter = task_body.get('node_filter', None)
        action = task_body.get('action', None)

        if design_id is None or action is None:
            raise errors.InvalidFormat('Task creation requires fields design_id, action')

        task = self.orchestrator.create_task(obj_task.OrchestratorTask, design_id=design_id,
                                               action=action, node_filter=node_filter)

        task_thread = threading.Thread(target=self.orchestrator.execute_task, args=[task.get_id()])
        task_thread.start()

        return task

class TaskResource(StatefulResource):

    def __init__(self, orchestrator=None, **kwargs):
        super(TaskResource, self).__init__(**kwargs)
        self.authorized_roles = ['user']
        self.orchestrator = orchestrator

    def on_get(self, req, resp, task_id):
        ctx = req.context
        policy_action = 'physical_provisioner:read_task'

        try:
            if not self.check_policy(policy_action, ctx):
                self.access_denied(req, resp, policy_action)
                return

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
