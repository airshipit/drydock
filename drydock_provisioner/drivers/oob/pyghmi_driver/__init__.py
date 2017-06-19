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

from pyghmi.ipmi.command import Command

import drydock_provisioner
import drydock_provisioner.error as errors

import drydock_provisioner.objects.fields as hd_fields
import drydock_provisioner.objects.task as task_model

import drydock_provisioner.drivers.oob as oob
import drydock_provisioner.drivers as drivers


class PyghmiDriver(oob.OobDriver):

    oob_types_supported = ['ipmi']

    def __init__(self, **kwargs):
        super(PyghmiDriver, self).__init__(**kwargs)

        self.driver_name = "pyghmi_driver"
        self.driver_key = "pyghmi_driver"
        self.driver_desc = "Pyghmi OOB Driver"

        self.logger = logging.getLogger("%s.%s" %
                                (drydock_provisioner.conf.logging.oobdriver_logger_name, self.driver_key))

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

        if task.action == hd_fields.OrchestratorAction.ValidateOobServices:
            self.orchestrator.task_field_update(task.get_id(),
                                status=hd_fields.TaskStatus.Complete,
                                result=hd_fields.ActionResult.Success)
            return
            
        site_design = self.orchestrator.get_effective_site(design_id)

        target_nodes = []

        if len(task.node_list) > 0:
            target_nodes.extend([x
                                 for x in site_design.baremetal_nodes
                                 if x.get_name() in task.node_list])
        else:
            target_nodes.extend(site_design.baremetal_nodes)

        incomplete_subtasks = []
        # For each target node, create a subtask and kick off a runner
        for n in target_nodes:
            subtask = self.orchestrator.create_task(task_model.DriverTask,
                        parent_task_id=task.get_id(), design_id=design_id,
                        action=task.action,
                        task_scope={'site': task.site_name,
                                    'node_names': [n.get_name()]})
            incomplete_subtasks.append(subtask.get_id())

            runner = PyghmiTaskRunner(state_manager=self.state_manager,
                        orchestrator=self.orchestrator,
                        task_id=subtask.get_id(), node=n)
            runner.start()

        attempts = 0
        while len(incomplete_subtasks) > 0 and attempts <= getattr(drydock_provisioner.conf.timeouts, task.action, 5):
            for n in incomplete_subtasks:
                t = self.state_manager.get_task(n)
                if t.get_status() in [hd_fields.TaskStatus.Terminated,
                                  hd_fields.TaskStatus.Complete,
                                  hd_fields.TaskStatus.Errored]:
                    incomplete_subtasks.remove(n)
            time.sleep(1 * 60)
            attempts = attempts + 1

        task = self.state_manager.get_task(task.get_id())
        subtasks = map(self.state_manager.get_task, task.get_subtasks())

        success_subtasks = [x
                            for x in subtasks
                            if x.get_result() == hd_fields.ActionResult.Success]
        nosuccess_subtasks = [x
                              for x in subtasks
                              if x.get_result() in [hd_fields.ActionResult.PartialSuccess,
                                                    hd_fields.ActionResult.Failure]]

        task_result = None
        if len(success_subtasks) > 0 and len(nosuccess_subtasks) > 0:
            task_result = hd_fields.ActionResult.PartialSuccess
        elif len(success_subtasks) == 0 and len(nosuccess_subtasks) > 0:
            task_result = hd_fields.ActionResult.Failure
        elif len(success_subtasks) > 0 and len(nosuccess_subtasks) == 0:
            task_result = hd_fields.ActionResult.Success
        else:
            task_result = hd_fields.ActionResult.Incomplete

        self.orchestrator.task_field_update(task.get_id(),
                            result=task_result,
                            status=hd_fields.TaskStatus.Complete)
        return

