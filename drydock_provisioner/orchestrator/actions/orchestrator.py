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
"""Actions for the Orchestrator level of the Drydock workflow."""

import time
import datetime
import logging
import concurrent.futures
import uuid

import drydock_provisioner.config as config
import drydock_provisioner.error as errors
import drydock_provisioner.objects.fields as hd_fields


class BaseAction(object):
    """The base class for actions starts by the orchestrator."""

    def __init__(self, task, orchestrator, state_manager):
        """Object initializer.

        :param task: objects.Task instance this action will execute against
        :param orchestrator: orchestrator.Orchestrator instance
        :param state_manager: state.DrydockState instnace used to access task state
        """
        self.task = task
        self.orchestrator = orchestrator
        self.state_manager = state_manager
        self.logger = logging.getLogger(
            config.config_mgr.conf.logging.global_logger_name)

    def _parallelize_subtasks(self, fn, subtask_id_list, *args, **kwargs):
        """Spawn threads to execute fn for each subtask using concurrent.futures.

        Return a dictionary of task_id:concurrent.futures.Future instance

        :param fn: The callable to execute in a thread, expected it takes a task_id as first argument
        :param subtask_id_list: List of uuid.UUID ID of the subtasks to execute on
        :param *args: The args to pass to fn
        :param **kwargs: The kwargs to pass to fn
        """
        task_futures = dict()

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as te:
            for t in subtask_id_list:
                task_futures[t.bytes] = te.submit(fn, t, *args, **kwargs)

        return task_futures

    def _split_action(self):
        """Start a parallel action for each node in scope.

        Start a threaded instance of this action for each node in
        scope of this action's task. A subtask will be created for each
        action. Returns all a list of concurrent.futures managed
        threads running the actions.

        :returns: dictionary of subtask_id.bytes => Future instance
        """
        target_nodes = self.orchestrator.get_target_nodes(self.task)

        if len(target_nodes) > 1:
            self.logger.info(
                "Found multiple target nodes in task %s, splitting..." % str(
                    self.task.get_id()))
            split_tasks = dict()

            with concurrent.futures.ThreadPoolExecutor() as te:
                for n in target_nodes:
                    split_task = self.orchestrator.create_task(
                        design_ref=self.task.design_ref,
                        action=hd_fields.OrchestratorAction.PrepareNodes,
                        node_filter=self.orchestrator.
                        create_nodefilter_from_nodelist([n]))
                    self.task.register_subtask(split_task)
                    action = self.__class__(split_task, self.orchestrator,
                                            self.state_manager)
                    split_tasks[split_task.get_id().bytes] = te.submit(
                        action.start)

            return split_tasks

    def _collect_subtask_futures(self, subtask_futures, timeout=300):
        """Collect Futures executing on subtasks or timeout.

        Wait for Futures to finish or timeout. After timeout, enumerate the subtasks
        that timed out in task result messages.

        :param subtask_futures: dictionary of subtask_id.bytes -> Future instance
        :param timeout: The number of seconds to wait for all Futures to complete
        :param bubble: Whether to bubble results from collected subtasks
        """
        finished, timed_out = concurrent.futures.wait(
            subtask_futures.values(), timeout=timeout)

        for k, v in subtask_futures.items():
            if not v.done():
                self.task.add_status_msg(
                    "Subtask thread for %s still executing after timeout." %
                    str(uuid.UUID(bytes=k)),
                    error=True,
                    ctx=str(self.task.get_id()),
                    ctx_type='task')
                self.task.failure()
            else:
                if v.exception():
                    self.logger.error(
                        "Uncaught excetion in subtask %s future:" % str(
                            uuid.UUID(bytes=k)),
                        exc_info=v.exception())
            st = self.state_manager.get_task(uuid.UUID(bytes=k))
            st.bubble_results()
            st.align_result()
            st.save()
        if len(timed_out) > 0:
            raise errors.CollectSubtaskTimeout(
                "One or more subtask threads did not finish in %d seconds." %
                timeout)

        self.task.align_result()
        return

    def _load_site_design(self):
        """Load the site design from this action's task.

        The design_ref in the task can be resolved to a set of design documents
        that reflect the site design to be operated on. Load this design for use
        by this action.
        """
        design_status, site_design = self.orchestrator.get_effective_site(
            self.task.design_ref)

        if design_status is None or design_status.status == hd_fields.ActionResult.Failure:
            raise errors.OrchestratorError("Site design failed load.")

        return site_design

    def _get_driver(self, driver_type, subtype=None):
        """Locate the correct driver instance based on type and subtype.

        :param driver_type: The type of driver, 'oob', 'node', or 'network'
        :param subtype: In cases where multiple drivers can be active, select
                        one based on subtype
        """
        driver = None
        if driver_type == 'oob':
            if subtype is None:
                return None
            for d in self.orchestrator.enabled_drivers['oob']:
                if d.oob_type_support(subtype):
                    driver = d
                    break
        else:
            driver = self.orchestrator.enabled_drivers[driver_type]

        return driver


