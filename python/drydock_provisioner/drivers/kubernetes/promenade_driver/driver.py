# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
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
"""Task driver for Promenade"""

import logging
import uuid
import concurrent.futures

from oslo_config import cfg

import drydock_provisioner.error as errors
import drydock_provisioner.objects.fields as hd_fields
import drydock_provisioner.config as config
from drydock_provisioner.drivers.kubernetes.driver import KubernetesDriver
from drydock_provisioner.drivers.kubernetes.promenade_driver.promenade_client \
    import PromenadeClient

from .actions.k8s_node import RelabelNode


class PromenadeDriver(KubernetesDriver):

    driver_name = 'promenadedriver'
    driver_key = 'promenadedriver'
    driver_desc = 'Promenade Kubernetes Driver'

    action_class_map = {
        hd_fields.OrchestratorAction.RelabelNode: RelabelNode,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.logger = logging.getLogger(
            cfg.CONF.logging.kubernetesdriver_logger_name)

    def execute_task(self, task_id):
        # actions that should be threaded for execution
        threaded_actions = [
            hd_fields.OrchestratorAction.RelabelNode,
        ]

        action_timeouts = {
            hd_fields.OrchestratorAction.RelabelNode:
            config.config_mgr.conf.timeouts.relabel_node,
        }

        task = self.state_manager.get_task(task_id)

        if task is None:
            raise errors.DriverError("Invalid task %s" % (task_id))

        if task.action not in self.supported_actions:
            raise errors.DriverError("Driver %s doesn't support task action %s"
                                     % (self.driver_desc, task.action))

        task.set_status(hd_fields.TaskStatus.Running)
        task.save()

        if task.action in threaded_actions:
            if task.retry > 0:
                msg = "Retrying task %s on previous failed entities." % str(
                    task.get_id())
                task.add_status_msg(
                    msg=msg,
                    error=False,
                    ctx=str(task.get_id()),
                    ctx_type='task')
                target_nodes = self.orchestrator.get_target_nodes(
                    task, failures=True)
            else:
                target_nodes = self.orchestrator.get_target_nodes(task)

            with concurrent.futures.ThreadPoolExecutor() as e:
                subtask_futures = dict()
                for n in target_nodes:
                    prom_client = PromenadeClient()
                    nf = self.orchestrator.create_nodefilter_from_nodelist([n])
                    subtask = self.orchestrator.create_task(
                        design_ref=task.design_ref,
                        action=task.action,
                        node_filter=nf,
                        retry=task.retry)
                    task.register_subtask(subtask)

                    action = self.action_class_map.get(task.action, None)(
                        subtask,
                        self.orchestrator,
                        self.state_manager,
                        prom_client=prom_client)
                    subtask_futures[subtask.get_id().bytes] = e.submit(
                        action.start)

                timeout = action_timeouts.get(
                    task.action, config.config_mgr.conf.timeouts.relabel_node)
                finished, running = concurrent.futures.wait(
                    subtask_futures.values(), timeout=(timeout * 60))

            for t, f in subtask_futures.items():
                if not f.done():
                    task.add_status_msg(
                        "Subtask timed out before completing.",
                        error=True,
                        ctx=str(uuid.UUID(bytes=t)),
                        ctx_type='task')
                    task.failure()
                else:
                    if f.exception():
                        msg = ("Subtask %s raised unexpected exception: %s" %
                               (str(uuid.UUID(bytes=t)), str(f.exception())))
                        self.logger.error(msg, exc_info=f.exception())
                        task.add_status_msg(
                            msg=msg,
                            error=True,
                            ctx=str(uuid.UUID(bytes=t)),
                            ctx_type='task')
                        task.failure()

            task.bubble_results()
            task.align_result()
        else:
            try:
                prom_client = PromenadeClient()
                action = self.action_class_map.get(task.action, None)(
                    task,
                    self.orchestrator,
                    self.state_manager,
                    prom_client=prom_client)
                action.start()
            except Exception as e:
                msg = ("Subtask for action %s raised unexpected exception: %s"
                       % (task.action, str(e)))
                self.logger.error(msg, exc_info=e)
                task.add_status_msg(
                    msg=msg,
                    error=True,
                    ctx=str(task.get_id()),
                    ctx_type='task')
                task.failure()

        task.set_status(hd_fields.TaskStatus.Complete)
        task.save()

        return
