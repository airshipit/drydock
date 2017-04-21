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
import uuid
import time
import threading
import importlib

from enum import Enum, unique
from copy import deepcopy

import helm_drydock.drivers as drivers
import helm_drydock.model.task as tasks
import helm_drydock.error as errors
import helm_drydock.enum as enum

class Orchestrator(object):

    # enabled_drivers is a map which provider drivers
    # should be enabled for use by this orchestrator
    def __init__(self, enabled_drivers=None, state_manager=None):
        self.enabled_drivers = {}

        self.state_manager = state_manager

        if enabled_drivers is not None:
            oob_driver_name = enabled_drivers.get('oob', None)
            if oob_driver_name is not None:
                m, c = oob_driver_name.rsplit('.', 1)
                oob_driver_class = \
                    getattr(importlib.import_module(m), c, None)
                if oob_driver_class is not None:
                    self.enabled_drivers['oob'] = oob_driver_class(state_manager=state_manager,
                                                                   orchestrator=self)

            node_driver_name = enabled_drivers.get('node', None)
            if node_driver_name is not None:
                m, c = node_driver_name.rsplit('.', 1)
                node_driver_class = \
                    getattr(importlib.import_module(m), c, None)
                if node_driver_class is not None:
                    self.enabled_drivers['node'] = node_driver_class(state_manager=state_manager,
                                                                   orchestrator=self)
            
            network_driver_name = enabled_drivers.get('network', None)
            if network_driver_name is not None:
                m, c = network_driver_name.rsplit('.', 1)
                network_driver_class = \
                    getattr(importlib.import_module(m), c, None)
                if network_driver_class is not None:
                    self.enabled_drivers['network'] = network_driver_class(state_manager=state_manager,
                                                                   orchestrator=self)


    """
    execute_task

    This is the core of the orchestrator. The task will describe the action
    to take and the context/scope of the command. We will then source
    the current designed state and current built state from the statemgmt
    module. Based on those 3 inputs, we'll decide what is needed next.
    """
    def execute_task(self, task_id):
        if self.state_manager is None:
            raise errors.OrchestratorError("Cannot execute task without" \
                                           " initialized state manager")

        task = self.state_manager.get_task(task_id)

        if task is None:
            raise errors.OrchestratorError("Task %s not found." 
                                            % (task_id))

        design_id = task.design_id
        task_site = task.site

        # Just for testing now, need to implement with enabled_drivers
        # logic
        if task.action == enum.OrchestratorAction.Noop:
            self.task_field_update(task_id,
                                   status=enum.TaskStatus.Running)        

            driver_task = self.create_task(tasks.DriverTask,
                            design_id=0,
                            action=enum.OrchestratorAction.Noop,
                            parent_task_id=task.get_id())

            driver = drivers.ProviderDriver(state_manager=self.state_manager,
                                            orchestrator=self)
            driver.execute_task(driver_task.get_id())
            driver_task = self.state_manager.get_task(driver_task.get_id())

            self.task_field_update(task_id, status=driver_task.get_status())
            
            return
        elif task.action == enum.OrchestratorAction.ValidateDesign:
            self.task_field_update(task_id,
                                   status=enum.TaskStatus.Running)
            try:
                site_design = self.get_effective_site(task_site,
                                                  change_id=design_id)
                self.task_field_update(task_id,
                                       result=enum.ActionResult.Success)
            except:
                self.task_field_update(task_id,
                                       result=enum.ActionResult.Failure)
            
            self.task_field_update(task_id, status=enum.TaskStatus.Complete)
            return
        elif task.action == enum.OrchestratorAction.VerifyNode:
            self.task_field_update(task_id,
                                   status=enum.TaskStatus.Running)

            driver = self.enabled_drivers['oob']

            if driver is None:
                self.task_field_update(task_id,
                        status=enum.TaskStatus.Errored,
                        result=enum.ActionResult.Failure)
                return

            site_design = self.get_effective_site(task_site,
                                                  change_id=design_id)

            node_filter = task.node_filter

            target_nodes = self.process_node_filter(node_filter, site_design)

            target_names = [x.get_name() for x in target_nodes]

            task_scope = {'site'        : task_site,
                          'node_names'  : target_names}

            driver_task = self.create_task(tasks.DriverTask,
                                           parent_task_id=task.get_id(),
                                           design_id=design_id,
                                           action=enum.OobAction.InterrogateNode,
                                           task_scope=task_scope)

            driver.execute_task(driver_task.get_id())

            driver_task = self.state_manager.get_task(driver_task.get_id())

            self.task_field_update(task_id,
                                   status=enum.TaskStatus.Complete,
                                   result=driver_task.get_result())
            return
        elif task.action == enum.OrchestratorAction.PrepareNode:
            self.task_field_update(task_id,
                                   status=enum.TaskStatus.Running)

            driver = self.enabled_drivers['oob']

            if driver is None:
                self.task_field_update(task_id,
                        status=enum.TaskStatus.Errored,
                        result=enum.ActionResult.Failure)
                return

            site_design = self.get_effective_site(task_site,
                                                  change_id=design_id)

            node_filter = task.node_filter

            target_nodes = self.process_node_filter(node_filter, site_design)

            target_names = [x.get_name() for x in target_nodes]

            task_scope = {'site'        : task_site,
                          'node_names'  : target_names}

            setboot_task = self.create_task(tasks.DriverTask,
                                           parent_task_id=task.get_id(),
                                           design_id=design_id,
                                           action=enum.OobAction.SetNodeBoot,
                                           task_scope=task_scope)

            driver.execute_task(setboot_task.get_id())

            setboot_task = self.state_manager.get_task(setboot_task.get_id())

            cycle_task = self.create_task(tasks.DriverTask,
                                           parent_task_id=task.get_id(),
                                           design_id=design_id,
                                           action=enum.OobAction.PowerCycleNode,
                                           task_scope=task_scope)
            driver.execute_task(cycle_task.get_id())

            cycle_task = self.state_manager.get_task(cycle_task.get_id())

            if (setboot_task.get_result() == enum.ActionResult.Success and
                cycle_task.get_result() == enum.ActionResult.Success):
                self.task_field_update(task_id,
                                       status=enum.TaskStatus.Complete,
                                       result=enum.ActionResult.Success)
            elif (setboot_task.get_result() == enum.ActionResult.Success or
                  cycle_task.get_result() == enum.ActionResult.Success):
                self.task_field_update(task_id,
                                       status=enum.TaskStatus.Complete,
                                       result=enum.ActionResult.PartialSuccess)
            else:
                self.task_field_update(task_id,
                                       status=enum.TaskStatus.Complete,
                                       result=enum.ActionResult.Failure)

            return
        else:
            raise errors.OrchestratorError("Action %s not supported"
                                     % (task.action))

    """
    terminate_task

    Mark a task for termination and optionally propagate the termination
    recursively to all subtasks
    """
    def terminate_task(self, task_id, propagate=True):
        task = self.state_manager.get_task(task_id)

        if task is None:
            raise errors.OrchestratorError("Could find task %s" % task_id)
        else:
            # Terminate initial task first to prevent add'l subtasks

            self.task_field_update(task_id, terminate=True)

            if propagate:
                # Get subtasks list
                subtasks = task.get_subtasks()
    
                for st in subtasks:
                    self.terminate_task(st, propagate=True)
            else:
                return True

    def create_task(self, task_class, **kwargs):
        parent_task_id = kwargs.get('parent_task_id', None)
        new_task = task_class(**kwargs)
        self.state_manager.post_task(new_task)

        if parent_task_id is not None:
            self.task_subtask_add(parent_task_id, new_task.get_id())

        return new_task

    # Lock a task and make all field updates, then unlock it
    def task_field_update(self, task_id, **kwargs):
        lock_id = self.state_manager.lock_task(task_id)
        if lock_id is not None:
            task = self.state_manager.get_task(task_id)
        
            for k,v in kwargs.items():
                setattr(task, k, v)

            self.state_manager.put_task(task, lock_id=lock_id)
            self.state_manager.unlock_task(task_id, lock_id)
            return True
        else:
            return False

    def task_subtask_add(self, task_id, subtask_id):
        lock_id = self.state_manager.lock_task(task_id)
        if lock_id is not None:
            task = self.state_manager.get_task(task_id)
            task.register_subtask(subtask_id)
            self.state_manager.put_task(task, lock_id=lock_id)
            self.state_manager.unlock_task(task_id, lock_id)
            return True
        else:
            return False

    """
    load_design_data - Pull all the defined models in statemgmt and assemble
    them into a representation of the site. Does not compute inheritance.
    Throws an exception if multiple Site models are found.

    param design_state - Instance of statemgmt.DesignState to load data from

    return a Site model populated with all components from the design state
    """

    def load_design_data(self, site_name, change_id=None):
        design_data = None

        if change_id is None or change_id == 0:
            try:
                design_data = self.state_manager.get_design_base()
            except DesignError(e):
                raise e
        else:
            design_data = self.state_manager.get_design_change(change_id)

        site = design_data.get_site(site_name)

        networks = design_data.get_networks()

        for n in networks:
            if n.site == site_name:
                site.networks.append(n)

        network_links = design_data.get_network_links()

        for l in network_links:
            if l.site == site_name:
                site.network_links.append(l)

        host_profiles = design_data.get_host_profiles()

        for p in host_profiles:
            if p.site == site_name:
                site.host_profiles.append(p)

        hardware_profiles = design_data.get_hardware_profiles()

        for p in hardware_profiles:
            if p.site == site_name:
                site.hardware_profiles.append(p)

        baremetal_nodes = design_data.get_baremetal_nodes()

        for n in baremetal_nodes:
            if n.site == site_name:
                site.baremetal_nodes.append(n)

        return site

    def compute_model_inheritance(self, site_root):
        
        # For now the only thing that really incorporates inheritance is
        # host profiles and baremetal nodes. So we'll just resolve it for
        # the baremetal nodes which recursively resolves it for host profiles
        # assigned to those nodes

        site_copy = deepcopy(site_root)

        for n in site_copy.baremetal_nodes:
            n.compile_applied_model(site_copy)
        
        return site_copy
    """
    compute_model_inheritance - given a fully populated Site model,
    compute the effecitve design by applying inheritance and references

    return a Site model reflecting the effective design for the site
    """

    def get_described_site(self, site_name, change_id=None):
        site_design = None

        if site_name is None:
            raise errors.OrchestratorError("Cannot source design for site None")

        site_design = self.load_design_data(site_name, change_id=change_id)
        
        return site_design

    def get_effective_site(self, site_name, change_id=None):
        site_design = self.get_described_site(site_name, change_id=change_id)

        site_model = self.compute_model_inheritance(site_design)

        return site_model

    def process_node_filter(self, node_filter, site_design):
        target_nodes = site_design.baremetal_nodes

        if node_filter is None:
            return target_nodes
            
        node_names = node_filter.get('node_names', [])
        node_racks = node_filter.get('rack_names', [])
        node_tags = node_filter.get('node_tags', [])

        if len(node_names) > 0:
            target_nodes = [x
                            for x in target_nodes
                            if x.get_name() in node_names]

        if len(node_racks) > 0:
            target_nodes = [x
                            for x in target_nodes
                            if x.get_rack() in node_racks]

        if len(node_tags) > 0:
            target_nodes = [x
                            for x in target_nodes
                            for t in node_tags
                            if x.has_tag(t)]

        return target_nodes