class Noop(BaseAction):
    """Dummy action to allow the full task completion flow without impacts."""

    def start(self):
        """Start executing this action."""
        self.logger.debug("Starting Noop Action.")
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()
        time.sleep(5)
        self.task = self.state_manager.get_task(self.task.get_id())
        if self.task.check_terminate():
            self.logger.debug("Terminating action.")
            self.task.set_status(hd_fields.TaskStatus.Terminated)
            self.task.failure()
            self.task.add_status_msg(
                msg="Action terminated.", ctx_type='NA', ctx='NA', error=False)
        else:
            self.logger.debug("Marked task as successful.")
            self.task.set_status(hd_fields.TaskStatus.Complete)
            target_nodes = self.orchestrator.get_target_nodes(self.task)
            for n in target_nodes:
                self.task.success(focus=n.name)
            self.task.add_status_msg(
                msg="Noop action.", ctx_type='NA', ctx='NA', error=False)
        self.task.save()
        self.logger.debug("Saved task state.")
        self.logger.debug("Finished Noop Action.")
        return


class DestroyNodes(BaseAction):
    """Action to destroy nodes in prepartion for a redeploy."""

    def start(self):
        """Start executing this action."""
        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.failure()
        self.task.save()

        return


class ValidateDesign(BaseAction):
    """Action for validating the design document referenced by the task."""

    def start(self):
        """Start executing this action."""
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        try:
            status, site_design = self.orchestrator.get_effective_site(
                self.task.design_ref)
            self.task.merge_status_messages(task_result=status)
            self.task.set_status(hd_fields.TaskStatus.Complete)
            if status.result.status == hd_fields.ActionResult.Success:
                self.task.success()
            else:
                self.task.failure()
            self.task.save()
        except Exception:
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.save()
        return


class VerifySite(BaseAction):
    """Action to verify downstream tools in the site are available and ready."""

    def start(self):
        """Start executing this action in the context of the local task."""
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        node_driver = self._get_driver('node')

        if node_driver is None:
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.add_status_msg(
                msg="No node driver enabled, ending task.",
                error=True,
                ctx=str(self.task.get_id()),
                ctx_type='task')
            self.task.result.set_message("No NodeDriver enabled.")
            self.task.result.set_reason("Bad Configuration.")
            self.task.failure()
            self.task.save()
            return

        node_driver_task = self.orchestrator.create_task(
            design_ref=self.task.design_ref,
            action=hd_fields.OrchestratorAction.ValidateNodeServices)
        self.task.register_subtask(node_driver_task)

        node_driver.execute_task(node_driver_task.get_id())

        node_driver_task = self.state_manager.get_task(
            node_driver_task.get_id())

        self.task.add_status_msg(
            msg="Collected subtask %s" % str(node_driver_task.get_id()),
            error=False,
            ctx=str(node_driver_task.get_id()),
            ctx_type='task')

        self.task = self.state_manager.get_task(self.task.get_id())
        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.align_result()
        self.task.save()
        return


