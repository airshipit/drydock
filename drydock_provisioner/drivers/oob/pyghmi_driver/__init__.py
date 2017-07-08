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

from pyghmi.ipmi.command import Command
from pyghmi.exceptions import IpmiException

import drydock_provisioner.error as errors

import drydock_provisioner.objects.fields as hd_fields
import drydock_provisioner.objects.task as task_model

import drydock_provisioner.drivers.oob as oob
import drydock_provisioner.drivers as drivers


class PyghmiDriver(oob.OobDriver):
    pyghmi_driver_options = [
        cfg.IntOpt('poll_interval', default=10, help='Polling interval in seconds for querying IPMI status'),
    ]

    oob_types_supported = ['ipmi']

    driver_name = "pyghmi_driver"
    driver_key = "pyghmi_driver"
    driver_desc = "Pyghmi OOB Driver"

    def __init__(self, **kwargs):
        super(PyghmiDriver, self).__init__(**kwargs)

        cfg.CONF.register_opts(PyghmiDriver.pyghmi_driver_options, group=PyghmiDriver.driver_key)

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
        max_attempts = getattr(cfg.CONF.timeouts, task.action, cfg.CONF.timeouts.drydock_timeout) * (60 / cfg.CONF.pyghmi_driver.poll_interval)
        while (len(incomplete_subtasks) > 0 and attempts <= max_attempts):
            for n in incomplete_subtasks:
                t = self.state_manager.get_task(n)
                if t.get_status() in [hd_fields.TaskStatus.Terminated,
                                  hd_fields.TaskStatus.Complete,
                                  hd_fields.TaskStatus.Errored]:
                    incomplete_subtasks.remove(n)
            time.sleep(cfg.CONF.pyghmi_driver.poll_interval)
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


        self.orchestrator.task_field_update(self.task.get_id(),
                            status=hd_fields.TaskStatus.Running)

        if task_action == hd_fields.OrchestratorAction.ConfigNodePxe:
            self.orchestrator.task_field_update(self.task.get_id(),
                result=hd_fields.ActionResult.Failure,
                status=hd_fields.TaskStatus.Complete)
            return
        elif task_action == hd_fields.OrchestratorAction.SetNodeBoot:
            
            worked = False
            
            self.logger.debug("Setting bootdev to PXE for %s" % self.node.name)
            self.exec_ipmi_command(Command.set_bootdev, 'pxe')
                
            time.sleep(3)

            bootdev = self.exec_ipmi_command(Command.get_bootdev)
                
            if bootdev.get('bootdev', '') == 'network':
                self.logger.debug("%s reports bootdev of network" % self.node.name)
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Success,
                    status=hd_fields.TaskStatus.Complete)
                return
            else:
                self.logger.warning("%s reports bootdev of %s" % (ipmi_address, bootdev.get('bootdev', None)))
                worked = False
                
            self.logger.error("Giving up on IPMI command to %s after 3 attempts" % self.node.name)
            self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Failure,
                    status=hd_fields.TaskStatus.Complete)
            return
        elif task_action == hd_fields.OrchestratorAction.PowerOffNode:
            worked = False

            self.logger.debug("Sending set_power = off command to %s" % self.node.name)
            self.exec_ipmi_command(Command.set_power, 'off')

            i = 18

            while i > 0:
                self.logger.debug("Polling powerstate waiting for success.")
                power_state = self.exec_ipmi_command(Command.get_power)
                if power_state.get('powerstate', '') == 'off':
                    self.logger.debug("Node reports powerstate of off")
                    worked = True
                    break
                time.sleep(10)
                i = i - 1

            if worked:
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Success,
                    status=hd_fields.TaskStatus.Complete)
            else:
                self.logger.error("Giving up on IPMI command to %s" % self.node.name)
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Failure,
                    status=hd_fields.TaskStatus.Complete)
            return
        elif task_action == hd_fields.OrchestratorAction.PowerOnNode:
            worked = False

            self.logger.debug("Sending set_power = off command to %s" % self.node.name)
            self.exec_ipmi_command(Command.set_power, 'off')

            i = 18

            while i > 0:
                self.logger.debug("Polling powerstate waiting for success.")
                power_state = self.exec_ipmi_command(Command.get_power)
                if power_state.get('powerstate', '') == 'off':
                    self.logger.debug("Node reports powerstate of off")
                    worked = True
                    break
                time.sleep(10)
                i = i - 1

            if worked:
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Success,
                    status=hd_fields.TaskStatus.Complete)
            else:
                self.logger.error("Giving up on IPMI command to %s" % self.node.name)
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Failure,
                    status=hd_fields.TaskStatus.Complete)
            return
        elif task_action == hd_fields.OrchestratorAction.PowerCycleNode:
            self.logger.debug("Sending set_power = off command to %s" % self.node.name)
            self.exec_ipmi_command(Command.set_power, 'off')

            # Wait for power state of off before booting back up
            # We'll wait for up to 3 minutes to power off
            i = 18

            while i > 0:
                power_state = self.exec_ipmi_command(Command.get_power)
                if power_state is not None and power_state.get('powerstate', '') == 'off':
                    self.logger.debug("%s reports powerstate of off" % self.node.name)
                    break
                elif power_state is None:
                    self.logger.debug("None response on IPMI power query to %s" % self.node.name)
                time.sleep(10)
                i = i - 1

            if power_state.get('powerstate', '') == 'on':
                self.logger.warning("Failed powering down node %s during power cycle task" % self.node.name)
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Failure,
                    status=hd_fields.TaskStatus.Complete)
                return

            self.logger.debug("Sending set_power = on command to %s" % self.node.name)
            self.exec_ipmi_command(Command.set_power, 'on')

            i = 18

            while i > 0:
                power_state = self.exec_ipmi_command(Command.get_power)
                if power_state is not None and power_state.get('powerstate', '') == 'on':
                    self.logger.debug("%s reports powerstate of on" % self.node.name)
                    break
                elif power_state is None:
                    self.logger.debug("None response on IPMI power query to %s" % self.node.name)
                time.sleep(10)
                i = i - 1

            if power_state.get('powerstate', '') == 'on':
                self.orchestrator.task_field_update(self.task.get_id(),
                    result=hd_fields.ActionResult.Success,
                    status=hd_fields.TaskStatus.Complete)
            else:
                self.logger.warning("Failed powering up node %s during power cycle task" % self.node.name)
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

    def get_ipmi_session(self):
        """
        Initialize a Pyghmi IPMI session to this runner's self.node

        :return: An instance of pyghmi.ipmi.command.Command initialized to nodes' IPMI interface
        """

        node = self.node

        if node.oob_type != 'ipmi':
            raise errors.DriverError("Node OOB type is not IPMI")

        ipmi_network = self.node.oob_parameters['network']
        ipmi_address = self.node.get_network_address(ipmi_network)

        if ipmi_address is None:
            raise errors.DriverError("Node %s has no IPMI address" %
                (node.name))

        
        ipmi_account = self.node.oob_parameters['account']
        ipmi_credential = self.node.oob_parameters['credential']

        self.logger.debug("Starting IPMI session to %s with %s/%s" %
                            (ipmi_address, ipmi_account, ipmi_credential[:1]))
        ipmi_session = Command(bmc=ipmi_address, userid=ipmi_account,
                               password=ipmi_credential)

        return ipmi_session

    def exec_ipmi_command(self, callable, *args):
        """
        Call an IPMI command after establishing a session with this runner's node

        :param callable: The pyghmi Command method to call
        :param args: The args to pass the callable
        """
        attempts = 0
        while attempts < 5:
            try:
                self.logger.debug("Initializing IPMI session")
                ipmi_session = self.get_ipmi_session()
            except IpmiException as iex:
                self.logger.error("Error initializing IPMI session for node %s" % self.node.name)
                self.logger.debug("IPMI Exception: %s" % str(iex))
                self.logger.warning("IPMI command failed, retrying after 15 seconds...")
                time.sleep(15)
                attempts =  attempts + 1
                continue

            try:
                self.logger.debug("Calling IPMI command %s on %s" % (callable.__name__, self.node.name))
                response = callable(ipmi_session, *args)
                ipmi_session.ipmi_session.logout()
                return response
            except IpmiException as iex:
                self.logger.error("Error sending command: %s" % str(iex))
                self.logger.warning("IPMI command failed, retrying after 15 seconds...")
                time.sleep(15)
                attempts = attempts + 1

def list_opts():
    return {PyghmiDriver.driver_key: PyghmiDriver.pyghmi_driver_options}
