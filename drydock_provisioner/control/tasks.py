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
"""Handler resources for task management API."""

import falcon
import json
import traceback
import uuid

from drydock_provisioner import policy
from drydock_provisioner import error as errors
from drydock_provisioner.objects import fields as hd_fields

from .base import StatefulResource


class TasksResource(StatefulResource):
    """Handler resource for /tasks collection endpoint."""

    def __init__(self, orchestrator=None, **kwargs):
        """Object initializer.

        :param orchestrator: instance of orchestrator.Orchestrator
        """
        super().__init__(**kwargs)
        self.orchestrator = orchestrator

    @policy.ApiEnforcer('physical_provisioner:read_task')
    def on_get(self, req, resp):
        """Handler for GET method."""
        try:
            task_model_list = self.state_manager.get_tasks()
            task_list = [str(x.to_dict()) for x in task_model_list]
            resp.body = json.dumps(task_list)
            resp.status = falcon.HTTP_200
        except Exception as ex:
            self.error(req.context, "Unknown error: %s\n%s" %
                       (str(ex), traceback.format_exc()))
            self.return_error(
                resp, falcon.HTTP_500, message="Unknown error", retry=False)

    @policy.ApiEnforcer('physical_provisioner:create_task')
    def on_post(self, req, resp):
        """Handler for POST method."""
        # A map of supported actions to the handlers for tasks for those actions
        supported_actions = {
            'validate_design': TasksResource.task_validate_design,
            'verify_site': TasksResource.task_verify_site,
            'prepare_site': TasksResource.task_prepare_site,
            'verify_nodes': TasksResource.task_verify_nodes,
            'prepare_nodes': TasksResource.task_prepare_nodes,
            'deploy_nodes': TasksResource.task_deploy_nodes,
            'destroy_nodes': TasksResource.task_destroy_nodes,
        }

        try:
            json_data = self.req_json(req)

            action = json_data.get('action', None)
            if supported_actions.get(action, None) is None:
                self.error(req.context, "Unsupported action %s" % action)
                self.return_error(
                    resp,
                    falcon.HTTP_400,
                    message="Unsupported action %s" % action,
                    retry=False)
            else:
                supported_actions.get(action)(self, req, resp, json_data)
        except Exception as ex:
            self.error(req.context, "Unknown error: %s\n%s" %
                       (str(ex), traceback.format_exc()))
            self.return_error(
                resp, falcon.HTTP_500, message="Unknown error", retry=False)

    @policy.ApiEnforcer('physical_provisioner:validate_design')
    def task_validate_design(self, req, resp, json_data):
        """Create async task for validate design."""
        action = json_data.get('action', None)

        if action != 'validate_design':
            self.error(
                req.context,
                "Task body ended up in wrong handler: action %s in task_validate_design"
                % action)
            self.return_error(
                resp, falcon.HTTP_500, message="Error", retry=False)

        try:
            task = self.create_task(json_data, req.context)
            resp.body = json.dumps(task.to_dict())
            resp.append_header('Location',
                               "/api/v1.0/tasks/%s" % str(task.task_id))
            resp.status = falcon.HTTP_201
        except errors.InvalidFormat as ex:
            self.error(req.context, ex.msg)
            self.return_error(
                resp, falcon.HTTP_400, message=ex.msg, retry=False)

    @policy.ApiEnforcer('physical_provisioner:verify_site')
    def task_verify_site(self, req, resp, json_data):
        """Create async task for verify site."""
        action = json_data.get('action', None)

        if action != 'verify_site':
            self.error(
                req.context,
                "Task body ended up in wrong handler: action %s in task_verify_site"
                % action)
            self.return_error(
                resp, falcon.HTTP_500, message="Error", retry=False)

        try:
            task = self.create_task(json_data, req.context)
            resp.body = json.dumps(task.to_dict())
            resp.append_header('Location',
                               "/api/v1.0/tasks/%s" % str(task.task_id))
            resp.status = falcon.HTTP_201
        except errors.InvalidFormat as ex:
            self.error(req.context, ex.msg)
            self.return_error(
                resp, falcon.HTTP_400, message=ex.msg, retry=False)

    @policy.ApiEnforcer('physical_provisioner:prepare_site')
    def task_prepare_site(self, req, resp, json_data):
        """Create async task for prepare site."""
        action = json_data.get('action', None)

        if action != 'prepare_site':
            self.error(
                req.context,
                "Task body ended up in wrong handler: action %s in task_prepare_site"
                % action)
            self.return_error(
                resp, falcon.HTTP_500, message="Error", retry=False)

        try:
            task = self.create_task(json_data, req.context)
            resp.body = json.dumps(task.to_dict())
            resp.append_header('Location',
                               "/api/v1.0/tasks/%s" % str(task.task_id))
            resp.status = falcon.HTTP_201
        except errors.InvalidFormat as ex:
            self.error(req.context, ex.msg)
            self.return_error(
                resp, falcon.HTTP_400, message=ex.msg, retry=False)

    @policy.ApiEnforcer('physical_provisioner:verify_nodes')
    def task_verify_nodes(self, req, resp, json_data):
        """Create async task for verify node."""
        action = json_data.get('action', None)

        if action != 'verify_nodes':
            self.error(
                req.context,
                "Task body ended up in wrong handler: action %s in task_verify_nodes"
                % action)
            self.return_error(
                resp, falcon.HTTP_500, message="Error", retry=False)

        try:
            task = self.create_task(json_data, req.context)
            resp.body = json.dumps(task.to_dict())
            resp.append_header('Location',
                               "/api/v1.0/tasks/%s" % str(task.task_id))
            resp.status = falcon.HTTP_201
        except errors.InvalidFormat as ex:
            self.error(req.context, ex.msg)
            self.return_error(
                resp, falcon.HTTP_400, message=ex.msg, retry=False)

    @policy.ApiEnforcer('physical_provisioner:prepare_nodes')
    def task_prepare_nodes(self, req, resp, json_data):
        """Create async task for prepare node."""
        action = json_data.get('action', None)

        if action != 'prepare_nodes':
            self.error(
                req.context,
                "Task body ended up in wrong handler: action %s in task_prepare_nodes"
                % action)
            self.return_error(
                resp, falcon.HTTP_500, message="Error", retry=False)

        try:
            task = self.create_task(json_data, req.context)
            resp.body = json.dumps(task.to_dict())
            resp.append_header('Location',
                               "/api/v1.0/tasks/%s" % str(task.task_id))
            resp.status = falcon.HTTP_201
        except errors.InvalidFormat as ex:
            self.error(req.context, ex.msg)
            self.return_error(
                resp, falcon.HTTP_400, message=ex.msg, retry=False)

    @policy.ApiEnforcer('physical_provisioner:deploy_nodes')
    def task_deploy_nodes(self, req, resp, json_data):
        """Create async task for deploy node."""
        action = json_data.get('action', None)

        if action != 'deploy_nodes':
            self.error(
                req.context,
                "Task body ended up in wrong handler: action %s in task_deploy_nodes"
                % action)
            self.return_error(
                resp, falcon.HTTP_500, message="Error", retry=False)

        try:
            task = self.create_task(json_data, req.context)
            resp.body = json.dumps(task.to_dict())
            resp.append_header('Location',
                               "/api/v1.0/tasks/%s" % str(task.task_id))
            resp.status = falcon.HTTP_201
        except errors.InvalidFormat as ex:
            self.error(req.context, ex.msg)
            self.return_error(
                resp, falcon.HTTP_400, message=ex.msg, retry=False)

    @policy.ApiEnforcer('physical_provisioner:destroy_nodes')
    def task_destroy_nodes(self, req, resp, json_data):
        """Create async task for destroy node."""
        action = json_data.get('action', None)

        if action != 'destroy_nodes':
            self.error(
                req.context,
                "Task body ended up in wrong handler: action %s in task_destroy_nodes"
                % action)
            self.return_error(
                resp, falcon.HTTP_500, message="Error", retry=False)

        try:
            task = self.create_task(json_data, req.context)
            resp.body = json.dumps(task.to_dict())
            resp.append_header('Location',
                               "/api/v1.0/tasks/%s" % str(task.task_id))
            resp.status = falcon.HTTP_201
        except errors.InvalidFormat as ex:
            self.error(req.context, ex.msg)
            self.return_error(
                resp, falcon.HTTP_400, message=ex.msg, retry=False)

    def create_task(self, task_body, req_context):
        """General task creation.

        Given the parsed ``task_body`` of a create task request, create the task
        and queue it in the database.

        :param dict task_body: Dict representing the JSON body of a create task request
           action - The action the task will execute
           design_ref - A URI reference to the design document set the task should operate on
           node_filter - A filter on which nodes will be affected by the task.
        :return: The Task object created
        """
        design_ref = task_body.get('design_ref', None)
        node_filter = task_body.get('node_filter', None)
        action = task_body.get('action', None)

        if design_ref is None or action is None:
            raise errors.InvalidFormat(
                'Task creation requires fields design_ref, action')

        task = self.orchestrator.create_task(
            design_ref=design_ref,
            action=action,
            node_filter=node_filter,
            context=req_context)

        task.set_status(hd_fields.TaskStatus.Queued)
        task.save()
        return task


class TaskResource(StatefulResource):
    """Handler resource for /tasks/<id> singleton endpoint."""

    def __init__(self, orchestrator=None, **kwargs):
        """Object initializer.

        :param orchestrator: instance of orchestrator.Orchestrator
        """
        super().__init__(**kwargs)
        self.orchestrator = orchestrator

    @policy.ApiEnforcer('physical_provisioner:read_task')
    def on_get(self, req, resp, task_id):
        """Handler for GET method."""
        try:
            task = self.state_manager.get_task(uuid.UUID(task_id))

            if task is None:
                self.info(req.context, "Task %s does not exist" % task_id)
                self.return_error(
                    resp,
                    falcon.HTTP_404,
                    message="Task %s does not exist" % task_id,
                    retry=False)
                return

            resp.body = json.dumps(task.to_dict())
            resp.status = falcon.HTTP_200
        except Exception as ex:
            self.error(req.context, "Unknown error: %s" % (str(ex)))
            self.return_error(
                resp, falcon.HTTP_500, message="Unknown error", retry=False)