class PrepareSite(BaseAction):
    """Action to configure site wide/inter-node settings."""

    def start(self):
        """Start executing this action in the context of the local task."""
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        driver = self._get_driver('node')

        if driver is None:
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.add_status_msg(
                msg="No node driver enabled, ending task.",
                error=True,
                ctx=str(self.task.get_id()),
                ctx_type='task')
            self.task.result.set_message("No NodeDriver enabled.")
            self.task.result.set_reason("Bad Configuration.")
            self.task.failure()
            self.task.save()
            return

        self.step_networktemplate(driver)
        self.step_usercredentials(driver)

        self.task.align_result()
        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return

    def step_networktemplate(self, driver):
        """Run the CreateNetworkTemplate step of this action.

        :param driver: The driver instance to use for execution.
        """
        site_network_task = self.orchestrator.create_task(
            design_ref=self.task.design_ref,
            action=hd_fields.OrchestratorAction.CreateNetworkTemplate)
        self.task.register_subtask(site_network_task)

        self.logger.info(
            "Starting node driver task %s to create network templates" %
            (site_network_task.get_id()))

        driver.execute_task(site_network_task.get_id())

        self.task.add_status_msg(
            msg="Collected subtask %s" % str(site_network_task.get_id()),
            error=False,
            ctx=str(site_network_task.get_id()),
            ctx_type='task')
        self.logger.info("Node driver task %s complete" %
                         (site_network_task.get_id()))

    def step_usercredentials(self, driver):
        """Run the ConfigureUserCredentials step of this action.

        :param driver: The driver instance to use for execution.
        """
        user_creds_task = self.orchestrator.create_task(
            design_ref=self.task.design_ref,
            action=hd_fields.OrchestratorAction.ConfigureUserCredentials)
        self.task.register_subtask(user_creds_task)

        self.logger.info(
            "Starting node driver task %s to configure user credentials" %
            (user_creds_task.get_id()))

        driver.execute_task(user_creds_task.get_id())

        self.task.add_status_msg(
            msg="Collected subtask %s" % str(user_creds_task.get_id()),
            error=False,
            ctx=str(user_creds_task.get_id()),
            ctx_type='task')
        self.logger.info("Node driver task %s complete" %
                         (user_creds_task.get_id()))


class VerifyNodes(BaseAction):
    """Action to verify the orchestrator has adequate access to a node to start the deployment."""

    def start(self):
        """Start executing this action."""
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        design_status, site_design = self.orchestrator.get_effective_site(
            self.task.design_ref)

        node_filter = self.task.node_filter

        oob_type_partition = {}

        target_nodes = self.orchestrator.process_node_filter(
            node_filter, site_design)

        for n in target_nodes:
            if n.oob_type not in oob_type_partition.keys():
                oob_type_partition[n.oob_type] = []

            oob_type_partition[n.oob_type].append(n)

        task_futures = dict()
        for oob_type, oob_nodes in oob_type_partition.items():
            oob_driver = self._get_driver('oob', oob_type)

            if oob_driver is None:
                self.logger.warning(
                    "Node OOB type %s has no enabled driver." % oob_type)
                self.task.failure()
                for n in oob_nodes:
                    self.task.add_status_msg(
                        msg="Node %s OOB type %s is not supported." %
                        (n.get_name(), oob_type),
                        error=True,
                        ctx=n.get_name(),
                        ctx_type='node')
                continue

            nf = self.orchestrator.create_nodefilter_from_nodelist(oob_nodes)

            oob_driver_task = self.orchestrator.create_task(
                design_ref=self.task.design_ref,
                action=hd_fields.OrchestratorAction.InterrogateOob,
                node_filter=nf)
            self.task.register_subtask(oob_driver_task)

            self.logger.info(
                "Starting task %s for node verification via OOB type %s" %
                (oob_driver_task.get_id(), oob_type))
            task_futures.update(
                self._parallelize_subtasks(oob_driver.execute_task,
                                           [oob_driver_task.get_id()]))

        try:
            self._collect_subtask_futures(
                task_futures,
                timeout=(config.config_mgr.conf.timeouts.drydock_timeout * 60))
            self.logger.debug(
                "Collected subtasks for task %s" % str(self.task.get_id()))
        except errors.CollectSubtaskTimeout as ex:
            self.logger.warning(str(ex))

        self.task.set_status(hd_fields.TaskStatus.Complete)

        return


