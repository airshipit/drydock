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
import time
import logging

from oslo_config import cfg

import drydock_provisioner.error as errors

import drydock_provisioner.objects.fields as hd_fields
import drydock_provisioner.objects.task as task_model

import drydock_provisioner.drivers.oob as oob
import drydock_provisioner.drivers as drivers


class ManualDriver(oob.OobDriver):

    oob_types_supported = ['manual']

    def __init__(self, **kwargs):
        super(ManualDriver, self).__init__(**kwargs)

        self.driver_name = "manual_driver"
        self.driver_key = "manual_driver"
        self.driver_desc = "Manual (Noop) OOB Driver"

        self.logger = logging.getLogger(cfg.CONF.logging.oobdriver_logger_name)

    def execute_task(self, task_id):
        task = self.state_manager.get_task(task_id)

        if task is None:
            self.logger.error("Invalid task %s" % (task_id))
            raise errors.DriverError("Invalid task %s" % (task_id))

        if task.action not in self.supported_actions:
            self.logger.error("Driver %s doesn't support task action %s"
                % (self.driver_desc, task.action))
            raise errors.DriverError("Driver %s doesn't support task action %s"
                % (self.driver_desc, task.action))

        design_id = getattr(task, 'design_id', None)

        if design_id is None:
            raise errors.DriverError("No design ID specified in task %s" %
                                     (task_id))


        if task.site_name is None:
            raise errors.DriverError("Not site specified for task %s." %
                                    (task_id))

        self.orchestrator.task_field_update(task.get_id(),
                            status=hd_fields.TaskStatus.Running)

        self.logger.info("Sleeping 60s to allow time for manual OOB %s action" % task.action)

        time.sleep(60)

        self.orchestrator.task_field_update(task.get_id(),
                            status=hd_fields.TaskStatus.Complete,
                            result=hd_fields.ActionResult.Success)
