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
"""Workflow orchestrator for Drydock tasks."""

import time
import importlib
import logging
import uuid
import ulid2
import concurrent.futures
import os

import drydock_provisioner.config as config
import drydock_provisioner.objects as objects
import drydock_provisioner.error as errors
import drydock_provisioner.objects.fields as hd_fields

from .actions.orchestrator import Noop
from .actions.orchestrator import ValidateDesign
from .actions.orchestrator import VerifySite
from .actions.orchestrator import PrepareSite
from .actions.orchestrator import VerifyNodes
from .actions.orchestrator import PrepareNodes
from .actions.orchestrator import DeployNodes
from .actions.orchestrator import RelabelNodes
from .actions.orchestrator import DestroyNodes
from .validations.validator import Validator


class Orchestrator(object):
    """Defines functionality for task execution workflow."""

    def __init__(self, enabled_drivers=None, state_manager=None,
                 ingester=None):
        """Initialize the orchestrator. A single instance should be executing at a time.

        :param enabled_drivers: a dictionary of drivers to enable for executing downstream tasks
        :param state_manager: the instance of statemgr.state.DrydockState to use for accessign app state
        :param ingester: instance of ingester.Ingester used to process design documents
        """
        self.orch_id = uuid.uuid4()

        self.stop_flag = False

        self.enabled_drivers = {}

        self.state_manager = state_manager
        self.ingester = ingester

        if self.state_manager is None or self.ingester is None:
            raise errors.OrchestratorError(
                "Orchestrator requires instantiated state manager and ingester."
            )

        self.logger = logging.getLogger('drydock.orchestrator')

        if enabled_drivers is not None:
            oob_drivers = enabled_drivers.oob_driver

            # This is because oslo_config changes the option value
            # for multiopt depending on if multiple values are actually defined

            for d in oob_drivers:
                self.logger.info("Enabling OOB driver %s" % d)
                if d is not None:
                    m, c = d.rsplit('.', 1)
                    oob_driver_class = \
                        getattr(importlib.import_module(m), c, None)
                    if oob_driver_class is not None:
                        if self.enabled_drivers.get('oob', None) is None:
                            self.enabled_drivers['oob'] = []
                        self.enabled_drivers['oob'].append(
                            oob_driver_class(
                                state_manager=state_manager,
                                orchestrator=self))

            node_driver_name = enabled_drivers.node_driver
            if node_driver_name is not None:
                m, c = node_driver_name.rsplit('.', 1)
                node_driver_class = \
                    getattr(importlib.import_module(m), c, None)
                if node_driver_class is not None:
                    self.enabled_drivers['node'] = node_driver_class(
                        state_manager=state_manager, orchestrator=self)

            network_driver_name = enabled_drivers.network_driver
            if network_driver_name is not None:
                m, c = network_driver_name.rsplit('.', 1)
                network_driver_class = getattr(
                    importlib.import_module(m), c, None)
                if network_driver_class is not None:
                    self.enabled_drivers['network'] = network_driver_class(
                        state_manager=state_manager, orchestrator=self)

            kubernetes_driver_name = enabled_drivers.kubernetes_driver
            if kubernetes_driver_name is not None:
                m, c = kubernetes_driver_name.rsplit('.', 1)
                kubernetes_driver_class = getattr(
                    importlib.import_module(m), c, None)
                if kubernetes_driver_class is not None:
                    self.enabled_drivers[
                        'kubernetes'] = kubernetes_driver_class(
                            state_manager=state_manager, orchestrator=self)

    def watch_for_tasks(self):
        """Start polling the database watching for Queued tasks to execute."""
        orch_task_actions = {
            hd_fields.OrchestratorAction.Noop: Noop,
            hd_fields.OrchestratorAction.ValidateDesign: ValidateDesign,
            hd_fields.OrchestratorAction.VerifySite: VerifySite,
            hd_fields.OrchestratorAction.PrepareSite: PrepareSite,
            hd_fields.OrchestratorAction.VerifyNodes: VerifyNodes,
            hd_fields.OrchestratorAction.PrepareNodes: PrepareNodes,
            hd_fields.OrchestratorAction.DeployNodes: DeployNodes,
            hd_fields.OrchestratorAction.RelabelNodes: RelabelNodes,
            hd_fields.OrchestratorAction.DestroyNodes: DestroyNodes,
        }

        # Loop trying to claim status as the active orchestrator

        tp = concurrent.futures.ThreadPoolExecutor(max_workers=16)

        while True:
            if self.stop_flag:
                tp.shutdown()
                return
            claim = self.state_manager.claim_leadership(self.orch_id)

            if not claim:
                self.logger.info(
                    "Orchestrator %s denied leadership, sleeping to try again."
                    % str(self.orch_id))
                # TODO(sh8121att) Make this configurable
                time.sleep(config.config_mgr.conf.leadership_claim_interval)
            else:
                self.logger.info(
                    "Orchestrator %s successfully claimed leadership, polling for tasks."
                    % str(self.orch_id))

                # As active orchestrator, loop looking for queued tasks.
                task_future = None
                while True:
                    # TODO(sh8121att) Need a timeout here
                    if self.stop_flag:
                        tp.shutdown()
                        self.state_manager.abdicate_leadership(self.orch_id)
                        return
                    if task_future is not None:
                        if task_future.done():
                            self.logger.debug(
                                "Task execution complete, looking for the next task."
                            )
                            exc = task_future.exception()
                            if exc is not None:
                                self.logger.error(
                                    "Error in starting orchestrator action.",
                                    exc_info=exc)
                            task_future = None

                    if task_future is None:
                        next_task = self.state_manager.get_next_queued_task(
                            allowed_actions=list(orch_task_actions.keys()))

                        if next_task is not None:
                            self.logger.info(
                                "Found task %s queued, starting execution." %
                                str(next_task.get_id()))
                            if next_task.check_terminate():
                                self.logger.info(
                                    "Task %s marked for termination, skipping execution."
                                    % str(next_task.get_id()))
                                next_task.set_status(
                                    hd_fields.TaskStatus.Terminated)
                                next_task.save()
                                continue
                            action = orch_task_actions[next_task.action](
                                next_task, self, self.state_manager)
                            if action:
                                task_future = tp.submit(action.start)
                            else:
                                self.logger.warning(
                                    "Task %s has unsupported action %s, ending execution."
                                    % (str(next_task.get_id()),
                                       next_task.action))
                                next_task.add_status_msg(
                                    msg="Unsupported action %s." %
                                    next_task.action,
                                    error=True,
                                    ctx=str(next_task.get_id()),
                                    ctx_type='task')
                                next_task.failure()
                                next_task.set_status(
                                    hd_fields.TaskStatus.Complete)
                                next_task.save()
                        else:
                            self.logger.info(
                                "No task found, waiting to poll again.")

                    # TODO(sh8121att) Make this configurable
                    time.sleep(config.config_mgr.conf.poll_interval)
                    claim = self.state_manager.maintain_leadership(
                        self.orch_id)
                    if not claim:
                        self.logger.info(
                            "Orchestrator %s lost leadership, attempting to reclaim."
                            % str(self.orch_id))
                        break

    def stop_orchestrator(self):
        """Indicate this orchestrator instance should stop attempting to run."""
        self.stop_flag = True

    def terminate_task(self, task, propagate=True, terminated_by=None):
        """Mark a task for termination.

        Optionally propagate the termination recursively to all subtasks

        :param task: A objects.Task instance to terminate
        :param propagate: whether the termination should propagatge to subtasks
        """
        if task is None:
            raise errors.OrchestratorError(
                "Could find task %s" % str(task.get_id()))
        else:
            # Terminate initial task first to prevent add'l subtasks
            self.logger.debug("Terminating task %s." % str(task.get_id()))
            task.terminate_task(terminated_by=terminated_by)

            if propagate:
                # Get subtasks list
                subtasks = task.get_subtasks()

                for st_id in subtasks:
                    st = self.state_manager.get_task(st_id)
                    self.terminate_task(
                        st, propagate=True, terminated_by=terminated_by)

    def create_task(self, **kwargs):
        """Create a new task and persist it."""
        new_task = objects.Task(statemgr=self.state_manager, **kwargs)
        self.state_manager.post_task(new_task)

        return new_task

    def compute_model_inheritance(self, site_design, resolve_aliases=False):
        """Compute inheritance of the design model.

        Given a fully populated Site model, compute the effective
        design by applying inheritance and references
        """
        node_failed = []

        try:
            nodes = site_design.baremetal_nodes
            for n in nodes or []:
                try:
                    n.compile_applied_model(
                        site_design,
                        state_manager=self.state_manager,
                        resolve_aliases=resolve_aliases)
                except Exception as ex:
                    node_failed.append(n)
                    self.logger.debug(
                        "Failed to build applied model for node %s.", n.name, exc_info=ex)
            if node_failed:
                raise errors.DesignError(
                    "Failed to build applied model for %s" % ",".join(
                        [x.name for x in node_failed]))
        except AttributeError:
            self.logger.debug(
                "Model inheritance skipped, no node definitions in site design."
            )

        return

    def get_described_site(self, design_ref):
        """Ingest design data referenced by design_ref.

        Return a tuple of the processing status and the populated instance
        of SiteDesign

        :param design_ref: Supported URI referencing a design document
        """
        status, site_design = self.ingester.ingest_data(
            design_ref=design_ref, design_state=self.state_manager)

        return status, site_design

    def get_effective_site(self, design_ref, resolve_aliases=False):
        """Ingest design data and compile the effective model of the design.

        Return a tuple of the processing status and the populated instance
        of SiteDesign after computing the inheritance chain

        :param design_ref: Supported URI referencing a design document
        """
        status = None
        site_design = None
        val = Validator(self)
        try:
            status, site_design = self.get_described_site(design_ref)
            if status.status == hd_fields.ValidationResult.Success:
                self.compute_model_inheritance(
                    site_design, resolve_aliases=resolve_aliases)
                self.compute_bootaction_targets(site_design)
                self.render_route_domains(site_design)
                status = val.validate_design(site_design, result_status=status)
        except Exception as ex:
            if status is not None:
                status.add_status_msg(
                    "Error loading effective site: %s" % str(ex),
                    error=True,
                    ctx='NA',
                    ctx_type='NA')
                status.set_status(hd_fields.ActionResult.Failure)
            self.logger.error(
                "Error getting site definition: %s" % str(ex), exc_info=ex)

        return status, site_design

    def get_target_nodes(self, task, failures=False, successes=False):
        """Compute list of target nodes for given ``task``.
        If failures is true, then create a node_filter based on task result
        failures. If successes is true, then create a node_filter based on
        task result successes. If both are true, raise an exception. If neither
        are true, build the list from the task node_filter.

        :param task: instance of objects.Task
        :param failures: whether to build target list from previous task failures
        :param successes: whether to build target list from previous task successes
        """
        design_status, site_design = self.get_effective_site(task.design_ref)

        if design_status.status != hd_fields.ValidationResult.Success:
            raise errors.OrchestratorError(
                "Unable to render effective site design.")
        if failures and successes:
            raise errors.OrchestratorError(
                "Cannot specify both failures and successes.")

        if failures:
            if len(task.result.failures) == 0:
                return []
            nf = task.node_filter_from_failures()
        elif successes:
            if len(task.result.successes) == 0:
                return []
            nf = task.node_filter_from_sucessess()
        else:
            nf = task.node_filter

        node_list = self.process_node_filter(nf, site_design)
        return node_list

    def create_nodefilter_from_nodelist(self, node_list):
        """Create a node filter to match list of nodes.

        Returns a dictionary that will be properly processed by the orchestrator

        :param node_list: List of objects.BaremetalNode instances the filter should match
        """
        nf = dict()

        nf['filter_set_type'] = 'intersection'
        nf['filter_set'] = [
            dict(
                node_names=[x.get_id() for x in node_list],
                filter_type='union')
        ]

        return nf

    def compute_bootaction_targets(self, site_design):
        """Find target nodes for each bootaction in ``site_design``.

        Calculate the node_filter for each bootaction and save the list
        of target node names.

        :param site_design: an instance of objects.SiteDesign
        """
        if site_design.bootactions is None:
            return
        for ba in site_design.bootactions:
            nf = ba.node_filter
            target_nodes = self.process_node_filter(nf, site_design)
            if not target_nodes:
                ba.target_nodes = []
            else:
                ba.target_nodes = [x.get_id() for x in target_nodes]

    def process_node_filter(self, node_filter, site_design):
        try:
            target_nodes = site_design.baremetal_nodes
            if target_nodes is None:
                raise AttributeError()
        except AttributeError:
            self.logger.debug(
                "Invalid site design, no baremetal nodes in site_design.")
            return []

        if node_filter is None:
            return target_nodes

        if not isinstance(node_filter, dict) and not isinstance(
                node_filter, objects.NodeFilterSet):
            msg = "Invalid node_filter, must be a dictionary with keys 'filter_set_type' and 'filter_set'."
            self.logger.error(msg)
            raise errors.OrchestratorError(msg)

        result_sets = []

        if isinstance(node_filter, dict):
            for f in node_filter.get('filter_set', []):
                result_sets.append(self.process_filter(target_nodes, f))

            return self.join_filter_sets(
                node_filter.get('filter_set_type'), result_sets)

        elif isinstance(node_filter, objects.NodeFilterSet):
            for f in node_filter.filter_set:
                result_sets.append(self.process_filter(target_nodes, f))

            return self.join_filter_sets(node_filter.filter_set_type,
                                         result_sets)

    def join_filter_sets(self, filter_set_type, result_sets):
        if filter_set_type == 'union':
            return self.list_union(*result_sets)
        elif filter_set_type == 'intersection':
            return self.list_intersection(*result_sets)
        else:
            raise errors.OrchestratorError(
                "Unknown filter set type %s" % filter_set_type)

    def process_filter(self, node_set, filter_set):
        """Take a filter and apply it to the node_set.

        :param node_set: A full set of objects.BaremetalNode
        :param filter_set: A node filter describing filters to apply to the node set.
                           Either a dict or objects.NodeFilter
        """
        try:
            if isinstance(filter_set, dict):
                set_type = filter_set.get('filter_type', None)
                node_names = filter_set.get('node_names', [])
                node_tags = filter_set.get('node_tags', [])
                node_labels = filter_set.get('node_labels', {})
                rack_names = filter_set.get('rack_names', [])
                rack_labels = filter_set.get('rack_labels', {})
            elif isinstance(filter_set, objects.NodeFilter):
                set_type = filter_set.filter_type
                node_names = filter_set.node_names
                node_tags = filter_set.node_tags
                node_labels = filter_set.node_labels
                rack_names = filter_set.rack_names
                rack_labels = filter_set.rack_labels
            else:
                raise errors.OrchestratorError(
                    "Node filter must be a dictionary or a NodeFilter instance"
                )

            target_nodes = dict()

            if node_names:
                self.logger.debug("Filtering nodes based on node names.")
                target_nodes['node_names'] = [
                    x for x in node_set if x.get_name() in node_names
                ]

            if node_tags:
                self.logger.debug("Filtering nodes based on node tags.")
                target_nodes['node_tags'] = [
                    x for x in node_set for t in node_tags if x.has_tag(t)
                ]

            if rack_names:
                self.logger.debug("Filtering nodes based on rack names.")
                target_nodes['rack_names'] = [
                    x for x in node_set if x.get_rack() in rack_names
                ]

            if node_labels:
                self.logger.debug("Filtering nodes based on node labels.")
                target_nodes['node_labels'] = []
                for k, v in node_labels.items():
                    target_nodes['node_labels'].extend([
                        x for x in node_set
                        if getattr(x, 'owner_data', {}).get(k, None) == v
                    ])

            if rack_labels:
                self.logger.info(
                    "Rack label filtering not yet implemented, returning all nodes."
                )
                target_nodes['rack_labels'] = node_set

            if set_type == 'union':
                return self.list_union(
                    target_nodes.get('node_names', []),
                    target_nodes.get('node_tags', []),
                    target_nodes.get('rack_names', []),
                    target_nodes.get('node_labels', []))
            elif set_type == 'intersection':
                return self.list_intersection(
                    target_nodes.get('node_names', None),
                    target_nodes.get('node_tags', None),
                    target_nodes.get('rack_names', None),
                    target_nodes.get('node_labels', None))

        except Exception as ex:
            self.logger.error("Error processing node filter.", exc_info=ex)
            raise errors.OrchestratorError(
                "Error processing node filter: %s" % str(ex))

    def list_intersection(self, a, *rest):
        """Take the intersection of a with the intersection of all the rest.

        :param a: list of values
        :params rest: 0 or more lists of values
        """
        if len(rest) > 1:
            result = self.list_intersection(rest[0], *rest[1:])
        elif rest:
            result = rest[0]
        else:
            result = None

        if a is None:
            return result
        elif result is None:
            return a
        else:
            return list(set(a).intersection(set(result)))

    def list_union(self, *lists):
        """Return a unique-ified union of all the lists.

        :param lists: indefinite number of lists
        """
        results = set()
        if len(lists) > 1:
            for l in lists:
                results = results.union(set(l))
            return list(results)
        elif len(lists) == 1:
            return list(set(lists[0]))
        else:
            return None

    def create_bootaction_context(self, nodename, task):
        """Save a boot action context for ``nodename``

        Generate a identity key and persist the boot action context
        for nodename pointing at the top level task. Return the
        generated identity key as ``bytes``.

        :param nodename: Name of the node the bootaction context is targeted for
        :param task: The task instigating the ndoe deployment
        """
        design_status, site_design = self.get_effective_site(task.design_ref)

        if site_design.bootactions is None:
            return None

        identity_key = None

        self.logger.debug(
            "Creating boot action context for node %s" % nodename)

        for ba in site_design.bootactions:
            self.logger.debug(
                "Boot actions target nodes: %s" % ba.target_nodes)
            if nodename in ba.target_nodes:
                if identity_key is None:
                    identity_key = os.urandom(32)
                    self.state_manager.post_boot_action_context(
                        nodename, task.get_id(), identity_key)
                self.logger.debug(
                    "Adding boot action %s for node %s to the database." %
                    (ba.name, nodename))
                if ba.signaling:
                    init_status = hd_fields.ActionResult.Incomplete
                else:
                    init_status = hd_fields.ActionResult.Unreported
                    self.logger.debug(
                        "Boot action %s has disabled signaling, marking unreported."
                        % ba.name)
                action_id = ulid2.generate_binary_ulid()
                self.state_manager.post_boot_action(
                    nodename,
                    task.get_id(),
                    identity_key,
                    action_id,
                    ba.name,
                    action_status=init_status)
        return identity_key

    def find_node_package_lists(self, nodename, task):
        """Return all packages to be installed on ``nodename``

        :param nodename: The name of the node to retrieve packages for
        :param task: The task initiating this request
        """
        design_status, site_design = self.get_effective_site(task.design_ref)

        if site_design.bootactions is None:
            return None

        self.logger.debug(
            "Extracting package install list for node %s" % nodename)

        pkg_list = dict()

        for ba in site_design.bootactions:
            if nodename in ba.target_nodes:
                # NOTE(sh8121att) the ulid generation below
                # is throw away data as these assets are only used to
                # get a full list of packages to deploy
                assets = ba.render_assets(
                    nodename,
                    site_design,
                    ulid2.generate_binary_ulid(),
                    ulid2.generate_binary_ulid(),
                    task.design_ref,
                    type_filter=hd_fields.BootactionAssetType.PackageList)
                for a in assets:
                    pkg_list.update(a.package_list)

        return pkg_list

    def render_route_domains(self, site_design):
        """Update site_design with static routes for route domains.

        site_design will be updated in place with explicit static routes
        for all routedomain members

        :param site_design: a populated instance of objects.SiteDesign
        """
        self.logger.info("Rendering routes for network route domains.")
        if site_design.networks is not None:
            routedomains = dict()
            for n in site_design.networks:
                if n.routedomain is not None:
                    if n.routedomain not in routedomains:
                        self.logger.info("Adding routedomain %s to render map."
                                         % n.routedomain)
                        routedomains[n.routedomain] = list()
                    routedomains[n.routedomain].append(n)
            for rd, nl in routedomains.items():
                rd_cidrs = [n.cidr for n in nl]
                self.logger.debug("Target CIDRs for routedomain %s: %s" %
                                  (rd, ','.join(rd_cidrs)))
                for n in site_design.networks:
                    gw = None
                    metric = None
                    for r in n.routes:
                        if 'routedomain' in r and r.get('routedomain',
                                                        None) == rd:
                            gw = r.get('gateway')
                            metric = r.get('metric')
                            self.logger.debug(
                                "Use gateway %s for routedomain %s on network %s."
                                % (gw, rd, n.get_name()))
                            break
                    if gw is not None and metric is not None:
                        for cidr in rd_cidrs:
                            if cidr != n.cidr:
                                n.routes.append(
                                    dict(
                                        subnet=cidr, gateway=gw,
                                        metric=metric))
