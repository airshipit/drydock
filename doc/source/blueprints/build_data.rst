..
      Copyright 2017 AT&T Intellectual Property.
      All Rights Reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

==================
Drydock Build Data
==================

Some site data is not known before the deployment of physical nodes begins.
Currently there is no method to harvest and persist this data for later reporting
or usage downstream in the deployment process. This blueprint for adding Drydock
support for harvesting, persisting, and reporting this build-time data.

Overview
--------

Build data is any data that is unknown until a site deployment actually begins. It
can be harvested any time during the deployment and will be persisted so that it
is available via the Drydock API for reporting. Each data element collected will
also be associated with the Drydock task that initiated the harvesting. When
requesting the details of the task, a client can optionally request the build data
harvested by that task directly be attached. Each build data element will be
described by the following fields.

  * Date/time - Same type of data can be collected multiple times and archived.
  * Task - The Drydock Task ID that initiated the collection.
  * Node - The node on which the data is collected.
  * Generator - A description of what generated the data. If it was a command line tool,
    the full command line. If it was something else, then a solid description
    such as an API endpoint.
  * Format - The format that the collected data is being persisted as.

Post-collection, the build data will be accessible in two ways

  #. Using the new builddata endpoint under the /nodes/ resource. See below for details.
  #. By requesting the details for the initiating task from the ``/api/v1.0/tasks``
     resource and including the ``builddata=true`` parameter to the request.

Currently no pruning system is in place, but if storage is a concern that can be
added as a follow-on feature.

Data Schema
-----------

A new table ``build_data`` with the following columns. No keys.

  * ``task_id`` - 128-bit binary task ID of the Drydock task that collected the build data.
  * ``collected_date`` - The datestamp when the data was collected.
  * ``generator`` - Description of the command or source of the build data.
  * ``node_name`` - The node the data is collected from.
  * ``format`` - The MIME-type of the storage format of the persisted data.
  * ``data_element`` - The data collected serialized in the format.

Build Data API
--------------

A new API endpoint of ``/api/v1.0/nodes/{node}/builddata/`` will be added to the API
to retrieve the build data for a node. This endpoint will only support a ``GET`` request
and supports a single query parameter of ``latest`` which defaults to ``true``. If ``true``
then the response will contain only the most recent ``data_element`` for each ``generator``.
If the parameter is ``false`` then the response will contain an ordered sequence of all
``data_elements`` for each generator in a descending time series.

The existing ``/api/v1.0/tasks/{task_id}/`` endpoint will be updated to support a query
parameter of ``builddata`` that defaults to ``false``. If set to ``true``, the response
with the task details will include any build data collected during the execution of the
task.

Expected Use Cases
------------------

Device Aliases
~~~~~~~~~~~~~~

The first use case is collecting data from ``lshw`` to resolve device bus addresses
into operating system device names. This is done for supporting the device aliases
in the HardwareProfile.

Network Topology
~~~~~~~~~~~~~~~~

During node deployment, LLDP (link level discovery protocol) can be used to validate
the network topology. The LLDP output can be collected and audited against expected
switch configurations.

Burn In Performance
~~~~~~~~~~~~~~~~~~~

New hardware can run burn-in routines to collect performance and stability information
before production workloads are installed.