class PrepareNodes(BaseAction):
    """Action to prepare a node for deployment."""

    def start(self):
        """Start executing this action."""
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        node_driver = self._get_driver('node')

        if node_driver is None:
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.add_status_msg(
                msg="No node driver enabled, ending task.",
                error=True,
                ctx=str(self.task.get_id()),
                ctx_type='task')
            self.task.result.set_message("No NodeDriver enabled.")
            self.task.result.set_reason("Bad Configuration.")
            self.task.failure()
            self.task.save()
            return

        design_status, site_design = self.orchestrator.get_effective_site(
            self.task.design_ref)

        target_nodes = self.orchestrator.get_target_nodes(self.task)

        # Parallelize this task so that node progression is
        # not interlinked
        if len(target_nodes) > 1:
            self.split_action()
        else:
            check_task_id = self.step_checkexist(node_driver)
            node_check_task = self.state_manager.get_task(check_task_id)

            # Build the node_filter from the failures of the node_check_task
            # as these are the nodes that are unknown to the node provisioner
            # and are likely save to be rebooted

            target_nodes = self.orchestrator.process_node_filter(
                node_check_task.node_filter_from_failures(), site_design)

            # And log the nodes that were found so they can be addressed

            for n in node_check_task.result.successes:
                self.logger.debug(
                    "Found node %s in provisioner, skipping OOB management." %
                    (n))
                self.task.add_status_msg(
                    msg="Node found in provisioner, skipping OOB management",
                    error=False,
                    ctx=n,
                    ctx_type='node')

            self.step_oob_set_netboot(target_nodes)

            # bubble results from the SetNodeBoot task and
            # continue the execution with successful targets

            self.task.bubble_results(
                action_filter=hd_fields.OrchestratorAction.SetNodeBoot)

            target_nodes = self.orchestrator.process_node_filter(
                self.task.node_filter_from_successes(), site_design)

            self.step_oob_powercycle(target_nodes)

            # bubble results from the Powercycle task and
            # continue the execution with successful targets
            self.task.bubble_results(
                action_filter=hd_fields.OrchestratorAction.PowerCycleNode)

            target_nodes = self.orchestrator.process_node_filter(
                self.task.node_filter_from_successes(), site_design)

            self.step_node_identify(node_driver, target_nodes)

            # We can only commission nodes that were successfully identified in the provisioner

            self.task.bubble_results(
                action_filter=hd_fields.OrchestratorAction.IdentifyNode)

            target_nodes = self.orchestrator.process_node_filter(
                self.task.node_filter_from_successes(), site_design)

            self.step_node_configure_hw(node_driver, target_nodes)

        self.task.bubble_results()
        self.task.align_result()
        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return

    def step_node_configure_hw(self, node_driver, node_list):
        """Execute the ConfigureHardware step of this action on a list of nodes.

        :param node_driver: driver instance to use for execution
        :param node_list: a list of objects.BaremetalNode instances
        """
        if len(node_list) > 0:
            self.logger.info(
                "Starting hardware configuration task on %d nodes." %
                len(node_list))

            node_commission_task = None
            while True:
                if node_commission_task is None:
                    node_commission_task = self.orchestrator.create_task(
                        design_ref=self.task.design_ref,
                        action=hd_fields.OrchestratorAction.ConfigureHardware,
                        node_filter=self.orchestrator.
                        create_nodefilter_from_nodelist(node_list))
                    self.task.register_subtask(node_commission_task)

                self.logger.info(
                    "Starting node driver task %s to commission nodes." %
                    (node_commission_task.get_id()))

                node_driver.execute_task(node_commission_task.get_id())

                node_commission_task = self.state_manager.get_task(
                    node_commission_task.get_id())
                try:
                    if not node_commission_task.retry_task(max_attempts=3):
                        break
                except errors.MaxRetriesReached:
                    self.task.failure()
                    break
        else:
            self.logger.warning(
                "No nodes successfully identified, skipping commissioning subtask"
            )

    def step_node_identify(self, node_driver, node_list):
        """Execute the IdentifyNode step of this action on a list of nodes.

        :param node_driver: driver instance to use for execution
        :param node_list: a list of objects.BaremetalNode instances
        :return: list of uuid.UUID task ids of the tasks executing this step
        """
        # IdentifyNode success will take some time after PowerCycleNode finishes
        # Retry the operation a few times if it fails before considering it a final failure
        # Each attempt is a new task which might make the final task tree a bit confusing

        max_attempts = config.config_mgr.conf.timeouts.identify_node * (
            60 / config.config_mgr.conf.poll_interval)

        self.logger.debug(
            "Will make max of %d attempts to complete the identify_node task."
            % max_attempts)
        node_identify_task = None

        while True:
            if node_identify_task is None:
                node_identify_task = self.orchestrator.create_task(
                    design_ref=self.task.design_ref,
                    action=hd_fields.OrchestratorAction.IdentifyNode,
                    node_filter=self.orchestrator.
                    create_nodefilter_from_nodelist(node_list))
                self.task.register_subtask(node_identify_task)

            self.logger.info(
                "Starting node driver task %s to identify nodes." %
                (node_identify_task.get_id()))

            node_driver.execute_task(node_identify_task.get_id())

            node_identify_task = self.state_manager.get_task(
                node_identify_task.get_id())
            node_identify_task.bubble_results()

            try:
                if not node_identify_task.retry_task(
                        max_attempts=max_attempts):
                    break

                time.sleep(config.config_mgr.conf.poll_interval)
            except errors.MaxRetriesReached:
                self.task.failure()
                break

        return [node_identify_task.get_id()]

    def step_oob_set_netboot(self, node_list):
        """Execute the SetNetBoot step of this action on a list of nodes.

        :param node_list: a list of objects.BaremetalNode instances
        :return: list of uuid.UUID task ids of the tasks executing this step
        """
        oob_type_partition = {}

        for n in node_list:
            if n.oob_type not in oob_type_partition.keys():
                oob_type_partition[n.oob_type] = []

            oob_type_partition[n.oob_type].append(n)

        task_futures = dict()

        for oob_type, oob_nodes in oob_type_partition.items():
            oob_driver = self._get_driver('oob', oob_type)

            if oob_driver is None:
                self.logger.warning(
                    "Node OOB type %s has no enabled driver." % oob_type)
                self.task.failure()
                for n in oob_nodes:
                    self.task.add_status_msg(
                        msg="Node %s OOB type %s is not supported." %
                        (n.get_name(), oob_type),
                        error=True,
                        ctx=n.get_name(),
                        ctx_type='node')
                continue

            setboot_task = self.orchestrator.create_task(
                design_ref=self.task.design_ref,
                action=hd_fields.OrchestratorAction.SetNodeBoot,
                node_filter=self.orchestrator.create_nodefilter_from_nodelist(
                    oob_nodes))
            self.task.register_subtask(setboot_task)

            self.logger.info(
                "Starting OOB driver task %s to set PXE boot for OOB type %s" %
                (setboot_task.get_id(), oob_type))
            task_futures.update(
                self._parallelize_subtasks(oob_driver.execute_task,
                                           [setboot_task.get_id()]))

        try:
            self._collect_subtask_futures(
                task_futures,
                timeout=(config.config_mgr.conf.timeouts.drydock_timeout * 60))
            self.logger.debug(
                "Collected subtasks for task %s" % str(self.task.get_id()))
        except errors.CollectSubtaskTimeout as ex:
            self.logger.warning(str(ex))

        return [uuid.UUID(bytes=x) for x in task_futures.keys()]

    def step_oob_powercycle(self, node_list):
        """Execute the NodePowerCycle step of this action on a list of nodes.

        :param node_list: a list of objects.BaremetalNode instances
        :return: list of uuid.UUID task ids of the tasks executing this step
        """
        oob_type_partition = {}

        for n in node_list:
            if n.oob_type not in oob_type_partition.keys():
                oob_type_partition[n.oob_type] = []

            oob_type_partition[n.oob_type].append(n)

        task_futures = dict()

        for oob_type, oob_nodes in oob_type_partition.items():
            oob_driver = self._get_driver('oob', oob_type)

            if oob_driver is None:
                self.logger.warning(
                    "Node OOB type %s has no enabled driver." % oob_type)
                self.task.failure()
                for n in oob_nodes:
                    self.task.add_status_msg(
                        msg="Node %s OOB type %s is not supported." %
                        (n.get_name(), oob_type),
                        error=True,
                        ctx=n.get_name(),
                        ctx_type='node')
                continue

            cycle_task = self.orchestrator.create_task(
                design_ref=self.task.design_ref,
                action=hd_fields.OrchestratorAction.PowerCycleNode,
                node_filter=self.orchestrator.create_nodefilter_from_nodelist(
                    oob_nodes))
            self.task.register_subtask(cycle_task)

            self.logger.info(
                "Starting OOB driver task %s to power cycle nodes for OOB type %s"
                % (cycle_task.get_id(), oob_type))

            task_futures.update(
                self._parallelize_subtasks(oob_driver.execute_task,
                                           [cycle_task.get_id()]))

        try:
            self._collect_subtask_futures(
                task_futures,
                timeout=(config.config_mgr.conf.timeouts.drydock_timeout * 60))
            self.logger.debug(
                "Collected subtasks for task %s" % str(self.task.get_id()))
        except errors.CollectSubtaskTimeout as ex:
            self.logger.warning(str(ex))

        return [uuid.UUID(bytes=x) for x in task_futures.keys()]

    def split_action(self):
        """Split this action into independent threads per node."""
        action_timeout = config.config_mgr.conf.timeouts.identify_node + \
            config.config_mgr.conf.timeouts.configure_hardware
        split_tasks = self._split_action()
        self._collect_subtask_futures(split_tasks, timeout=action_timeout * 60)

    def step_checkexist(self, driver):
        """Query the driver for node existence to prevent impacting deployed nodes.

        :param driver: driver instance to use for execution
        :returns: uuid.UUID task id of the task that executed this step
        """
        node_check_task = self.orchestrator.create_task(
            design_ref=self.task.design_ref,
            action=hd_fields.OrchestratorAction.IdentifyNode,
            node_filter=self.task.node_filter)

        self.logger.info("Starting check task %s before rebooting nodes" %
                         (node_check_task.get_id()))

        task_futures = self._parallelize_subtasks(driver.execute_task,
                                                  [node_check_task.get_id()])
        self._collect_subtask_futures(
            task_futures,
            timeout=(config.config_mgr.conf.timeouts.drydock_timeout * 60))

        node_check_task = self.state_manager.get_task(node_check_task.get_id())
        node_check_task.bubble_results()
        node_check_task.save()

        return node_check_task.get_id()


