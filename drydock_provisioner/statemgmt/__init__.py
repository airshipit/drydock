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
from copy import deepcopy
from datetime import datetime
from datetime import timezone
from threading import Lock

import uuid

import drydock_provisioner.objects as objects
import drydock_provisioner.objects.task as tasks

from drydock_provisioner.error import DesignError, StateError

class DesignState(object):

    def __init__(self):
        self.designs = {}
        self.designs_lock = Lock()

        self.promenade = {}
        self.promenade_lock = Lock()

        self.builds = []
        self.builds_lock = Lock()

        self.tasks = []
        self.tasks_lock = Lock()

        self.bootdata = {}
        self.bootdata_lock = Lock()

        return

    # TODO Need to lock a design base or change once implementation
    # has started
    def get_design(self, design_id):
        if design_id not in self.designs.keys():

            raise DesignError("Design ID %s not found" % (design_id))

        return objects.SiteDesign.obj_from_primitive(self.designs[design_id])

    def post_design(self, site_design):
        if site_design is not None:
            my_lock = self.designs_lock.acquire(blocking=True,
                timeout=10)
            if my_lock:
                design_id = site_design.id
                if design_id not in self.designs.keys():
                    self.designs[design_id] = site_design.obj_to_primitive()
                else:
                    self.designs_lock.release()
                    raise StateError("Design ID %s already exists" % design_id)
                self.designs_lock.release()
                return True
            raise StateError("Could not acquire lock")
        else:
            raise DesignError("Design change must be a SiteDesign instance")

    def put_design(self, site_design):
        if site_design is not None:
            my_lock = self.designs_lock.acquire(blocking=True,
                timeout=10)
            if my_lock:
                design_id = site_design.id
                if design_id not in self.designs.keys():
                    self.designs_lock.release()
                    raise StateError("Design ID %s does not exist" % design_id)
                else:
                    self.designs[design_id] = site_design.obj_to_primitive()
                    self.designs_lock.release()
                    return True
            raise StateError("Could not acquire lock")
        else:
            raise DesignError("Design base must be a SiteDesign instance")

    def get_current_build(self):
        latest_stamp = 0
        current_build = None

        for b in self.builds:
            if b.build_id > latest_stamp:
                latest_stamp = b.build_id
                current_build = b

        return deepcopy(current_build)

    def get_build(self, build_id):
        for b in self.builds:
            if b.build_id == build_id:
                return b

        return None

    def post_build(self, site_build):
        if site_build is not None and isinstance(site_build, SiteBuild):
            my_lock = self.builds_lock.acquire(block=True, timeout=10)
            if my_lock:
                exists = [b for b in self.builds
                          if b.build_id == site_build.build_id]

                if len(exists) > 0:
                    self.builds_lock.release()
                    raise DesignError("Already a site build with ID %s" %
                        (str(site_build.build_id)))
                self.builds.append(deepcopy(site_build))
                self.builds_lock.release()
                return True
            raise StateError("Could not acquire lock")
        else:
            raise DesignError("Design change must be a SiteDesign instance")

    def put_build(self, site_build):
        if site_build is not None and isinstance(site_build, SiteBuild):
            my_lock = self.builds_lock.acquire(block=True, timeout=10)
            if my_lock:
                buildid = site_build.buildid
                for b in self.builds:
                    if b.buildid == buildid:
                        b.merge_updates(site_build)
                        self.builds_lock.release()
                        return True
                self.builds_lock.release()
                return False
            raise StateError("Could not acquire lock")
        else:
            raise DesignError("Design change must be a SiteDesign instance")

    def get_task(self, task_id):
        for t in self.tasks:
            if t.get_id() == task_id or str(t.get_id()) == task_id:
                return deepcopy(t)
        return None

    def post_task(self, task):
        if task is not None and isinstance(task, tasks.Task):
            my_lock = self.tasks_lock.acquire(blocking=True, timeout=10)
            if my_lock:
                task_id = task.get_id()
                matching_tasks = [t for t in self.tasks
                                  if t.get_id() == task_id]
                if len(matching_tasks) > 0:
                    self.tasks_lock.release()
                    raise StateError("Task %s already created" % task_id)

                self.tasks.append(deepcopy(task))
                self.tasks_lock.release()
                return True
            else:
                raise StateError("Could not acquire lock")
        else:
            raise StateError("Task is not the correct type")

    def put_task(self, task, lock_id=None):
        if task is not None and isinstance(task, tasks.Task):
            my_lock = self.tasks_lock.acquire(blocking=True, timeout=10)
            if my_lock:
                task_id = task.get_id()
                t = self.get_task(task_id)
                if t.lock_id is not None and t.lock_id != lock_id:
                    self.tasks_lock.release()
                    raise StateError("Task locked for updates")

                task.lock_id = lock_id
                self.tasks = [i
                              if i.get_id() != task_id
                              else deepcopy(task)
                              for i in self.tasks]

                self.tasks_lock.release()
                return True
            else:
                raise StateError("Could not acquire lock")
        else:
            raise StateError("Task is not the correct type")

    def lock_task(self, task_id):
        my_lock = self.tasks_lock.acquire(blocking=True, timeout=10)
        if my_lock:
            lock_id = uuid.uuid4()
            for t in self.tasks:
                if t.get_id() == task_id and t.lock_id is None:
                    t.lock_id = lock_id
                    self.tasks_lock.release()
                    return lock_id
            self.tasks_lock.release()
            return None
        else:
            raise StateError("Could not acquire lock")

    def unlock_task(self, task_id, lock_id):
        my_lock = self.tasks_lock.acquire(blocking=True, timeout=10)
        if my_lock:
            for t in self.tasks:
                if t.get_id() == task_id and t.lock_id == lock_id:
                    t.lock_id = None
                    self.tasks_lock.release()
                    return True
            self.tasks_lock.release()
            return False
        else:
            raise StateError("Could not acquire lock")

    def post_promenade_part(self, part):
        my_lock = self.promenade_lock.acquire(blocking=True, timeout=10)
        if my_lock:
            if self.promenade.get(part.target, None) is not None:
                self.promenade[part.target].append(part.obj_to_primitive())
            else:
                self.promenade[part.target] = [part.obj_to_primitive()]
            self.promenade_lock.release()
            return None
        else:
            raise StateError("Could not acquire lock")        
    
    def get_promenade_parts(self, target):
        parts = self.promenade.get(target, None)

        if parts is not None:
            return [objects.PromenadeConfig.obj_from_primitive(p) for p in parts]
        else:
            # Return an empty list just to play nice with extend
            return []

    def set_bootdata_key(self, hostname, design_id, data_key):
        my_lock = self.bootdata_lock.acquire(blocking=True, timeout=10)
        if my_lock:
            self.bootdata[hostname] = {'design_id': design_id, 'key': data_key}
            self.bootdata_lock.release()
            return None
        else:
            raise StateError("Could not acquire lock")

    def get_bootdata_key(self, hostname):
        return self.bootdata.get(hostname, None)
