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

from copy import deepcopy

import helm_drydock.drivers as drivers
import helm_drydock.objects.task as tasks
import helm_drydock.error as errors
import helm_drydock.objects.fields as hd_fields

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
        if task.action == hd_fields.OrchestratorAction.Noop:
            self.task_field_update(task_id,
                                   status=hd_fields.TaskStatus.Running)        

            driver_task = self.create_task(tasks.DriverTask,
                            design_id=0,
                            action=hd_fields.OrchestratorAction.Noop,
                            parent_task_id=task.get_id())

            driver = drivers.ProviderDriver(state_manager=self.state_manager,
                                            orchestrator=self)
            driver.execute_task(driver_task.get_id())
            driver_task = self.state_manager.get_task(driver_task.get_id())

            self.task_field_update(task_id, status=driver_task.get_status())
            
            return
        elif task.action == hd_fields.OrchestratorAction.ValidateDesign:
            self.task_field_update(task_id,
                                   status=hd_fields.TaskStatus.Running)
            try:
                site_design = self.get_effective_site(task_site,
                                                  change_id=design_id)
                self.task_field_update(task_id,
                                       result=hd_fields.ActionResult.Success)
            except:
                self.task_field_update(task_id,
                                       result=hd_fields.ActionResult.Failure)
            
            self.task_field_update(task_id, status=hd_fields.TaskStatus.Complete)
            return
        elif task.action == hd_fields.OrchestratorAction.VerifyNode:
            self.task_field_update(task_id,
                                   status=hd_fields.TaskStatus.Running)

            driver = self.enabled_drivers['oob']

            if driver is None:
                self.task_field_update(task_id,
                        status=hd_fields.TaskStatus.Errored,
                        result=hd_fields.ActionResult.Failure)
                return

            site_design = self.get_effective_site(design_id, task_site)

            node_filter = task.node_filter

            target_nodes = self.process_node_filter(node_filter, site_design)

            target_names = [x.get_name() for x in target_nodes]

            task_scope = {'site'        : task_site,
                          'node_names'  : target_names}

            driver_task = self.create_task(tasks.DriverTask,
                                           parent_task_id=task.get_id(),
                                           design_id=design_id,
                                           action=hd_fields.OrchestratorAction.InterrogateNode,
                                           task_scope=task_scope)

            driver.execute_task(driver_task.get_id())

            driver_task = self.state_manager.get_task(driver_task.get_id())

            self.task_field_update(task_id,
                                   status=hd_fields.TaskStatus.Complete,
                                   result=driver_task.get_result())
            return
        elif task.action == hd_fields.OrchestratorAction.PrepareNode:
            self.task_field_update(task_id,
                                   status=hd_fields.TaskStatus.Running)

            driver = self.enabled_drivers['oob']

            if driver is None:
                self.task_field_update(task_id,
                        status=hd_fields.TaskStatus.Errored,
                        result=hd_fields.ActionResult.Failure)
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
                                           action=hd_fields.OrchestratorAction.SetNodeBoot,
                                           task_scope=task_scope)

            driver.execute_task(setboot_task.get_id())

            setboot_task = self.state_manager.get_task(setboot_task.get_id())

            cycle_task = self.create_task(tasks.DriverTask,
                                           parent_task_id=task.get_id(),
                                           design_id=design_id,
                                           action=hd_fields.OrchestratorAction.PowerCycleNode,
                                           task_scope=task_scope)
            driver.execute_task(cycle_task.get_id())

            cycle_task = self.state_manager.get_task(cycle_task.get_id())

            if (setboot_task.get_result() == hd_fields.ActionResult.Success and
                cycle_task.get_result() == hd_fields.ActionResult.Success):
                self.task_field_update(task_id,
                                       status=hd_fields.TaskStatus.Complete,
                                       result=hd_fields.ActionResult.Success)
            elif (setboot_task.get_result() == hd_fields.ActionResult.Success or
                  cycle_task.get_result() == hd_fields.ActionResult.Success):
                self.task_field_update(task_id,
                                       status=hd_fields.TaskStatus.Complete,
                                       result=hd_fields.ActionResult.PartialSuccess)
            else:
                self.task_field_update(task_id,
                                       status=hd_fields.TaskStatus.Complete,
                                       result=hd_fields.ActionResult.Failure)

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

    def compute_model_inheritance(self, site_design):
        
        # For now the only thing that really incorporates inheritance is
        # host profiles and baremetal nodes. So we'll just resolve it for
        # the baremetal nodes which recursively resolves it for host profiles
        # assigned to those nodes

        for n in site_design.baremetal_nodes:
            n.compile_applied_model(site_design)
        
        return
    """
    compute_model_inheritance - given a fully populated Site model,
    compute the effecitve design by applying inheritance and references

    return a Site model reflecting the effective design for the site
    """

    def get_described_site(self, design_id, site_name):
        site_design = None

        if site_name is None:
            raise errors.OrchestratorError("Cannot source design for site None")

        site_design = self.state_manager.get_design(design_id)
        
        return site_design

    def get_effective_site(self, design_id, site_name):
        site_design = self.get_described_site(design_id, site_name)

        self.compute_model_inheritance(site_design)

        return site_design

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
