# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
            task_list = [x.to_dict() for x in task_model_list]
            resp.body = json.dumps(task_list)
            resp.status = falcon.HTTP_200
        except Exception as ex:
            self.error(
                req.context,
                "Unknown error: %s\n%s" % (str(ex), traceback.format_exc()))
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
            'relabel_nodes': TasksResource.task_relabel_nodes,
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
            self.error(
                req.context,
                "Unknown error: %s\n%s" % (str(ex), traceback.format_exc()))
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

    @policy.ApiEnforcer('physical_provisioner:relabel_nodes')
    def task_relabel_nodes(self, req, resp, json_data):
        """Create async task for relabel nodes."""
        action = json_data.get('action', None)

        if action != 'relabel_nodes':
            self.error(
                req.context,
                "Task body ended up in wrong handler: action %s in task_relabel_nodes"
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
            builddata = req.get_param_as_bool('builddata')
            subtask_errors = req.get_param_as_bool('subtaskerrors')
            try:
                layers = int(req.params.get('layers', '0'))
            except Exception as ex:
                layers = 0

            first_task = self.get_task(req, resp, task_id, builddata)

            if first_task is None:
                self.info(req.context, "Task %s does not exist" % task_id)
                self.return_error(
                    resp,
                    falcon.HTTP_404,
                    message="Task %s does not exist" % task_id,
                    retry=False)
            else:
                # If layers is passed in then it returns a dict of tasks instead of the task dict.
                if layers:
                    resp_data, errors = self.handle_layers(
                        req, resp, task_id, builddata, subtask_errors, layers,
                        first_task)
                    # Includes subtask_errors if the query param 'subtaskerrors' is passed in as true.
                    if (subtask_errors):
                        resp_data['subtask_errors'] = errors
                else:
                    resp_data = first_task
                    # Includes subtask_errors if the query param 'subtaskerrors' is passed in as true.
                    if (subtask_errors):
                        _, errors = self.handle_layers(req, resp, task_id,
                                                       False, subtask_errors,
                                                       1, first_task)
                        resp_data['subtask_errors'] = errors

                resp.body = json.dumps(resp_data)
                resp.status = falcon.HTTP_200
        except Exception as ex:
            self.error(req.context, "Unknown error: %s" % (str(ex)))
            self.return_error(
                resp, falcon.HTTP_500, message="Unknown error", retry=False)

    def get_task(self, req, resp, task_id, builddata):
        try:
            task = self.state_manager.get_task(uuid.UUID(task_id))
            if task is None:
                return None

            task_dict = task.to_dict()

            if builddata:
                task_bd = self.state_manager.get_build_data(
                    task_id=task.get_id())
                task_dict['build_data'] = [bd.to_dict() for bd in task_bd]

            return task_dict
        except Exception as ex:
            self.error(req.context, "Unknown error: %s" % (str(ex)))
            self.return_error(
                resp, falcon.HTTP_500, message="Unknown error", retry=False)

    def handle_layers(self, req, resp, task_id, builddata, subtask_errors,
                      layers, first_task):
        resp_data = {}
        errors = {}
        resp_data['init_task_id'] = task_id
        resp_data[first_task['task_id']] = first_task
        queued_ids = first_task['subtask_id_list']
        # first_task is layer 1
        current_layer = 1
        # The while loop handles each layer.
        while queued_ids and (current_layer < layers or layers == -1
                              or subtask_errors):
            # Copies the current list (a layer) then clears the queue for the next layer.
            processing_ids = list(queued_ids)
            queued_ids = []
            # The for loop handles each task in a layer.
            for id in processing_ids:
                task = self.get_task(req, resp, id, builddata)
                # Only adds the task if within the layers range.
                if current_layer < layers or layers == -1:
                    resp_data[id] = task
                if task:
                    queued_ids.extend(task.get('subtask_id_list', []))
                    if task.get('result', {}).get('details', {}).get(
                            'errorCount', 0) > 0 and subtask_errors:
                        result = task.get('result', {})
                        result['task_id'] = id
                        errors[id] = task.get('result', {})
            # Finished this layer, incrementing for the next while loop.
            current_layer = current_layer + 1
        return resp_data, errors


class TaskBuilddataResource(StatefulResource):
    """Handler resource for /tasks/<id>/builddata singleton endpoint."""

    @policy.ApiEnforcer('physical_provisioner:read_build_data')
    def on_get(self, req, resp, task_id):
        try:
            bd_list = self.state_manager.get_build_data(
                task_id=uuid.UUID(task_id))
            if not bd_list:
                resp.status = falcon.HTTP_404
                return
            resp.body = json.dumps([bd.to_dict() for bd in bd_list])
        except Exception as e:
            self.error(req.context, "Unknown error: %s" % (str(e)))
            resp.body = "Unexpected error."
            resp.status = falcon.HTTP_500
            return
        resp.status = falcon.HTTP_200
