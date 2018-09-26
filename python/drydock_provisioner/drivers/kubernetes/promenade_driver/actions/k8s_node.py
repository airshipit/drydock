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
"""Task driver for Promenade interaction."""

import logging

import drydock_provisioner.error as errors
import drydock_provisioner.config as config
import drydock_provisioner.objects.fields as hd_fields
from drydock_provisioner.orchestrator.actions.orchestrator import BaseAction


class PromenadeAction(BaseAction):
    def __init__(self, *args, prom_client=None):
        super().__init__(*args)

        self.promenade_client = prom_client

        self.logger = logging.getLogger(
            config.config_mgr.conf.logging.kubernetesdriver_logger_name)


class RelabelNode(PromenadeAction):
    """Action to relabel kubernetes node."""

    def start(self):

        self.task.set_status(hd_fields.TaskStatus.Running)
        self.task.save()

        try:
            site_design = self._load_site_design()
        except errors.OrchestratorError:
            self.task.add_status_msg(
                msg="Error loading site design.",
                error=True,
                ctx='NA',
                ctx_type='NA')
            self.task.set_status(hd_fields.TaskStatus.Complete)
            self.task.failure()
            self.task.save()
            return

        nodes = self.orchestrator.process_node_filter(self.task.node_filter,
                                                      site_design)

        for n in nodes:
            # Relabel node through Promenade
            try:
                self.logger.info(
                    "Relabeling node %s with node label data." % n.name)

                labels_dict = n.get_node_labels()
                msg = "Set labels %s for node %s" % (str(labels_dict), n.name)

                self.task.add_status_msg(
                    msg=msg, error=False, ctx=n.name, ctx_type='node')

                # Call promenade to invoke relabel node
                self.promenade_client.relabel_node(n.get_id(), labels_dict)
                self.task.success(focus=n.get_id())
            except Exception as ex:
                msg = "Error relabeling node %s with label data" % n.name
                self.logger.warning(msg + ": " + str(ex))
                self.task.failure(focus=n.get_id())
                self.task.add_status_msg(
                    msg=msg, error=True, ctx=n.name, ctx_type='node')
                continue

        self.task.set_status(hd_fields.TaskStatus.Complete)
        self.task.save()

        return
