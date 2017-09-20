======================================
Statemgmt - Persisted State Management
======================================

Statemgmt is the interface to the persistence store for managing task data and build
data for nodes. Currently Drydock only supports a Postgres database backend. This module
will also resolve design references to retrieve the design data from the specified
external reference

Tables
======

tasks
-----

The ``tasks`` table stores all tasks - Queued, Running, Complete. The orchestrator
will source all tasks from this table.

result_message
--------------

The ``result_message`` table is used for storing all of the detailed messages produced
while executing a task. These are sequenced and attached to the task when serializing
a task.

build_data
----------

The ``build_data`` table is used for storing the build history and details of nodes
in the site. When a node is destroyed and redeployed, the history will persist showing
that transition.

active_instance
---------------

``active_instance`` is a small semaphore table so that multiple instances of Drydock
can organize and ensure only a single orchestrator instance is executing tasks.

Design References
=================

Rather than Drydock storing design data internally, it instead supports a URI-based
reference scheme. The URI should specify the driver and transport details required to
source the data. Once the data is retrieved by the driver, it will be sent to an
ingester for translation into the internal Drydock object model.

Example design reference URI: ``deckhand+https://deckhand-api.ucp.svc.cluster.local:8443/e50b4d74-9fab-11e7-b7cc-080027ef795a``

Current Drivers
---------------

Drydock currently can resolve design references to simple ``file://`` and ``http://`` endpoints
with no authentication required. Local files must provide absolute paths.

Planned Drivers
---------------

There is planned support for ``https://`` and ``deckhand+https://`` endpoints.
