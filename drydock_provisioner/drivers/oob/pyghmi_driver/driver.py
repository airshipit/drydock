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
"""Driver for controlling OOB interface via IPMI.

Based on Openstack Ironic Pyghmi driver.
"""

import uuid
import logging
import concurrent.futures

from oslo_config import cfg

import drydock_provisioner.error as errors
import drydock_provisioner.config as config

import drydock_provisioner.objects.fields as hd_fields

import drydock_provisioner.drivers.oob.driver as oob_driver
import drydock_provisioner.drivers.driver as generic_driver

from .actions.oob import ValidateOobServices
from .actions.oob import ConfigNodePxe
from .actions.oob import SetNodeBoot
from .actions.oob import PowerOffNode
from .actions.oob import PowerOnNode
from .actions.oob import PowerCycleNode
from .actions.oob import InterrogateOob


class PyghmiDriver(oob_driver.OobDriver):
    """Driver for executing OOB actions via Pyghmi IPMI library."""

    pyghmi_driver_options = [
        cfg.IntOpt(
            'poll_interval',
            default=10,
            help='Polling interval in seconds for querying IPMI status'),
    ]

    oob_types_supported = ['ipmi']

    driver_name = "pyghmi_driver"
    driver_key = "pyghmi_driver"
    driver_desc = "Pyghmi OOB Driver"

    oob_types_supported = ['ipmi']

    action_class_map = {
        hd_fields.OrchestratorAction.ValidateOobServices: ValidateOobServices,
        hd_fields.OrchestratorAction.ConfigNodePxe: ConfigNodePxe,
        hd_fields.OrchestratorAction.SetNodeBoot: SetNodeBoot,
        hd_fields.OrchestratorAction.PowerOffNode: PowerOffNode,
        hd_fields.OrchestratorAction.PowerOnNode: PowerOnNode,
        hd_fields.OrchestratorAction.PowerCycleNode: PowerCycleNode,
        hd_fields.OrchestratorAction.InterrogateOob: InterrogateOob,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        cfg.CONF.register_opts(
            PyghmiDriver.pyghmi_driver_options, group=PyghmiDriver.driver_key)

        self.logger = logging.getLogger(
            config.config_mgr.conf.logging.oobdriver_logger_name)

    def execute_task(self, task_id):
        task = self.state_manager.get_task(task_id)

        if task is None:
            self.logger.error("Invalid task %s" % (task_id))
            raise errors.DriverError("Invalid task %s" % (task_id))

        if task.action not in self.supported_actions:
            self.logger.error("Driver %s doesn't support task action %s" %
                              (self.driver_desc, task.action))
            raise errors.DriverError(
                "Driver %s doesn't support task action %s" % (self.driver_desc,
                                                              task.action))

        task.set_status(hd_fields.TaskStatus.Running)
        task.save()

        target_nodes = self.orchestrator.get_target_nodes(task)

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as e:
            subtask_futures = dict()
            for n in target_nodes:
                sub_nf = self.orchestrator.create_nodefilter_from_nodelist([n])
                subtask = self.orchestrator.create_task(
                    action=task.action,
                    design_ref=task.design_ref,
                    node_filter=sub_nf)
                task.register_subtask(subtask)
                self.logger.debug(
                    "Starting Pyghmi subtask %s for action %s on node %s" %
                    (str(subtask.get_id()), task.action, n.name))

                action_class = self.action_class_map.get(task.action, None)
                if action_class is None:
                    self.logger.error(
                        "Could not find action resource for action %s" %
                        task.action)
                    self.task.failure()
                    break
                action = action_class(subtask, self.orchestrator,
                                      self.state_manager)
                subtask_futures[subtask.get_id().bytes] = e.submit(
                    action.start)

            timeout = config.config_mgr.conf.timeouts.drydock_timeout
            finished, running = concurrent.futures.wait(
                subtask_futures.values(), timeout=(timeout * 60))

            for t, f in subtask_futures.items():
                if not f.done():
                    task.add_status_msg(
                        "Subtask %s timed out before completing.",
                        error=True,
                        ctx=str(uuid.UUID(bytes=t)),
                        ctx_type='task')
                    task.failure()
                else:
                    if f.exception():
                        self.logger.error(
                            "Uncaught exception in subtask %s" % str(
                                uuid.UUID(bytes=t)),
                            exc_info=f.exception())
            task.align_result()
            task.set_status(hd_fields.TaskStatus.Complete)
            task.save()

        return


class PyghmiActionRunner(generic_driver.DriverActionRunner):
    """Threaded runner for a Pyghmi Action."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.logger = logging.getLogger(
            config.config_mgr.conf.logging.oobdriver_logger_name)


def list_opts():
    return {PyghmiDriver.driver_key: PyghmiDriver.pyghmi_driver_options}
