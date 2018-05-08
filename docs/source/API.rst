.. _api:

===========
Drydock API
===========

The Drydock API is a RESTful interface used for accessing the services provided by Drydock.
All endpoints are located under ``/api/<version>/``.

Secured endpoints require Keystone authentication and proper role assignment for authorization

v1.0
====

.. _tasks-api:

tasks API
---------

The Tasks API is used for creating and listing asynchronous tasks to be executed by the
Drydock orchestrator. See :ref:`task` for details on creating tasks and field information.

nodes API
---------

GET nodes
^^^^^^^^^

The Nodes API will provide a report of current nodes as known by the node provisioner
and their status with a few hardware details.

GET nodes/hostname/builddata
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get all the build data record for node ``hostname``. The response will be a list of
objects in the below form.::

    {
      "node_name": "hostname",
      "generator": "description of how data was generated",
      "collected_date": ios8601 UTC datestamp,
      "task_id": "UUID of task initiating collection",
      "data_format": "MIME-type of data_element",
      "data_element": "Collected data"
    }

If the query parameter ``latest`` is passed with a value of ``true``, then only
the most recently collected data for each ``generator`` will be included in the
response.

nodefilter API
--------------

POST nodefilter
^^^^^^^^^^^^^^^

The Nodes API will provide a list of node names based on design_ref.  This API
requires design_ref in the POST body with an optional node_filter to return the node
names.

bootdata
--------

The boot data API is used by deploying nodes to load the appropriate boot actions to be
instantiated on the node. It uses alternative authentication and is not accessible with
Keystone.

GET bootdata/hostname/files
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Returns a gzipped tar file containing all the file-type boot action data assets for
the node ``hostname`` with appropriate permissions set in the tar-file.

GET bootdata/hostname/units
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Returns a gzipped tar file containing all the unit-type boot action data assets for
the node ``hostname`` with appropriate permissions set in the tar-file.

.. _bootaction-api:

bootaction API
--------------

The boot action API is used by deploying nodes to report status and results of running
boot actions. It expects a JSON-formatted body with the top-level entity of an object.
The status of the boot action and any detail status messages for it will be added to the
DeployNode task that prompted the node deployment the boot action is associated with.

POST bootaction/bootaction-id
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Example::

    {
        "status": "Failure"|"Success",
        "details": [
            {
                "message": "Boot action status message",
                "error": true|false,
                ...
            },
            ...
        ]
    }

POSTs to this endpoint can be made repeatedly omitting the ``status`` field and simply
adding one or more detail status messages. The ``message`` and ``error`` fields are required and
the ``context``, ``context_type`` and ``ts`` fields are reserved. Otherwise the message
object in details can be extended with additional fields as needed.

Once a POST containing the ``status`` field is made to a bootaction-id, that bootaction-id can no
longer be updated with status changes nor additional detailed status messages.

validatedesign API
------------------

The Validatedesign API is used for validating documents before they will be used by Drydock. See
:ref:`validatedesign` for more details on validating documents.