class DeployNodes(BaseAction):
    """Action to deploy a node with a persistent OS."""

    def start(self):
        """Start executing this action."""
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        node_driver = self.orchestrator.enabled_drivers['node']

        if node_driver is None:
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.add_status_msg(
                msg="No node driver enabled, ending task.",
                error=True,
                ctx=str(self.task.get_id()),
                ctx_type='task')
            self.task.result.set_message("No NodeDriver enabled.")
            self.task.result.set_reason("Bad Configuration.")
            self.task.failure()
            self.task.save()
            return

        node_networking_task = self.orchestrator.create_task(
            design_ref=self.task.design_ref,
            action=hd_fields.OrchestratorAction.ApplyNodeNetworking,
            node_filter=self.task.node_filter)
        self.task.register_subtask(node_networking_task)

        self.logger.info(
            "Starting node driver task %s to apply networking on nodes." %
            (node_networking_task.get_id()))

        node_driver.execute_task(node_networking_task.get_id())

        node_networking_task = self.state_manager.get_task(
            node_networking_task.get_id())

        node_storage_task = None

        if len(node_networking_task.result.successes) > 0:
            self.logger.info(
                "Found %s successfully networked nodes, configuring storage." %
                (len(node_networking_task.result.successes)))

            node_storage_task = self.orchestrator.create_task(
                design_ref=self.task.design_ref,
                action=hd_fields.OrchestratorAction.ApplyNodeStorage,
                node_filter=node_networking_task.node_filter_from_successes())

            self.logger.info(
                "Starting node driver task %s to configure node storage." %
                (node_storage_task.get_id()))

            node_driver.execute_task(node_storage_task.get_id())

            node_storage_task = self.state_manager.get_task(
                node_storage_task.get_id())

        else:
            self.logger.warning(
                "No nodes successfully networked, skipping storage configuration subtask."
            )

        node_platform_task = None
        if (node_storage_task is not None
                and len(node_storage_task.result.successes) > 0):
            self.logger.info(
                "Configured storage on %s nodes, configuring platform." %
                (len(node_storage_task.result.successes)))

            node_platform_task = self.orchestrator.create_task(
                design_ref=self.task.design_ref,
                action=hd_fields.OrchestratorAction.ApplyNodePlatform,
                node_filter=node_storage_task.node_filter_from_successes())
            self.task.register_subtask(node_platform_task)

            self.logger.info(
                "Starting node driver task %s to configure node platform." %
                (node_platform_task.get_id()))

            node_driver.execute_task(node_platform_task.get_id())

            node_platform_task = self.state_manager.get_task(
                node_platform_task.get_id())

        else:
            self.logger.warning(
                "No nodes with storage configuration, skipping platform configuration subtask."
            )

        node_deploy_task = None
        if node_platform_task is not None and len(
                node_platform_task.result.successes) > 0:
            self.logger.info(
                "Configured platform on %s nodes, starting deployment." %
                (len(node_platform_task.result.successes)))

            while True:
                if node_deploy_task is None:
                    node_deploy_task = self.orchestrator.create_task(
                        design_ref=self.task.design_ref,
                        action=hd_fields.OrchestratorAction.DeployNode,
                        node_filter=node_platform_task.
                        node_filter_from_successes())
                    self.task.register_subtask(node_deploy_task)

                self.logger.info(
                    "Starting node driver task %s to deploy nodes." %
                    (node_deploy_task.get_id()))
                node_driver.execute_task(node_deploy_task.get_id())

                node_deploy_task = self.state_manager.get_task(
                    node_deploy_task.get_id())

                try:
                    if not node_deploy_task.retry_task(max_attempts=3):
                        break
                except errors.MaxRetriesReached:
                    self.task.failure()
                    break
        else:
            self.logger.warning(
                "Unable to configure platform on any nodes, skipping deploy subtask"
            )

        if (node_deploy_task is not None
                and node_deploy_task.result is not None
                and len(node_deploy_task.result.successes) > 0):
            node_bootaction_task = self.orchestrator.create_task(
                design_ref=self.task.design_ref,
                action=hd_fields.OrchestratorAction.BootactionReport,
                node_filter=node_deploy_task.node_filter_from_successes())
            self.task.register_subtask(node_bootaction_task)
            action = BootactionReport(node_bootaction_task, self.orchestrator,
                                      self.state_manager)
            action.start()
            self.task.bubble_results(
                action_filter=hd_fields.OrchestratorAction.BootactionReport)
            self.task.align_result()
        else:
            self.task.bubble_results(
                action_filter=hd_fields.OrchestratorAction.DeployNode)
            self.task.align_result()

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return