class PyghmiTaskRunner(drivers.DriverTaskRunner):

    def __init__(self, node=None, **kwargs):
        super(PyghmiTaskRunner, self).__init__(**kwargs)

        self.logger = logging.getLogger('drydock.oobdriver.pyghmi')
        # We cheat here by providing the Node model instead
        # of making the runner source it from statemgmt
        if node is None:
            self.logger.error("Did not specify target node")
            raise errors.DriverError("Did not specify target node")

        self.node = node

    def execute_task(self):
        task_action = self.task.action

        if len(self.task.node_list) != 1:
            self.orchestrator.task_field_update(self.task.get_id(),
                result=hd_fields.ActionResult.Incomplete,
                status=hd_fields.TaskStatus.Errored)
            raise errors.DriverError("Multiple names (%s) in task %s node_list"
                % (len(self.task.node_list), self.task.get_id()))

        target_node_name = self.task.node_list[0]
        
        if self.node.get_name() != target_node_name:
            self.orchestrator.task_field_update(self.task.get_id(),
                result=hd_fields.ActionResult.Incomplete,
                status=hd_fields.TaskStatus.Errored)
            raise errors.DriverError("Runner node does not match " \
                                     "task node scope")

        ipmi_network = self.node.oob_network
        ipmi_address = self.node.get_network_address(ipmi_network)

        if ipmi_address is None:
            self.orchestrator.task_field_update(self.task.get_id(),
                result=hd_fields.ActionResult.Incomplete,
                status=hd_fields.TaskStatus.Errored)
            raise errors.DriverError("Node %s has no IPMI address" %
                (target_node_name))

        self.orchestrator.task_field_update(self.task.get_id(),
                status=hd_fields.TaskStatus.Running)
        ipmi_account = self.node.oob_account
        ipmi_credential = self.node.oob_credential

        ipmi_session = Command(bmc=ipmi_address, userid=ipmi_account,
                               password=ipmi_credential)

        if task_action == hd_fields.OrchestratorAction.ConfigNodePxe:
            self.orchestrator.task_field_update(self.task.get_id(),
                result=hd_fields.ActionResult.Failure,
                status=hd_fields.TaskStatus.Complete)
            return
        elif task_action == hd_fields.OrchestratorAction.SetNodeBoot:
            ipmi_session.set_bootdev('pxe')

            time.sleep(3)

            bootdev = ipmi_session.get_bootdev()

            if bootdev.get('bootdev', '') == 'network':
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Success,
                    status=hd_fields.TaskStatus.Complete)
            else:
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Failure,
                    status=hd_fields.TaskStatus.Complete)
            return
        elif task_action == hd_fields.OrchestratorAction.PowerOffNode:
            ipmi_session.set_power('off')

            i = 18

            while i > 0:
                power_state = ipmi_session.get_power()
                if power_state.get('powerstate', '') == 'off':
                    break
                time.sleep(10)
                i = i - 1

            if power_state.get('powerstate', '') == 'off':
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Success,
                    status=hd_fields.TaskStatus.Complete)
            else:
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Failure,
                    status=hd_fields.TaskStatus.Complete)
            return
        elif task_action == hd_fields.OrchestratorAction.PowerOnNode:
            ipmi_session.set_power('on')

            i = 18

            while i > 0:
                power_state = ipmi_session.get_power()
                if power_state.get('powerstate', '') == 'on':
                    break
                time.sleep(10)
                i = i - 1

            if power_state.get('powerstate', '') == 'on':
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Success,
                    status=hd_fields.TaskStatus.Complete)
            else:
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Failure,
                    status=hd_fields.TaskStatus.Complete)
            return
        elif task_action == hd_fields.OrchestratorAction.PowerCycleNode:
            ipmi_session.set_power('off')

            # Wait for power state of off before booting back up
            # We'll wait for up to 3 minutes to power off
            i = 18

            while i > 0:
                power_state = ipmi_session.get_power()
                if power_state.get('powerstate', '') == 'off':
                    break
                time.sleep(10)
                i = i - 1

            if power_state.get('powerstate', '') == 'on':
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Failure,
                    status=hd_fields.TaskStatus.Complete)
                return

            ipmi_session.set_power('on')

            i = 18

            while i > 0:
                power_state = ipmi_session.get_power()
                if power_state.get('powerstate', '') == 'on':
                    break
                time.sleep(10)
                i = i - 1

            if power_state.get('powerstate', '') == 'on':
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Success,
                    status=hd_fields.TaskStatus.Complete)
            else:
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Failure,
                    status=hd_fields.TaskStatus.Complete)
            return
        elif task_action == hd_fields.OrchestratorAction.InterrogateOob:
            mci_id = ipmi_session.get_mci()

            self.orchestrator.task_field_update(self.task.get_id(),
                result=hd_fields.ActionResult.Success,
                status=hd_fields.TaskStatus.Complete,
                result_detail=mci_id)
            return