class BootactionReport(BaseAction):
    """Wait for nodes to report status of boot action."""

    def start(self):
        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        poll_start = datetime.datetime.utcnow()

        still_running = True
        timeout = datetime.timedelta(
            minutes=config.config_mgr.conf.timeouts.bootaction_final_status)
        running_time = datetime.datetime.utcnow() - poll_start
        nodelist = [
            n.get_id() for n in self.orchestrator.get_target_nodes(self.task)
        ]

        self.logger.debug(
            "Waiting for bootaction response signals to complete.")
        while running_time < timeout:
            still_running = False
            for n in nodelist:
                bas = self.state_manager.get_boot_actions_for_node(n)
                running_bas = {
                    k: v
                    for (k, v) in bas.items() if v.get('action_status') ==
                    hd_fields.ActionResult.Incomplete
                }
                if len(running_bas) > 0:
                    still_running = True
                    break
            if still_running:
                self.logger.debug("Still waiting on %d running bootactions." %
                                  len(running_bas))
                time.sleep(config.config_mgr.conf.poll_interval)
                running_time = datetime.datetime.utcnow() - poll_start
            else:
                break

        self.logger.debug("Signals complete or timeout reached.")

        for n in nodelist:
            bas = self.state_manager.get_boot_actions_for_node(n)
            success_bas = {
                k: v
                for (k, v) in bas.items()
                if v.get('action_status') == hd_fields.ActionResult.Success
            }
            running_bas = {
                k: v
                for (k, v) in bas.items()
                if v.get('action_status') == hd_fields.ActionResult.Incomplete
            }
            failure_bas = {
                k: v
                for (k, v) in bas.items()
                if v.get('action_status') == hd_fields.ActionResult.Failure
            }
            for ba in success_bas.values():
                self.task.add_status_msg(
                    msg="Boot action %s completed with status %s" %
                    (ba['action_name'], ba['action_status']),
                    error=False,
                    ctx=n,
                    ctx_type='node')
            for ba in failure_bas.values():
                self.task.add_status_msg(
                    msg="Boot action %s completed with status %s" %
                    (ba['action_name'], ba['action_status']),
                    error=True,
                    ctx=n,
                    ctx_type='node')
            for ba in running_bas.values():
                self.task.add_status_msg(
                    msg="Boot action %s timed out." % (ba['action_name']),
                    error=True,
                    ctx=n,
                    ctx_type='node')

            if len(failure_bas) == 0 and len(running_bas) == 0:
                self.task.success(focus=n)
            else:
                self.task.failure(focus=n)

        self.logger.debug("Completed collecting bootaction signals.")
        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()
        return
